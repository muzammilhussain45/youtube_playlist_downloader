import shutil


def check_ffmpeg():

    return shutil.which(
        "ffmpeg"
    ) is not None