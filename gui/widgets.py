import customtkinter as ctk



class SectionFrame(ctk.CTkFrame):
    """
    Reusable application section.
    """

    def __init__(
        self,
        parent,
        title=None,
        **kwargs
    ):

        super().__init__(
            parent,
            **kwargs
        )


        if title:

            label = ctk.CTkLabel(

                self,

                text=title,

                font=(
                    "Arial",
                    16,
                    "bold"
                )

            )

            label.pack(

                anchor="w",

                padx=10,

                pady=5

            )



class StatusCard(ctk.CTkFrame):
    """
    Displays status information.
    """


    def __init__(
        self,
        parent,
        title
    ):

        super().__init__(
            parent
        )


        self.title = ctk.CTkLabel(

            self,

            text=title,

            font=(
                "Arial",
                14,
                "bold"
            )

        )

        self.title.pack(
            pady=5
        )


        self.value = ctk.CTkLabel(

            self,

            text="0",

            font=(
                "Arial",
                22
            )

        )

        self.value.pack(
            pady=5
        )



    def update(
        self,
        text
    ):

        self.value.configure(
            text=text
        )