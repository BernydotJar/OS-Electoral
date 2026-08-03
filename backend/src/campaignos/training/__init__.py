"""Governed bilingual Training Academy."""

from campaignos.training.catalog import (
    CATALOG,
    CATALOG_DIGEST,
    grade_attempt,
    module_by_ref,
    path_by_ref,
    project_catalog,
)
from campaignos.training.service import (
    SqlAlchemyTrainingService,
    TrainingService,
    UnavailableTrainingService,
)

__all__ = [
    "CATALOG",
    "CATALOG_DIGEST",
    "SqlAlchemyTrainingService",
    "TrainingService",
    "UnavailableTrainingService",
    "grade_attempt",
    "module_by_ref",
    "path_by_ref",
    "project_catalog",
]
