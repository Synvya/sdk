"""
Tests for Profile geohash functionality (Issue #40)
"""

import json

import pytest
from nostr_sdk import (
    Alphabet,
    Event,
    EventBuilder,
    Keys,
    Kind,
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


@pytest.fixture(scope="function", name="test_geohash")
def test_geohash_fixture() -> str:
    """Fixture providing a test geohash"""
    return "9q8yyk8yu"


class TestProfileGeohash:
    """Test Profile geohash functionality"""

    def test_profile_geohash_property(
        self, test_keys: NostrKeys, test_geohash: str
    ) -> None:
        """Test that profile has geohash property"""
        profile = Profile(test_keys.get_public_key(KeyEncoding.HEX))

        # Should default to empty string
        assert profile.geohash == ""

        # Should be settable
        profile.geohash = test_geohash
        assert profile.geohash == test_geohash

    def test_profile_geohash_getter(
        self, test_keys: NostrKeys, test_geohash: str
    ) -> None:
        """Test profile get_geohash method"""
        profile = Profile(test_keys.get_public_key(KeyEncoding.HEX))

        # Should return empty string by default
        assert profile.get_geohash() == ""

        # Should return set value
        profile.geohash = test_geohash
        assert profile.get_geohash() == test_geohash

    def test_profile_geohash_setter(
        self, test_keys: NostrKeys, test_geohash: str
    ) -> None:
        """Test profile set_geohash method"""
        profile = Profile(test_keys.get_public_key(KeyEncoding.HEX))

        # Should set geohash
        profile.set_geohash(test_geohash)
        assert profile.geohash == test_geohash
        assert profile.get_geohash() == test_geohash

    def test_profile_geohash_to_dict(
        self, test_keys: NostrKeys, test_geohash: str
    ) -> None:
        """Test that geohash is included in to_dict()"""
        profile = Profile(test_keys.get_public_key(KeyEncoding.HEX))
        profile.set_name("Test Profile")
        profile.set_geohash(test_geohash)

        profile_dict = profile.to_dict()

        # Should include geohash in dict
        assert "geohash" in profile_dict
        assert profile_dict["geohash"] == test_geohash

    def test_profile_geohash_to_json(
        self, test_keys: NostrKeys, test_geohash: str
    ) -> None:
        """Test that geohash is included in to_json()"""
        profile = Profile(test_keys.get_public_key(KeyEncoding.HEX))
        profile.set_name("Test Profile")
        profile.set_geohash(test_geohash)

        profile_json = profile.to_json()
        profile_data = json.loads(profile_json)

        # Should include geohash in JSON
        assert "geohash" in profile_data
        assert profile_data["geohash"] == test_geohash

    def test_profile_geohash_from_json(
        self, test_keys: NostrKeys, test_geohash: str
    ) -> None:
        """Test that geohash is parsed from JSON"""
        profile_json = json.dumps(
            {
                "public_key": test_keys.get_public_key(KeyEncoding.HEX),
                "name": "Test Profile",
                "geohash": test_geohash,
                "about": "",
                "banner": "",
                "bot": False,
                "city": "",
                "country": "",
                "created_at": 0,
                "display_name": "",
                "email": "",
                "hashtags": [],
                "locations": [],
                "namespace": "",
                "nip05": "",
                "picture": "",
                "phone": "",
                "state": "",
                "street": "",
                "website": "",
                "zip_code": "",
            }
        )

        profile = Profile.from_json(profile_json)

        # Should parse geohash from JSON
        assert profile.get_geohash() == test_geohash

    async def test_profile_geohash_from_event(
        self, test_keys: NostrKeys, test_geohash: str
    ) -> None:
        """Test that geohash is parsed from Nostr event with geo: i tag (NIP-73)"""
        keys = Keys.generate()

        # Create a kind:0 event with metadata and geo: i tag for geohash
        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
            picture="https://example.com/pic.jpg",
        )
        metadata = Metadata.from_record(metadata_record)

        # Build event with geo: i tag (NIP-73 format)
        event_builder = EventBuilder.metadata(metadata).tags(
            [
                Tag.custom(
                    TagKind.SINGLE_LETTER(SingleLetterTag.lowercase(Alphabet.I)),
                    [f"geo:{test_geohash}", "https://geohash.org"],
                ),
            ]
        )

        event = event_builder.sign_with_keys(keys)

        # Parse event to Profile
        profile = await Profile.from_event(event)

        # Should parse geohash from geo: i tag
        assert profile.get_geohash() == test_geohash

    async def test_profile_without_geohash_from_event(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that profile without geohash parses correctly"""
        keys = Keys.generate()

        # Create a kind:0 event without g tag
        metadata_record = MetadataRecord(
            name="Test Profile",
            about="Test about",
            picture="https://example.com/pic.jpg",
        )
        metadata = Metadata.from_record(metadata_record)

        event = EventBuilder.metadata(metadata).sign_with_keys(keys)

        # Parse event to Profile
        profile = await Profile.from_event(event)

        # Should have empty geohash
        assert profile.get_geohash() == ""

    def test_profile_geohash_empty_string(self, test_keys: NostrKeys) -> None:
        """Test that empty geohash is handled correctly"""
        profile = Profile(test_keys.get_public_key(KeyEncoding.HEX))
        profile.set_name("Test Profile")

        # Set empty geohash
        profile.set_geohash("")

        # Should be empty
        assert profile.get_geohash() == ""

        # Should be in dict
        profile_dict = profile.to_dict()
        assert "geohash" in profile_dict
        assert profile_dict["geohash"] == ""

    def test_profile_geohash_from_json_missing_field(
        self, test_keys: NostrKeys
    ) -> None:
        """Test that profile without geohash in JSON defaults to empty string"""
        profile_json = json.dumps(
            {
                "public_key": test_keys.get_public_key(KeyEncoding.HEX),
                "name": "Test Profile",
                "about": "",
                "banner": "",
                "bot": False,
                "city": "",
                "country": "",
                "created_at": 0,
                "display_name": "",
                "email": "",
                "hashtags": [],
                "locations": [],
                "namespace": "",
                "nip05": "",
                "picture": "",
                "phone": "",
                "state": "",
                "street": "",
                "website": "",
                "zip_code": "",
                # Note: geohash field is intentionally omitted
            }
        )

        profile = Profile.from_json(profile_json)

        # Should default to empty string
        assert profile.get_geohash() == ""
