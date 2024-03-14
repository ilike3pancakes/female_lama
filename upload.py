import hashlib
import logging
import requests
from threading import Thread
from typing import Dict

from kik_unofficial.datatypes.exceptions import KikUploadError
from kik_unofficial.utilities.cryptographic_utilities import CryptographicUtils
from kik_unofficial.device_configuration import kik_version_info


log = logging.getLogger('kik_unofficial')
SALT = "YA=57aSA!ztajE5"


class VoiceNoteSerilizeWrapper:
    def __init__(self, packets: list, message_id: str, content_id: str, parsed: Dict[str, str]):
        self.packets = packets
        self.message_id = message_id
        self.content_id = content_id
        self.parsed = parsed

    def serialize(self) -> list:
        return self.packets


def upload_gallery_video(
    video: VoiceNoteSerilizeWrapper,
    jid: str,
    username: str,
    password: str,
):
    url = f"https://platform.kik.com/content/files/{video.content_id}"
    _send(
        url,
        video.parsed['original'],
        video.content_id,
        video.parsed["size"],
        video.parsed["MD5"],
        jid,
        username,
        password,
    )


def _send(
    url: str,
    video: bytes,
    content_id: str,
    size: int,
    md5: str,
    jid: str,
    username: str,
    password: str,
):
    username_passkey = CryptographicUtils.key_from_password(username, password)
    app_id = "com.kik.ext.gallery-video"
    v = SALT + content_id + app_id

    verification = hashlib.sha1(v.encode('UTF-8')).hexdigest()
    headers = {
        'Host': 'platform.kik.com',
        'Connection': 'Keep-Alive',
        'Content-Length': str(size),
        'User-Agent': f'Kik/{kik_version_info["kik_version"]} (Android 7.1.2) Content',
        'x-kik-jid': jid,
        'x-kik-password': username_passkey,
        'x-kik-verification': verification,
        'x-kik-app-id': app_id,
        'x-kik-content-chunks': '1',
        'x-kik-content-size': str(size),
        'x-kik-content-md5': md5,
        'x-kik-chunk-number': '0',
        'x-kik-chunk-md5': md5,
        'Content-Type': 'video/mp4',
        'x-kik-content-extension': '.mp4'
    }
    # Sometimes Kik's servers throw 5xx when they're having issues, the new thread won't handle the exception
    Thread(
        target=_content_upload_thread,
        args=(url, video, headers),
        name='KikContent'
    ).start()


def _content_upload_thread(
    url: str, video_bytes: bytes, headers: Dict[str, str],
):
    r = requests.put(url, data=video_bytes, headers=headers)
    if r.status_code != 200:
        log.error(f"failed to upload video {r.status_code}")
        raise KikUploadError(r.status_code, r.reason)
