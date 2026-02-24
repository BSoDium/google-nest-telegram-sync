import logging
import subprocess
import json
import tempfile
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_video_metadata(video_bytes: bytes) -> dict:
    """Extract width, height, and duration from MP4 video bytes using ffprobe.
    
    Returns a dict with keys:
      - 'width': display width in pixels (SAR/rotation-corrected)
      - 'height': display height in pixels (SAR/rotation-corrected)
      - 'duration': duration in seconds
      - 'reliable': True if dimensions were confidently determined
    """
    width, height, duration = None, None, None
    reliable = False
    tmp_path = None
    try:
        # Write bytes to a temp file for ffprobe to read
        fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
        with os.fdopen(fd, "wb") as f:
            f.write(video_bytes)

        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_streams", "-show_format",
                tmp_path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            probe = json.loads(result.stdout)
            for stream in probe.get("streams", []):
                if stream.get("codec_type") == "video":
                    width = int(stream["width"])
                    height = int(stream["height"])

                    # Account for non-square pixels (Sample Aspect Ratio)
                    sar = stream.get("sample_aspect_ratio", "1:1")
                    if sar and sar != "1:1" and ":" in sar:
                        try:
                            sar_num, sar_den = map(int, sar.split(":"))
                            if sar_num > 0 and sar_den > 0:
                                width = width * sar_num // sar_den
                                logger.info(f"Applied SAR correction ({sar}): display width adjusted to {width}")
                        except (ValueError, ZeroDivisionError):
                            logger.warning(f"Could not parse SAR value: {sar}")

                    # Account for rotation metadata (common on doorbell cameras)
                    rotation = 0
                    # Check tags.rotate (older ffprobe)
                    tags = stream.get("tags", {})
                    if "rotate" in tags:
                        try:
                            rotation = int(tags["rotate"])
                        except (ValueError, TypeError):
                            pass
                    # Check side_data_list for displaymatrix rotation (newer ffprobe)
                    if rotation == 0:
                        for side_data in stream.get("side_data_list", []):
                            if "rotation" in side_data:
                                try:
                                    rotation = int(side_data["rotation"])
                                except (ValueError, TypeError):
                                    pass
                                break

                    if abs(rotation) in (90, 270):
                        width, height = height, width
                        logger.info(f"Applied rotation correction ({rotation}°): swapped to {width}x{height}")

                    reliable = True
                    break

            fmt = probe.get("format", {})
            if "duration" in fmt:
                duration = int(float(fmt["duration"]))
        else:
            logger.warning(f"ffprobe returned non-zero exit code: {result.returncode}, stderr: {result.stderr[:200]}")
    except Exception as e:
        logger.warning(f"Failed to extract video metadata: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {"width": width, "height": height, "duration": duration, "reliable": reliable}
