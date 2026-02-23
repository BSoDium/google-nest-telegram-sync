import logging
import subprocess
import json
import tempfile
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_video_metadata(video_bytes: bytes) -> dict:
    """Extract width, height, and duration from MP4 video bytes using ffprobe.
    
    Returns a dict with keys 'width', 'height', and 'duration' (in seconds).
    Values may be None if extraction fails.
    """
    width, height, duration = None, None, None
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
                    break
            fmt = probe.get("format", {})
            if "duration" in fmt:
                duration = int(float(fmt["duration"]))
    except Exception as e:
        logger.warning(f"Failed to extract video metadata: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return {"width": width, "height": height, "duration": duration}
