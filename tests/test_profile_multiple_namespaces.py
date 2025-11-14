"""
Tests for Profile multiple namespaces support.
"""

import json

import pytest
from nostr_sdk import (
    Alphabet,
    EventBuilder,
    Keys,
    Kind,
    Metadata,
    MetadataRecord,
    SingleLetterTag,
    Tag,
    TagKind,
)

from synvya_sdk import KeyEncoding, Label, Namespace, NostrKeys, Profile, ProfileFilter


@pytest.fixture(scope="function", name="test_keys")
def test_keys_fixture() -> NostrKeys:
    """Fixture providing test keys"""
    return NostrKeys()


class TestProfileMultipleNamespaces:
    """Test Profile multiple namespaces functionality"""

    async def test_profile_from_event_with_multiple_namespaces(self) -> None:
        """Test that Profile.from_event() collects namespaces from labels"""
        keys = Keys.generate()

        # Create a kind:0 event with multiple namespace tags and labels
        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
            picture="https://example.com/pic.jpg",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with multiple L tags (namespaces) and l tags (labels)
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
                    ["retail", "com.synvya.chamber"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)

        # Parse event to Profile
        profile = await Profile.from_event(event)

        # Should have both namespaces (derived from labels)
        namespaces = profile.get_namespaces()
        assert len(namespaces) == 2
        assert "com.synvya.merchant" in namespaces
        assert "com.synvya.chamber" in namespaces

    async def test_profile_from_event_with_single_namespace(self) -> None:
        """Test that Profile.from_event() works with single namespace from labels"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.uppercase(Alphabet.L)),
                    ["com.synvya.merchant"],
                ),
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
                    ["restaurant", "com.synvya.merchant"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        namespaces = profile.get_namespaces()
        assert len(namespaces) == 1
        assert "com.synvya.merchant" in namespaces

    async def test_profile_from_event_with_no_namespace(self) -> None:
        """Test that Profile.from_event() handles no namespace/label tags"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        event = EventBuilder.metadata(metadata).sign_with_keys(keys)
        profile = await Profile.from_event(event)

        namespaces = profile.get_namespaces()
        assert len(namespaces) == 0

    def test_profile_get_namespaces_derived_from_labels(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that get_namespaces() returns namespaces derived from labels"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.add_label("restaurant", "com.synvya.merchant")
        profile.add_label("retail", "com.synvya.chamber")

        namespaces = profile.get_namespaces()
        assert len(namespaces) == 2
        assert "com.synvya.merchant" in namespaces
        assert "com.synvya.chamber" in namespaces

    def test_profile_matches_filter_with_multiple_namespaces(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that matches_filter() works with multiple namespaces"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.add_label(Label.RESTAURANT.value, "com.synvya.merchant")
        profile.add_label(Label.RESTAURANT.value, "com.synvya.chamber")

        # Filter should match if namespace and label match
        filter1 = ProfileFilter(
            namespace="com.synvya.merchant",
            label=Label.RESTAURANT.value,
            hashtags=[],
        )
        assert profile.matches_filter(filter1) is True

        filter2 = ProfileFilter(
            namespace="com.synvya.chamber",
            label=Label.RESTAURANT.value,
            hashtags=[],
        )
        assert profile.matches_filter(filter2) is True

        filter3 = ProfileFilter(
            namespace="com.synvya.other",
            label=Label.RESTAURANT.value,
            hashtags=[],
        )
        assert profile.matches_filter(filter3) is False

    def test_profile_to_json_with_multiple_namespaces(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that to_json() serializes namespaces derived from labels"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.add_label("restaurant", "com.synvya.merchant")
        profile.add_label("retail", "com.synvya.chamber")

        json_str = profile.to_json()
        data = json.loads(json_str)

        assert "namespaces" in data
        assert isinstance(data["namespaces"], list)
        assert len(data["namespaces"]) == 2
        assert "com.synvya.merchant" in data["namespaces"]
        assert "com.synvya.chamber" in data["namespaces"]

    def test_profile_from_json_with_multiple_namespaces(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that from_json() deserializes labels and derives namespaces"""
        public_key = test_keys.get_public_key(KeyEncoding.HEX)
        json_data = {
            "public_key": public_key,
            "labels": {
                "com.synvya.merchant": ["restaurant"],
                "com.synvya.chamber": ["retail"],
            },
        }

        profile = Profile.from_json(json.dumps(json_data))

        namespaces = profile.get_namespaces()
        assert len(namespaces) == 2
        assert "com.synvya.merchant" in namespaces
        assert "com.synvya.chamber" in namespaces

    def test_profile_from_json_backward_compatibility(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that from_json() ignores old namespace fields, only uses labels"""
        public_key = test_keys.get_public_key(KeyEncoding.HEX)
        json_data = {
            "public_key": public_key,
            "namespace": "com.synvya.merchant",  # Old format - should be ignored
            "labels": {
                "com.synvya.chamber": ["retail"],  # Only labels create namespaces
            },
        }

        profile = Profile.from_json(json.dumps(json_data))

        namespaces = profile.get_namespaces()
        # Should only have namespace from labels, not from old namespace field
        assert len(namespaces) == 1
        assert "com.synvya.chamber" in namespaces
        assert "com.synvya.merchant" not in namespaces
