import hashlib
import logging
import requests


class VoiceNoteSerilizeWrapper:
    def __init__(self, packets: list, message_id: str, content_id: str, parsed: dict[str, str]):
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
    raise NotImplemented()
