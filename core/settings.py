import json
from pathlib import Path
from typing import Any


class SettingsManager:
    """
    Handles application settings stored in settings.json.
    """


    DEFAULT_SETTINGS = {

        "download_folder": "",

        "quality": "1080p",

        "theme": "dark",

        "last_playlist": "",

        "max_threads": 3

    }



    def __init__(
        self,
        file_path: str = "settings.json"
    ):

        self.file_path = Path(
            file_path
        )

        self.settings = {}

        self.load_settings()



    def load_settings(self) -> None:
        """
        Loads settings from JSON file.
        Creates file if it does not exist.
        """


        if not self.file_path.exists():

            self.settings = self.DEFAULT_SETTINGS.copy()

            self.save_settings()

            return



        try:

            with open(
                self.file_path,
                "r",
                encoding="utf-8"
            ) as file:

                self.settings = json.load(file)



            # Add missing settings

            for key, value in self.DEFAULT_SETTINGS.items():

                if key not in self.settings:

                    self.settings[key] = value



            # Save if new keys were added

            self.save_settings()



        except (
            json.JSONDecodeError,
            IOError
        ):

            self.settings = self.DEFAULT_SETTINGS.copy()

            self.save_settings()



    def save_settings(self) -> None:
        """
        Saves current settings permanently.
        """


        with open(
            self.file_path,
            "w",
            encoding="utf-8"
        ) as file:


            json.dump(

                self.settings,

                file,

                indent=4

            )



    def get(
        self,
        key: str
    ) -> Any:
        """
        Returns a setting value.
        """


        return self.settings.get(

            key,

            self.DEFAULT_SETTINGS.get(key)

        )



    def set(
        self,
        key: str,
        value: Any
    ) -> None:
        """
        Updates a setting.
        """


        self.settings[key] = value



    def update(
        self,
        new_settings: dict
    ) -> None:
        """
        Updates multiple settings.
        """


        self.settings.update(
            new_settings
        )



    def reset(self) -> None:
        """
        Restores default settings.
        """


        self.settings = self.DEFAULT_SETTINGS.copy()

        self.save_settings()