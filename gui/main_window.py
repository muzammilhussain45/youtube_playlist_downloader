import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading


from core.settings import SettingsManager
from core.database import DatabaseManager
from core.playlist import PlaylistAnalyzer
from core.downloader import VideoDownloader
from core.queue_manager import DownloadQueue
from gui.history_window import HistoryWindow
from gui.sidebar import Sidebar
from gui.widgets import SectionFrame, StatusCard
from gui.widgets import StatusCard
from gui.settings_window import SettingsWindow
from core.system_check import check_ffmpeg


class MainWindow(ctk.CTk):
    """
    Main application window.
    """

    def __init__(self):
        super().__init__()
      
        self.settings = SettingsManager()
        self.database = DatabaseManager()

        # Check FFmpeg availability

        if not check_ffmpeg():

            messagebox.showwarning(

                "FFmpeg Missing",

                "FFmpeg was not detected.\n\n"
                "For best quality downloads, please install FFmpeg "
                "and add it to your system PATH."

            )

        self.playlist_analyzer = PlaylistAnalyzer(
            self.database
        )
        self.downloader = VideoDownloader(
            self.database
        )


        self.current_playlist_result = None
        self.download_queue = DownloadQueue(
            self.database
        )
        self.title("YouTube Playlist Downloader")

        self.geometry("900x650")

        self.minsize(
            850,
            600
        )

        # Theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")


        self.download_folder = self.settings.get("download_folder")


        self.create_widgets()
        self.check_previous_session()
        # Handle application closing
        self.protocol(
           "WM_DELETE_WINDOW",
            self.close_application
        )



    def create_widgets(self):
        """
        Creates all GUI components.
        """


        # ================= Main Container =================

        self.container = ctk.CTkFrame(
            self
        )

        self.container.pack(
            fill="both",
            expand=True
        )


        # ================= Sidebar =================

        self.sidebar = Sidebar(

            self.container,

            {
                "analyze": self.analyze_playlist,
                "history": self.open_history,
                "settings": self.open_settings
            }

        )


        self.sidebar.pack(

            side="left",

            fill="y"

        )



        # ================= Main Area =================

        self.main_area = ctk.CTkFrame(
            self.container
        )


        self.main_area.pack(

            side="right",

            fill="both",

            expand=True,

            padx=20,

            pady=20

        )



        # ---------------- Header ----------------


        self.header = ctk.CTkLabel(
            self.main_area,
            text="YouTube Playlist Downloader",
            font=(
                "Arial",
                26,
                "bold"
            )
        )

        self.header.pack(
            pady=20
        )




        # ---------------- Playlist Frame ----------------


        playlist_frame = ctk.CTkFrame(
            self.main_area
        )


        playlist_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )


        playlist_label = ctk.CTkLabel(
            playlist_frame,
            text="Playlist URL"
        )


        playlist_label.pack(
            anchor="w",
            padx=10,
            pady=5
        )


        self.playlist_entry = ctk.CTkEntry(
            playlist_frame,
            width=700,
            placeholder_text="Paste YouTube playlist URL"
        )


        last_playlist = self.settings.get(
            "last_playlist"
        )


        if last_playlist:

            self.playlist_entry.insert(
                0,
                last_playlist
            )


        self.playlist_entry.pack(
            padx=10,
            pady=10
        )




        # ---------------- Folder Section ----------------


        folder_frame = ctk.CTkFrame(
            self.main_area
        )


        folder_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )


        folder_label = ctk.CTkLabel(
            folder_frame,
            text="Download Folder"
        )


        folder_label.pack(
            anchor="w",
            padx=10
        )


        folder_inside = ctk.CTkFrame(
            folder_frame,
            fg_color="transparent"
        )


        folder_inside.pack(
            pady=10
        )


        self.folder_entry = ctk.CTkEntry(
            folder_inside,
            width=550
        )


        saved_folder = self.settings.get(
            "download_folder"
        )


        if saved_folder:

            self.folder_entry.insert(
                0,
                saved_folder
            )


        self.folder_entry.pack(
            side="left",
            padx=10
        )


        browse_button = ctk.CTkButton(
            folder_inside,
            text="Browse",
            command=self.select_folder
        )


        browse_button.pack(
            side="left"
        )




        # ---------------- Quality ----------------


        quality_frame = ctk.CTkFrame(
            self.main_area
        )


        quality_frame.pack(
            padx=30,
            pady=10,
            fill="x"
        )


        quality_label = ctk.CTkLabel(
            quality_frame,
            text="Quality"
        )


        quality_label.pack(
            side="left",
            padx=10
        )


        self.quality_dropdown = ctk.CTkOptionMenu(
            quality_frame,
            values=[
                "1080p",
                "720p",
                "Best Available"
            ]
        )


        saved_quality = self.settings.get(
            "quality"
        )


        self.quality_dropdown.set(
            saved_quality
        )


        self.quality_dropdown.pack(
            side="left",
            padx=10
        )




        # ---------------- Buttons ----------------


        button_frame = ctk.CTkFrame(
            self.main_area
        )


        button_frame.pack(
            pady=20
        )



        self.history_button = ctk.CTkButton(

            button_frame,

            text="History",

            command=self.open_history

        )


        self.history_button.pack(

            side="left",

            padx=10

        )



        self.analyze_button = ctk.CTkButton(
            button_frame,
            text="Analyze Playlist",
            command=self.analyze_playlist
        )


        self.analyze_button.pack(
            side="left",
            padx=10
        )



        self.start_button = ctk.CTkButton(
            button_frame,
            text="Start Download",
            command=self.start_download
        )


        self.start_button.pack(
            side="left",
            padx=10
        )



        self.pause_button = ctk.CTkButton(
            button_frame,
            text="Pause",
            command=self.pause_download
        )


        self.pause_button.pack(
            side="left",
            padx=10
        )



        self.resume_button = ctk.CTkButton(
            button_frame,
            text="Resume",
            command=self.resume_download
        )


        self.resume_button.pack(
            side="left",
            padx=10
        )



        self.cancel_button = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.cancel_download
        )


        self.cancel_button.pack(
            side="left",
            padx=10
        )




        # ---------------- Progress ----------------


        progress_frame = ctk.CTkFrame(
            self.main_area
        )


        progress_frame.pack(
            fill="x",
            padx=30,
            pady=20
        )



        self.status_label = ctk.CTkLabel(
            progress_frame,
            text="Waiting..."
        )


        self.status_label.pack(
            pady=10
        )



        self.playlist_info_label = ctk.CTkLabel(
            progress_frame,
            text=""
        )


        self.playlist_info_label.pack(
            pady=5
        )



        self.video_progress = ctk.CTkProgressBar(
            progress_frame
        )


        self.video_progress.pack(
            fill="x",
            padx=20
        )


        self.video_progress.set(
            0
        )



        self.total_progress = ctk.CTkProgressBar(
            progress_frame
        )


        self.total_progress.pack(
            fill="x",
            padx=20,
            pady=20
        )


        self.total_progress.set(
            0
        )

        # ================= Statistics Cards =================


        stats_frame = ctk.CTkFrame(
            self.main_area
        )


        stats_frame.pack(
            fill="x",
            padx=30,
            pady=10
        )



        self.completed_card = StatusCard(
            stats_frame,
            "Completed"
        )


        self.completed_card.pack(
            side="left",
            expand=True,
            padx=10
        )



        self.failed_card = StatusCard(
            stats_frame,
            "Failed"
        )


        self.failed_card.pack(
            side="left",
            expand=True,
            padx=10
        )



        self.remaining_card = StatusCard(
            stats_frame,
            "Remaining"
        )


        self.remaining_card.pack(
            side="left",
            expand=True,
            padx=10
        )

        # ================= Queue Display =================


        queue_frame = ctk.CTkFrame(
            self.main_area
        )


        queue_frame.pack(
            fill="both",
            expand=True,
            padx=30,
            pady=10
        )



        queue_title = ctk.CTkLabel(
            queue_frame,
            text="Download Queue",
            font=(
                "Arial",
                18,
                "bold"
            )
        )


        queue_title.pack(
            anchor="w",
            padx=10,
            pady=5
        )



        self.queue_box = ctk.CTkTextbox(
            queue_frame,
            height=200
        )


        self.queue_box.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10
        )




    def select_folder(self):
        """
        Opens folder selection dialog.
        """

        folder = filedialog.askdirectory()


        if folder:

            self.download_folder = folder


            self.folder_entry.delete(
                0,
                "end"
            )


            self.folder_entry.insert(
                0,
                folder
            )


            self.settings.set(
                "download_folder",
                folder
            )

    def close_application(self):
        """
        Saves settings before closing.
        """


        self.settings.update(
            {
                "download_folder":
                    self.folder_entry.get(),

                "last_playlist":
                    self.playlist_entry.get(),

                "quality":
                    self.quality_dropdown.get()
            }
        )


        self.destroy()


    def analyze_playlist(self):
        """
        Starts playlist analysis in background.
        """

        url = self.playlist_entry.get().strip()


        if not url:

            self.status_label.configure(
                text="Please enter playlist URL"
            )

            return


        self.analyze_button.configure(
            state="disabled"
        )


        self.status_label.configure(
            text="Analyzing playlist..."
        )


        thread = threading.Thread(
            target=self.run_analysis,
            args=(url,),
            daemon=True
        )


        thread.start()

    def run_analysis(
        self,
        url
    ):
        """
        Runs yt-dlp analysis without freezing GUI.
        """

        try:

            result = self.playlist_analyzer.analyze(
                url
            )


            self.after(
                0,
                lambda:
                self.show_analysis_result(result)
            )


        except Exception as e:


            self.after(
                0,
                lambda:
                self.analysis_failed(str(e))
            )

    def show_analysis_result(
        self,
        result
    ):
        """
        Updates GUI after successful analysis.
        """

        self.current_playlist_result = result


        text = (
            f"Playlist: {result.playlist_title}\n"
            f"Total Videos: {result.total_videos}\n"
            f"Already Downloaded: {result.downloaded}\n"
            f"Need Download: {len(result.new_videos)}"
        )


        self.playlist_info_label.configure(
            text=text
        )


        self.status_label.configure(
            text="Analysis Complete"
        )


        self.analyze_button.configure(
            state="normal"
        )

    def analysis_failed(
        self,
        error
    ):
        """
        Shows analysis errors.
        """


        self.status_label.configure(
            text=f"Error: {error}"
        )


        self.analyze_button.configure(
            state="normal"
        )


    def start_download(self):
        """
        Starts playlist download.
        """

        self.downloader.cancel_event.clear()
        self.downloader.pause_event.set()

        if not self.current_playlist_result:

            self.status_label.configure(
                text="Analyze playlist first"
            )

            return


       
        videos = self.current_playlist_result.new_videos


        self.download_queue.clear()


        self.download_queue.add_videos(
            videos
        )

        if not videos:

            self.status_label.configure(
                text="No new videos to download"
            )

            return


        folder = self.folder_entry.get()


        if not folder:

            self.status_label.configure(
                text="Select download folder"
            )

            return


        self.start_button.configure(
            state="disabled"
        )


        thread = threading.Thread(
            target=self.download_playlist,
            args=(videos, folder),
            daemon=True
        )


        thread.start()


    def download_playlist(
        self,
        videos,
        folder
    ):
        """
        Downloads videos in background.
        """


        total = len(videos)



        total = self.download_queue.total_count()



        while True:


            video = self.download_queue.get_next()
            self.after(
                 0,
                 self.update_queue_display
            )

            self.database.update_queue_status(

                video.video_id,

                "DOWNLOADING"

            )


            if video is None:

                break



            self.after(
                0,
                lambda v=video:
                self.update_status(
                    f"Downloading: {v.title}"
                )
            )


            success = self.downloader.download(

                video,

                self.playlist_entry.get(),

                folder,

                self.quality_dropdown.get(),

                self.update_progress

            )



            if success:

                self.download_queue.mark_completed(
                    video
                )

                self.database.update_queue_status(

                    video.video_id,

                    "COMPLETED"

                )

                self.after(
                 0,
                 self.update_queue_display
                )

            else:

                self.download_queue.mark_failed(
                    video
                )

                self.database.update_queue_status(

                    video.video_id,

                    "FAILED"

                )

                self.after(
                    0,
                    self.update_queue_display
                )


            self.after(

                0,

                lambda:
                self.completed_card.update(
                    self.download_queue.completed_count()
                )

            )


            self.after(

                0,

                lambda:
                self.failed_card.update(
                    self.download_queue.failed_count()
                )

            )


            self.after(

                0,

                lambda:
                self.remaining_card.update(
                    self.download_queue.remaining_count()
                )

            )


            completed = (
                self.download_queue.completed_count()
                +
                self.download_queue.failed_count()
            )


            progress = completed / total


            self.after(
                0,
                lambda p=progress:
                self.total_progress.set(p)
            )


        self.after(
            0,
            self.download_finished
        )


    def update_status(
        self,
        text
    ):

        self.status_label.configure(
            text=text
        )


    def update_progress(
        self,
        data
    ):
        """
        Updates current video progress.
        """


        if data["status"] == "downloading":

            total = (
                data.get("total_bytes")
                or
                data.get("total_bytes_estimate")
            )


            downloaded = data.get(
                "downloaded_bytes",
                0
            )


            if total:

                percent = downloaded / total


                self.after(
                    0,
                    lambda: self.video_progress.set(percent)
                )


    def download_finished(self):

        self.status_label.configure(
            text="Download Completed"
        )


        self.start_button.configure(
            state="normal"
        )


        self.video_progress.set(
            0
        )


        self.total_progress.set(
            1
        )


    def pause_download(self):

        self.downloader.pause()

        self.status_label.configure(
            text="Download Paused"
        )


    def resume_download(self):

        self.downloader.resume()

        self.status_label.configure(
            text="Download Resumed"
        )


    def cancel_download(self):

        self.downloader.cancel()


        self.status_label.configure(
            text="Cancelling..."
        )

    def update_queue_status(self):

        text = (

            f"Completed: "
            f"{self.download_queue.completed_count()}\n"

            f"Failed: "
            f"{self.download_queue.failed_count()}\n"

            f"Remaining: "
            f"{self.download_queue.remaining_count()}"

        )


        self.playlist_info_label.configure(
            text=text
        )


    def open_history(self):

        HistoryWindow(

            self,

            self.database

        )

    def update_queue_display(self):
        """
        Updates queue information in GUI.
        """


        self.queue_box.delete(
            "1.0",
            "end"
        )


        if self.download_queue.current_video:

            self.queue_box.insert(
                "end",
                "Downloading:\n"
            )


            self.queue_box.insert(
                "end",
                f"▶ {self.download_queue.current_video.title}\n\n"
            )



        self.queue_box.insert(
            "end",
            "Waiting:\n"
        )


        for index, video in enumerate(
            self.download_queue.queue,
            start=1
        ):

            self.queue_box.insert(

                "end",

                f"{index}. {video.title}\n"

            )



        self.queue_box.insert(
            "end",
            "\nCompleted: "
            +
            str(
                self.download_queue.completed_count()
            )
        )


        self.queue_box.insert(
            "end",
            "\nFailed: "
            +
            str(
                self.download_queue.failed_count()
            )
        )

    def open_settings(self):

        SettingsWindow(

            self,

            self.settings

        )


    def check_previous_session(self):


        pending = self.database.get_pending_downloads()


        if pending:


            response = messagebox.askyesno(

                "Resume Downloads",

                f"{len(pending)} unfinished downloads found.\nResume?"

            )


            if response:

                self.restore_queue(
                    pending
                )


    def restore_queue(
        self,
        downloads
    ):

        videos = []


        for row in downloads:

            video = VideoInfo(

                video_id=row[0],

                title=row[1],

                url=row[2],

                duration=0

            )


            videos.append(
                video
            )


        self.download_queue.add_videos(
            videos
        )


        self.update_queue_display()