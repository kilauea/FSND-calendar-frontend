import calendar
from datetime import date, datetime, timedelta

class Calendar():
    @staticmethod
    def month_names():
        return [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

    @staticmethod
    def month_name(month):
        return Calendar.month_names()[month - 1]

    @staticmethod
    def set_first_weekday(weekday):
        calendar.setfirstweekday(weekday)

    @staticmethod
    def weekdays(week_starting_day):
        weekdays_headers = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        ret = weekdays_headers[week_starting_day:] + weekdays_headers[0:week_starting_day]
        return ret

    @staticmethod
    def previous_month_and_year(year, month):
        previous_month_date = date(year, month, 1) - timedelta(days=2)
        return previous_month_date.month, previous_month_date.year

    @staticmethod
    def next_month_and_year(year, month):
        last_day_of_month = calendar.monthrange(year, month)[1]
        next_month_date = date(year, month, last_day_of_month) + timedelta(days=2)
        return next_month_date.month, next_month_date.year

    @staticmethod
    def current_date():
        today_date = datetime.date(datetime.now())
        return today_date.day, today_date.month, today_date.year

    @staticmethod
    def month_days(year, month):
        return calendar.Calendar(calendar.firstweekday()).itermonthdates(year, month)

    @staticmethod
    def month_days_with_weekday(year, month):
        return calendar.Calendar(calendar.firstweekday()).monthdayscalendar(year, month)

    @staticmethod
    def previous_month_link(year, month, min_year, max_year):
        month, year = Calendar.previous_month_and_year(year=year, month=month)
        return (
            ""
            if year < min_year or year > max_year
            else "?y={}&m={}".format(year, month)
        )

    @staticmethod
    def next_month_link(year, month, min_year, max_year):
        month, year = Calendar.next_month_and_year(year=year, month=month)
        return (
            ""
            if year < min_year or year > max_year
            else "?y={}&m={}".format(year, month)
        )
