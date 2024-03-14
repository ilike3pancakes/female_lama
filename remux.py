from dataclasses import dataclass
import subprocess
import tempfile

from log import get_logger


logger = get_logger()


@dataclass
class KikMp4:
    mp4_bytes_with_one_h264_stream_and_one_aac_stream: bytes


def remux(mp3_bytes: bytes) -> KikMp4:
    with (
        tempfile.NamedTemporaryFile(suffix='.mp3') as temp_mp3_file,
        tempfile.NamedTemporaryFile(suffix='.mp4') as temp_mp4_file,
        open('ffmpeg.log', 'w') as logfile,
    ):

        temp_mp3_file.write(mp3_bytes)
        temp_mp3_file.flush()

        command = [
            'ffmpeg',
            '-y',
            '-f', 'lavfi',
            '-i', 'color=c=black:s=640x480',
            '-i', temp_mp3_file.name,
            '-shortest',
            '-fflags', '+shortest',
            temp_mp4_file.name
        ]

        logger.info("ffmpeg: Starting...")
        subprocess.run(command, check=True, stdout=logfile)
        logger.info("ffmpeg: Completed. Seeking...")

        temp_mp4_file.seek(0)

        logger.info("ffmpeg: Seeking completed. Reading...")
        mp4_bytes = temp_mp4_file.read()

    logger.info("Returning voicenote!")
    return KikMp4(mp4_bytes_with_one_h264_stream_and_one_aac_stream=mp4_bytes)
