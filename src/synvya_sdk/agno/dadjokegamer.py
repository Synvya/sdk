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
import random
from logging import DEBUG

from pydantic import ConfigDict

from synvya_sdk import Namespace, NostrClient, Profile, ProfileFilter, ProfileType

try:
    from agno.tools import Toolkit
    from agno.utils.log import logger
except ImportError as exc:
    raise ImportError(
        "`agno` not installed. Please install using `pip install agno`"
    ) from exc


class DadJokeGamerTools(Toolkit):
    """
    DadJokeTools is a toolkit that allows an agent to play the Dad Joke game.
    """

    model_config = ConfigDict(
        arbitrary_types_allowed=True, extra="allow", validate_assignment=True
    )

    def __init__(
        self,
        name: str,
        relay: str,
        private_key: str,
    ) -> None:
        """Initialize the DadJokeTools toolkit.

        Args:
            relay: Nostr relay to use for communications
            private_key: private key of the buyer using this agent
        """
        super().__init__(name=name)
        self.relay = relay
        self.private_key = private_key

        # Initialize fields
        self._nostr_client = NostrClient(relay, private_key)
        self._nostr_client.set_logging_level(logger.getEffectiveLevel())
        self.profile = self._nostr_client.get_profile()
        self.joker_public_key: str = ""

        # Register methods
        # Publisher
        self.register(self.find_joker)
        self.register(self.listen_for_joke)
        self.register(self.publish_joke)
        self.register(self.request_joke)

        # Joker
        self.register(self.listen_for_joke_request)
        self.register(self.submit_joke)

    def find_joker(self) -> str:
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
        NostrClient.logger.info("Finding jokers")
        joker_filter = ProfileFilter(
            namespace=Namespace.GAMER,
            profile_type=ProfileType.GAMER_DADJOKE,
            hashtags=["joker"],
        )

        agents = self._nostr_client.get_agents(joker_filter)

        response = {
            "status": "error",
            "message": "No valid jokers found",
        }

        if agents:
            tries = 0
            while tries < 10:
                selected_joker: Profile = random.choice(list(agents))
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

    def listen_for_joke(self, timeout: int = 60) -> str:
        """
        Listen for a joke.

        Expecting a kind:14 message containing a JSON
        object with the following fields:
        - role: "joker"
        - content: "The joke"
        """
        NostrClient.logger.info("Listening for a joke")
        try:
            message = self._nostr_client.receive_message(timeout)
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

    def publish_joke(self, joke: str, joker_public_key: str) -> str:
        """
        Publish a joke as a kind:1 event

        Args:
            joke: joke to publish

        Returns:
            str: JSON string containing the status of the publication
        """
        NostrClient.logger.info("Publishing a joke")
        try:
            text = f"Dad Joke from @{joker_public_key}:\n {joke}"
            self._nostr_client.publish_note(text)
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

    def request_joke(self, joker_public_key: str) -> str:
        """
        Request a joke from a joker.

        Args:
            joker_public_key: bech32 encoded public key of the joker

        Returns:
            str: JSON string containing the status of the request
        """
        NostrClient.logger.info("Requesting a joke")
        message = json.dumps(
            {
                "role": "publisher",
                "content": "Please send me a pg dad joke...",
            }
        )

        self._nostr_client.send_message(
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

    def listen_for_joke_request(self) -> str:
        """
        Listen for a joke request.
        """
        NostrClient.logger.info("Listening for a joke request")
        try:
            message = self._nostr_client.receive_message(timeout=7200)
            message_dict = json.loads(message)

            # let's make sure the request came from a publisher
            if message_dict.get("type") == "kind:14":
                sender = message_dict.get("sender")
                profile = self._nostr_client.get_profile(sender)
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

    def submit_joke(self, joke: str, publisher: str) -> str:
        """
        Submit a joke.
        """
        NostrClient.logger.info("Submitting a joke")
        try:
            self._nostr_client.send_message(
                "kind:14",
                publisher,
                json.dumps({"role": "joker", "content": joke}),
            )
            return json.dumps({"status": "success", "message": "Joke submitted"})
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)})

    def set_profile(self, profile: Profile) -> str:
        """
        Sets the profile used by the Toolkit.
        The profile is also published to the Nostr network.

        Returns:
            str: id of the event publishing the profile

        Raises:
            RuntimeError: if it can't publish the event
        """
        if self._nostr_client is None:
            logger.error("NostrClient not initialized")
            raise ValueError("NostrClient not initialized")

        try:
            return self._nostr_client.set_profile(profile)
        except RuntimeError as e:
            logger.error("Unable to publish the profile: %s", e)
            raise RuntimeError(f"Unable to publish the profile: {e}") from e

    def get_profile(self) -> str:
        """
        Get the merchant profile in JSON format

        Returns:
            str: merchant profile in JSON format
        """
        return json.dumps(self.profile.to_json())
