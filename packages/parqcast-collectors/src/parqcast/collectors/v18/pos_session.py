from parqcast.core.version import V18
from parqcast.schemas.outbound import POS_SESSION_SCHEMA

from ..base import PosCollector


class PosSessionCollectorV18(PosCollector[V18]):
    """``pos_session`` columns (id/name/state, config_id, user_id, start_at,
    stop_at, cash_register_balance_start/end_real, cash_real_transaction)
    are identical in v18 and v19."""

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
