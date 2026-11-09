"""Module 9 migration - experimental_factors, factor_levels, factorial_comparisons

Revision ID: 004_module_9_factorial_analysis
Revises: 003_module_7_experiment_workbench
Create Date: 2026-10-15 15:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "004_module_9_factorial_analysis"
down_revision: str | None = "003_module_7_experiment_workbench"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Experimental Factors table
    op.create_table(
        "experimental_factors",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("experiment_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("factor_type", sa.String(length=50), nullable=True),
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
        sa.UniqueConstraint("experiment_id", "name", name="uq_experimental_factors_experiment_name"),
    )
    op.create_index(
        op.f("ix_experimental_factors_experiment_id"),
        "experimental_factors",
        ["experiment_id"],
        unique=False,
    )

    # 2. Factor Levels table
    op.create_table(
        "factor_levels",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("factor_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("order_index", sa.Integer(), server_default=sa.text("0"), nullable=False),
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
        sa.ForeignKeyConstraint(["factor_id"], ["experimental_factors.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("factor_id", "name", name="uq_factor_levels_factor_name"),
    )
    op.create_index(
        op.f("ix_factor_levels_factor_id"),
        "factor_levels",
        ["factor_id"],
        unique=False,
    )

    # 3. Factorial Comparisons table
    op.create_table(
        "factorial_comparisons",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("experiment_id", sa.UUID(), nullable=False),
        sa.Column("analysis_id", sa.UUID(), nullable=True),
        sa.Column("dataset_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=50), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("factor_a_id", sa.UUID(), nullable=True),
        sa.Column("factor_b_id", sa.UUID(), nullable=True),
        sa.Column("factor_a_column", sa.String(length=255), nullable=False),
        sa.Column("factor_b_column", sa.String(length=255), nullable=False),
        sa.Column("measurement_column", sa.String(length=255), nullable=False),
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
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["experiment_id"], ["experiments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["factor_a_id"], ["experimental_factors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["factor_b_id"], ["experimental_factors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "factor_a_id IS NULL OR factor_b_id IS NULL OR factor_a_id != factor_b_id",
            name="ck_factorial_comparisons_distinct_factors",
        ),
    )
    op.create_index(
        op.f("ix_factorial_comparisons_experiment_id"),
        "factorial_comparisons",
        ["experiment_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_factorial_comparisons_analysis_id"),
        "factorial_comparisons",
        ["analysis_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_factorial_comparisons_dataset_id"),
        "factorial_comparisons",
        ["dataset_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_factorial_comparisons_factor_a_id"),
        "factorial_comparisons",
        ["factor_a_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_factorial_comparisons_factor_b_id"),
        "factorial_comparisons",
        ["factor_b_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_factorial_comparisons_factor_b_id"), table_name="factorial_comparisons")
    op.drop_index(op.f("ix_factorial_comparisons_factor_a_id"), table_name="factorial_comparisons")
    op.drop_index(op.f("ix_factorial_comparisons_dataset_id"), table_name="factorial_comparisons")
    op.drop_index(op.f("ix_factorial_comparisons_analysis_id"), table_name="factorial_comparisons")
    op.drop_index(op.f("ix_factorial_comparisons_experiment_id"), table_name="factorial_comparisons")
    op.drop_table("factorial_comparisons")
    op.drop_index(op.f("ix_factor_levels_factor_id"), table_name="factor_levels")
    op.drop_table("factor_levels")
    op.drop_index(op.f("ix_experimental_factors_experiment_id"), table_name="experimental_factors")
    op.drop_table("experimental_factors")
