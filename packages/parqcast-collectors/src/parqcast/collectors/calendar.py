from parqcast.schemas.outbound import CALENDAR_SCHEMA

from .base import CoreCollector


class CalendarCollector[V](CoreCollector[V]):
    """Odoo 19: no resource_id, no date_from/date_to on attendance. Has duration_days/hours."""

    name = "calendar"
    schema = CALENDAR_SCHEMA
    required_tables = {"resource_calendar", "resource_calendar_attendance"}

    def get_sql(self):
        return (
            """
            SELECT
                rca.calendar_id,
                rc.name || ' ' || rc.id,
                rc.tz,
                rca.id,
                CASE WHEN rca.day_period IN ('morning', 'afternoon') THEN true ELSE false END,
                rca.dayofweek::int,
                rca.hour_from, rca.hour_to,
                COALESCE(rca.duration_days, 0),
                COALESCE(rca.duration_hours, 0),
                rca.week_type, rca.day_period
            FROM resource_calendar_attendance rca
            JOIN resource_calendar rc ON rca.calendar_id = rc.id
            WHERE rca.display_type IS NULL OR rca.display_type = '' OR rca.display_type = 'false'
        """,
            None,
        )
