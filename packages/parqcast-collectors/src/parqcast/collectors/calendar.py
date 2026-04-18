from parqcast.schemas.outbound import CALENDAR_SCHEMA

from .base import CoreCollector


class CalendarCollector[V](CoreCollector[V]):
    """Resource-calendar attendance collector, shared across Odoo majors.

    ``resource_calendar_attendance.duration_hours`` was added in Odoo 19;
    v18 lacks the column and Odoo derives the same value from
    ``hour_to - hour_from`` at runtime. We mirror that derivation here via
    :meth:`col_or_default` so one collector serves both majors.
    """

    name = "calendar"
    schema = CALENDAR_SCHEMA
    required_tables = {"resource_calendar", "resource_calendar_attendance"}

    optional_columns = {
        "resource_calendar_attendance.duration_hours": (
            "COALESCE(rca.duration_hours, 0)",
            "COALESCE(rca.hour_to - rca.hour_from, 0)",
        ),
    }

    def get_sql(self):
        duration_hours_col = self.col_or_default(
            "resource_calendar_attendance", "duration_hours", "COALESCE(rca.hour_to - rca.hour_from, 0)"
        )
        return (
            f"""
            SELECT
                rca.calendar_id,
                rc.name || ' ' || rc.id,
                rc.tz,
                rca.id,
                CASE WHEN rca.day_period IN ('morning', 'afternoon') THEN true ELSE false END,
                rca.dayofweek::int,
                rca.hour_from, rca.hour_to,
                COALESCE(rca.duration_days, 0),
                {duration_hours_col},
                rca.week_type, rca.day_period
            FROM resource_calendar_attendance rca
            JOIN resource_calendar rc ON rca.calendar_id = rc.id
            WHERE rca.display_type IS NULL OR rca.display_type = '' OR rca.display_type = 'false'
        """,
            None,
        )
