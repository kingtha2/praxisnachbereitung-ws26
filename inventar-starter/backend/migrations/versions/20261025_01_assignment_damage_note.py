"""Schaden-Vermerk bei der Rückgabe: assignment.damage_note

Das Basisschema kommt weiterhin aus db/init/*.sql (beim ersten Start der DB).
Diese Migration ist die erste Änderung darauf und hat deshalb keinen Vorgänger.

Revision ID: 20261025_01_damage_note
Revises:
Create Date: 2026-10-25
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20261025_01_damage_note"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # optional: NULL = kein Schaden gemeldet (gilt auch für alle bestehenden Ausleihen)
    op.add_column(
        "assignment",
        sa.Column("damage_note", sa.Text(), nullable=True),
    )
    # Ein Schaden kann erst bei der Rückgabe erfasst werden, und leere Texte zählen nicht als Vermerk
    op.create_check_constraint(
        "assignment_damage_note_check",
        "assignment",
        "damage_note is null or (returned_at is not null and length(trim(damage_note)) > 0)",
    )


def downgrade() -> None:
    op.drop_constraint("assignment_damage_note_check", "assignment", type_="check")
    op.drop_column("assignment", "damage_note")
