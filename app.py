import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, abort
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant, ChatGrant
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

load_dotenv()
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_api_key_sid = os.environ.get('TWILIO_API_KEY_SID')
twilio_api_key_secret = os.environ.get('TWILIO_API_KEY_SECRET')
twilio_client = Client(twilio_api_key_sid, twilio_api_key_secret,
                       twilio_account_sid)

app = Flask(__name__)


def get_chatroom(name):
    for conversation in twilio_client.conversations.conversations.list():
        if conversation.friendly_name == name:
            return conversation

    # a conversation with the given name does not exist ==> create a new one
    return twilio_client.conversations.conversations.create(
        friendly_name=name)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST'])
def login():
    username = request.get_json(force=True).get('username')
    if not username:
        abort(401)

    conversation = get_chatroom('StudyHall_name')
    try:
        conversation.participants.create(identity=username)
    except TwilioRestException as exc:
        # do not error if the user is already in the conversation
        if exc.status != 409:
            raise

    token = AccessToken(twilio_account_sid, twilio_api_key_sid,
                        twilio_api_key_secret, identity=username)
    token.add_grant(VideoGrant(room='StudyHall_name'))
    token.add_grant(ChatGrant(service_sid=conversation.chat_service_sid))

    return {'token': token.to_jwt().decode(),
            'conversation_sid': conversation.sid}

def start_ngrok():
    from pyngrok import ngrok
    url = ngrok.connect(8000)
    print(' * Tunnel URL:', url.replace("http", "https", 1))


if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        start_ngrok()
    app.run(port=8000, debug=True)
