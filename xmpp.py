from __future__ import annotations
import hashlib
import io
import time
from kik_unofficial.client import KikClient
from kik_unofficial.utilities.cryptographic_utilities import CryptographicUtils
from kik_unofficial.utilities.parsing_utilities import ParsingUtilities

from log import get_logger
from upload import upload_gallery_video, VoiceNoteSerilizeWrapper


logger = get_logger()


def parse_audio(mp4_bytes: bytes) -> dict[str, str]:
    mp4_bytes = io.BytesIO(mp4_bytes)
    mp4_bytes.name = "temp.mp4"

    size = len(mp4_bytes.getvalue())
    final_og = mp4_bytes.getvalue()
    final_pre = mp4_bytes.getvalue()

    base64 = ParsingUtilities.read_file_as_base64(final_pre)
    md5 = hashlib.md5(final_og).hexdigest()
    mp4_bytes.close()

    return {
        'base64': base64,
        'size': size,
        'original': final_og,
        'MD5': md5,
    }


def vn_packets(peer_jid: str, content: bytes, is_group: bool = True) -> VoiceNoteSerilizeWrapper:
    timestamp = str(int(round(time.time() * 1000)))
    message_type = "groupchat" if is_group else "chat"
    message_id = CryptographicUtils.make_kik_uuid()
    content_id = CryptographicUtils.make_kik_uuid()

    parsed = parse_audio(content)

    xmlns = "kik:groups" if is_group else "jabber:client"

    data = (
f'<message cts="{timestamp}" id="{message_id}" to="{peer_jid}" type="{message_type}" xmlns="{xmlns}">'
    f'<pb/>'
    f'<kik push="true" qos="true" timestamp="{timestamp}"/>'
    f'<request d="true" r="true" xmlns="kik:message:receipt"/>'
    f'<content app-id="com.kik.ext.video-gallery" id="{content_id}" v="2">'
        f'<strings>'
            f'<app-name>audio</app-name>'  # "Gallery" does something but Schizo says it should be called "audio"
            f'<file-size>{parsed["size"]}</file-size>'
            f'<layout>video</layout>'  # audio seems to send an empty/broken message with a share button. video gives a clickable element with a play button.
            f'<allow-forward>true</allow-forward>'
            f'<file-name>{content_id}.mp4</file-name>'
            f'<duration>{1570}</duration>'
            f'<a>1</a>'
        f'</strings>'
        f'<extras>'
            f'<item>'
                f'<key>needstranscoding</key>'
                f'<val>false</val>'
            f'</item>'
        f'</extras>'
        f'<hashes/>'
        f'<images>'
            f'<preview>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</preview>'
            f'<icon>iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAYAAABXAvmHAAAAAXNSR0IArs4c6QAAAARzQklUCAgICHwIZIgAAAMpSURBVGiB7ZdNSBRhGMd/M1NJhZaGlRHmIRULsmN0sGsXqUOnoEMQhF07WRB0SPuAkjBCSTzUIfDS0sEgsCw6lVQmmbrq+oHa5k7q6urqzkyHSXTdHZuvnF3Z32n2fR/m/f/3fd73eUZA04SydxxWFao1OAPkkdrIAvhEidruCvxCWbtWrCi8BEq9VmaRHkmiUlQVqkk/8QClqkK1UNKmhUj9tDFCFklf8QB5otcKnJIx4DUZA16zxWjidD5cL4a9WRspJ5FgFGr6oPVX8nnDHUgF8aBruFZsPG9oIBXEL7OelrQ/AxkDXuO6gZgG84rbbzXG8Bq1w6cpeDgIEQVO5MKVItghublCIq4ZGIrA1e8wEdV/d4Vh91a4VBgfp2owp0C2Syu7lkKd4RXxABrwdDQxbmQeqr7B2II767pmQEg2tmZQ0aBhGD5OwYMBWFKdr+uagWM5ULCq4AjAhYPxMa+C8GJCf34bgt455+s6NjC+AFEVCrdD3VE4mQvlOVBVBOcPrMT9ikJ9QN8FgJkYPArot5YTHB2l0QW4+AUuH4JzBXB8Fzwp10Vlrflrno9DIBI/9mYSWoNQuc++Bts7EFXhrh+G5/Vuse9vOkhCoviuMDQEYG3Kq0DjEPxesqvCgYGvM/Be1p/nFLjZC9NJhMzE4LYflgxSpT8Crw1aZTPYMjCvwL1+vWAt0zEFvp+JsW2T8Hna+F2KBnWDEFq0o8SGAQ1oGoHOmfhxFagbgI5VYscX4I7/3wc1tAj3B1YOuBUsGwhEoGUs+dycArf69JyOqnrqyCbzu20SematqrFhoGk4vuKu5UcYno3qKdUum3+vvASNw1bVWLhGNeCDDC3j68cpwOMhvahZ7Upbg3B2P5zak7yyJ8P0DszGoH7QXKyi6TXCDo1DEImZjze9AzsluFECIQd3thnyt1lrwU0bEAU4km1H0v8l80npNYYGgutclRvNeloMDdT0pYaJYFQvjkYIJW2aw47cWzbvGUgXMga8ZlMYsND0phyyKIDPaxV2EcAnihK1QI/XYmzQI0rUit0V+CWJSgGaSY90kgVoliQquyvw/wEBywt7TQ67XwAAAABJRU5ErkJggg==</icon>'
        f'</images>'
        f'<uris/>'
        # Uris do not work for video.
    f'</content>'
f'</message>'
    )

    packets = [data[s:s+16384].encode() for s in range(0, len(data), 16384)]
    return VoiceNoteSerilizeWrapper(list(packets), message_id, content_id, parsed)


def send_vn(client: KikClient, group_jid: str, voice_mp4_bytes: bytes, *, is_group: bool = True) -> str:
    peer_jid = client.get_jid(group_jid)
    vn_request = vn_packets(peer_jid, voice_mp4_bytes, is_group=is_group)
    upload_gallery_video(
        vn_request,
        f'{client.kik_node}@talk.kik.com',
        client.username,
        client.password,
    )
    logger.info(f"Got {len(vn_request.serialize())} vn packets")
    return client._send_xmpp_element(vn_request)
