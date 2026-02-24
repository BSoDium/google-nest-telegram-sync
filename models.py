from __future__ import annotations

import isodate
import datetime
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, model_validator

if TYPE_CHECKING:
    from nest_api import NestDoorbellDevice

try:
    datetime.datetime.fromisoformat('2024-02-24T19:51:58.217Z')
    z_date_parser = datetime.datetime.fromisoformat
except ValueError:
    import dateutil.parser
    z_date_parser = dateutil.parser.parse


class CameraEvent(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    device: NestDoorbellDevice
    start_time: datetime.datetime
    duration: datetime.timedelta
    end_time: Optional[datetime.datetime] = None

    @model_validator(mode="after")
    def set_end_time(self):
        """Calculate end_time from start_time + duration if not provided."""
        if self.end_time is None:
            self.end_time = self.start_time + self.duration
        return self

    @property
    def event_id(self):
        """Stable identifier: start_time + device_id only (duration may change between polls)."""
        return f"{self.start_time.isoformat()}|{self.device.device_id}"

    @property
    def duration_seconds(self) -> float:
        """Duration in seconds for comparison across polls."""
        return self.duration.total_seconds()

    @classmethod
    def from_attrib(cls, xml_period_attributes: dict, nest_device):
        return CameraEvent(
            device=nest_device,
            start_time=z_date_parser(xml_period_attributes["programDateTime"]),
            duration=min(datetime.timedelta(minutes=1), isodate.parse_duration(
                xml_period_attributes["duration"]))
        )
