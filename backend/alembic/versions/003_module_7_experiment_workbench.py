"""Module 7 migration - experiment workbench fields, dataset.experiment_id, analysis.experiment_id

Revision ID: 003_module_7_experiment_workbench
Revises: 002_module_6_experimental_comparison
Create Date: 2026-10-04 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_module_7_experiment_workbench"
down_revision: str | None = "002_module_6_experimental_comparison"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Experiments table updates
    op.add_column("experiments", sa.Column("status", sa.String(length=50), server_default="draft", nullable=False))
    op.add_column("experiments", sa.Column("objective", sa.Text(), nullable=True))

    # 2. Datasets table updates
    op.add_column("datasets", sa.Column("experiment_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_datasets_experiment_id",
        "datasets",
        "experiments",
        ["experiment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_datasets_experiment_id"), "datasets", ["experiment_id"], unique=False)

    # 3. Analyses table updates
    op.add_column("analyses", sa.Column("experiment_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_analyses_experiment_id",
        "analyses",
        "experiments",
        ["experiment_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_analyses_experiment_id"), "analyses", ["experiment_id"], unique=False)


def downgrade() -> None:
    # 1. Revert analyses table updates
    op.drop_index(op.f("ix_analyses_experiment_id"), table_name="analyses")
    op.drop_constraint("fk_analyses_experiment_id", "analyses", type_="foreignkey")
    op.drop_column("analyses", "experiment_id")

    # 2. Revert datasets table updates
    op.drop_index(op.f("ix_datasets_experiment_id"), table_name="datasets")
    op.drop_constraint("fk_datasets_experiment_id", "datasets", type_="foreignkey")
    op.drop_column("datasets", "experiment_id")

    # 3. Revert experiments table updates
    op.drop_column("experiments", "objective")
    op.drop_column("experiments", "status")
