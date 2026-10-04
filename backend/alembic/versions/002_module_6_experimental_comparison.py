"""Module 6 migration - experiments, experimental_groups, replicates, comparisons

Revision ID: 002_module_6_experimental_comparison
Revises: 001_initial_migration
Create Date: 2026-10-04 10:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_module_6_experimental_comparison"
down_revision: str | None = "001_initial_migration"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Experiments table
    op.create_table(
        "experiments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("dataset_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("organism", sa.String(length=100), nullable=True),
        sa.Column("condition_type", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_experiments_project_id"), "experiments", ["project_id"], unique=False)
    op.create_index(op.f("ix_experiments_dataset_id"), "experiments", ["dataset_id"], unique=False)

    # 2. Experimental Groups table
    op.create_table(
        "experimental_groups",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("experiment_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("group_code", sa.String(length=50), nullable=False),
        sa.Column("is_control", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "metadata_payload",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_experimental_groups_experiment_id"), "experimental_groups", ["experiment_id"], unique=False
    )

    # 3. Replicates table
    op.create_table(
        "replicates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("replicate_name", sa.String(length=255), nullable=False),
        sa.Column("sample_identifier", sa.String(length=255), nullable=True),
        sa.Column("row_index", sa.Integer(), nullable=True),
        sa.Column("replicate_type", sa.String(length=50), server_default=sa.text("'biological'"), nullable=False),
        sa.Column(
            "metadata_payload",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["group_id"], ["experimental_groups.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_replicates_group_id"), "replicates", ["group_id"], unique=False)

    # 4. Comparisons table
    op.create_table(
        "comparisons",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("experiment_id", sa.UUID(), nullable=False),
        sa.Column("analysis_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("comparison_type", sa.String(length=50), nullable=False),
        sa.Column("group_a_id", sa.UUID(), nullable=True),
        sa.Column("group_b_id", sa.UUID(), nullable=True),
        sa.Column("measurement_column", sa.String(length=255), nullable=False),
        sa.Column("group_column", sa.String(length=255), nullable=True),
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "result_summary",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["group_a_id"], ["experimental_groups.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["group_b_id"], ["experimental_groups.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comparisons_experiment_id"), "comparisons", ["experiment_id"], unique=False)
    op.create_index(op.f("ix_comparisons_analysis_id"), "comparisons", ["analysis_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_comparisons_analysis_id"), table_name="comparisons")
    op.drop_index(op.f("ix_comparisons_experiment_id"), table_name="comparisons")
    op.drop_table("comparisons")
    op.drop_index(op.f("ix_replicates_group_id"), table_name="replicates")
    op.drop_table("replicates")
    op.drop_index(op.f("ix_experimental_groups_experiment_id"), table_name="experimental_groups")
    op.drop_table("experimental_groups")
    op.drop_index(op.f("ix_experiments_dataset_id"), table_name="experiments")
    op.drop_index(op.f("ix_experiments_project_id"), table_name="experiments")
    op.drop_table("experiments")
