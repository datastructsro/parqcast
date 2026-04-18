from parqcast.schemas.outbound import CALENDAR_LEAVES_SCHEMA

from .base import CoreCollector


class CalendarLeavesCollector[V](CoreCollector[V]):
    name = "calendar_leaves"
    schema = CALENDAR_LEAVES_SCHEMA
    depends_on = ["calendar"]
    required_tables = {"resource_calendar_leaves"}

    def get_sql(self):
        return (
            """
            SELECT
                rcl.id, rcl.name,
                rcl.date_from, rcl.date_to,
                rcl.resource_id,
                rcl.calendar_id,
                rcl.time_type,
                rcl.company_id
            FROM resource_calendar_leaves rcl
        """,
            None,
        )
