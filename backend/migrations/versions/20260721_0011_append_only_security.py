"""Protect append-only evidence from non-owner mutation.

Revision ID: 20260721_0011
Revises: 20260721_0010
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260721_0011"
down_revision: str | None = "20260721_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APPEND_ONLY_TABLES = (
    "audit_events",
    "idempotency_records",
    "candidate_section_approvals",
    "war_room_snapshots",
    "strategy_decision_receipts",
    "agent_runs",
)
TRIGGER_NAME = "campaignos_append_only_guard"
FUNCTION_NAME = "campaignos_reject_append_only_mutation"


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            CREATE FUNCTION public.campaignos_reject_append_only_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            SECURITY DEFINER
            SET search_path = pg_catalog
            AS $function$
            DECLARE
                owner_name name;
            BEGIN
                SELECT pg_catalog.pg_get_userbyid(relation.relowner)
                INTO owner_name
                FROM pg_catalog.pg_class AS relation
                WHERE relation.oid = TG_RELID;

                IF owner_name IS NULL THEN
                    RAISE EXCEPTION USING
                        ERRCODE = '42501',
                        MESSAGE = 'append-only relation owner is unavailable';
                END IF;

                IF session_user = owner_name
                   OR pg_catalog.pg_has_role(session_user, owner_name, 'MEMBER') THEN
                    IF TG_OP = 'DELETE' THEN
                        RETURN OLD;
                    END IF;
                    RETURN NEW;
                END IF;

                RAISE EXCEPTION USING
                    ERRCODE = '42501',
                    MESSAGE = pg_catalog.format(
                        'append-only relation %I.%I rejects %s for role %I',
                        TG_TABLE_SCHEMA,
                        TG_TABLE_NAME,
                        TG_OP,
                        session_user
                    );
            END
            $function$
            """
        )
    )
    op.execute(
        sa.text(
            "REVOKE ALL ON FUNCTION public.campaignos_reject_append_only_mutation() FROM PUBLIC"
        )
    )
    for table in APPEND_ONLY_TABLES:
        trigger_sql = (  # noqa: S608 - identifiers are from a fixed migration allow-list.
            f'CREATE TRIGGER "{TRIGGER_NAME}" '
            f'BEFORE UPDATE OR DELETE ON "{table}" '
            f"FOR EACH ROW EXECUTE FUNCTION public.{FUNCTION_NAME}()"
        )
        op.execute(sa.text(trigger_sql))


def downgrade() -> None:
    for table in reversed(APPEND_ONLY_TABLES):
        trigger_sql = (  # noqa: S608 - identifiers are from a fixed migration allow-list.
            f'DROP TRIGGER IF EXISTS "{TRIGGER_NAME}" ON "{table}"'
        )
        op.execute(sa.text(trigger_sql))
    op.execute(sa.text("DROP FUNCTION IF EXISTS public.campaignos_reject_append_only_mutation()"))
