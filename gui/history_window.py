import customtkinter as ctk
from tkinter import ttk, messagebox


class HistoryWindow(ctk.CTkToplevel):
    """
    Displays download history.
    """


    def __init__(self, parent, database):
        super().__init__(parent)


        self.database = database


        self.title(
            "Download History"
        )


        self.geometry(
            "1000x500"
        )


        self.create_widgets()


        self.load_history()



    def create_widgets(self):


        title = ctk.CTkLabel(
            self,
            text="Download History",
            font=(
                "Arial",
                24,
                "bold"
            )
        )

        title.pack(
            pady=15
        )


        # Table


        columns = (

            "Title",
            "URL",
            "Path",
            "Date",
            "Status"

        )


        self.table = ttk.Treeview(

            self,

            columns=columns,

            show="headings"

        )


        for column in columns:

            self.table.heading(
                column,
                text=column
            )


            self.table.column(
                column,
                width=180
            )


        self.table.pack(

            fill="both",

            expand=True,

            padx=20,

            pady=10

        )



        # Buttons


        button_frame = ctk.CTkFrame(
            self
        )


        button_frame.pack(
            pady=10
        )


        refresh = ctk.CTkButton(

            button_frame,

            text="Refresh",

            command=self.load_history

        )

        refresh.pack(

            side="left",

            padx=10

        )



        delete = ctk.CTkButton(

            button_frame,

            text="Delete Selected",

            command=self.delete_selected

        )

        delete.pack(

            side="left",

            padx=10

        )



        clear = ctk.CTkButton(

            button_frame,

            text="Clear History",

            command=self.clear_history

        )

        clear.pack(

            side="left",

            padx=10

        )



    def load_history(self):

        """
        Loads records from database.
        """


        # Remove old rows

        for item in self.table.get_children():

            self.table.delete(
                item
            )



        history = self.database.get_download_history()



        for row in history:


            self.table.insert(

                "",

                "end",

                values=row

            )



    def delete_selected(self):

        """
        Deletes selected history item.
        """


        selected = self.table.selection()


        if not selected:

            return



        item = self.table.item(
            selected[0]
        )


        values = item["values"]


        video_url = values[1]


        video_id = video_url.split(
            "v="
        )[-1]



        confirm = messagebox.askyesno(

            "Confirm",

            "Delete selected history?"

        )


        if confirm:

            self.database.remove_video(
                video_id
            )


            self.load_history()



    def clear_history(self):

        confirm = messagebox.askyesno(

            "Confirm",

            "Delete all history?"

        )


        if confirm:

            self.database.clear_history()


            self.load_history()