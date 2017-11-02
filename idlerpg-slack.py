from slackclient import SlackClient
import time, os, pprint, sys, logging

from dotenv import load_dotenv

class IdleRpgBot():
    """A Slack bot for playing IdleRPG. An IdleRPG Slack bot will track the
    time users are active in the rpg channel, and will respond to commands.
    """

    def __init__(self, slack_token, rpg_channel_name):
        """Return an IdleRPG Slack bot with with the token *slack_token* for
        the channel *rpg_channel_name*."""
        self._sc = SlackClient(slack_token)
        self._name = None
        self._id = None
        self._rpg_channel_id = None
        self._rpg_channel_name = rpg_channel_name
        self._users = {}

    def connect(self):
        """Initiate a connection with Slack"""
        if self._sc.rtm_connect():
            self._post_connection_init()

            while True:
                events = self._sc.rtm_read()

                for event in events:
                    self._handle_event(event)
                time.sleep(1)
        else:
            raise RuntimeError('Connection Failed')

    def _post_connection_init(self):
        login_data = self._sc.server.login_data

        self._name = login_data['self']['name']
        self._id = login_data['self']['id']

        channels_list_response = self._sc.api_call(
            'channels.list'
        )
        channels = channels_list_response['channels']

        rpg_channel = None
        for channel in channels:
            if (channel['name'] == self._rpg_channel_name):
                rpg_channel = channel
                break
        else:
            raise RuntimeError('Channel {} not found'.format(name))

        channel_users_response = self._sc.api_call(
            'conversations.members',
            channel=channel['id']
        )

        member_ids = channel_users_response['members']

        for member_id in member_ids:
            self._user_update(member_id)

    def _user_update(self, id):
        if not id in self._users:
            user_info_response = self._sc.api_call(
                'users.info',
                user=id
            )

            user = user_info_response['user']

            if user['is_bot']:
                return

            self._users[id] = {
                'profile': user['profile'],
                'active': False,
                'first_seen': None,
                'total': 0
            }

        user_presence_response = self._sc.api_call(
            'users.getPresence',
            user=id
        )

        active = user_presence_response['presence'] == 'active'

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
        print(self._id)
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
            self._sc.api_call(
                'chat.postMessage',
                channel='#general',
                text='Scores:\n{}'.format('\n'.join(scores))
            )

    def _handle_presence_change(self, event):
        self._user_update(event['user'])
    
    def _hello(self, channel):
        self._sc.api_call(
            'chat.postMessage',
            channel=channel,
            text='Hello from Python! :tada:'
        )

def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    load_dotenv('.env')

    slack_token = os.environ['SLACK_API_TOKEN']
    rpg_channel_name = 'general'

    bot = IdleRpgBot(slack_token, rpg_channel_name)
    bot.connect()

if __name__ == '__main__':
    main()
