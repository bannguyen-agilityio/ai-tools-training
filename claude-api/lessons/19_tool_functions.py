"""Tool use: Tool functions.

A tool is an ordinary function. Keep names descriptive, validate inputs and
raise clear errors: Claude can read the message and correct itself later.
"""

from datetime import datetime, timedelta


def get_current_datetime(date_format: str = "%Y-%m-%d %H:%M:%S") -> str:
    if not date_format:
        raise ValueError("date_format cannot be empty")
    return datetime.now().strftime(date_format)


def add_duration_to_datetime(
    datetime_str: str, days: int = 0, hours: int = 0, minutes: int = 0
) -> str:
    try:
        start = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise ValueError("datetime_str must look like 'YYYY-MM-DD HH:MM:SS'")
    end = start + timedelta(days=days, hours=hours, minutes=minutes)
    return end.strftime("%Y-%m-%d %H:%M:%S")


def set_reminder(content: str, timestamp: str) -> str:
    if not content.strip():
        raise ValueError("content cannot be empty")
    return f"Reminder set for {timestamp}: {content}"


if __name__ == "__main__":
    now = get_current_datetime()
    print(now)
    due = add_duration_to_datetime(now, days=3)
    print(due)
    print(set_reminder("Submit the report", due))
