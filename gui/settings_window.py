import customtkinter as ctk
from tkinter import filedialog


class SettingsWindow(ctk.CTkToplevel):
    """
    Application settings window.
    """


    def __init__(
        self,
        parent,
        settings,
        on_save=None
    ):

        super().__init__(
            parent
        )


        self.settings = settings
        self.on_save = on_save


        self.title(
            "Settings"
        )


        self.geometry(
            "500x450"
        )


        self.create_widgets()



    def create_widgets(self):


        title = ctk.CTkLabel(

            self,

            text="Application Settings",

            font=(
                "Arial",
                24,
                "bold"
            )

        )


        title.pack(
            pady=20
        )



        # ---------------- Download Folder ----------------


        folder_label = ctk.CTkLabel(

            self,

            text="Default Download Folder"

        )


        folder_label.pack(
            anchor="w",
            padx=30
        )



        folder_frame = ctk.CTkFrame(
            self
        )


        folder_frame.pack(
            pady=10,
            padx=30,
            fill="x"
        )



        self.folder_entry = ctk.CTkEntry(

            folder_frame

        )


        self.folder_entry.pack(

            side="left",

            expand=True,

            fill="x",

            padx=10

        )



        current_folder = self.settings.get(
            "download_folder"
        )


        if current_folder:

            self.folder_entry.insert(
                0,
                current_folder
            )



        browse = ctk.CTkButton(

            folder_frame,

            text="Browse",

            command=self.select_folder

        )


        browse.pack(
            side="right",
            padx=10
        )




        # ---------------- Quality ----------------


        quality_label = ctk.CTkLabel(

            self,

            text="Default Quality"

        )


        quality_label.pack(
            anchor="w",
            padx=30,
            pady=(20,0)
        )



        self.quality_menu = ctk.CTkOptionMenu(

            self,

            values=[

                "1080p",

                "720p",

                "Best Available"

            ]

        )


        self.quality_menu.pack(
            padx=30,
            pady=10
        )



        current_quality = self.settings.get(
            "quality"
        )


        self.quality_menu.set(
            current_quality
        )




        # ---------------- Theme ----------------


        theme_label = ctk.CTkLabel(

            self,

            text="Theme"

        )


        theme_label.pack(
            anchor="w",
            padx=30,
            pady=(20,0)
        )



        self.theme_menu = ctk.CTkOptionMenu(

            self,

            values=[

                "Dark",

                "Light",

                "System"

            ]

        )


        self.theme_menu.pack(
            padx=30,
            pady=10
        )



        current_theme = self.settings.get(
            "theme"
        )


        self.theme_menu.set(
            current_theme
        )




        # ---------------- Save ----------------


        save_button = ctk.CTkButton(

            self,

            text="Save Settings",

            command=self.save_settings

        )


        save_button.pack(

            pady=30

        )




    def select_folder(self):


        folder = filedialog.askdirectory()


        if folder:

            self.folder_entry.delete(
                0,
                "end"
            )


            self.folder_entry.insert(
                0,
                folder
            )




    def save_settings(self):


        self.settings.update({

            "download_folder":
                self.folder_entry.get(),


            "quality":
                self.quality_menu.get(),


            "theme":
                self.theme_menu.get()

        })


        self.settings.save_settings()


        if self.on_save:

            self.on_save()


        self.destroy()