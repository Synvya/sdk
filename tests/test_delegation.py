"""
Tests for the Delegation class (NIP-26 support).

This test suite covers the complete functionality of the Delegation class including:

1. **Happy Path Tests:**
   - Valid delegation parsing from dict and JSON string
   - Successful event validation for allowed kinds and non-expired delegations
   - Proper access to delegation properties (tag, author, etc.)

2. **Error Cases:**
   - Wrong event kind (not 30078)
   - Invalid merchant signatures
   - Missing delegation tags
   - Expired delegations
   - Event kinds not allowed by delegation

3. **Edge Cases:**
   - Malformed conditions strings
   - Non-numeric kinds in conditions
   - Empty allowed_kinds (accepting all kinds)

The tests use mocks to avoid dependency on actual Nostr event verification
while ensuring the delegation logic works correctly.
"""

import json
import time
from unittest.mock import Mock, patch

import pytest
from nostr_sdk import Event

from synvya_sdk.models import Delegation


class TestDelegation:
    """Test suite for Delegation class"""

    @pytest.fixture
    def valid_delegation_event(self) -> dict:
        """Fixture providing a valid delegation event"""
        return {
            "kind": 30078,
            "pubkey": "merchant_pubkey_hex",
            "created_at": int(time.time()) - 3600,  # Created 1 hour ago
            "content": "",
            "tags": [
                [
                    "delegation",
                    "delegatee_pubkey_hex",
                    (
                        f"kind=30017,30018&created_at={int(time.time()) - 3600}"
                        f"&expires_at={int(time.time()) + 3600}"
                    ),
                    "delegation_token_signature",
                ]
            ],
            "sig": "valid_signature",
        }

    @pytest.fixture
    def expired_delegation_event(self) -> dict:
        """Fixture providing an expired delegation event"""
        expired_time = int(time.time()) - 1800  # Expired 30 minutes ago
        return {
            "kind": 30078,
            "pubkey": "merchant_pubkey_hex",
            "created_at": int(time.time()) - 7200,  # Created 2 hours ago
            "content": "",
            "tags": [
                [
                    "delegation",
                    "delegatee_pubkey_hex",
                    (
                        f"kind=30017,30018&created_at={int(time.time()) - 7200}"
                        f"&expires_at={expired_time}"
                    ),
                    "delegation_token_signature",
                ]
            ],
            "sig": "valid_signature",
        }

    @pytest.fixture
    def wrong_kind_delegation_event(self) -> dict:
        """Fixture providing a delegation event with wrong kind"""
        return {
            "kind": 1,  # Wrong kind (should be 30078)
            "pubkey": "merchant_pubkey_hex",
            "created_at": int(time.time()) - 3600,
            "content": "This is not a delegation",
            "tags": [],
            "sig": "some_signature",
        }

    @pytest.fixture
    def mock_event_allowed_kind(self) -> Mock:
        """Mock Event object with allowed kind"""
        mock = Mock(spec=Event)
        mock.kind.return_value = 30017
        return mock

    @pytest.fixture
    def mock_event_wrong_kind(self) -> Mock:
        """Mock Event object with wrong kind"""
        mock = Mock(spec=Event)
        mock.kind.return_value = 1  # Note kind (not allowed)
        return mock

    def test_parse_valid_delegation_success(self, valid_delegation_event: dict) -> None:
        """Test parsing a valid delegation event succeeds"""
        with patch("synvya_sdk.models.Event") as mock_event_class:
            # Mock Event.from_json and verify methods
            mock_event = Mock()
            mock_event.verify.return_value = True
            mock_event_class.from_json.return_value = mock_event

            # Test parsing from dict
            delegation = Delegation.parse(valid_delegation_event)

            assert delegation.author == "merchant_pubkey_hex"
            assert delegation.sig == "valid_signature"
            assert 30017 in delegation.allowed_kinds
            assert 30018 in delegation.allowed_kinds
            assert len(delegation.tag) == 4
            assert delegation.tag[0] == "delegation"

    def test_parse_valid_delegation_json_string(
        self, valid_delegation_event: dict
    ) -> None:
        """Test parsing a valid delegation event from JSON string"""
        with patch("synvya_sdk.models.Event") as mock_event_class:
            mock_event = Mock()
            mock_event.verify.return_value = True
            mock_event_class.from_json.return_value = mock_event

            json_string = json.dumps(valid_delegation_event)
            delegation = Delegation.parse(json_string)

            assert delegation.author == "merchant_pubkey_hex"
            assert 30017 in delegation.allowed_kinds
            assert 30018 in delegation.allowed_kinds

    def test_parse_wrong_kind_raises_error(
        self, wrong_kind_delegation_event: dict
    ) -> None:
        """Test parsing event with wrong kind raises ValueError"""
        with pytest.raises(
            ValueError, match="Event is not a delegation \\(kind 30078\\)"
        ):
            Delegation.parse(wrong_kind_delegation_event)

    def test_parse_invalid_signature_raises_error(
        self, valid_delegation_event: dict
    ) -> None:
        """Test parsing event with invalid signature raises ValueError"""
        with patch("synvya_sdk.models.Event") as mock_event_class:
            # Mock Event.from_json but verify returns False (invalid signature)
            mock_event = Mock()
            mock_event.verify.return_value = False
            mock_event_class.from_json.return_value = mock_event

            with pytest.raises(ValueError, match="Invalid delegation signature"):
                Delegation.parse(valid_delegation_event)

    def test_parse_missing_delegation_tag_raises_error(
        self, valid_delegation_event: dict
    ) -> None:
        """Test parsing event without delegation tag raises ValueError"""
        # Remove delegation tag
        valid_delegation_event["tags"] = [["some", "other", "tag"]]

        with patch("synvya_sdk.models.Event") as mock_event_class:
            mock_event = Mock()
            mock_event.verify.return_value = True
            mock_event_class.from_json.return_value = mock_event

            with pytest.raises(ValueError, match="Delegation tag missing"):
                Delegation.parse(valid_delegation_event)

    def test_validate_event_success(
        self, valid_delegation_event: dict, mock_event_allowed_kind: Mock
    ) -> None:
        """Test validate_event succeeds for allowed kind and non-expired delegation"""
        with patch("synvya_sdk.models.Event") as mock_event_class:
            mock_event_obj = Mock()
            mock_event_obj.verify.return_value = True
            mock_event_class.from_json.return_value = mock_event_obj

            delegation = Delegation.parse(valid_delegation_event)

            # Should not raise any exception
            delegation.validate_event(mock_event_allowed_kind)

    def test_validate_event_expired_delegation_raises_error(
        self, expired_delegation_event: dict, mock_event_allowed_kind: Mock
    ) -> None:
        """Test validate_event raises ValueError for expired delegation"""
        with patch("synvya_sdk.models.Event") as mock_event_class:
            mock_event_obj = Mock()
            mock_event_obj.verify.return_value = True
            mock_event_class.from_json.return_value = mock_event_obj

            delegation = Delegation.parse(expired_delegation_event)

            with pytest.raises(ValueError, match="Delegation expired"):
                delegation.validate_event(mock_event_allowed_kind)

    def test_validate_event_kind_not_allowed_raises_error(
        self, valid_delegation_event: dict, mock_event_wrong_kind: Mock
    ) -> None:
        """Test validate_event raises ValueError for disallowed event kind"""
        with patch("synvya_sdk.models.Event") as mock_event_class:
            mock_event_obj = Mock()
            mock_event_obj.verify.return_value = True
            mock_event_class.from_json.return_value = mock_event_obj

            delegation = Delegation.parse(valid_delegation_event)

            with pytest.raises(
                ValueError, match="Event kind not allowed by delegation"
            ):
                delegation.validate_event(mock_event_wrong_kind)

    def test_validate_event_empty_allowed_kinds_accepts_all(
        self, valid_delegation_event: dict, mock_event_wrong_kind: Mock
    ) -> None:
        """Test validate_event accepts any kind when allowed_kinds is empty"""
        # Modify delegation to have no specific kinds allowed
        valid_delegation_event["tags"][0][
            2
        ] = f"created_at={int(time.time()) - 3600}&expires_at={int(time.time()) + 3600}"

        with patch("synvya_sdk.models.Event") as mock_event_class:
            mock_event_obj = Mock()
            mock_event_obj.verify.return_value = True
            mock_event_class.from_json.return_value = mock_event_obj

            delegation = Delegation.parse(valid_delegation_event)

            # Should not raise any exception even for "wrong" kind
            delegation.validate_event(mock_event_wrong_kind)

    def test_delegation_tag_property(self, valid_delegation_event: dict) -> None:
        """Test delegation_tag property returns the correct tag"""
        with patch("synvya_sdk.models.Event") as mock_event_class:
            mock_event = Mock()
            mock_event.verify.return_value = True
            mock_event_class.from_json.return_value = mock_event

            delegation = Delegation.parse(valid_delegation_event)

            tag = delegation.delegation_tag
            assert tag == valid_delegation_event["tags"][0]
            assert tag[0] == "delegation"
            assert len(tag) == 4

    def test_parse_malformed_conditions_handles_gracefully(
        self, valid_delegation_event: dict
    ) -> None:
        """Test parsing delegation with malformed conditions string"""
        # Create malformed conditions string
        valid_delegation_event["tags"][0][2] = "malformed&conditions&without=equals"

        with patch("synvya_sdk.models.Event") as mock_event_class:
            mock_event = Mock()
            mock_event.verify.return_value = True
            mock_event_class.from_json.return_value = mock_event

            delegation = Delegation.parse(valid_delegation_event)

            # Should parse without error, but allowed_kinds might be empty
            assert isinstance(delegation.allowed_kinds, set)

    def test_parse_handles_non_numeric_kinds(
        self, valid_delegation_event: dict
    ) -> None:
        """Test parsing delegation with non-numeric kinds in conditions"""
        # Add non-numeric kinds that should be filtered out
        valid_delegation_event["tags"][0][
            2
        ] = "kind=30017,invalid,30018,abc&created_at=123&expires_at=456"

        with patch("synvya_sdk.models.Event") as mock_event_class:
            mock_event = Mock()
            mock_event.verify.return_value = True
            mock_event_class.from_json.return_value = mock_event

            delegation = Delegation.parse(valid_delegation_event)

            # Should only include numeric kinds
            assert 30017 in delegation.allowed_kinds
            assert 30018 in delegation.allowed_kinds
            assert len(delegation.allowed_kinds) == 2
