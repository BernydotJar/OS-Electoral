"""Evidence-governed campaign team workspace contracts."""

from campaignos.teams.contracts import (
    RaciAssignment,
    TeamAccessRecommendation,
    TeamRoleCard,
    TeamTrainingRequirement,
    TeamWorkItem,
    TeamWorkspaceAssessmentInput,
    TeamWorkspaceCheck,
    TeamWorkspaceContractError,
    TeamWorkspaceCreate,
    TeamWorkspaceCreateEvidence,
    TeamWorkspaceProjection,
    TeamWorkspaceReadEvidence,
    TeamWorkspaceUpdate,
    TeamWorkspaceUpdateEvidence,
    assess_team_workspace,
)

__all__ = [
    "RaciAssignment",
    "TeamAccessRecommendation",
    "TeamRoleCard",
    "TeamTrainingRequirement",
    "TeamWorkItem",
    "TeamWorkspaceAssessmentInput",
    "TeamWorkspaceCheck",
    "TeamWorkspaceContractError",
    "TeamWorkspaceCreate",
    "TeamWorkspaceCreateEvidence",
    "TeamWorkspaceProjection",
    "TeamWorkspaceReadEvidence",
    "TeamWorkspaceUpdate",
    "TeamWorkspaceUpdateEvidence",
    "assess_team_workspace",
]

from campaignos.teams.service import (
    SqlAlchemyTeamWorkspaceService,
    TeamWorkspaceConflict,
    TeamWorkspaceEvidenceConflict,
    TeamWorkspaceIdempotencyConflict,
    TeamWorkspaceNotFound,
    TeamWorkspacePrerequisiteConflict,
    TeamWorkspaceService,
    TeamWorkspaceUnavailable,
    TeamWorkspaceVersionConflict,
    UnavailableTeamWorkspaceService,
)

__all__ += [
    "SqlAlchemyTeamWorkspaceService",
    "TeamWorkspaceConflict",
    "TeamWorkspaceEvidenceConflict",
    "TeamWorkspaceIdempotencyConflict",
    "TeamWorkspaceNotFound",
    "TeamWorkspacePrerequisiteConflict",
    "TeamWorkspaceService",
    "TeamWorkspaceUnavailable",
    "TeamWorkspaceVersionConflict",
    "UnavailableTeamWorkspaceService",
]
