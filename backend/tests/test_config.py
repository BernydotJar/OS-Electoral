from __future__ import annotations

import pytest
from pydantic import ValidationError

from campaignos import __version__
from campaignos.config import Environment, Settings


def test_default_service_version_matches_package_version() -> None:
    assert Settings().service_version == __version__


def test_partial_oidc_configuration_is_rejected() -> None:
    with pytest.raises(ValidationError, match="configured together"):
        Settings(oidc_issuer="https://identity.example.test/")


def test_non_https_oidc_endpoint_is_rejected() -> None:
    with pytest.raises(ValidationError, match="absolute HTTPS URL"):
        Settings(
            oidc_issuer="http://identity.example.test/",
            oidc_audience="campaignos",
            oidc_jwks_url="https://identity.example.test/.well-known/jwks.json",
        )


def test_production_requires_oidc_and_hidden_docs() -> None:
    with pytest.raises(ValidationError, match="OIDC configuration is required"):
        Settings(environment=Environment.PRODUCTION, expose_api_docs=False)

    with pytest.raises(ValidationError, match="documentation must be disabled"):
        Settings(
            environment=Environment.PRODUCTION,
            expose_api_docs=True,
            oidc_issuer="https://identity.example.test/",
            oidc_audience="campaignos",
            oidc_jwks_url="https://identity.example.test/.well-known/jwks.json",
        )


def test_token_use_validation_cannot_be_disabled() -> None:
    with pytest.raises(ValidationError):
        Settings(oidc_token_use=None)


def test_database_url_must_use_psycopg_postgresql() -> None:
    with pytest.raises(ValidationError, match=r"postgresql\+psycopg"):
        Settings(database_url="sqlite:///campaignos.db")


def test_production_requires_postgresql_configuration() -> None:
    with pytest.raises(ValidationError, match="PostgreSQL configuration is required"):
        Settings(
            environment=Environment.PRODUCTION,
            expose_api_docs=False,
            oidc_issuer="https://identity.example.test/",
            oidc_audience="campaignos",
            oidc_jwks_url="https://identity.example.test/.well-known/jwks.json",
        )


def test_partial_object_storage_configuration_is_rejected() -> None:
    with pytest.raises(ValidationError, match="must be configured together"):
        Settings(object_storage_endpoint="http://s3mock:9090")


def test_local_object_storage_configuration_is_typed_and_secret_is_redacted() -> None:
    settings = Settings(
        object_storage_endpoint="http://s3mock:9090",
        object_storage_access_key="campaignos_local_only",
        object_storage_secret_key="campaignos_local_secret",  # noqa: S106 - local dummy.
        object_storage_bucket="campaignos-local",
        object_storage_force_path_style=True,
    )

    assert settings.object_storage_configured
    assert settings.object_storage_force_path_style
    assert str(settings.object_storage_secret_key) == "**********"


def test_shared_environment_object_storage_requires_https() -> None:
    with pytest.raises(ValidationError, match="must use HTTPS"):
        Settings(
            environment=Environment.STAGING,
            expose_api_docs=False,
            database_url="postgresql+psycopg://campaignos:secret@postgres/campaignos",
            oidc_issuer="https://identity.example.test/",
            oidc_audience="campaignos",
            oidc_jwks_url="https://identity.example.test/.well-known/jwks.json",
            object_storage_endpoint="http://s3.example.test",
            object_storage_access_key="campaignos",
            object_storage_secret_key="not-a-real-secret",  # noqa: S106 - test value.
            object_storage_bucket="campaignos-staging",
        )


def test_smtp_configuration_is_all_or_none() -> None:
    with pytest.raises(ValidationError, match="configured together"):
        Settings(smtp_host="mailpit")

    settings = Settings(smtp_host="mailpit", smtp_port=1025, smtp_from="app@localhost")
    assert settings.smtp_configured


def test_development_identity_is_local_only_and_mutually_exclusive_with_oidc() -> None:
    token = "campaignos-local-development-token"  # noqa: S105 - explicit local fixture.
    settings = Settings(development_access_token=token)

    assert settings.development_identity_configured
    assert str(settings.development_access_token) == "**********"

    with pytest.raises(ValidationError, match="development environment"):
        Settings(environment=Environment.TEST, development_access_token=token)

    with pytest.raises(ValidationError, match="cannot be combined"):
        Settings(
            development_access_token=token,
            oidc_issuer="https://identity.example.test/",
            oidc_audience="campaignos",
            oidc_jwks_url="https://identity.example.test/.well-known/jwks.json",
        )


def test_development_identity_rejects_short_token() -> None:
    with pytest.raises(ValidationError, match="at least 24 characters"):
        Settings(development_access_token="too-short")  # noqa: S106 - invalid fixture.


def test_metrics_token_is_required_in_shared_environments_when_enabled() -> None:
    with pytest.raises(ValidationError, match="Metrics bearer token is required"):
        Settings(
            environment=Environment.STAGING,
            expose_api_docs=False,
            database_url="postgresql+psycopg://campaignos:secret@postgres/campaignos",
            oidc_issuer="https://identity.example.test/",
            oidc_audience="campaignos",
            oidc_jwks_url="https://identity.example.test/.well-known/jwks.json",
        )


def test_metrics_token_is_redacted_and_has_a_minimum_length() -> None:
    token = "campaignos-metrics-test-token"  # noqa: S105 - deterministic test fixture.
    configured = Settings(metrics_bearer_token=token)
    assert str(configured.metrics_bearer_token) == "**********"

    with pytest.raises(ValidationError, match="at least 24 characters"):
        Settings(metrics_bearer_token="too-short")  # noqa: S106 - invalid fixture.
