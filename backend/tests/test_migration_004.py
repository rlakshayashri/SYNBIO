import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect

# Import existing models so Base.metadata knows about them
import app.models  # noqa: F401
from app.db.base import Base


def _load_migration_module(name: str):
    backend_dir = Path(__file__).resolve().parents[1]
    migration_path = backend_dir / "alembic" / "versions" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, migration_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_migration_004_upgrade_and_downgrade(tmp_path: Path):
    """Verify that migration 004 upgrade creates tables/indexes/constraints and downgrade cleans up."""
    test_db_path = tmp_path / "test_migration_004.db"
    test_db_url = f"sqlite:///{test_db_path.as_posix()}"
    engine = create_engine(test_db_url)

    # 1. Create baseline schema using Base.metadata (excluding Module 9 new tables)
    baseline_tables = [
        Base.metadata.tables["projects"],
        Base.metadata.tables["datasets"],
        Base.metadata.tables["experiments"],
        Base.metadata.tables["analyses"],
        Base.metadata.tables["experimental_groups"],
        Base.metadata.tables["replicates"],
        Base.metadata.tables["comparisons"],
    ]
    Base.metadata.create_all(bind=engine, tables=baseline_tables)

    inspector = inspect(engine)
    existing_before = set(inspector.get_table_names())
    assert "experiments" in existing_before
    assert "experimental_factors" not in existing_before
    assert "factor_levels" not in existing_before
    assert "factorial_comparisons" not in existing_before

    # 2. Load migration 004 and run upgrade()
    m004 = _load_migration_module("004_module_9_factorial_analysis")

    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)
        m004.op = op
        m004.upgrade()

    # Verify tables, columns, and constraints created by migration 004
    inspector = inspect(engine)
    existing_after = set(inspector.get_table_names())
    assert "experimental_factors" in existing_after
    assert "factor_levels" in existing_after
    assert "factorial_comparisons" in existing_after

    ef_cols = {c["name"] for c in inspector.get_columns("experimental_factors")}
    assert {"id", "experiment_id", "name", "description", "factor_type", "created_at", "updated_at"}.issubset(ef_cols)

    fl_cols = {c["name"] for c in inspector.get_columns("factor_levels")}
    assert {"id", "factor_id", "name", "description", "order_index", "created_at", "updated_at"}.issubset(fl_cols)

    fc_cols = {c["name"] for c in inspector.get_columns("factorial_comparisons")}
    assert {
        "id",
        "experiment_id",
        "analysis_id",
        "dataset_id",
        "name",
        "status",
        "factor_a_id",
        "factor_b_id",
        "factor_a_column",
        "factor_b_column",
        "measurement_column",
        "parameters",
        "result_summary",
        "created_at",
        "updated_at",
    }.issubset(fc_cols)

    # 3. Run migration 004 downgrade()
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)
        m004.op = op
        m004.downgrade()

    # Verify clean teardown
    inspector = inspect(engine)
    existing_reverted = set(inspector.get_table_names())
    assert "experimental_factors" not in existing_reverted
    assert "factor_levels" not in existing_reverted
    assert "factorial_comparisons" not in existing_reverted
    assert "experiments" in existing_reverted

    engine.dispose()
