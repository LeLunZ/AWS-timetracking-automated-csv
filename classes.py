from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class ExportTime:
    in_time: datetime
    out_time: datetime
    remark: str
    is_generated: bool = False
    ap: str = None


class ExportDay:
    def __init__(self, day):
        self.times = []
        self.day: datetime = day
        self.work_hours = 0  # in seconds
        self.valid: bool = True
        self.validation_str = []

    def time_diff(self, time_):
        return time_ - self.work_hours

    def add_times(self, e_time: ExportTime):
        self.times.append(e_time)

        self.work_hours += (e_time.out_time - e_time.in_time).total_seconds()

    def add_validation(self, text):
        self.valid = False
        self.validation_str.append(text)


@dataclass
class Logs:
    date: datetime
    remarks: str


@dataclass
class WorkTimes:
    begin: List = field(default_factory=lambda: [])
    end: List = field(default_factory=lambda: [])
