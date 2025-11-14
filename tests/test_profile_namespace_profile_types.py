"""
Tests for Profile labels per NIP-32 labeling specification.
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

from synvya_sdk import KeyEncoding, Label, Namespace, NostrKeys, Profile


@pytest.fixture(scope="function", name="test_keys")
def test_keys_fixture() -> NostrKeys:
    """Fixture providing test keys"""
    return NostrKeys()


class TestProfileLabels:
    """Test Profile labels functionality per NIP-32"""

    async def test_profile_from_event_with_multiple_labels_per_namespace(self) -> None:
        """Test that Profile.from_event() collects multiple labels per namespace"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with multiple labels per namespace
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
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
                    ["reservations", "com.synvya.merchant"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        # Should have multiple labels for the namespace
        labels = profile.get_labels("com.synvya.merchant")
        assert "restaurant" in labels
        assert "reservations" in labels
        assert len(labels) == 2

    async def test_profile_from_event_with_same_label_multiple_namespaces(self) -> None:
        """Test that Profile.from_event() handles same label in multiple namespaces"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with same label in different namespaces
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
                    ["restaurant", "com.synvya.chamber"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        # Should have restaurant label in both namespaces
        assert profile.has_label("restaurant", "com.synvya.merchant")
        assert profile.has_label("restaurant", "com.synvya.chamber")
        # Should be able to get namespaces for the label
        namespaces = profile.get_namespaces_for_label("restaurant")
        assert "com.synvya.merchant" in namespaces
        assert "com.synvya.chamber" in namespaces

    async def test_profile_from_event_with_ugc_namespace(self) -> None:
        """Test that Profile.from_event() uses 'ugc' namespace when no L tags"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with l tag but no L tag
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

        # Should use 'ugc' namespace
        assert profile.has_label("restaurant", "ugc")

    async def test_profile_from_event_with_qualified_labels(self) -> None:
        """Test that Profile.from_event() correctly parses qualified labels format"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with qualified labels: ["l", "namespace:label"]
        # This is the preferred format that minimizes search load
        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
                    ["com.synvya.merchant:restaurant"],
                ),
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
                    ["com.synvya.merchant:reservations"],
                ),
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.L)),
                    ["com.synvya.chamber:retail"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        # Should correctly parse qualified labels
        assert profile.has_label("restaurant", "com.synvya.merchant")
        assert profile.has_label("reservations", "com.synvya.merchant")
        assert profile.has_label("retail", "com.synvya.chamber")

        # Verify namespaces are derived from labels
        namespaces = profile.get_namespaces()
        assert "com.synvya.merchant" in namespaces
        assert "com.synvya.chamber" in namespaces
        assert len(namespaces) == 2

    def test_profile_add_label(self, test_keys: NostrKeys) -> None:
        """Test add_label() method"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.add_label("restaurant", "com.synvya.merchant")
        profile.add_label("reservations", "com.synvya.merchant")

        assert profile.has_label("restaurant", "com.synvya.merchant")
        assert profile.has_label("reservations", "com.synvya.merchant")
        labels = profile.get_labels("com.synvya.merchant")
        assert len(labels) == 2
        assert "restaurant" in labels
        assert "reservations" in labels

    def test_profile_add_label_deduplicates(self, test_keys: NostrKeys) -> None:
        """Test that add_label() deduplicates labels"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.add_label("restaurant", "com.synvya.merchant")
        profile.add_label("restaurant", "com.synvya.merchant")  # Duplicate

        labels = profile.get_labels("com.synvya.merchant")
        assert len(labels) == 1
        assert labels[0] == "restaurant"

    def test_profile_remove_label(self, test_keys: NostrKeys) -> None:
        """Test remove_label() method"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.add_label("restaurant", "com.synvya.merchant")
        profile.add_label("reservations", "com.synvya.merchant")

        profile.remove_label("restaurant", "com.synvya.merchant")

        assert not profile.has_label("restaurant", "com.synvya.merchant")
        assert profile.has_label("reservations", "com.synvya.merchant")
        labels = profile.get_labels("com.synvya.merchant")
        assert len(labels) == 1
        assert labels[0] == "reservations"

    def test_profile_get_labels(self, test_keys: NostrKeys) -> None:
        """Test get_labels() method"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.add_label("restaurant", "com.synvya.merchant")
        profile.add_label("reservations", "com.synvya.merchant")
        profile.add_label("retail", "com.synvya.chamber")

        # Get labels for specific namespace
        merchant_labels = profile.get_labels("com.synvya.merchant")
        assert len(merchant_labels) == 2
        assert "restaurant" in merchant_labels
        assert "reservations" in merchant_labels

        # Get all labels
        all_labels = profile.get_labels()
        assert len(all_labels) == 3
        # Now returns list of (label, namespace) tuples
        assert ("restaurant", "com.synvya.merchant") in all_labels
        assert ("reservations", "com.synvya.merchant") in all_labels
        assert ("retail", "com.synvya.chamber") in all_labels

    def test_profile_get_namespaces_for_label(self, test_keys: NostrKeys) -> None:
        """Test get_namespaces_for_label() method"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.add_label("restaurant", "com.synvya.merchant")
        profile.add_label("restaurant", "com.synvya.chamber")

        namespaces = profile.get_namespaces_for_label("restaurant")
        assert len(namespaces) == 2
        assert "com.synvya.merchant" in namespaces
        assert "com.synvya.chamber" in namespaces

    def test_profile_to_json_with_labels(self, test_keys: NostrKeys) -> None:
        """Test that to_json() serializes labels"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.add_label("restaurant", "com.synvya.merchant")
        profile.add_label("reservations", "com.synvya.merchant")
        profile.add_label("retail", "com.synvya.chamber")

        json_str = profile.to_json()
        data = json.loads(json_str)

        assert "labels" in data
        assert isinstance(data["labels"], dict)
        assert "com.synvya.merchant" in data["labels"]
        assert "restaurant" in data["labels"]["com.synvya.merchant"]
        assert "reservations" in data["labels"]["com.synvya.merchant"]
        assert "com.synvya.chamber" in data["labels"]
        assert "retail" in data["labels"]["com.synvya.chamber"]

    def test_profile_from_json_with_labels(self, test_keys: NostrKeys) -> None:
        """Test that from_json() deserializes labels"""
        public_key = test_keys.get_public_key(KeyEncoding.HEX)
        json_data = {
            "public_key": public_key,
            "labels": {
                "com.synvya.merchant": ["restaurant", "reservations"],
                "com.synvya.chamber": ["retail"],
            },
        }

        profile = Profile.from_json(json.dumps(json_data))

        assert profile.has_label("restaurant", "com.synvya.merchant")
        assert profile.has_label("reservations", "com.synvya.merchant")
        assert profile.has_label("retail", "com.synvya.chamber")
