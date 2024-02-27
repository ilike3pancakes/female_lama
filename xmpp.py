from __future__ import annotations
import base64
import hashlib
import io
import time
from kik_unofficial.client import KikClient
from kik_unofficial.utilities.blockhash import blockhash
from kik_unofficial.utilities.cryptographic_utilities import CryptographicUtils
from kik_unofficial.utilities.parsing_utilities import ParsingUtilities

from log import get_logger


logger = get_logger()


# Derived from image:
# data = (
#     f'<message to="{peer_jid}" id="{message_id}" cts="{timestamp}" type="{message_type}" xmlns="jabber:client">'
#     f'<kik timestamp="{timestamp}" qos="true" push="true"/>'
#     '<request xmlns="kik:message:receipt" d="true" r="true" />'
#     f'<content id="{content_id}" v="2" app-id="com.kik.ext.gallery">'
#     '<strings>'
#     '<app-name>Gallery</app-name>'
#     # f'<file-size>{self.parsed["size"]}</file-size>'
#     f'<allow-forward>{str(True).lower()}</allow-forward>'
#     '<disallow-save>false</disallow-save>'
#     '<file-content-type>image/jpeg</file-content-type>'
#     f'<file-name>{content_id}.jpg</file-name>'
#     '</strings>'
#     '<extras />'
#     '<hashes>'
#     # f'<sha1-original>{self.parsed["SHA1"]}</sha1-original>'
#     # f'<sha1-scaled>{self.parsed["SHA1Scaled"]}</sha1-scaled>'
#     # f'<blockhash-scaled>{self.parsed["blockhash"]}</blockhash-scaled>'
#     '</hashes>'
#     '<images>'
#     f'<preview>{encoded}</preview>'
#     '<icon></icon>'
#     '</images>'
#     '<uris />'
#     '</content>'
#     '</message>'
# )

# First attempt with audio from video:    data = (
    #     f'<message to="{peer_jid}" id="{message_id}" cts="{timestamp}" type="{message_type}" xmlns="jabber:client">'
    #     f'<kik timestamp="{timestamp}" qos="true" push="true"/>'
    #     '<request xmlns="kik:message:receipt" d="true" r="true" />'
    #     f'<content id="{content_id}" v="2" app-id="com.kik.ext.gallery">'

    #     '<strings>'
    #     '<app-name>Gallery</app-name>'
    #     f'<allow-forward>{str(True).lower()}</allow-forward>'
    #     '<disallow-save>false</disallow-save>'
    #     f'<file-url>data:audio/mpeg;base64,{encoded}</file-url>'
    #     '</strings>'

    #     '<images>'
    #     f'<preview>{encoded}</preview>'
    #     '<icon></icon>'
    #     '</images>'

    #     '<uris />'

    #     '</content>'
    #     '</message>'
    # )


def parse_audio(mp3_audio_bytes: bytes) -> dict[str, str]:
    mp3_audio_bytes = io.BytesIO(mp3_audio_bytes)
    mp3_audio_bytes.name = "temp.mp3"

    size = mp3_audio_bytes.tell()
    final_og = mp3_audio_bytes.getvalue()
    final_pre = mp3_audio_bytes.getvalue()

    base64 = ParsingUtilities.read_file_as_base64(final_pre)
    sha1_og = ParsingUtilities.read_file_as_sha1(final_og)
    sha1_scaled = ParsingUtilities.read_file_as_sha1(final_pre)
    block_scaled = blockhash(mp3_audio_bytes, 16)
    md5 = hashlib.md5(final_og).hexdigest()
    mp3_audio_bytes.close()

    return {
        'base64': base64,
        'size': size,
        'original': final_og,
        'SHA1': sha1_og,
        'SHA1Scaled': sha1_scaled,
        'blockhash': block_scaled,
        'MD5': md5,
    }


class VoiceNoteSerilizeWrapper:
    def __init__(self, packets: list):
        self.packets = packets

    def serialize(self) -> list:
        return self.packets


def vn_packets(peer_jid: str, content: bytes, is_group: bool = True) -> VoiceNoteSerilizeWrapper:
    timestamp = str(int(round(time.time() * 1000)))
    message_type = "groupchat" if is_group else "chat"
    message_id = CryptographicUtils.make_kik_uuid()
    content_id = CryptographicUtils.make_kik_uuid()

    encoded = base64.b64encode(content)

    # data = (
    #     f'<message to="{peer_jid}" id="{message_id}" cts="{timestamp}" type="{message_type}" xmlns="jabber:client">'
    #     f'<kik timestamp="{timestamp}" qos="true" push="true"/>'
    #     '<request xmlns="kik:message:receipt" d="true" r="true" />'

    #     f'<content id="{content_id}" v="2" app-id="com.kik.ext.gallery">'

    #     '<strings>'
    #     '<app-name>Audio</app-name>'
    #     f'<allow-forward>{str(True).lower()}</allow-forward>'
    #     '<disallow-save>false</disallow-save>'
    #     f'<file-url>data:audio/mpeg;base64,{encoded}</file-url>'
    #     '</strings>'

    #     '<images>'
    #     f'<preview>{encoded}</preview>'
    #     '<icon></icon>'
    #     '</images>'

    #     '<uris />'

    #     '</content>'
    #     '</message>'
    # )

# Working video XML that schizo gave me:
    """
<message cts="[TS]" id="[UUID]" to="[GROUP_JID]@groups.kik.com" type="groupchat" xmlns="kik:groups">
    <pb/>
    <kik push="true" qos="true" timestamp="[TS]"/>
    <request d="true" r="true" xmlns="kik:message:receipt"/>
    <content app-id="com.kik.ext.video-gallery" id="[CONTENT_ID]" v="2">
        <strings>
            <app-name>Gallery</app-name>
            <file-size>[FILE_SIZE]</file-size>
            <allow-forward>true</allow-forward>
            <layout>video</layout>
            <file-name>[FILE_NAME].mp4</file-name>
            <duration>[DURATION_MS]</duration>
        </strings>
        <extras>
            <item>
                <key>needstranscoding</key>
                <val>false</val>
            </item>
        </extras>
        <hashes/>
        <images>
            <preview>BLOB</preview>
            <icon>[ICON_BASE64]</icon>
        </images>
        <uris/>
    </content>
</message>
    """

    parsed = parse_audio(content)

    data = (
f'<message cts="{timestamp}" id="{message_id}" to="{peer_jid}" type="{message_type}" xmlns="kik:groups">'
    f'<pb/>'
    f'<kik push="true" qos="true" timestamp="{timestamp}"/>'
    f'<request d="true" r="true" xmlns="kik:message:receipt"/>'
    f'<content app-id="com.kik.ext.gallery" id="{content_id}" v="2">'
        f'<strings>'
            f'<app-name>Gallery</app-name>'
            f'<file-size>{parsed["size"]}</file-size>'
            f'<layout>video</layout>'  # TODO: try audio
            f'<allow-forward>false</allow-forward>'
            f'<file-name>{content_id}.mp3</file-name>'
            f'<duration>{5000}</duration>'
        f'</strings>'
        f'<extras>'
            f'<item>'
                f'<key>needstranscoding</key>'
                f'<val>false</val>'
            f'</item>'
        f'</extras>'
        f'<hashes/>'
        f'<images>'
            f'<preview>{encoded}</preview>'
            f'<icon></icon>'
        f'</images>'
        f'<uris/>'
    f'</content>'
f'</message>'
    )

    packets = [data[s:s+16384].encode() for s in range(0, len(data), 16384)]
    return VoiceNoteSerilizeWrapper(list(packets))


def send_vn(client: KikClient, group_jid: str, voice_mp3_bytes: bytes, *, is_group: bool = True) -> str:
    peer_jid = client.get_jid(group_jid)
    vn_request = vn_packets(peer_jid, voice_mp3_bytes, is_group=is_group)
    logger.info(f"Got {len(vn_request.serialize())} vn packets")
    return client._send_xmpp_element(vn_request)
