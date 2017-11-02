import time
import os
import logging

from dotenv import load_dotenv

from api import SlackApiClient

READ_EVENT_PAUSE = .1

class IdleRpgBot():
    """A Slack bot for playing IdleRPG. An IdleRPG Slack bot will track the
    time users are active in the rpg channel, and will respond to commands.
    """

    def __init__(self, slack_token, rpg_channel_name):
        """Return an IdleRPG Slack bot

        Args:
            slack_token: The token used to authenticate with Slack
            rpg_channel_name: The name of the Slack channel used to play IdleRPG
        """
        self._api = SlackApiClient(slack_token)
        self._name = None
        self._id = None
        self._rpg_channel_id = None
        self._rpg_channel_name = rpg_channel_name
        self._users = {}

    def connect(self):
        """Initiate a connection with Slack"""
        self._api.connect()
        self._post_connection_init()

        while True:
            events = self._api.read()

            for event in events:
                self._handle_event(event)
            time.sleep(READ_EVENT_PAUSE)

    def _post_connection_init(self):
        self_user = self._api.get_self()

        self._name = self_user['name']
        self._id = self_user['id']

        rpg_channel = self._api.get_channel(self._rpg_channel_name)
        member_ids = self._api.get_channel_users(rpg_channel['id'])

        for member_id in member_ids:
            self._user_update(member_id)

    def _user_update(self, id):
        if not id in self._users:
            user = self._api.get_user_info(id)

            if user['is_bot']:
                return

            self._users[id] = {
                'profile': user['profile'],
                'active': False,
                'first_seen': None,
                'total': 0
            }

        active = self._api.is_user_active(id)

        if active:
            if not self._users[id]['active']:
                self._users[id]['active'] = True
                self._users[id]['first_seen'] = time.time()
        else:
            if self._users[id]['active']:
                self._users[id]['active'] = False
                self._users[id]['total'] += time.time() - self._users[id]['first_seen']
                self._users[id]['first_seen'] = None
    
    def _handle_event(self, event):
        logging.debug('Recieved event: {}'.format(event))
        if event['type'] == 'message':
            self._handle_message(event)
        elif event['type'] == 'presence_change':
            self._handle_presence_change(event)

    def _handle_message(self, event):
        text = event['text']
        if text.startswith('<@{}>'.format(self._id)):
            chunks = text.split()

            if len(chunks) > 1:
                args = []
                if len(chunks) > 2:
                    args = chunks[2:]
                self._handle_command(event, chunks[1], args)

    def _handle_command(self, event, command, args):
        if command.lower() == 'hello' or command.lower() == 'hi':
            self._hello(event['channel'])
        elif command.lower() == 'scores':
            scores = []
            for user_id, user in self._users.items():
                name = user['profile']['display_name']
                if len(name) == 0:
                    name = user['profile']['real_name']
                if len(name) == 0:
                    name = user['profile']['email']

                total = user['total']

                if user['active']:
                    total += time.time() - user['first_seen']
                scores.append('{}: {}'.format(name, total))
            self._api.send_message(event['channel'], 'Scores:\n{}'.format('\n'.join(scores))
            )

    def _handle_presence_change(self, event):
        self._user_update(event['user'])

    def _hello(self, channel_id):
        self._api.send_message(channel_id, 'Hello from Python! :tada:')

def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    load_dotenv('.env')

    slack_token = os.environ['SLACK_API_TOKEN']
    rpg_channel_name = 'general'

    bot = IdleRpgBot(slack_token, rpg_channel_name)
    bot.connect()

if __name__ == '__main__':
    main()
