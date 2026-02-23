from nest_api import NestDoorbellDevice
from tools import logger, get_video_metadata
from models import CameraEvent

from io import BytesIO
import pytz
import datetime

from telegram import Bot, InputMediaVideo

class TelegramEventsSync(object):
    
    TELEGRAM_TIME_FORMAT = '%H:%M:%S %d/%m/%Y'
    
    def __init__(self, telegram_bot_token, telegram_channel_id, timezone, nest_camera_devices) -> None:
        self._telegram_bot = Bot(token=telegram_bot_token)
        self._telegram_channel_id = telegram_channel_id
        self._timezone = timezone
        self._nest_camera_devices = nest_camera_devices
 
        self._recent_events = set()

    async def sync_single_nest_camera(self, nest_device : NestDoorbellDevice):
    
        logger.info(f"Syncing: {nest_device.device_id}")
        all_recent_camera_events : list[CameraEvent] = nest_device.get_events(
            end_time = pytz.timezone(self._timezone).localize(datetime.datetime.now()),
            duration_minutes=3 * 60 # Maximum saved events is 3 hours (free plan)
        )

        logger.info(f"[{nest_device.device_id}] Received {len(all_recent_camera_events)} camera events")

        skipped = 0
        for camera_event_obj in all_recent_camera_events:
            if camera_event_obj.event_id in self._recent_events:
                logger.info(f"CameraEvent ({camera_event_obj}) already sent, skipping..")
                skipped += 1
                continue

            logger.debug(f"Downloading camera event: {camera_event_obj}")
            video_data = nest_device.download_camera_event(camera_event_obj)
            video_io = BytesIO(video_data)

            metadata = get_video_metadata(video_data)
            logger.debug(f"Video metadata: {metadata}")

            event_local_time = camera_event_obj.start_time.astimezone(pytz.timezone(self._timezone))
            video_media = InputMediaVideo(
                media=video_io, 
                caption=f"{nest_device.device_name} - {event_local_time.strftime(self.TELEGRAM_TIME_FORMAT)}",
                width=metadata["width"],
                height=metadata["height"],
                duration=metadata["duration"],
            )
            
            await self._telegram_bot.send_media_group(
                chat_id=self._telegram_channel_id, 
                media=[video_media],
                disable_notification=True,
            )
            logger.debug("Sent clip successfully")

            self._recent_events.add(camera_event_obj.event_id)

        downloaded_and_sent = len(all_recent_camera_events) - skipped
        logger.info(f"[{nest_device.device_id}] Downloaded and sent: {downloaded_and_sent}, skipped (already sent): {skipped}")

    async def sync(self):
        logger.info("Syncing all camera devices")
        for nest_device in self._nest_camera_devices:
            await self.sync_single_nest_camera(nest_device)
