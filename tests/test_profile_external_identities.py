"""
Tests for Profile external identity verification (NIP-39) support.
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

from synvya_sdk import KeyEncoding, NostrKeys, Profile


@pytest.fixture(scope="function", name="test_keys")
def test_keys_fixture() -> NostrKeys:
    """Fixture providing test keys"""
    return NostrKeys()


class TestProfileExternalIdentities:
    """Test Profile external identity verification (NIP-39) functionality"""

    async def test_profile_from_event_with_nip39_external_identity(self) -> None:
        """Test that Profile.from_event() parses NIP-39 format i tags"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with NIP-39 format i tag: ["i", "platform:identity", "proof"]
        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    ["com.synvya.chamber:snovalley", "1234"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        external_identities = profile.get_external_identities()
        assert len(external_identities) == 1
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert external_identities[0]["proof"] == "1234"

    async def test_profile_from_event_with_multiple_external_identities(self) -> None:
        """Test that Profile.from_event() parses multiple NIP-39 i tags"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with multiple NIP-39 format i tags
        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    ["com.synvya.chamber:snovalley", "1234"],
                ),
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    ["twitter:username", "proof123"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        external_identities = profile.get_external_identities()
        assert len(external_identities) == 2

        # Check first identity
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert external_identities[0]["proof"] == "1234"

        # Check second identity
        assert external_identities[1]["platform"] == "twitter"
        assert external_identities[1]["identity"] == "username"
        assert external_identities[1]["proof"] == "proof123"

    async def test_profile_from_event_with_empty_proof(self) -> None:
        """Test that Profile.from_event() handles NIP-39 i tags with empty proof"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with NIP-39 format i tag with empty proof
        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    ["com.synvya.chamber:snovalley", ""],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        external_identities = profile.get_external_identities()
        assert len(external_identities) == 1
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert external_identities[0]["proof"] == ""

    async def test_profile_from_event_legacy_i_tags_still_work(self) -> None:
        """Test that legacy i tags (email, phone, location) still work"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with legacy i tags
        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    ["email:test@example.com", ""],
                ),
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    ["phone:5551234567", ""],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        # Legacy tags should set email and phone
        assert profile.get_email() == "test@example.com"
        assert profile.get_phone() == "5551234567"

        # Should not be stored as external identities
        external_identities = profile.get_external_identities()
        assert len(external_identities) == 0

    async def test_profile_from_event_mixed_legacy_and_nip39(self) -> None:
        """Test that Profile.from_event() handles both legacy and NIP-39 i tags"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with both legacy and NIP-39 i tags
        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    ["email:test@example.com", ""],
                ),
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    ["com.synvya.chamber:snovalley", "1234"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        # Legacy tag should set email
        assert profile.get_email() == "test@example.com"

        # NIP-39 tag should be stored as external identity
        external_identities = profile.get_external_identities()
        assert len(external_identities) == 1
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert external_identities[0]["proof"] == "1234"

    def test_profile_add_external_identity(self, test_keys: NostrKeys) -> None:
        """Test adding external identity to profile"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))

        profile.add_external_identity("com.synvya.chamber", "snovalley", "1234")

        external_identities = profile.get_external_identities()
        assert len(external_identities) == 1
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert external_identities[0]["proof"] == "1234"

    def test_profile_add_external_identity_no_duplicates(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that adding duplicate external identity doesn't create duplicates"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))

        profile.add_external_identity("com.synvya.chamber", "snovalley", "1234")
        profile.add_external_identity("com.synvya.chamber", "snovalley", "1234")

        external_identities = profile.get_external_identities()
        assert len(external_identities) == 1

    def test_profile_add_external_identity_default_proof(
        self, test_keys: NostrKeys
    ) -> None:
        """Test adding external identity without proof (defaults to empty string)"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))

        profile.add_external_identity("com.synvya.chamber", "snovalley")

        external_identities = profile.get_external_identities()
        assert len(external_identities) == 1
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert external_identities[0]["proof"] == ""

    def test_profile_to_dict_with_external_identities(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that to_dict() includes external_identities"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))

        profile.add_external_identity("com.synvya.chamber", "snovalley", "1234")
        profile.add_external_identity("twitter", "username", "proof123")

        profile_dict = profile.to_dict()

        assert "external_identities" in profile_dict
        external_identities = profile_dict["external_identities"]
        assert len(external_identities) == 2
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert external_identities[0]["proof"] == "1234"

    def test_profile_to_json_with_external_identities(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that to_json() includes external_identities"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))

        profile.add_external_identity("com.synvya.chamber", "snovalley", "1234")

        profile_json = profile.to_json()
        profile_dict = json.loads(profile_json)

        assert "external_identities" in profile_dict
        external_identities = profile_dict["external_identities"]
        assert len(external_identities) == 1
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert external_identities[0]["proof"] == "1234"

    def test_profile_from_json_with_external_identities(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that from_json() loads external_identities"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))

        profile.add_external_identity("com.synvya.chamber", "snovalley", "1234")
        profile.add_external_identity("twitter", "username", "proof123")

        profile_json = profile.to_json()
        loaded_profile = Profile.from_json(profile_json)

        external_identities = loaded_profile.get_external_identities()
        assert len(external_identities) == 2
        assert external_identities[0]["platform"] == "com.synvya.chamber"
        assert external_identities[0]["identity"] == "snovalley"
        assert external_identities[0]["proof"] == "1234"
        assert external_identities[1]["platform"] == "twitter"
        assert external_identities[1]["identity"] == "username"
        assert external_identities[1]["proof"] == "proof123"

    def test_profile_from_json_backward_compatibility(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that from_json() handles missing external_identities (backward compatibility)"""
        profile = Profile(public_key=test_keys.get_public_key(KeyEncoding.HEX))
        profile.set_name("Test Profile")

        profile_json = profile.to_json()
        profile_dict = json.loads(profile_json)

        # Remove external_identities to simulate old JSON format
        if "external_identities" in profile_dict:
            del profile_dict["external_identities"]

        old_json = json.dumps(profile_dict)
        loaded_profile = Profile.from_json(old_json)

        # Should not crash and external_identities should be empty list
        external_identities = loaded_profile.get_external_identities()
        assert external_identities == []

    async def test_profile_from_event_unknown_claim_type_as_external_identity(
        self,
    ) -> None:
        """Test that unknown claim types in 2-element i tags are stored as external identities"""
        keys = Keys.generate()

        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with unknown claim type (not email, phone, location)
        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    ["unknown:value", ""],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)
        profile = await Profile.from_event(event)

        # Should be stored as external identity
        external_identities = profile.get_external_identities()
        assert len(external_identities) == 1
        assert external_identities[0]["platform"] == "unknown"
        assert external_identities[0]["identity"] == "value"
        assert external_identities[0]["proof"] == ""
