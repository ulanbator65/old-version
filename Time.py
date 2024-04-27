
from datetime import datetime, timedelta
from tostring import *


@auto_str
class Time:

    def __init__(self, timestamp: float):
        self.timestamp: float = timestamp


    @staticmethod
    def now() -> 'Time':
        now: datetime = datetime.now()
        return Time(now.timestamp())


    @staticmethod
    def time_parts(tdelta: timedelta) -> tuple:

        total_min = int(tdelta.total_seconds()/60)
        day = int(total_min/24.0/60.0)
        hour = int((total_min/60) - day*24)
        min = total_min - day*24*60 - hour*60
        #        min = int(min)
        return day, hour, min


    def subtract(self, hours: float, minutes: float) -> 'Time':
        new_time: datetime = datetime.fromtimestamp(self.timestamp) + timedelta(hours=hours, minutes=minutes)
        print(new_time)
        print(type(new_time))
        return Time(new_time.timestamp())

    def timedelta_from(self, timestamp2: float) -> timedelta:
        t2 = datetime.fromtimestamp(timestamp2)

        return datetime.fromtimestamp(self.timestamp) - t2


    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)


    def get_age_in_seconds(self, from_time: float) -> int:
        tdelta: timedelta = self.timedelta_from(from_time)
        seconds = tdelta.seconds
        seconds += tdelta.days*24*3600
        return seconds


    def get_age_in_hours(self, from_time: float) -> float:
        return self.get_age_in_seconds(from_time) / 3600


    def get_time_parts(self) -> tuple:
        tdelta: timedelta = self.timedelta_from(0)
        return Time.time_parts(tdelta)

