import json
import logging


class Profile:
    """
    Generic Profile class that holds the metadata of a Nostr profile.
    """

    logger = logging.getLogger("Profile")

    def __init__(self) -> None:
        self.about = ""
        self.display_name = ""
        self.name = ""
        self.picture = ""
        self.website = ""

    def get_about(self) -> str:
        return self.about

    def get_display_name(self) -> str:
        return self.display_name

    def get_name(self) -> str:
        return self.name

    def get_picture(self) -> str:
        return self.picture

    def get_website(self) -> str:
        return self.website

    def set_about(self, about: str) -> None:
        self.about = about

    def set_display_name(self, display_name: str) -> None:
        self.display_name = display_name

    def set_name(self, name: str) -> None:
        self.name = name

    def set_picture(self, picture: str) -> None:
        self.picture = picture

    def set_website(self, website: str) -> None:
        self.website = website

    def to_json(self) -> str:
        data = {
            "name": self.name,
            "display_name": self.display_name,
            "about": self.about,
            "picture": self.picture,
            "website": self.website,
        }
        return json.dumps(data)
