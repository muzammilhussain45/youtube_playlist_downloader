import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading


from core.settings import SettingsManager
from core.database import DatabaseManager
from core.playlist import PlaylistAnalyzer, VideoInfo
from core.downloader import VideoDownloader
from core.queue_manager import DownloadQueue
from gui.history_window import HistoryWindow
from gui.sidebar import Sidebar
from gui.widgets import StatusCard
from core.system_check import check_ffmpeg
from core.utils import (
    format_size,
    format_speed,
    format_duration,
    format_eta,
    estimate_video_size,
    load_thumbnail
)


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

        self.playlist_analyzer = PlaylistAnalyzer(self.database)
        self.downloader = VideoDownloader(self.database)

        self.current_playlist_result = None
        self.selected_videos = []
        self.thumbnail_images = []
        self.video_rows = {}
        self._last_speed = 0.0

        self.download_queue = DownloadQueue(self.database)

        self.title("YouTube Playlist Downloader")
        self.geometry("1100x750")
        self.minsize(950, 650)

        # Theme - apply saved theme automatically
        self.apply_theme()

        self.download_folder = self.settings.get("download_folder")

        self.create_widgets()
        self.check_previous_session()

        # Handle application closing
        self.protocol("WM_DELETE_WINDOW", self.close_application)

    # =================================================================
    # Layout
    # =================================================================

    def create_widgets(self):
        """
        Creates all GUI components.
        """

        # ================= Main Container =================
        self.container = ctk.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        # ================= Sidebar =================
        self.sidebar = Sidebar(
            self.container,
            {
                "analyze": self.analyze_playlist,
                "history": self.open_history
            }
        )
        self.sidebar.pack(side="left", fill="y")

        # ================= Main Area (scrollable) =================
        self.main_area = ctk.CTkScrollableFrame(
            self.container,
            fg_color="transparent"
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
            text="YouTube Downloader",
            font=("Arial", 26, "bold")
        )
        self.header.pack(pady=(0, 15))

        # ---------------- Section 1 & 2: URL + Folder side by side ----------------
        top_frame = ctk.CTkFrame(self.main_area)
        top_frame.pack(fill="x", padx=10, pady=5)
        top_frame.grid_columnconfigure(0, weight=1)
        top_frame.grid_columnconfigure(1, weight=1)

        # ----- Left column: Playlist URL -----
        url_col = ctk.CTkFrame(top_frame)
        url_col.grid(row=0, column=0, padx=(0, 5), pady=5, sticky="nsew")

        url_label = ctk.CTkLabel(url_col, text="Playlist URL:")
        url_label.pack(anchor="w", padx=10, pady=(10, 2))

        self.playlist_entry = ctk.CTkEntry(
            url_col,
            placeholder_text="[ Paste YouTube playlist URL ]"
        )
        last_playlist = self.settings.get("last_playlist")
        if last_playlist:
            self.playlist_entry.insert(0, last_playlist)
        self.playlist_entry.pack(
            fill="x", padx=10, pady=(0, 8)
        )

        url_btn_row = ctk.CTkFrame(url_col, fg_color="transparent")
        url_btn_row.pack(fill="x", padx=10, pady=(0, 10))

        fetch_button = ctk.CTkButton(
            url_btn_row,
            text="Fetch Playlist",
            width=140,
            state="disabled",
            command=self.analyze_playlist
        )
        fetch_button.pack(side="left", padx=(0, 8))
        self.fetch_button = fetch_button

        quality_label = ctk.CTkLabel(url_btn_row, text="Quality:")
        quality_label.pack(side="left", padx=(0, 5))

        self.quality_dropdown = ctk.CTkOptionMenu(
            url_btn_row,
            values=["1080p", "720p", "Best Available"],
            command=self.on_quality_selected
        )
        saved_quality = self.settings.get("quality")
        self.quality_dropdown.set(saved_quality)
        # Fetch stays disabled until the user picks a resolution
        if not saved_quality:
            self.quality_dropdown.set("Select Resolution")
            self.fetch_button.configure(state="disabled")
        else:
            self.fetch_button.configure(state="normal")
        self.quality_dropdown.pack(side="left", padx=5)

        # ----- Right column: Download Folder -----
        folder_col = ctk.CTkFrame(top_frame)
        folder_col.grid(row=0, column=1, padx=(5, 0), pady=5, sticky="nsew")

        folder_label = ctk.CTkLabel(folder_col, text="Download Folder:")
        folder_label.pack(anchor="w", padx=10, pady=(10, 2))

        self.folder_entry = ctk.CTkEntry(folder_col)
        saved_folder = self.settings.get("download_folder")
        if saved_folder:
            self.folder_entry.insert(0, saved_folder)
        self.folder_entry.pack(
            fill="x", padx=10, pady=(0, 8)
        )

        browse_button = ctk.CTkButton(
            folder_col,
            text="Browse",
            width=100,
            command=self.select_folder
        )
        browse_button.pack(anchor="w", padx=10, pady=(0, 10))

        # ---------------- Section 3: Playlist Content ----------------
        list_outer = ctk.CTkFrame(self.main_area)
        list_outer.pack(fill="x", expand=False, padx=10, pady=10,
                        ipady=10)
        list_outer.configure(height=320)

        # Column headers
        header_row = ctk.CTkFrame(list_outer, fg_color="transparent")
        header_row.pack(fill="x", padx=10, pady=(8, 2))

        headers = [
            ("[x]", 40),
            ("Thumbnail", 120),
            ("Title", 300),
            ("Duration", 90),
            ("Size", 100),
            ("Downloaded", 140),
            ("Status", 110)
        ]
        for text, width in headers:
            ctk.CTkLabel(
                header_row,
                text=text,
                width=width,
                font=("Arial", 12, "bold"),
                text_color=("gray75", "gray25"),
                anchor="w"
            ).pack(side="left", padx=2)

        # Scrollable list
        self.video_list = ctk.CTkScrollableFrame(
            list_outer,
            fg_color="transparent"
        )
        self.video_list.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=(0, 10)
        )

        # ---------------- Section 4: Compact Controls ----------------
        control_frame = ctk.CTkFrame(self.main_area)
        control_frame.pack(fill="x", padx=10, pady=5)

        self.start_button = ctk.CTkButton(
            control_frame,
            text="Start All Downloads",
            width=200,
            command=self.start_download
        )
        self.start_button.pack(side="left", padx=5, pady=10)

        # ---------------- Section 5: Activity & Progress ----------------
        activity_frame = ctk.CTkFrame(self.main_area)
        activity_frame.pack(fill="x", padx=10, pady=5)

        # Row 1: Status text
        self.status_label = ctk.CTkLabel(
            activity_frame,
            text="Waiting...",
            anchor="w"
        )
        self.status_label.pack(
            anchor="w",
            padx=10,
            pady=(8, 2)
        )

        # Rows 2-5: Current video (left) and Whole playlist (right)
        progress_grid = ctk.CTkFrame(activity_frame, fg_color="transparent")
        progress_grid.pack(fill="x", padx=10, pady=(6, 2))
        progress_grid.grid_columnconfigure(0, weight=1)
        progress_grid.grid_columnconfigure(1, weight=1)

        # ----- Left column: Current Video -----
        current_col = ctk.CTkFrame(progress_grid, fg_color="transparent")
        current_col.grid(
            row=0, column=0, padx=(0, 5), pady=2, sticky="nsew")

        current_label = ctk.CTkLabel(
            current_col,
            text="Current Video:",
            anchor="w",
            font=("Arial", 11, "bold")
        )
        current_label.pack(anchor="w", pady=(0, 2))

        current_row = ctk.CTkFrame(current_col, fg_color="transparent")
        current_row.pack(fill="x", pady=2)

        self.current_progress = ctk.CTkProgressBar(current_row)
        self.current_progress.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )
        self.current_progress.set(0)

        self.current_percent_label = ctk.CTkLabel(
            current_row,
            text="0%",
            width=55
        )
        self.current_percent_label.pack(side="left", padx=(0, 10))

        # Current video metrics
        current_metrics = ctk.CTkFrame(
            current_col, fg_color="transparent")
        current_metrics.pack(fill="x", pady=2)

        self.speed_label = ctk.CTkLabel(
            current_metrics, text="Speed: --")
        self.speed_label.pack(side="left", padx=5)

        self.current_eta_label = ctk.CTkLabel(
            current_metrics, text="Time Left: --:--")
        self.current_eta_label.pack(side="left", padx=5)

        # Pause / Resume / Skip beneath current video bar
        current_btn_row = ctk.CTkFrame(
            current_col, fg_color="transparent")
        current_btn_row.pack(fill="x", pady=(4, 0))

        self.pause_button = ctk.CTkButton(
            current_btn_row,
            text="Pause",
            width=100,
            state="disabled",
            command=self.pause_download
        )
        self.pause_button.pack(side="left", padx=(0, 5), pady=2)

        self.resume_button = ctk.CTkButton(
            current_btn_row,
            text="Resume",
            width=100,
            state="disabled",
            command=self.resume_download
        )
        self.resume_button.pack(side="left", padx=5, pady=2)

        self.current_skip_button = ctk.CTkButton(
            current_btn_row,
            text="Skip",
            width=100,
            fg_color="#B8860B",
            hover_color="#DAA520",
            state="disabled",
            command=self.skip_download
        )
        self.current_skip_button.pack(side="left", padx=5, pady=2)

        # ----- Right column: Whole Playlist -----
        playlist_col = ctk.CTkFrame(progress_grid, fg_color="transparent")
        playlist_col.grid(
            row=0, column=1, padx=(5, 0), pady=2, sticky="nsew")

        playlist_label = ctk.CTkLabel(
            playlist_col,
            text="Whole Playlist:",
            anchor="w",
            font=("Arial", 11, "bold")
        )
        playlist_label.pack(anchor="w", pady=(0, 2))

        playlist_row = ctk.CTkFrame(
            playlist_col, fg_color="transparent")
        playlist_row.pack(fill="x", pady=2)

        self.total_progress = ctk.CTkProgressBar(playlist_row)
        self.total_progress.pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 10)
        )
        self.total_progress.set(0)

        self.progress_percent_label = ctk.CTkLabel(
            playlist_row,
            text="0%",
            width=55
        )
        self.progress_percent_label.pack(side="right")

        # Playlist metrics
        playlist_metrics = ctk.CTkFrame(
            playlist_col, fg_color="transparent")
        playlist_metrics.pack(fill="x", pady=2)

        self.playlist_eta_label = ctk.CTkLabel(
            playlist_metrics, text="Playlist Time Left: --:--")
        self.playlist_eta_label.pack(side="left", padx=5)

        self.playlist_size_label = ctk.CTkLabel(
            playlist_metrics, text="Downloaded: 0 B / 0 B")
        self.playlist_size_label.pack(side="left", padx=5)

        # Cancel beneath playlist bar
        playlist_btn_row = ctk.CTkFrame(
            playlist_col, fg_color="transparent")
        playlist_btn_row.pack(fill="x", pady=(4, 0))

        self.cancel_button = ctk.CTkButton(
            playlist_btn_row,
            text="Cancel",
            width=120,
            fg_color="#8B0000",
            hover_color="#B22222",
            command=self.cancel_download
        )
        self.cancel_button.pack(side="left", padx=(0, 5), pady=2)

        # Right area: small log view
        log_frame = ctk.CTkFrame(activity_frame)
        log_frame.pack(
            anchor="e",
            padx=10,
            pady=(2, 8)
        )

        self.log_box = ctk.CTkTextbox(
            log_frame,
            height=70,
            width=260,
            font=("Consolas", 10)
        )
        self.log_box.pack(padx=5, pady=5)
        self.log_box.insert("0.0", "Ready.\n")
        self.log_box.configure(state="disabled")

    # =================================================================
    # Playlist list rendering
    # =================================================================

    def render_video_list(self, videos):
        """
        Renders the playlist videos into the scrollable list.
        """

        # Clear previous rows
        for child in self.video_list.winfo_children():
            child.destroy()
        self.video_rows.clear()
        self.thumbnail_images.clear()

        for video in videos:
            row = ctk.CTkFrame(self.video_list, fg_color="transparent")
            row.pack(fill="x", padx=4, pady=3)

            # Checkbox
            checkbox = ctk.CTkCheckBox(
                row,
                text="",
                width=24,
                checkbox_width=22,
                checkbox_height=22,
                command=lambda v=video: self.toggle_video(v)
            )
            if video.selected:
                checkbox.select()
            checkbox.pack(side="left", padx=8)

            # Thumbnail
            thumb = load_thumbnail(video.thumbnail)
            if thumb:
                self.thumbnail_images.append(thumb)
                img_label = ctk.CTkLabel(row, image=thumb, text="")
            else:
                img_label = ctk.CTkLabel(
                    row,
                    text="No\nImg",
                    width=120,
                    height=68
                )
            img_label.pack(side="left", padx=4)

            # Title
            title_label = ctk.CTkLabel(
                row,
                text=video.title,
                width=300,
                anchor="w",
                justify="left",
                wraplength=290
            )
            title_label.pack(side="left", padx=4, fill="x", expand=True)

            # Duration
            duration_label = ctk.CTkLabel(
                row,
                text=format_duration(video.duration),
                width=90,
                anchor="w"
            )
            duration_label.pack(side="left", padx=4)

            # Size (estimated for the selected resolution)
            quality = self.quality_dropdown.get()
            if quality == "Select Resolution":
                quality = "1080p"
            est_size = estimate_video_size(video.duration, quality)
            size_label = ctk.CTkLabel(
                row,
                text=format_size(est_size),
                width=100,
                anchor="w"
            )
            size_label.pack(side="left", padx=4)

            # Downloaded status
            if video.downloaded:
                dl_text = "Already Downloaded"
                dl_color = ("#3a7d44", "#5cb85c")
            else:
                dl_text = "Not Downloaded"
                dl_color = ("gray60", "gray40")
            downloaded_label = ctk.CTkLabel(
                row,
                text=dl_text,
                width=140,
                anchor="w",
                text_color=dl_color
            )
            downloaded_label.pack(side="left", padx=4)

            # Status
            status_label = ctk.CTkLabel(
                row,
                text="Ready",
                width=110,
                anchor="w"
            )
            status_label.pack(side="left", padx=4)

            self.video_rows[video.video_id] = {
                "row": row,
                "status": status_label,
                "downloaded": downloaded_label,
                "checkbox": checkbox
            }

    def toggle_video(self, video):
        """
        Toggles a video's selected state from its checkbox.
        """

        video.selected = not video.selected
        self.update_selected_count()

    def update_selected_count(self):
        """
        Updates the status line with the number of selected videos.
        """

        if not self.current_playlist_result:
            return
        count = sum(1 for v in self.current_playlist_result.new_videos
                    if v.selected)
        self.status_label.configure(
            text=f"{count} video(s) selected for download"
        )

    def log(self, message):
        """
        Appends a line to the activity log view.
        """

        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # =================================================================
    # Folder / settings
    # =================================================================

    def select_folder(self):
        """
        Opens folder selection dialog.
        """

        folder = filedialog.askdirectory()
        if folder:
            self.download_folder = folder
            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, folder)
            self.settings.set("download_folder", folder)

    def on_quality_selected(self, quality):
        """
        Enables the Fetch button once a resolution is chosen and
        refreshes the displayed sizes if a playlist is already shown.
        """

        if quality == "Select Resolution":
            self.fetch_button.configure(state="disabled")
            return

        self.settings.set("quality", quality)
        self.fetch_button.configure(state="normal")

        # Re-render sizes for the current playlist at the new resolution
        if self.current_playlist_result:
            self.render_video_list(self.current_playlist_result.new_videos)

    def close_application(self):
        """
        Saves settings before closing.
        """

        self.settings.update({
            "download_folder": self.folder_entry.get(),
            "last_playlist": self.playlist_entry.get(),
            "quality": self.quality_dropdown.get()
        })
        self.destroy()

    # =================================================================
    # Analysis
    # =================================================================

    def analyze_playlist(self):
        """
        Starts playlist analysis in background.
        """

        url = self.playlist_entry.get().strip()
        if not url:
            self.status_label.configure(text="Please enter playlist URL")
            return

        self.status_label.configure(text="Analyzing playlist...")
        self.log("Analyzing playlist...")

        thread = threading.Thread(
            target=self.run_analysis,
            args=(url,),
            daemon=True
        )
        thread.start()

    def run_analysis(self, url):
        """
        Runs yt-dlp analysis without freezing GUI.
        """

        try:
            result = self.playlist_analyzer.analyze(url)
            self.after(0, lambda: self.show_analysis_result(result))
        except Exception as e:
            self.after(0, lambda: self.analysis_failed(str(e)))

    def show_analysis_result(self, result):
        """
        Updates GUI after successful analysis.
        """

        self.current_playlist_result = result
        self.selected_videos = list(result.new_videos)

        self.render_video_list(result.new_videos)

        not_downloaded = sum(
            1 for v in result.new_videos if not v.downloaded
        )

        self.status_label.configure(
            text=(
                f"Playlist: {result.playlist_title} | "
                f"Total: {result.total_videos} | "
                f"Already Downloaded: {result.downloaded} | "
                f"Available: {not_downloaded}"
            )
        )
        self.log(
            f"Found {result.total_videos} video(s): "
            f"{result.downloaded} already downloaded, "
            f"{not_downloaded} available to download."
        )
        self.update_selected_count()

    def analysis_failed(self, error):
        """
        Shows analysis errors.
        """

        self.status_label.configure(text=f"Error: {error}")
        self.log(f"Error: {error}")

    # =================================================================
    # Download
    # =================================================================

    def start_download(self):
        """
        Starts playlist download.
        """

        self.downloader.cancel_event.clear()
        self.downloader.pause_event.set()

        if not self.current_playlist_result:
            self.status_label.configure(text="Analyze playlist first")
            return

        videos = [v for v in self.current_playlist_result.new_videos
                  if v.selected]

        if not videos:
            self.status_label.configure(text="No videos selected to download")
            return

        folder = self.folder_entry.get()
        if not folder:
            self.status_label.configure(text="Select download folder")
            return

        self.download_queue.clear()
        self.download_queue.add_videos(videos)

        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.resume_button.configure(state="disabled")
        self.current_skip_button.configure(state="normal")

        thread = threading.Thread(
            target=self.download_playlist,
            args=(videos, folder),
            daemon=True
        )
        thread.start()

    def download_playlist(self, videos, folder):
        """
        Downloads videos in background. Progress is weighted by the
        estimated size of each video so large videos advance the bar
        more than small ones.
        """

        quality = self.quality_dropdown.get()

        # Total estimated size of the selected videos (bytes)
        total_size = sum(
            estimate_video_size(v.duration, quality) for v in videos
        )
        downloaded_size = 0.0

        # Reset progress display for this run
        self.after(0, lambda: self.total_progress.set(0))
        self.after(0, lambda: self.update_percent_label(0))
        self.after(0, lambda: self.current_progress.set(0))
        self.after(0, lambda: self.current_percent_label.configure(text="0%"))
        self.after(0, lambda: self.speed_label.configure(text="Speed: --"))
        self.after(0, lambda: self.current_eta_label.configure(
            text="Time Left: --:--"))
        self.after(0, lambda: self.playlist_eta_label.configure(
            text="Playlist Time Left: --:--"))
        self.after(0, lambda: self.playlist_size_label.configure(
            text=f"Downloaded: 0 B / {format_size(total_size)}"))

        while True:
            # Stop immediately if the user cancelled
            if self.downloader.cancel_event.is_set():
                self.log("Download cancelled by user.")
                break

            video = self.download_queue.get_next()
            if video is None:
                break

            self.after(0, lambda v=video: self.set_row_status(
                v.video_id, "Downloading"))
            self.after(0, self.update_queue_display)
            self.database.update_queue_status(
                video.video_id, "DOWNLOADING")
            self.after(0, lambda v=video: self.set_current_video(v))
            # Reset current-video bar for the new video
            self.after(0, lambda: self.current_progress.set(0))
            self.after(0, lambda: self.current_percent_label.configure(
                text="0%"))

            success = self.downloader.download(
                video,
                self.playlist_entry.get(),
                folder,
                quality,
                self.update_progress
            )

            # If cancelled mid-download, stop the queue
            if self.downloader.cancel_event.is_set():
                self.after(0, lambda v=video: self.set_row_status(
                    v.video_id, "Cancelled"))
                self.log(f"Cancelled: {video.title}")
                break

            # If skipped, mark as skipped and move to the next video
            if self.downloader.skip_event.is_set():
                self.after(0, lambda v=video: self.set_row_status(
                    v.video_id, "Skipped"))
                self.log(f"Skipped: {video.title}")
                continue

            if success:
                self.download_queue.mark_completed(video)
                self.database.update_queue_status(
                    video.video_id, "COMPLETED")
                self.after(0, lambda v=video: self.set_row_status(
                    v.video_id, "Completed"))
                self.after(0, lambda v=video: self.mark_downloaded(v))
                # Count this video's estimated size as downloaded
                downloaded_size += estimate_video_size(
                    video.duration, quality)
            else:
                self.download_queue.mark_failed(video)
                self.database.update_queue_status(
                    video.video_id, "FAILED")
                self.after(0, lambda v=video: self.set_row_status(
                    v.video_id, "Failed"))

            self.after(0, self.update_queue_display)

            # Size-weighted playlist progress
            progress = (downloaded_size / total_size) if total_size else 1

            self.after(0, lambda p=progress: self.total_progress.set(p))
            self.after(0, lambda p=progress: self.update_percent_label(p))
            self.after(0, lambda d=downloaded_size, t=total_size:
                       self.playlist_size_label.configure(
                           text=(
                               f"Downloaded: "
                               f"{format_size(d)} / {format_size(t)}"
                           )))
            self.after(0, lambda c=downloaded_size, t=total_size:
                       self.update_playlist_eta(c, t))

        self.after(0, self.download_finished)

    def set_row_status(self, video_id, status):
        """
        Updates the status column for a video row.
        """

        info = self.video_rows.get(video_id)
        if info:
            info["status"].configure(text=status)

    def mark_downloaded(self, video):
        """
        Marks a video row as already downloaded after completion.
        """

        video.downloaded = True
        info = self.video_rows.get(video.video_id)
        if info:
            info["downloaded"].configure(
                text="Already Downloaded",
                text_color=("#3a7d44", "#5cb85c")
            )

    def set_current_video(self, video):
        """
        Updates the status line for the current video.
        """

        self.status_label.configure(text=f"Downloading: {video.title}")
        self.log(f"Downloading: {video.title}")

    def update_status_line(self, completed, total):
        """
        Updates the status text with overall progress.
        """

        percent = int((completed / total * 100) if total else 100)
        self.status_label.configure(
            text=f"{completed} of {total} videos done, {percent}% complete"
        )

    def update_percent_label(self, progress):
        """
        Updates the percentage overlay next to the playlist bar.
        """

        self.progress_percent_label.configure(
            text=f"{int(progress * 100)}%"
        )

    def update_playlist_eta(self, downloaded_size, total_size):
        """
        Estimates the remaining time for the whole playlist based on
        the current download speed and size-weighted progress.
        """

        # Use the latest measured speed
        speed = self._last_speed or 0.0
        remaining = max(total_size - downloaded_size, 0.0)
        if speed > 0:
            eta = remaining / speed
            self.playlist_eta_label.configure(
                text=f"Playlist Time Left: {format_eta(eta)}")
        else:
            self.playlist_eta_label.configure(
                text="Playlist Time Left: calculating...")

    def update_progress(self, data):
        """
        Updates the current-video progress bar, speed, and ETAs from
        the yt-dlp progress hook.
        """

        if data["status"] == "downloading":
            speed = data.get("speed")
            eta = data.get("eta")
            downloaded = data.get("downloaded_bytes") or 0
            total = (data.get("total_bytes")
                     or data.get("total_bytes_estimate") or 0)
            self._last_speed = speed or 0.0

            # Current video progress
            if total:
                frac = min(downloaded / total, 1.0)
            else:
                frac = 0.0
            self.after(0, lambda f=frac:
                       self.current_progress.set(f))
            self.after(0, lambda f=frac:
                       self.current_percent_label.configure(
                           text=f"{int(f * 100)}%"))

            self.after(0, lambda s=speed:
                       self.speed_label.configure(
                           text=f"Speed: {format_speed(s)}"))
            self.after(0, lambda e=eta:
                       self.current_eta_label.configure(
                           text=f"Time Left: {format_eta(e)}"))

        elif data["status"] == "finished":
            self.after(0, lambda: self.current_progress.set(1))
            self.after(0, lambda:
                       self.current_percent_label.configure(text="100%"))
            self.after(0, lambda:
                       self.speed_label.configure(text="Speed: --"))
            self.after(0, lambda:
                       self.current_eta_label.configure(
                           text="Time Left: --:--"))

    def download_finished(self):
        """
        Resets controls after downloads finish or are cancelled.
        """

        if self.downloader.cancel_event.is_set():
            self.status_label.configure(text="Download Cancelled")
            self.log("Download cancelled.")
        else:
            self.status_label.configure(text="Download Completed")
            self.log("All downloads finished.")
            self.total_progress.set(1)
            self.update_percent_label(1)

        self.start_button.configure(state="normal")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
        self.current_skip_button.configure(state="disabled")
        self.speed_label.configure(text="Speed: --")
        self.current_eta_label.configure(text="Time Left: --:--")
        self.playlist_eta_label.configure(
            text="Playlist Time Left: --:--")
        self.current_progress.set(0)
        self.current_percent_label.configure(text="0%")

    def pause_download(self):
        self.downloader.pause()
        self.status_label.configure(text="Download Paused")
        self.log("Download paused.")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="normal")

    def resume_download(self):
        self.downloader.resume()
        self.status_label.configure(text="Download Resumed")
        self.log("Download resumed.")
        self.pause_button.configure(state="normal")
        self.resume_button.configure(state="disabled")

    def cancel_download(self):
        self.downloader.cancel()
        self.status_label.configure(text="Cancelling...")
        self.log("Cancelling downloads...")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
        self.current_skip_button.configure(state="disabled")

    def skip_download(self):
        self.downloader.skip()
        self.status_label.configure(text="Skipping current video...")
        self.log("Skipping current video...")
        self.current_skip_button.configure(state="disabled")

    def update_queue_display(self):
        """
        Kept for compatibility; row statuses already reflect state.
        """

        pass

    def open_history(self):
        HistoryWindow(self, self.database)

    def apply_theme(self):
        """
        Applies the saved theme to the running application.
        """

        saved_theme = self.settings.get("theme")
        theme_map = {
            "dark": "Dark",
            "light": "Light",
            "system": "System"
        }
        ctk.set_appearance_mode(theme_map.get(saved_theme, "Dark"))

    def check_previous_session(self):
        pending = self.database.get_pending_downloads()
        if pending:
            response = messagebox.askyesno(
                "Resume Downloads",
                f"{len(pending)} unfinished downloads found.\nResume?"
            )
            if response:
                self.restore_queue(pending)

    def restore_queue(self, downloads):
        videos = []
        for row in downloads:
            video = VideoInfo(
                video_id=row[0],
                title=row[1],
                url=row[2],
                duration=0
            )
            videos.append(video)

        self.download_queue.add_videos(videos)
        self.update_queue_display()
