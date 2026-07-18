import sqlite3
import threading
from pathlib import Path
from datetime import datetime



class DatabaseManager:
    """
    Handles all SQLite operations for the application.
    """



    def __init__(
        self,
        db_path: str = "database/history.db"
    ):

        self.db_path = Path(
            db_path
        )


        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )


        self.lock = threading.Lock()


        self._initialize_database()





    def _get_connection(self):

        return sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )





    def _initialize_database(self):

        """
        Creates required tables.
        """


        with self.lock:


            conn = self._get_connection()

            cursor = conn.cursor()



            # Download history table

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS downloads
                (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,


                    video_id TEXT UNIQUE,


                    video_url TEXT,


                    playlist_url TEXT,


                    title TEXT,


                    duration INTEGER,


                    download_path TEXT,


                    download_date TEXT,


                    status TEXT

                )
                """
            )



            # Resume queue table

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS download_queue
                (

                    id INTEGER PRIMARY KEY AUTOINCREMENT,


                    video_id TEXT UNIQUE,


                    title TEXT,


                    url TEXT,


                    playlist_url TEXT,


                    status TEXT,


                    created_at TEXT

                )
                """
            )



            conn.commit()

            conn.close()







    # ================= HISTORY =================


    def add_download(
        self,
        video_id,
        video_url,
        playlist_url,
        title,
        duration,
        download_path,
        download_date,
        status="COMPLETED"

    ):


        with self.lock:


            conn = self._get_connection()

            cursor = conn.cursor()



            try:


                cursor.execute(

                    """
                    INSERT INTO downloads
                    (
                        video_id,
                        video_url,
                        playlist_url,
                        title,
                        duration,
                        download_path,
                        download_date,
                        status
                    )

                    VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?)

                    """,

                    (

                        video_id,
                        video_url,
                        playlist_url,
                        title,
                        duration,
                        download_path,
                        download_date,
                        status

                    )

                )


                conn.commit()

                return True



            except sqlite3.IntegrityError:


                return False



            finally:


                conn.close()







    def video_exists(
        self,
        video_id
    ):


        with self.lock:


            conn = self._get_connection()

            cursor = conn.cursor()



            cursor.execute(

                """
                SELECT 1
                FROM downloads
                WHERE video_id=?
                LIMIT 1
                """,

                (
                    video_id,
                )

            )


            result = cursor.fetchone()


            conn.close()


            return result is not None








    def get_download_history(self):


        with self.lock:


            conn = self._get_connection()

            cursor = conn.cursor()



            cursor.execute(

                """
                SELECT
                    title,
                    video_url,
                    playlist_url,
                    download_path,
                    download_date,
                    status

                FROM downloads

                ORDER BY id DESC

                """

            )



            rows = cursor.fetchall()


            conn.close()


            return rows







    def total_downloads(self):


        with self.lock:


            conn = self._get_connection()

            cursor = conn.cursor()



            cursor.execute(

                "SELECT COUNT(*) FROM downloads"

            )


            total = cursor.fetchone()[0]


            conn.close()


            return total







    def remove_video(
        self,
        video_id
    ):


        with self.lock:


            conn = self._get_connection()

            cursor = conn.cursor()



            cursor.execute(

                """
                DELETE FROM downloads
                WHERE video_id=?
                """,

                (
                    video_id,
                )

            )


            conn.commit()


            affected = cursor.rowcount


            conn.close()


            return affected > 0







    def clear_history(self):


        with self.lock:


            conn = self._get_connection()

            cursor = conn.cursor()



            cursor.execute(

                "DELETE FROM downloads"

            )


            conn.commit()

            conn.close()







    # ================= DOWNLOAD QUEUE =================



    def add_to_queue(
        self,
        video
    ):

        """
        Stores unfinished downloads.
        """

        with self.lock:


            conn = self._get_connection()

            cursor = conn.cursor()



            cursor.execute(

                """
                INSERT OR REPLACE INTO download_queue

                (
                    video_id,
                    title,
                    url,
                    playlist_url,
                    status,
                    created_at
                )


                VALUES
                (?, ?, ?, ?, ?, ?)

                """,

                (

                    video.video_id,

                    video.title,

                    video.url,

                    getattr(
                        video,
                        "playlist_url",
                        ""
                    ),

                    "QUEUED",

                    datetime.now().isoformat()

                )

            )



            conn.commit()


            conn.close()








    def update_queue_status(
        self,
        video_id,
        status
    ):


        with self.lock:


            conn = self._get_connection()

            cursor = conn.cursor()



            cursor.execute(

                """
                UPDATE download_queue

                SET status=?

                WHERE video_id=?

                """,

                (

                    status,

                    video_id

                )

            )


            conn.commit()


            conn.close()







    def get_pending_downloads(self):

        """
        Returns unfinished downloads.
        """


        with self.lock:


            conn = self._get_connection()

            cursor = conn.cursor()



            cursor.execute(

                """
                SELECT

                    video_id,
                    title,
                    url,
                    playlist_url


                FROM download_queue


                WHERE status != 'COMPLETED'


                ORDER BY id ASC

                """

            )


            rows = cursor.fetchall()


            conn.close()


            return rows