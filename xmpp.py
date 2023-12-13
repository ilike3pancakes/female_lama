from __future__ import annotations
import base64
import time
from kik_unofficial.client import KikClient
from kik_unofficial.utilities.cryptographic_utilities import CryptographicUtils


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


def vn_packets(peer_jid: str, content: bytes, is_group: bool = True) -> list[str]:
    timestamp = str(int(round(time.time() * 1000)))
    message_type = "groupchat" if is_group else "chat"
    message_id = CryptographicUtils.make_kik_uuid()
    content_id = CryptographicUtils.make_kik_uuid()

    encoded = base64.b64encode(content)

    data = (
        f'<message to="{peer_jid}" id="{message_id}" cts="{timestamp}" type="{message_type}" xmlns="jabber:client">'
        f'<kik timestamp="{timestamp}" qos="true" push="true"/>'
        '<request xmlns="kik:message:receipt" d="true" r="true" />'

        f'<content id="{content_id}" v="2" app-id="com.kik.ext.gallery">'

        '<strings>'
        '<app-name>Audio</app-name>'
        f'<allow-forward>{str(True).lower()}</allow-forward>'
        '<disallow-save>false</disallow-save>'
        f'<file-url>data:audio/mpeg;base64,{encoded}</file-url>'
        '</strings>'

        '<uris />'

        '</content>'
        '</message>'
    )


    packets =  [data[s:s+16384].encode() for s in range(0, len(data), 16384)]
    return list(packets)


def send_vn(client: KikClient, group_jid: str, voice_mp3_bytes: bytes, *, is_group: bool = True) -> str:
    peer_jid = client.get_jid(group_jid)
    vn_request = vn_packets(peer_jid, voice_mp3_bytes, is_group=is_group)
    return client._send_xmpp_element(vn_request)
