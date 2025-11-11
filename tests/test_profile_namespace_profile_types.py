"""
Tests for Profile namespace-specific profile types support.
"""

import json

import pytest
from nostr_sdk import (
    Alphabet,
    EventBuilder,
    Keys,
    Metadata,
    MetadataRecord,
    SingleLetterTag,
    Tag,
    TagKind,
)

from synvya_sdk import KeyEncoding, Namespace, NostrKeys, Profile, ProfileType


@pytest.fixture(scope="function", name="test_keys")
def test_keys_fixture() -> NostrKeys:
    """Fixture providing test keys"""
    return NostrKeys()


class TestProfileNamespaceProfileTypes:
    """Test Profile namespace-specific profile types functionality"""

    async def test_profile_from_event_with_namespace_profile_types(self) -> None:
        """Test that Profile.from_event() collects namespace-specific profile types"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with lowercase l tags that include namespaces
        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.uppercase(Alphabet.L)),
                    ["com.synvya.merchant"],
                ),
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.uppercase(Alphabet.L)),
                    ["com.synvya.chamber"],
                ),
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
                    ["restaurant", "com.synvya.merchant"],
                ),
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
                    ["test-chamber", "com.synvya.chamber"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        # Should have namespace-specific profile types
        assert profile.get_profile_type("com.synvya.merchant") == ProfileType.RESTAURANT
        # test-chamber is not a valid ProfileType enum, so it should be stored as string
        # but get_profile_type should return primary if not valid enum
        profile_type_str = profile.namespace_profile_types.get("com.synvya.chamber")
        assert profile_type_str == "test-chamber"

    async def test_profile_from_event_with_single_lowercase_l_tag(self) -> None:
        """Test that Profile.from_event() works with single lowercase l tag without namespace"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
                    ["restaurant"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        # Should set primary profile type
        assert profile.get_profile_type() == ProfileType.RESTAURANT
        assert len(profile.namespace_profile_types) == 0

    def test_profile_get_profile_type_with_namespace(
        self, test_keys: NostrKeys
    ) -> None:
        """Test get_profile_type() with namespace parameter"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.set_profile_type("restaurant", namespace="com.synvya.merchant")
        profile.set_profile_type("retail", namespace="com.synvya.chamber")

        assert profile.get_profile_type("com.synvya.merchant") == ProfileType.RESTAURANT
        assert profile.get_profile_type("com.synvya.chamber") == ProfileType.RETAIL
        # Primary should be restaurant (first one set)
        assert profile.get_profile_type() == ProfileType.RESTAURANT

    def test_profile_set_profile_type_with_namespace(
        self, test_keys: NostrKeys
    ) -> None:
        """Test set_profile_type() with namespace parameter"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.set_profile_type("restaurant", namespace="com.synvya.merchant")

        assert "com.synvya.merchant" in profile.namespace_profile_types
        assert profile.namespace_profile_types["com.synvya.merchant"] == "restaurant"
        assert profile.get_profile_type("com.synvya.merchant") == ProfileType.RESTAURANT

    def test_profile_to_json_with_namespace_profile_types(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that to_json() serializes namespace_profile_types"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.set_profile_type("restaurant", namespace="com.synvya.merchant")
        profile.set_profile_type("retail", namespace="com.synvya.chamber")

        json_str = profile.to_json()
        data = json.loads(json_str)

        assert "namespace_profile_types" in data
        assert isinstance(data["namespace_profile_types"], dict)
        assert data["namespace_profile_types"]["com.synvya.merchant"] == "restaurant"
        assert data["namespace_profile_types"]["com.synvya.chamber"] == "retail"

    def test_profile_from_json_with_namespace_profile_types(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that from_json() deserializes namespace_profile_types"""
        public_key = test_keys.get_public_key(KeyEncoding.HEX)
        json_data = {
            "public_key": public_key,
            "namespace_profile_types": {
                "com.synvya.merchant": "restaurant",
                "com.synvya.chamber": "retail",
            },
        }

        profile = Profile.from_json(json.dumps(json_data))

        assert profile.get_profile_type("com.synvya.merchant") == ProfileType.RESTAURANT
        assert profile.get_profile_type("com.synvya.chamber") == ProfileType.RETAIL
