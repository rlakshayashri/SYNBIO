import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# --- FactorLevel Schemas ---


class FactorLevelBase(BaseModel):
    """Base schema for FactorLevel attributes."""

    name: str = Field(..., min_length=1, max_length=255, description="Category name/identifier for the level.")
    description: str | None = Field(default=None, description="Optional description of the level.")
    order_index: int = Field(default=0, description="Display and analysis ordering index.")


class FactorLevelCreate(FactorLevelBase):
    """Schema for creating a new FactorLevel."""

    pass


class FactorLevelUpdate(BaseModel):
    """Schema for updating an existing FactorLevel."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None)
    order_index: int | None = Field(default=None)


class FactorLevelResponse(FactorLevelBase):
    """Schema for returning FactorLevel details."""

    id: uuid.UUID
    factor_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- ExperimentalFactor Schemas ---


class ExperimentalFactorBase(BaseModel):
    """Base schema for ExperimentalFactor attributes."""

    name: str = Field(..., min_length=1, max_length=255, description="Name of the experimental factor.")
    description: str | None = Field(default=None, description="Scientific description of the factor.")
    factor_type: str | None = Field(
        default=None, max_length=50, description="Optional factor category (e.g. treatment, genotype, time)."
    )


class ExperimentalFactorCreate(ExperimentalFactorBase):
    """Schema for creating an ExperimentalFactor with optional initial levels."""

    levels: list[FactorLevelCreate] = Field(default_factory=list, description="Initial list of factor levels.")


class ExperimentalFactorUpdate(BaseModel):
    """Schema for updating an existing ExperimentalFactor."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None)
    factor_type: str | None = Field(default=None, max_length=50)


class ExperimentalFactorResponse(ExperimentalFactorBase):
    """Schema for returning ExperimentalFactor details."""

    id: uuid.UUID
    experiment_id: uuid.UUID
    levels: list[FactorLevelResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
