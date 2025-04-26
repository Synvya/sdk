from typing import ClassVar, List, Optional, Set, Union

from pydantic import ConfigDict

from agno.tools import Toolkit
from synvya_sdk import NostrClient, Profile

class DadJokeGamerTools(Toolkit):
    # Class variables
    _instances_from_create: ClassVar[Set[int]]
    model_config: ClassVar[ConfigDict]

    # Instance variables
    relays: List[str]
    private_key: str
    profile: Optional[Profile]
    nostr_client: Optional[NostrClient]
    joker_public_key: Optional[str]
    _instance_id: int

    # Initialization
    def __init__(
        self,
        name: str,
        relays: Union[str, List[str]],
        private_key: str,
        _from_create: bool = False,
    ) -> None: ...
    def __del__(self) -> None: ...
    @classmethod
    async def create(
        cls, name: str, relays: Union[str, List[str]], private_key: str
    ) -> "DadJokeGamerTools": ...

    # Publisher methods
    async def async_find_joker(self) -> str: ...
    async def async_listen_for_joke(self, timeout: int = 60) -> str: ...
    async def async_publish_joke(self, joke: str, joker_public_key: str) -> str: ...
    async def async_request_joke(self, joker_public_key: str) -> str: ...

    # Joker methods
    async def async_listen_for_joke_request(self, timeout: int = 7200) -> str: ...
    async def async_submit_joke(self, joke: str, publisher: str) -> str: ...

    # Common methods
    async def async_set_profile(self, profile: Profile) -> str: ...
    def get_profile(self) -> str: ...
