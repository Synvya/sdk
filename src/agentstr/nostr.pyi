from datetime import datetime
from typing import List, Optional, Union

class PublicKey:
    @classmethod
    def parse(cls, hex_str: str) -> "PublicKey": ...

class Kind:
    def __init__(self, value: int) -> None: ...

class Timestamp:
    @classmethod
    def from_secs(cls, secs: int) -> "Timestamp": ...

class Event:
    def __init__(
        self,
        id: str,
        pubkey: PublicKey,
        created_at: Timestamp,
        kind: Kind,
        tags: List[List[str]],
        content: str,
    ) -> None: ...

class EventBuilder:
    def __init__(self, content: str) -> None: ...
    def kind(self, kind: Kind) -> "EventBuilder": ...
    def tags(self, tags: List[List[str]]) -> "EventBuilder": ...

class Keys:
    def __init__(self, secret_key: Optional[str] = None) -> None: ...
    @property
    def public_key(self) -> PublicKey: ...

class Metadata:
    def __init__(self, name: str, about: str, picture: str) -> None: ...
