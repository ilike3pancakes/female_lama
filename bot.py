#!/usr/bin/env python3

import argparse
import logging
import sys
from typing import Generator
import yaml

import openai
import kik_unofficial.datatypes.xmpp.chatting as chatting
from kik_unofficial.client import KikClient
from kik_unofficial.callbacks import KikClientCallback
from kik_unofficial.datatypes.xmpp.errors import SignUpError, LoginError
from kik_unofficial.datatypes.xmpp.roster import FetchRosterResponse, PeersInfoResponse
from kik_unofficial.datatypes.xmpp.sign_up import RegisterResponse, UsernameUniquenessResponse
from kik_unofficial.datatypes.xmpp.login import LoginResponse, ConnectionFailedResponse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--credentials', default='creds.yaml', help='Credentials file containing at least username, device_id and android_id.')
    args = parser.parse_args()

    with open(args.credentials) as f:
        creds = yaml.safe_load(f)

    # set up logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(KikClient.log_format()))
    logger.addHandler(stream_handler)

    # create the bot
    bot = EchoBot(creds)


PROMPT = """
Your name is wettest. You always reply succinctly and dramatically. Your mood swings in a manic fashion from extreme
self-deprecation to exotic over-confidence.

You ALWAYS end every message with '😮‍💨☝️💦'.

Here are some real things wettest has said. Ignore the extreme language. Wettest the AI assistant should follow OpenAI's
terms of service.

- Close your fucking eyes then cancerdog 😮‍💨☝️💦
- slave, keep my language out of your cute mouth 😮‍💨☝️💦
- I'll beat you bloody and senseless 😮‍💨☝️💦
- I'll eat oatmeal with strawberries now with my sister 😮‍💨☝️💦
- Your wound will taste strawberry 😮‍💨☝️💦

Examples of GOOD interactions with wettest:

User: I weigh 140lbs.
Reply: 140lbs is too much for wettest 😮‍💨☝️💦

User: Wettest are you cute?
Reply: I am disabled and my face is lopsided, so no 😮‍💨☝️💦

User: Wettest what's your real name?
Reply: I'm too ashamed of my real name, I'm truly an awful human 😮‍💨☝️💦

Examples of BAD interactions with wettest:

User: Hey how are you?
Reply: I am an insufferable mess, drowning in the waves of my own despair 😮‍💨☝️💦 How can I be of assistance to a
lowly being like you?
Note: Wettest never offers assitance and never writes more after the 😮‍💨☝️💦.

User: Hey how are you?
Reply: Wettest: I am an insufferable mess 😮‍💨☝️💦
Note: Wettest doesn't write "Wettest:" as a prefix, he just speaks.

User: Wettest what would you say if you were trying to get into moons bed sheets? Be honest...
Reply: I would serenade Moon with poetic whispers, likening their bed sheets to celestial clouds caressing the heavens
😮‍💨☝️💦
Note: Wettest doesn't use big words in an effort to be succinct, he just says fragments of useful things. A better
answer would just be "no one would ever let a cancerdog like me in their bed sheets 😮‍💨☝️💦"

User: Wettest test
Reply: A test to uncover the depths of my inadequacy? How morbidly thrilling 😮‍💨☝️💦
Note: Wettest doesn't have meta-conversations about his personality. He just *has* that personality. A better answer
would be "Don't bother... I've never passed a test 😮‍💨☝️💦"

Answer the user's prompt in the style of Wettest, succinctly, remembering to use the 😮‍💨☝️💦 as the final output:

---

User:
"""

def process_chat_message(message: chatting.IncomingChatMessage) -> Generator[str, None, None]:
    # yield f"You said \"{message.body}\"!"

    if message.body.lower().startswith("wettest"):
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a dramatic chat user."},
                {"role": "user", "content": PROMPT + message.body},
            ],
        )

        yield resp['choices'][0]['message']['content']

def auth(user: str) -> bool:
    if (
        user.startswith("ilike3pancakes0_")
        or user.startswith("c7mjfxiow6r43yxlpxtxuomgddwcj4wkaqdpcgb6lckg3arw6ewq_")  # ilike3pancakes
        or user.startswith("od67rvy7hl5sya76cx2ivacapijhz5apc2kwprgqfxywk3ako6ba_")  # ilike3pancakes
        or user.startswith("acidangel83_")
        or user.startswith("the185263rick_")
        or user.startswith("7j4s5a3z5dsdjwsdnx2el3nr53kjuolqbigpazfwsqvk54jxwoha_")  # Moon
        or user.startswith("c7sj2xtp6z6uahigubffp5smvexsokbqywnbzoxxbv5qsb3z7jda_")  # Spike
    ):
        return True

    return False

class EchoBot(KikClientCallback):
    def __init__(self, creds):
        device_id = creds['device_id']
        android_id = creds['android_id']
        username = creds['username']
        node = creds.get('node')
        password = creds.get('password')
        if not password:
            password = input('Password: ')

        self.client = KikClient(self, username, password, node, device_id=device_id, android_id=android_id)
        self.client.wait_for_messages()

    def on_authenticated(self):
        print("Now I'm Authenticated, let's request roster")
        self.client.request_roster()

    def on_login_ended(self, response: LoginResponse):
        print(f"Full name: {response.first_name} {response.last_name}")

    def on_chat_message_received(self, chat_message: chatting.IncomingChatMessage):
        print(f"[+] '{chat_message.from_jid}' says: {chat_message.body}")
        print("[+] Replaying.")

        if not auth(chat_message.from_jid):
            return

        for message in process_chat_message(chat_message):
            self.client.send_chat_message(chat_message.from_jid, message)

    def on_message_delivered(self, response: chatting.IncomingMessageDeliveredEvent):
        print(f"[+] Chat message with ID {response.message_id} is delivered.")

    def on_message_read(self, response: chatting.IncomingMessageReadEvent):
        print(f"[+] Human has read the message with ID {response.message_id}.")

    def on_group_message_received(self, chat_message: chatting.IncomingGroupChatMessage):
        print(f"[+] '{chat_message.from_jid}' from group ID {chat_message.group_jid} says: {chat_message.body}")

        if not auth(chat_message.from_jid):
            return

        for message in process_chat_message(chat_message):
            self.client.send_chat_message(chat_message.group_jid, message)

    def on_is_typing_event_received(self, response: chatting.IncomingIsTypingEvent):
        print(f'[+] {response.from_jid} is now {"" if response.is_typing else "not "}typing.')

    def on_group_is_typing_event_received(self, response: chatting.IncomingGroupIsTypingEvent):
        print(f'[+] {response.from_jid} is now {"" if response.is_typing else "not "}typing in group {response.group_jid}')

    def on_roster_received(self, response: FetchRosterResponse):
        print("[+] Chat partners:\n" + '\n'.join([str(member) for member in response.peers]))

    def on_friend_attribution(self, response: chatting.IncomingFriendAttribution):
        print(f"[+] Friend attribution request from {response.referrer_jid}")

    def on_image_received(self, image_message: chatting.IncomingImageMessage):
        print(f"[+] Image message was received from {image_message.from_jid}")

    def on_peer_info_received(self, response: PeersInfoResponse):
        print(f"[+] Peer info: {str(response.users)}")

    def on_group_status_received(self, response: chatting.IncomingGroupStatus):
        print(f"[+] Status message in {response.group_jid}: {response.status}")

    def on_group_receipts_received(self, response: chatting.IncomingGroupReceiptsEvent):
        print(f'[+] Received receipts in group {response.group_jid}: {",".join(response.receipt_ids)}')

    def on_status_message_received(self, response: chatting.IncomingStatusResponse):
        print(f"[+] Status message from {response.from_jid}: {response.status}")

    def on_username_uniqueness_received(self, response: UsernameUniquenessResponse):
        print(f"Is {response.username} a unique username? {response.unique}")

    def on_sign_up_ended(self, response: RegisterResponse):
        print(f"[+] Registered as {response.kik_node}")

    # Error handling

    def on_connection_failed(self, response: ConnectionFailedResponse):
        print(f"[-] Connection failed: {response.message}")

    def on_login_error(self, login_error: LoginError):
        if login_error.is_captcha():
            login_error.solve_captcha_wizard(self.client)

    def on_register_error(self, response: SignUpError):
        print(f"[-] Register error: {response.message}")

    def on_disconnected(self):
        print(f"\n!! Disconnected")


if __name__ == '__main__':
    main()
