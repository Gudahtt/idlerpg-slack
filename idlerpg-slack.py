from slackclient import SlackClient
import time, os, pprint, sys, logging

from dotenv import load_dotenv

logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)

load_dotenv('.env')

slack_token = os.environ["SLACK_API_TOKEN"]
active_channel_name = 'general'

bot_id = None
bot_name = None

sc = SlackClient(slack_token)

pp = pprint.PrettyPrinter(indent=4)

users = {}

def hello(channel):
    sc.api_call(
        "chat.postMessage",
        channel=channel,
        text="Hello from Python! :tada:"
    )

def handle_event(event):
    if event["type"] == "message":
        handle_message(event)
    elif event["type"] == "presence_change":
        handle_presence_change(event)

def handle_message(event):
    print(event)
    text = event["text"]
    if text.startswith('<@{}>'.format(bot_id)):
        chunks = text.split()

        if len(chunks) > 1:
            args = []
            if len(chunks) > 2:
                args = chunks[2:]
            handle_command(event, chunks[1], args)

def handle_command(event, command, args):
    if command.lower() == "hello" or command.lower() == "hi":
        hello(event['channel'])
    elif command.lower() == "scores":
        scores = []
        for user_id, user in users.items():
            name = user['profile']['display_name']
            if len(name) == 0:
                name = user['profile']['real_name']
            if len(name) == 0:
                name = user['profile']['email']

            total = user['total']

            if user['active']:
                total += time.time() - user['first_seen']
            scores.append('{}: {}'.format(name, total))
        sc.api_call(
            "chat.postMessage",
            channel="#general",
            text='Scores:\n{}'.format('\n'.join(scores))
        )


def handle_presence_change(event):
    user_update(event['user'])

def get_channel_by_name(channels, name):
    for channel in channels:
        if (channel['name'] == name):
            return channel
    else:
        raise RuntimeError("Channel {} not found".format(name))

def user_update(id):
    timestamp = time.time()

    if not id in users:
        user_info_response = sc.api_call(
            "users.info",
            user=id
        )

        user = user_info_response["user"]

        if user['is_bot']:
            return

        users[id] = {
            'profile': user["profile"],
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


def init(login_data):
    global bot_name
    global bot_id

    bot_name = login_data['self']['name']
    bot_id = login_data['self']['id']

    channels_list_response = sc.api_call(
        "channels.list"
    )

    channels = channels_list_response['channels']

    channel = get_channel_by_name(channels, active_channel_name)

    channel_users_response = sc.api_call(
        "conversations.members",
        channel=channel["id"]
    )

    member_ids = channel_users_response['members']

    for member_id in member_ids:
        user_update(member_id)

def main():
    if sc.rtm_connect():
        login_data = sc.server.login_data
        init(login_data)
        while True:
            events = sc.rtm_read()

            for event in events:
                handle_event(event)
            time.sleep(1)
    else:
        logging.error("Connection Failed")
        sys.exit(1)

if __name__ == '__main__':
    main()
