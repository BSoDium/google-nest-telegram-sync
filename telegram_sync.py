from nest_api import NestDoorbellDevice
from tools import logger, get_video_metadata
from models import CameraEvent

from io import BytesIO
import pytz
import datetime
import json
import os

from telegram import Bot, InputMediaVideo


class TelegramEventsSync(object):

    TELEGRAM_TIME_FORMAT = '%H:%M:%S %d/%m/%Y'
    STATE_FILE_PATH = os.getenv("STATE_FILE_PATH", "/data/sent_events.json")

    def __init__(self, telegram_bot_token, telegram_channel_id, timezone, nest_camera_devices) -> None:
        self._telegram_bot = Bot(token=telegram_bot_token)
        self._telegram_channel_id = telegram_channel_id
        self._timezone = timezone
        self._nest_camera_devices = nest_camera_devices

        # Dict: event_id -> {"message_id": int, "duration_seconds": float, "timestamp": str}
        self._sent_events = self._load_state()

    def _load_state(self) -> dict:
        """Load persisted dedup state from JSON file, pruning entries older than 3 hours."""
        if not os.path.exists(self.STATE_FILE_PATH):
            logger.info(
                f"No state file found at {self.STATE_FILE_PATH}, starting fresh")
            return {}
        try:
            with open(self.STATE_FILE_PATH, "r") as f:
                state = json.load(f)
            cutoff = (datetime.datetime.now(datetime.timezone.utc) -
                      datetime.timedelta(hours=3)).isoformat()
            pruned = {k: v for k, v in state.items() if v.get(
                "timestamp", "") > cutoff}
            removed = len(state) - len(pruned)
            if removed:
                logger.info(
                    f"Pruned {removed} expired entries from state file")
            logger.info(
                f"Loaded {len(pruned)} tracked events from {self.STATE_FILE_PATH}")
            return pruned
        except Exception as e:
            logger.warning(f"Failed to load state file: {e}, starting fresh")
            return {}

    def _save_state(self):
        """Persist dedup state to JSON file."""
        try:
            os.makedirs(os.path.dirname(self.STATE_FILE_PATH), exist_ok=True)
            with open(self.STATE_FILE_PATH, "w") as f:
                json.dump(self._sent_events, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state file: {e}")

    async def sync_single_nest_camera(self, nest_device: NestDoorbellDevice):

        logger.info(f"Syncing: {nest_device.device_id}")
        all_recent_camera_events: list[CameraEvent] = nest_device.get_events(
            end_time=pytz.timezone(self._timezone).localize(
                datetime.datetime.now()),
            # Maximum saved events is 3 hours (free plan)
            duration_minutes=3 * 60
        )

        logger.info(
            f"[{nest_device.device_id}] Received {len(all_recent_camera_events)} camera events")

        sent_new = 0
        edited = 0
        skipped = 0
        skipped_metadata = 0

        for camera_event_obj in all_recent_camera_events:
            event_id = camera_event_obj.event_id
            new_duration = camera_event_obj.duration_seconds
            existing = self._sent_events.get(event_id)

            if existing and new_duration <= existing["duration_seconds"]:
                # Same or shorter duration — nothing to do
                skipped += 1
                continue

            # Either a new event or an existing one with a longer duration
            is_update = existing is not None

            logger.debug(
                f"{'Updating' if is_update else 'Downloading'} camera event: {camera_event_obj}")
            video_data = nest_device.download_camera_event(camera_event_obj)
            video_io = BytesIO(video_data)

            metadata = get_video_metadata(video_data)
            logger.debug(f"Video metadata: {metadata}")

            # Guard against unreliable metadata — skip video, send text alert
            if not metadata["reliable"]:
                event_local_time = camera_event_obj.start_time.astimezone(
                    pytz.timezone(self._timezone))
                warning_msg = (
                    f"⚠️ {nest_device.device_name} - {event_local_time.strftime(self.TELEGRAM_TIME_FORMAT)}: "
                    f"Video skipped (unreliable metadata — dimensions could not be determined)"
                )
                logger.warning(warning_msg)
                if not is_update:
                    # Only send a text alert for new events, not for updates of already-sent ones
                    await self._telegram_bot.send_message(
                        chat_id=self._telegram_channel_id,
                        text=warning_msg,
                        disable_notification=True,
                    )
                skipped_metadata += 1
                continue

            event_local_time = camera_event_obj.start_time.astimezone(
                pytz.timezone(self._timezone))
            caption = f"{nest_device.device_name} - {event_local_time.strftime(self.TELEGRAM_TIME_FORMAT)}"

            if is_update:
                # Edit existing message with updated (longer) video
                try:
                    video_media = InputMediaVideo(
                        media=video_io,
                        caption=caption,
                        width=metadata["width"],
                        height=metadata["height"],
                        duration=metadata["duration"],
                    )
                    await self._telegram_bot.edit_message_media(
                        media=video_media,
                        chat_id=self._telegram_channel_id,
                        message_id=existing["message_id"],
                    )
                    self._sent_events[event_id] = {
                        "message_id": existing["message_id"],
                        "duration_seconds": new_duration,
                        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    }
                    self._save_state()
                    edited += 1
                    logger.info(f"Edited message {existing['message_id']} with updated clip "
                                f"(duration {existing['duration_seconds']}s -> {new_duration}s)")
                except Exception as e:
                    logger.warning(
                        f"Failed to edit message {existing['message_id']}: {e}")
            else:
                # Send new video
                msg = await self._telegram_bot.send_video(
                    chat_id=self._telegram_channel_id,
                    video=video_io,
                    caption=caption,
                    width=metadata["width"],
                    height=metadata["height"],
                    duration=metadata["duration"],
                    disable_notification=True,
                )
                self._sent_events[event_id] = {
                    "message_id": msg.message_id,
                    "duration_seconds": new_duration,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
                self._save_state()
                sent_new += 1
                logger.debug("Sent clip successfully")

        logger.info(
            f"[{nest_device.device_id}] Sent new: {sent_new}, edited: {edited}, "
            f"skipped (already sent): {skipped}, skipped (bad metadata): {skipped_metadata}"
        )

    async def sync(self):
        logger.info("Syncing all camera devices")
        for nest_device in self._nest_camera_devices:
            await self.sync_single_nest_camera(nest_device)
