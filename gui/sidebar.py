import customtkinter as ctk



class Sidebar(ctk.CTkFrame):


    def __init__(
        self,
        parent,
        callbacks
    ):

        super().__init__(
            parent,
            width=200
        )


        self.pack_propagate(
            False
        )


        title = ctk.CTkLabel(

            self,

            text="YT Downloader",

            font=(
                "Arial",
                20,
                "bold"
            )

        )

        title.pack(
            pady=30
        )



        buttons = [

            (
                "Analyze",
                callbacks["analyze"]
            ),

            (
                "History",
                callbacks["history"]
            ),

            (
                "Settings",
                callbacks["settings"]
            )

        ]


        for text, command in buttons:


            button = ctk.CTkButton(

                self,

                text=text,

                command=command

            )


            button.pack(

                padx=20,

                pady=10

            )