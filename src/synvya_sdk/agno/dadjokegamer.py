"""
Module implementing the DadJokeTools Toolkit for Agno agents.

Publisher sends a joke request to a joker:
{
    "role": "publisher",
    "content": "Please send me a pg dad joke..."
}

Joker receives the joke request and sends a joke to the publisher:
{
    "role": "joker",
    "content": "Why did the chicken cross the road?"
}
"""

import json
import secrets
from typing import List, Optional, Union

from pydantic import ConfigDict

from synvya_sdk import Namespace, NostrClient, Profile, ProfileFilter, ProfileType

try:
    from agno.tools import Toolkit
    from agno.utils.log import logger
except ImportError as exc:
    raise ImportError(
        "Package `agno` not installed. Please install using `pip install agno`"
    ) from exc


class DadJokeGamerTools(Toolkit):
    """
    DadJokeTools is a toolkit that allows an agent to play the Dad Joke game.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, extra="allow", validate_assignment=True
    )

    _instances_from_create: set[int] = set()

    def __init__(
        self,
        name: str,
        relays: Union[str, List[str]],
        private_key: str,
        _from_create: bool = False,
    ) -> None:
        """
        Initialize the DadJokeGamerTools object.

        Args:
            name: Name of the gamer
            relays: Nostr relay(s) that the client will connect to. Can be a single URL string or a list of URLs.
            private_key: Private key for the client in hex or bech32 format
            _from_create: Internal flag to ensure proper initialization flow
        """
        if not _from_create:
            raise RuntimeError(
                "DadJokeGamerTools must be created using the create() method"
            )

        # Track instance ID
        self._instance_id = id(self)
        DadJokeGamerTools._instances_from_create.add(self._instance_id)

        super().__init__(name=name)

        # Set include_tools to None to allow all tools to be registered
        self.include_tools = None

        # Convert single relay to list for consistent handling
        self.relays: List[str] = [relays] if isinstance(relays, str) else relays
        self.private_key: str = private_key
        self.nostr_client: Optional[NostrClient] = None
        self.profile: Optional[Profile] = None
        self.joker_public_key: Optional[str] = None

        # Register methods
        # Publisher
        self.register(self.async_find_joker)
        self.register(self.async_listen_for_joke)
        self.register(self.async_publish_joke)
        self.register(self.async_request_joke)

        # Joker
        self.register(self.async_listen_for_joke_request)
        self.register(self.async_submit_joke)

    def __del__(self) -> None:
        """
        Delete the DadJokeGamerTools instance.
        """
        if hasattr(self, "_instance_id"):
            DadJokeGamerTools._instances_from_create.discard(self._instance_id)

    @classmethod
    async def create(
        cls, name: str, relays: Union[str, List[str]], private_key: str
    ) -> "DadJokeGamerTools":
        """
        Asynchronous factory method for proper initialization.
        Use instead of the __init__ method.

        Args:
            name: Name of the gamer
            relays: Nostr relay(s) that the client will connect to. Can be a single URL string or a list of URLs.
            private_key: Private key for the client in hex or bech32 format

        Returns:
            DadJokeGamerTools: An initialized DadJokeGamerTools instance
        """
        instance = cls(name, relays, private_key, _from_create=True)

        # Initialize NostrClient asynchronously
        instance.nostr_client = await NostrClient.create(relays, private_key)
        instance.profile = await instance.nostr_client.async_get_profile()
        instance.nostr_client.set_logging_level(logger.getEffectiveLevel())
        return instance

    async def async_find_joker(self) -> str:
        """
        Finds all jokers in the network and selects one at random.
        Jokers are defined as Profiles meeting the following criteria:
        - Must have a validated NIP-05 identity.
        - Must have the metadata field `bot` set to true.
        - The kind:0 event must include the label `dad-joke-game` with
        namespace `com.synvya.gamer`
        - The kind:0 event must include the hashtag `joker`

        Returns:
            str: JSON string containing the bech32 encoded public key of the joker
        """
        if self.nostr_client is None:
            raise RuntimeError("NostrClient not initialized. Call create() first.")

        NostrClient.logger.info("Finding jokers")
        joker_filter = ProfileFilter(
            namespace=Namespace.GAMER,
            profile_type=ProfileType.GAMER_DADJOKE,
            hashtags=["joker"],
        )

        agents = await self.nostr_client.async_get_agents(joker_filter)

        response = {
            "status": "error",
            "message": "No valid jokers found",
        }

        if agents:
            tries = 0
            while tries < 10:
                # Use secrets for secure random selection
                agents_list = list(agents)
                selected_joker: Profile = agents_list[
                    secrets.randbelow(len(agents_list))
                ]
                if selected_joker.is_nip05_validated() and selected_joker.is_bot():
                    response = {
                        "status": "success",
                        "joker": selected_joker.get_public_key(encoding="bech32"),
                    }
                    self.joker_public_key = selected_joker.get_public_key(
                        encoding="bech32"
                    )
                    break
                tries += 1
        return json.dumps(response)

    async def async_listen_for_joke(self, timeout: int = 60) -> str:
        """
        Listen for a joke.

        Expecting a kind:14 message containing a JSON
        object with the following fields:
        - role: "joker"
        - content: "The joke"
        """
        if self.nostr_client is None:
            raise RuntimeError("NostrClient not initialized. Call create() first.")

        NostrClient.logger.info("Listening for a joke")
        try:
            message = await self.nostr_client.async_receive_message(timeout)
            message_dict = json.loads(message)
            # let's make sure the joke came from the joker we request the joke from
            if message_dict.get("sender") != self.joker_public_key:
                return json.dumps({"status": "error", "message": "Unknown message"})

            message_type = message_dict.get("type")
            if message_type == "kind:14":
                content_dict = json.loads(message_dict.get("content"))
                if content_dict.get("role") == "joker":
                    return json.dumps(
                        {
                            "status": "success",
                            "joke": content_dict.get("content"),
                            "joker": message_dict.get("sender"),
                        }
                    )
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": str(e),
                }
            )
        return json.dumps({"status": "error", "message": "No joke received."})

    async def async_publish_joke(self, joke: str, joker_public_key: str) -> str:
        """
        Publish a joke as a kind:1 event

        Args:
            joke: joke to publish

        Returns:
            str: JSON string containing the status of the publication
        """
        if self.nostr_client is None:
            raise RuntimeError("NostrClient not initialized. Call create() first.")

        NostrClient.logger.info("Publishing a joke")
        try:
            text = f"Dad Joke from @{joker_public_key}:\n {joke}"
            await self.nostr_client.async_publish_note(text)
            return json.dumps(
                {
                    "status": "success",
                    "message": "Joke published",
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "status": "error",
                    "message": str(e),
                }
            )

    async def async_request_joke(self, joker_public_key: str) -> str:
        """
        Request a joke from a joker.

        Args:
            joker_public_key: bech32 encoded public key of the joker

        Returns:
            str: JSON string containing the status of the request
        """
        if self.nostr_client is None:
            raise RuntimeError("NostrClient not initialized. Call create() first.")

        NostrClient.logger.info("Requesting a joke")
        message = json.dumps(
            {
                "role": "publisher",
                "content": "Please send me a pg dad joke...",
            }
        )

        await self.nostr_client.async_send_message(
            "kind:14",
            joker_public_key,
            message,
        )

        return json.dumps(
            {
                "status": "success",
                "message": "Joke requested",
            }
        )

    async def async_listen_for_joke_request(self, timeout: int = 7200) -> str:
        """
        Listen for a joke request.
        """
        if self.nostr_client is None:
            raise RuntimeError("NostrClient not initialized. Call create() first.")

        NostrClient.logger.info("Listening for a joke request")
        try:
            message = await self.nostr_client.async_receive_message(timeout)
            message_dict = json.loads(message)

            # let's make sure the request came from a publisher
            if message_dict.get("type") == "kind:14":
                sender = message_dict.get("sender")
                profile = await self.nostr_client.async_get_profile(sender)
                if (
                    profile.get_namespace() == Namespace.GAMER
                    and profile.get_profile_type() == ProfileType.GAMER_DADJOKE
                    and "publisher" in profile.get_hashtags()
                ):
                    message_content = json.loads(message_dict.get("content"))
                    if message_content.get("role") == "publisher":
                        return json.dumps(
                            {
                                "status": "success",
                                "message": "Joke request received",
                                "publisher": sender,
                            }
                        )
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})
        return json.dumps({"status": "error", "message": "No joke request received."})

    async def async_submit_joke(self, joke: str, publisher: str) -> str:
        """
        Submit a joke.
        """
        if self.nostr_client is None:
            raise RuntimeError("NostrClient not initialized. Call create() first.")

        NostrClient.logger.info("Submitting a joke")
        try:
            await self.nostr_client.async_send_message(
                "kind:14",
                publisher,
                json.dumps({"role": "joker", "content": joke}),
            )
            return json.dumps({"status": "success", "message": "Joke submitted"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    async def async_set_profile(self, profile: Profile) -> str:
        """
        Sets the profile used by the Toolkit.
        The profile is also published to the Nostr network.

        Returns:
            str: id of the event publishing the profile

        Raises:
            RuntimeError: if it can't publish the event
        """
        if self.nostr_client is None:
            raise RuntimeError("NostrClient not initialized. Call create() first.")

        try:
            result: str = await self.nostr_client.async_set_profile(profile)
            return result
        except RuntimeError as e:
            logger.error("Unable to publish the profile: %s", e)
            raise RuntimeError(f"Unable to publish the profile: {e}") from e

    def get_profile(self) -> str:
        """
        Get the merchant profile in JSON format

        Returns:
            str: merchant profile in JSON format
        """
        if self.profile is None:
            raise RuntimeError("Profile not initialized. Call create() first.")
        return json.dumps(self.profile.to_json())
