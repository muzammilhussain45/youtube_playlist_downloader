from dataclasses import dataclass
from typing import List

import yt_dlp

from core.database import DatabaseManager



@dataclass
class VideoInfo:
    """
    Stores information about one YouTube video.
    """

    video_id: str
    title: str
    url: str
    duration: int | None
    thumbnail: str | None = None
    selected: bool = True
    downloaded: bool = False



@dataclass
class PlaylistInfo:
    """
    Stores analyzed playlist information.
    """

    playlist_title: str
    total_videos: int
    downloaded: int
    new_videos: List[VideoInfo]



class PlaylistAnalyzer:
    """
    Extracts playlist information using yt-dlp.
    """


    def __init__(
        self,
        database: DatabaseManager
    ):

        self.database = database



    def analyze(
        self,
        playlist_url: str
    ) -> PlaylistInfo:
        """
        Analyze playlist. Already-downloaded videos are still shown
        (marked as downloaded and auto-deselected) so the user can
        re-download them if the files were deleted.
        """


        options = {
            "quiet": True,
            "extract_flat": True,
            "skip_download": True
        }


        with yt_dlp.YoutubeDL(options) as ydl:

            playlist_data = ydl.extract_info(
                playlist_url,
                download=False
            )


        videos = []

        downloaded_count = 0


        entries = playlist_data.get(
            "entries",
            []
        )


        for item in entries:

            if not item:
                continue


            video_id = item.get(
                "id"
            )


            title = item.get(
                "title",
                "Unknown"
            )


            video_url = (
                f"https://www.youtube.com/watch?v={video_id}"
            )


            duration = item.get(
                "duration"
            )


            thumbnail = item.get(
                "thumbnail"
            ) or (
                f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
            )


            already = self.database.video_exists(video_id)

            if already:
                downloaded_count += 1


            videos.append(
                VideoInfo(
                    video_id=video_id,
                    title=title,
                    url=video_url,
                    duration=duration,
                    thumbnail=thumbnail,
                    # Already-downloaded videos are shown but
                    # deselected so they aren't re-downloaded
                    # unless the user explicitly selects them.
                    selected=not already,
                    downloaded=already
                )
            )



        return PlaylistInfo(

            playlist_title=
                playlist_data.get(
                    "title",
                    "Unknown Playlist"
                ),

            total_videos=len(entries),

            downloaded=downloaded_count,

            new_videos=videos
        )