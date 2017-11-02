from slackclient import SlackClient
import time, os

from dotenv import load_dotenv

load_dotenv('.env')

slack_token = os.environ["SLACK_API_TOKEN"]
active_channel_name = 'general'

sc = SlackClient(slack_token)

users = {}

def handle_event(event):
    if event["type"] == "message":
        handle_message(event)
    elif event["type"] == "presence_change":
        handle_presence_change(event)

def handle_message(event):
    text = event["text"]
    if text.lower() == "hello" or text.lower() == "hi":
        sc.api_call(
        "chat.postMessage",
        channel=event['channel'],
        text="Hello from Python! :tada:"
    )
    elif text.lower() == "scores":
        scores = []
        for user_id, user in users.items():
            total = user['total']
            if user['active']:
                total += time.time() - user['first_seen']

            scores.append('{}: {}'.format(user_id, total))

        sc.api_call(
            "chat.postMessage",
            channel=active_channel_name,
            text='Scores:\n{}'.format('\n'.join(scores))
        )

def handle_presence_change(event):
    user_update(event['user'])

def user_update(id):
    timestamp = time.time()

    if not id in users:
        users[id] = {
            'active': False,
            'first_seen': None,
            'total': 0
        }

    user_presence_response = sc.api_call(
        "users.getPresence",
        user=id
    )

    active = user_presence_response['presence'] == 'active'

    if active:
        if not users[id]['active']:
            users[id]['active'] = True
            users[id]['first_seen'] = timestamp
    else:
        if users[id]['active']:
            users[id]['active'] = False
            users[id]['total'] += time.time() - users[id]['first_seen']
            users[id]['first_seen'] = None

if sc.rtm_connect():
    while True:
        events = sc.rtm_read()

        for event in events:
            handle_event(event)
        time.sleep(1)
else:
    print("Connection Failed")
