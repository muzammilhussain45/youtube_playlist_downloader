from collections import deque
from typing import Optional

from core.playlist import VideoInfo



class DownloadQueue:
    """
    Manages videos waiting for download.
    """


    def __init__(self,database):
        self.database = database
        
        self.queue = deque()

        self.completed = []

        self.failed = []

        self.current_video: Optional[VideoInfo] = None



    def add_videos(
        self,
        videos
    ):

        self.queue.extend(
            videos
        )


        for video in videos:

            self.database.add_to_queue(
                video
            )


    def get_next(self) -> Optional[VideoInfo]:
        """
        Returns next video.
        """

        if self.queue:

            self.current_video = self.queue.popleft()

            return self.current_video


        self.current_video = None

        return None



    def mark_completed(
        self,
        video: VideoInfo
    ):
        """
        Store completed video.
        """

        self.completed.append(
            video
        )



    def mark_failed(
        self,
        video: VideoInfo
    ):
        """
        Store failed video.
        """

        self.failed.append(
            video
        )



    def remaining_count(self):

        return len(
            self.queue
        )



    def completed_count(self):

        return len(
            self.completed
        )



    def failed_count(self):

        return len(
            self.failed
        )



    def total_count(self):

        return (
            self.remaining_count()
            +
            self.completed_count()
            +
            self.failed_count()
            +
            (1 if self.current_video else 0)
        )



    def clear(self):

        self.queue.clear()

        self.completed.clear()

        self.failed.clear()

        self.current_video = None