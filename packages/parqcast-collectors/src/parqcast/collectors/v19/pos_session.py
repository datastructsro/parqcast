from parqcast.core.version import V19
from parqcast.schemas.outbound import POS_SESSION_SCHEMA

from ..base import PosCollector


class PosSessionCollectorV19(PosCollector[V19]):
    name = "pos_session"
    schema = POS_SESSION_SCHEMA
    required_tables = {"pos_session"}

    def get_sql(self):
        return (
            """
            SELECT
                ps.id, ps.name, ps.state,
                ps.config_id, ps.user_id,
                ps.start_at, ps.stop_at,
                ps.cash_register_balance_start,
                ps.cash_register_balance_end_real,
                ps.cash_real_transaction
            FROM pos_session ps
        """,
            None,
        )
