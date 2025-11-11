"""
Tests for BuyerTools knowledge base storage of namespace profile types and external identities.
"""

from unittest.mock import AsyncMock, Mock, call

import pytest

from synvya_sdk import KeyEncoding, Namespace, NostrKeys, Profile, ProfileType
from synvya_sdk.agno import BuyerTools


@pytest.fixture(scope="function", name="test_keys")
def test_keys_fixture() -> NostrKeys:
    """Fixture providing test keys"""
    return NostrKeys()


@pytest.fixture(scope="function", name="mock_vector_db")
def mock_vector_db_fixture() -> Mock:
    """Fixture providing a mocked VectorDb"""
    mock_db = Mock()
    mock_db.async_upsert = AsyncMock()
    mock_db.upsert = Mock()
    return mock_db


@pytest.fixture(scope="function", name="mock_knowledge_base_with_vector_db")
def mock_knowledge_base_with_vector_db_fixture(mock_vector_db: Mock) -> Mock:
    """Fixture providing a mocked Knowledge with VectorDb"""
    mock_kb = Mock()
    mock_kb.vector_db = mock_vector_db
    mock_kb.add_filters = Mock()
    return mock_kb


@pytest.mark.asyncio
async def test_store_profile_in_kb_with_namespace_profile_types(
    mock_knowledge_base_with_vector_db: Mock,
    mock_vector_db: Mock,
    test_keys: NostrKeys,
) -> None:
    """Test that _store_profile_in_kb stores namespace_profile_types in metadata and filters"""
    from unittest.mock import patch

    # Create a profile with namespace-specific profile types
    profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
    profile.set_name("Test Merchant")
    profile.set_namespace(["com.synvya.merchant", "com.synvya.chamber"])
    profile.set_profile_type("restaurant", namespace="com.synvya.merchant")
    profile.set_profile_type("test-chamber", namespace="com.synvya.chamber")

    # Create BuyerTools with mocked dependencies
    with patch("synvya_sdk.NostrClient.create") as mock_create:
        mock_client = Mock()
        mock_client.async_get_profile = AsyncMock()
        mock_client.async_get_profile.return_value = profile
        mock_create.return_value = mock_client

        buyer_tools = await BuyerTools.create(
            mock_knowledge_base_with_vector_db,
            ["wss://relay.example.com"],
            test_keys.get_private_key(KeyEncoding.HEX),
        )

        # Call _store_profile_in_kb
        await buyer_tools._store_profile_in_kb(profile)

        # Verify async_upsert was called
        assert mock_vector_db.async_upsert.called

        # Get the filters that were passed
        call_args = mock_vector_db.async_upsert.call_args
        filters = (
            call_args[0][2]
            if len(call_args[0]) > 2
            else call_args[1].get("filters", {})
        )

        # Verify namespace_profile_types is in metadata
        assert "namespace_profile_types" in filters
        assert filters["namespace_profile_types"] == {
            "com.synvya.merchant": "restaurant",
            "com.synvya.chamber": "test-chamber",
        }

        # Verify boolean filters for each namespace→profile_type mapping
        assert filters["profile_type_com.synvya.merchant:restaurant"] is True
        assert filters["profile_type_com.synvya.chamber:test-chamber"] is True


@pytest.mark.asyncio
async def test_store_profile_in_kb_with_external_identities(
    mock_knowledge_base_with_vector_db: Mock,
    mock_vector_db: Mock,
    test_keys: NostrKeys,
) -> None:
    """Test that _store_profile_in_kb stores external_identities in metadata and filters"""
    from unittest.mock import patch

    # Create a profile with external identities
    profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
    profile.set_name("Test Merchant")
    profile.add_external_identity("com.synvya.chamber", "snovalley", "1234")
    profile.add_external_identity("twitter", "username", "proof123")

    # Create BuyerTools with mocked dependencies
    with patch("synvya_sdk.NostrClient.create") as mock_create:
        mock_client = Mock()
        mock_client.async_get_profile = AsyncMock()
        mock_client.async_get_profile.return_value = profile
        mock_create.return_value = mock_client

        buyer_tools = await BuyerTools.create(
            mock_knowledge_base_with_vector_db,
            ["wss://relay.example.com"],
            test_keys.get_private_key(KeyEncoding.HEX),
        )

        # Call _store_profile_in_kb
        await buyer_tools._store_profile_in_kb(profile)

        # Verify async_upsert was called
        assert mock_vector_db.async_upsert.called

        # Get the filters that were passed
        call_args = mock_vector_db.async_upsert.call_args
        filters = (
            call_args[0][2]
            if len(call_args[0]) > 2
            else call_args[1].get("filters", {})
        )

        # Verify external_identities is in metadata
        assert "external_identities" in filters
        external_identities = filters["external_identities"]
        assert len(external_identities) == 2

        # Verify the external identities are stored correctly
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert external_identities[0]["proof"] == "1234"

        assert external_identities[1]["platform"] == "twitter"
        assert external_identities[1]["identity"] == "username"
        assert external_identities[1]["proof"] == "proof123"

        # Verify boolean filters for each external identity
        assert filters["external_identity_com.synvya.chamber:snovalley"] is True
        assert filters["external_identity_twitter:username"] is True


@pytest.mark.asyncio
async def test_store_profile_in_kb_with_both_namespace_types_and_external_identities(
    mock_knowledge_base_with_vector_db: Mock,
    mock_vector_db: Mock,
    test_keys: NostrKeys,
) -> None:
    """Test that _store_profile_in_kb stores both namespace_profile_types and external_identities"""
    from unittest.mock import patch

    # Create a profile with both namespace-specific profile types and external identities
    profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
    profile.set_name("Test Merchant")
    profile.set_namespace(["com.synvya.merchant"])
    profile.set_profile_type("restaurant", namespace="com.synvya.merchant")
    profile.add_external_identity("com.synvya.chamber", "snovalley", "1234")

    # Create BuyerTools with mocked dependencies
    with patch("synvya_sdk.NostrClient.create") as mock_create:
        mock_client = Mock()
        mock_client.async_get_profile = AsyncMock()
        mock_client.async_get_profile.return_value = profile
        mock_create.return_value = mock_client

        buyer_tools = await BuyerTools.create(
            mock_knowledge_base_with_vector_db,
            ["wss://relay.example.com"],
            test_keys.get_private_key(KeyEncoding.HEX),
        )

        # Call _store_profile_in_kb
        await buyer_tools._store_profile_in_kb(profile)

        # Verify async_upsert was called
        assert mock_vector_db.async_upsert.called

        # Get the filters that were passed
        call_args = mock_vector_db.async_upsert.call_args
        filters = (
            call_args[0][2]
            if len(call_args[0]) > 2
            else call_args[1].get("filters", {})
        )

        # Verify both are stored
        assert "namespace_profile_types" in filters
        assert "external_identities" in filters

        # Verify namespace_profile_types
        assert filters["namespace_profile_types"] == {
            "com.synvya.merchant": "restaurant"
        }
        assert filters["profile_type_com.synvya.merchant:restaurant"] is True

        # Verify external_identities
        external_identities = filters["external_identities"]
        assert len(external_identities) == 1
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert filters["external_identity_com.synvya.chamber:snovalley"] is True


@pytest.mark.asyncio
async def test_store_profile_in_kb_without_namespace_types_or_external_identities(
    mock_knowledge_base_with_vector_db: Mock,
    mock_vector_db: Mock,
    test_keys: NostrKeys,
) -> None:
    """Test that _store_profile_in_kb works correctly when no namespace types or external identities"""
    from unittest.mock import patch

    # Create a profile without namespace-specific profile types or external identities
    profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
    profile.set_name("Test Merchant")
    profile.set_namespace(["com.synvya.merchant"])

    # Create BuyerTools with mocked dependencies
    with patch("synvya_sdk.NostrClient.create") as mock_create:
        mock_client = Mock()
        mock_client.async_get_profile = AsyncMock()
        mock_client.async_get_profile.return_value = profile
        mock_create.return_value = mock_client

        buyer_tools = await BuyerTools.create(
            mock_knowledge_base_with_vector_db,
            ["wss://relay.example.com"],
            test_keys.get_private_key(KeyEncoding.HEX),
        )

        # Call _store_profile_in_kb
        await buyer_tools._store_profile_in_kb(profile)

        # Verify async_upsert was called
        assert mock_vector_db.async_upsert.called

        # Get the filters that were passed
        call_args = mock_vector_db.async_upsert.call_args
        filters = (
            call_args[0][2]
            if len(call_args[0]) > 2
            else call_args[1].get("filters", {})
        )

        # Verify namespace_profile_types and external_identities are not in filters
        # (or are empty/None)
        if "namespace_profile_types" in filters:
            assert not filters["namespace_profile_types"]
        if "external_identities" in filters:
            assert not filters["external_identities"]
