from flask import Flask, request, Response

from kik import KikApi, Configuration
from kik.messages import messages_from_json, TextMessage

app = Flask(__name__)
kik = KikApi("female_lama", "42cd379e-5f1a-4390-881d-955f028221e2")

kik.set_configuration(Configuration(webhook="https://22e81a38.ngrok.io/incoming"))

live_dict = {}

def user_is_admin(username):
    return username in ["ilike3pancakes",
                        "oskarsbanana",
                        "YG_Bands_",
                        "vikiid95",
                        "goditee",
                        "BossJordan_g",
                        "Its_Margo_",
                        "yoitscass28"]

def maybe_do_verify(_text_message):
    if not user_is_admin(_text_message.from_user):
        return _text_message.body

    user = _text_message.body.split("verify with me ")
    if len(user) < 2 or len(user[1]) < 1:
        return "Please verify with the admin @%s" % _text_message.from_user

    return "Hello %s, the group admin @%s is asking for verification. Please send a live photo to them using the kik camera to prove that your kik profile is real." % (user[1], _text_message.from_user)


def maybe_add_live_dict(user, bod):
    if not user_is_admin(user):
        return "Sorry, only lama admins can do that..."

    drop_cmd = bod.split("!badd ")
    if len(drop_cmd) != 2 or len(drop_cmd[1]) < 1:
        return "Malformed expression..."

    lr = drop_cmd[1].split(":=")
    if len(lr) != 2 or len(lr[0]) < 1 or len(lr[1]) < 1:
        return "Malformed expression..."

    live_dict[lr[0]] = lr[1]

    return "Nice one."


def clap_text(bod):
    drop_cmd = bod.split("!clap ")
    if len(drop_cmd) != 2 or len(drop_cmd[1]) < 1:
        return "Malformed lamaspression..."

    words = drop_cmd[1].split(" ")
    if len(words) < 2:
        return "One does not simply clap a single word..."

    return " 👏 ".join(words)


def get_response(_text_message):
    bod = _text_message.body.lower()

    if len(bod) < 1:
        return "I'm not that kind of lama."
    elif bod == "ping":
        return "pong"
    elif bod == "hi":
        return "suh dude"
    elif bod == "who your bae":
        return "@lammmmas"
    elif bod == "who your daddy":
        return "@ilike3pancakes"
    elif bod == "blake":
        return "Blake is Milly's bae"
    elif bod == "anal":
        return "I'm not that kind of bot. But try asking my bae..."
    elif bod == "sleep":
        return '\n'.join(["sleep", "s l e e p", "SLEEP", "s l  e   e    p", "", "", "", "", "sleep."])
    elif bod == "lama":
        return "lama is bae"
    elif bod.startswith("verify with me"):
        return maybe_do_verify(_text_message)
    elif bod in live_dict.keys():
        return live_dict[bod]
    elif bod.startswith("!badd "):
        return maybe_add_live_dict(_text_message.from_user, bod)
    elif bod.startswith("!clap "):
        return clap_text(bod)

    return bod


@app.route('/incoming', methods=['POST'])
def incoming():
    if not kik.verify_signature(request.headers.get('X-Kik-Signature'), request.get_data()):
        return Response(status=403)

    messages = messages_from_json(request.json['messages'])

    for message in messages:
        if isinstance(message, TextMessage):
            kik.send_messages([
                TextMessage(
                    to=message.from_user,
                    chat_id=message.chat_id,
                    body=get_response(message)
                )
            ])

    return Response(status=200)


if __name__ == "__main__":
    app.run(port=8080, debug=True)
