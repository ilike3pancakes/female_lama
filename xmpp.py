from __future__ import annotations
import base64
import time
from kik_unofficial.client import KikClient
from kik_unofficial.utilities.cryptographic_utilities import CryptographicUtils

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

class VoiceNoteSerilizeWrapper:
    def __init__(self, packets: list):
        self.packets = packets

    def serialize(self) -> list:
        return self.packets


def vn_packets(peer_jid: str, content: bytes, is_group: bool = True) -> VoiceNoteSerilizeWrapper:
    logger.info("Building vn packets...")
    timestamp = str(int(round(time.time() * 1000)))
    message_type = "groupchat" if is_group else "chat"
    message_id = CryptographicUtils.make_kik_uuid()
    content_id = CryptographicUtils.make_kik_uuid()

    encoded = base64.b64encode(content)

    logger.info("Have b64-encoded content...")

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

    data = (
        """
<message cts="{timestamp}" id="{message_id}" to="{peer_jid}" type="{message_type}" xmlns="kik:groups">
    <pb/>
    <kik push="true" qos="true" timestamp="{timestamp}"/>
    <request d="true" r="true" xmlns="kik:message:receipt"/>
    <content app-id="com.kik.ext.video-gallery" id="{content_id}" v="2">
        <strings>
            <app-name>Gallery</app-name>
            <allow-forward>false</allow-forward>
            <layout>video</layout>
            <file-url>data:audio/mpeg;base64,{encoded}</file-url>
        </strings>
        <extras>
            <item>
                <key>needstranscoding</key>
                <val>false</val>
            </item>
        </extras>
        <hashes/>
        <images>
            <preview>{encoded}</preview>
            <icon></icon>
        </images>
        <uris/>
    </content>
</message>
        """
        .strip()
        .format(
            timestamp=timestamp,
            message_id=message_id,
            peer_jid=peer_jid,
            message_type=message_type,
            content_id=content_id,
            encoded=encoded,
        )
    )

    packets = [data[s:s+16384].encode() for s in range(0, len(data), 16384)]
    return VoiceNoteSerilizeWrapper(list(packets))


def send_vn(client: KikClient, group_jid: str, voice_mp3_bytes: bytes, *, is_group: bool = True) -> str:
    logger.info("send_vn")
    peer_jid = client.get_jid(group_jid)
    logger.info("Got peer jid")
    vn_request = vn_packets(peer_jid, voice_mp3_bytes, is_group=is_group)
    logger.info(f"Got {len(vn_request.serialize())} vn packets")
    return client._send_xmpp_element(vn_request)
