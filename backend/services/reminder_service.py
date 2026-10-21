"""Reminder Service for generating iCalendar (.ics) files for notice deadlines."""

from typing import Optional
from fastapi import HTTPException, status
from ics import Calendar, Event
import dateutil.parser


class ReminderService:
    def __init__(self):
        pass

    def generate_ics(self, title: str, deadline: str, language: str = "en") -> bytes:
        """
        Create an iCalendar (.ics) all-day event for the given deadline.
        Returns the .ics content as bytes.
        """
        if not title or not title.strip():
            title = "Notice Deadline Reminder"

        if not deadline or not deadline.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Deadline cannot be empty.",
            )

        # Parse deadline date with flexible fallback
        try:
            parsed_dt = dateutil.parser.parse(deadline.strip(), fuzzy=True, dayfirst=True)
        except (ValueError, OverflowError, TypeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The deadline format '{deadline}' could not be understood. Please check the date string.",
            )

        # Create calendar event
        try:
            cal = Calendar()
            event = Event()
            event.name = title.strip()
            event.begin = parsed_dt.date()
            event.make_all_day()

            if language.lower() == "hi":
                event.description = f"नोटिस साथी से रिमाइंडर - अंतिम तिथि: {deadline.strip()}"
            else:
                event.description = f"Reminder from Notice Saathi - Deadline: {deadline.strip()}"

            cal.events.add(event)
            return cal.serialize().encode("utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate calendar event: {str(e)}",
            )


# Global singleton instance
reminder_service = ReminderService()
