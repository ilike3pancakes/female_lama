from dataclasses import dataclass
import subprocess
import tempfile

@dataclass
class KikMp4:
    mp4_bytes_with_one_h264_stream_and_one_aac_stream: bytes

def remux(mp3_bytes: bytes) -> KikMp4:
    # Create temporary files to hold the input MP3 and the output MP4
    with tempfile.NamedTemporaryFile(suffix='.mp3') as temp_mp3_file, \
         tempfile.NamedTemporaryFile(suffix='.mp4') as temp_mp4_file:

        # Write the MP3 bytes to the temporary file
        temp_mp3_file.write(mp3_bytes)
        temp_mp3_file.flush()

        # Construct the ffmpeg command
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

        # Execute the ffmpeg command
        subprocess.run(command, check=True)

        # Read the output MP4 file back into Python
        temp_mp4_file.seek(0)
        mp4_bytes = temp_mp4_file.read()

    # Return the MP4 bytes wrapped in the KikMp4 dataclass
    return KikMp4(mp4_bytes_with_one_h264_stream_and_one_aac_stream=mp4_bytes)
