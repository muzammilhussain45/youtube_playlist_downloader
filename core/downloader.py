from pathlib import Path
from datetime import datetime
from typing import Callable, Optional
import threading
import re

import yt_dlp

from core.database import DatabaseManager
from core.playlist import VideoInfo



class VideoDownloader:
    """
    Handles YouTube video downloading using yt-dlp.
    """



    def __init__(
        self,
        database: DatabaseManager
    ):

        self.database = database


        self.pause_event = threading.Event()

        self.pause_event.set()


        self.cancel_event = threading.Event()


        self.skip_event = threading.Event()


        self.status = "IDLE"




    def pause(self):
        """
        Pause current download.
        """

        self.status = "PAUSED"

        self.pause_event.clear()




    def resume(self):
        """
        Resume current download.
        """

        self.status = "DOWNLOADING"

        self.pause_event.set()




    def cancel(self):
        """
        Cancel current download.
        """

        self.status = "CANCELLED"

        self.cancel_event.set()


    def skip(self):
        """
        Skip the current download and move to the next video.
        """

        self.status = "SKIPPED"

        self.skip_event.set()




    def download(
        self,
        video: VideoInfo,
        playlist_url: str,
        download_folder: str,
        quality: str,
        progress_callback: Optional[Callable] = None

    ) -> bool:
        """
        Downloads a single video.
        """



        self.status = "DOWNLOADING"


        # Reset skip flag for this individual video so a skip requested
        # for a previous video does not carry over.
        self.skip_event.clear()


        # NOTE: cancel_event is intentionally NOT cleared here so that a
        # cancel requested by the user persists across the whole queue.
        # It is cleared in start_download() before a new run begins.



        # ---------------- Playlist Folder ----------------


        playlist_title = getattr(
            video,
            "playlist_title",
            "Unknown Playlist"
        )


        playlist_title = self.clean_filename(
            playlist_title
        )



        output_path = (

            Path(download_folder)

            /

            "YouTube Downloads"

            /

            playlist_title

        )



        output_path.mkdir(

            parents=True,

            exist_ok=True

        )




        # ---------------- Progress Hook ----------------


        def progress_hook(data):


            # Pause support

            self.pause_event.wait()



            # Cancel support

            if self.cancel_event.is_set():

                raise Exception(
                    "Download cancelled"
                )



            # Skip support

            if self.skip_event.is_set():

                raise Exception(
                    "Download skipped"
                )



            if progress_callback:

                progress_callback(data)





        # ---------------- yt-dlp Options ----------------


        options = {


            "format":
                self.get_format(
                    quality
                ),



            # Download single video only

            "noplaylist":
                True,



            # Continue partial downloads

            "continuedl":
                True,



            # Ignore broken videos

            "ignoreerrors":
                False,



            # Clean filenames

            "restrictfilenames":
                True,



            "outtmpl":

                str(

                    output_path

                    /

                    "%(title).100s.%(ext)s"

                ),




            # Merge to MP4

            "merge_output_format":

                "mp4",




            "postprocessors":

            [

                {

                    "key":

                    "FFmpegVideoConvertor",


                    "preferedformat":

                    "mp4"

                }

            ],



            "progress_hooks":

            [

                progress_hook

            ],



            "quiet":

                True

        }




        try:


            self.status = "DOWNLOADING"



            with yt_dlp.YoutubeDL(options) as ydl:


                result = ydl.download(

                    [

                        video.url

                    ]

                )




            # yt-dlp successful

            if result != 0:


                self.status = "FAILED"


                return False




            # ---------------- Save History ----------------


            self.database.add_download(

                video_id=
                    video.video_id,


                video_url=
                    video.url,


                playlist_url=
                    playlist_url,


                title=
                    video.title,


                duration=
                    video.duration or 0,


                download_path=
                    str(output_path),


                download_date=
                    datetime.now().isoformat(),


                status=
                    "COMPLETED"

            )



            self.status = "COMPLETED"


            return True





        except Exception as error:



            self.status = "FAILED"



            print(

                f"Download failed: {video.title}"

            )


            print(
                error
            )



            return False







    def get_format(
        self,
        quality
    ):
        """
        Returns yt-dlp format according to quality.
        """



        if quality in [

            "1080",

            "1080p"

        ]:


            return (

                "bestvideo[height<=1080]"

                "+bestaudio/"

                "best[height<=1080]"

            )




        elif quality in [

            "720",

            "720p"

        ]:


            return (

                "bestvideo[height<=720]"

                "+bestaudio/"

                "best[height<=720]"

            )



        else:


            return (

                "bestvideo+bestaudio/"

                "best"

            )







    def clean_filename(
        self,
        filename
    ):
        """
        Removes invalid Windows filename characters.
        """



        filename = re.sub(

            r'[<>:"/\\|?*]',

            '',

            filename

        )


        filename = filename.strip()



        if not filename:

            filename = "Unknown"



        return filename