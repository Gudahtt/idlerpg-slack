import copy
import time
import logging

from .api import SlackApiClient, SlackApiError
from . import db

READ_EVENT_PAUSE = .1
LEVEL_MULTIPLIER = 300
LEVEL_EXPONENTIAL_FACTOR = 1.16
UPDATE_INTERVAL = 5 * 60 # Update every 5 minutes

class IdleRpgBot():
    """A Slack bot for playing IdleRPG. An IdleRPG Slack bot will track the
    time users are active in the rpg channel, and will respond to commands.
    """

    def __init__(self, slack_token, rpg_channel_name, db_filename):
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
        self._db_filename = db_filename
        self._users = {}
        self._active = False

        self.load()

    def connect(self):
        """Initiate a connection with Slack"""
        self._api.connect()
        self._post_connection_init()

        last_update = time.time()
        while True:
            events = self._api.read()

            for event in events:
                self._handle_event(event)

            if self._active:
                current_time = time.time()
                if current_time > last_update + UPDATE_INTERVAL:
                    last_update = current_time
                    self._update_all_users()
            time.sleep(READ_EVENT_PAUSE)

    def save(self):
        """Save the current user information to disk

        A clone is created of the user copy before saving, so that all users
        can be set to offline before being saved to disk
        """
        current_users = copy.deepcopy(self._users)
        for user_id, user in current_users.items():
            if user['active']:
                set_offline(current_users, user_id)

        db.save(self._db_filename, current_users)
        logging.debug('Users saved to %s', self._db_filename)

    def load(self):
        """Load user information from disk"""
        saved_users = db.load(self._db_filename)
        if saved_users:
            self._users = saved_users
            logging.debug('Users loaded from %s', self._db_filename)
        else:
            logging.debug('No database found at %s; load skipped', self._db_filename)

    def _post_connection_init(self):
        self_user = self._api.get_self()

        self._name = self_user['name']
        self._id = self_user['id']

        rpg_channel = self._api.get_channel(self._rpg_channel_name)
        self._rpg_channel_id = rpg_channel['id']

        member_ids = self._api.get_channel_users(self._rpg_channel_id)
        if not self._id in member_ids:
            logging.warning('Bot is not in RPG channel "%s". Invite to allow game to proceed', self._rpg_channel_name)
            self._api.send_message(
                self._rpg_channel_name,
                "Please invite me to this channel if you want to play IdleRPG!"
            )
        else:
            self._active = True
            self._update_all_users(member_ids)

    def _update_user(self, user_id):
        if not user_id in self._users:
            user = self._api.get_user_info(user_id)

            if user['is_bot']:
                return

            self._users[user_id] = {
                'profile': user['profile'],
                'active': False,
                'first_seen': None,
                'total': 0,
                'current_level_total': 0,
                'level': 0
            }

        active = self._api.is_user_active(user_id)

        if active:
            if not self._users[user_id]['active']:
                set_online(self._users, user_id)
            else:
                update_totals(self._users, user_id)
        else:
            if self._users[user_id]['active']:
                set_offline(self._users, user_id)

    def _handle_event(self, event):
        logging.debug('Recieved event: %s', event)
        if event['type'] == 'message':
            self._handle_message(event)
        elif event['type'] == 'presence_change':
            self._handle_presence_change(event)
        elif event['type'] == 'channel_joined':
            if event['channel']['id'] == self._rpg_channel_id:
                self._active = True
                self._update_all_users(event['channel']['members'])
                self._api.send_message(
                    event['channel']['id'],
                    'Thanks for the invite! IdleRPG has resumed.'
                )
        elif event['type'] == 'channel_left':
            if event['channel'] == self._rpg_channel_id:
                self._active = False
                for user_id, user in self._users.items():
                    if user['active']:
                        set_offline(self._users, user_id)
                self._api.send_message(
                    event['channel'],
                    'IdleRPG has been paused. Invite me back into the channel to resume the game'
                )

    def _handle_message(self, event):
        if not 'subtype' in event:
            text = event['text']
            if text.startswith('<@{}>'.format(self._id)):
                chunks = text.split()

                if len(chunks) > 1:
                    self._handle_command(event, chunks[1], chunks[2:])

    def _handle_command(self, event, command, args):
        command = command.lower()
        if command == 'hello' or command == 'hi':
            self._hello(event['channel'])
        elif command == 'scores':
            scores = []
            self._update_all_users()
            for user in self._users.values():
                name = user['profile']['display_name']
                if not name:
                    name = user['profile']['real_name']
                if not name:
                    name = user['profile']['email']

                level = user['level']
                total = user['total']

                if user['active']:
                    total += time.time() - user['first_seen']
                scores.append('{}: level {}, idle time: {}'.format(name, level, total))
            self._api.send_message(event['channel'], 'Scores:\n{}'.format('\n'.join(scores)))
        elif command == 'save':
            self.save()
        elif command == 'load':
            self.load()
            self._update_all_users()
        elif command == "api":
            try:
                method = args.pop(0)
            except IndexError:
                self._api.send_message(
                    event['channel'],
                    'API method missing.\nUsage: `api method [argName=argValue] ...`'
                )
                return

            api_args = {}

            for arg in args:
                key, val = arg.split('=')
                if key is None or val is None:
                    self._api.send_message(
                        event['channel'],
                        'Invalid api argument: "{}"\nShould be in format "key=value"'.format(arg)
                    )
                    return
                api_args[key] = val

            try:
                response = self._api.custom_api_call(method, **api_args)
            except SlackApiError as error:
                self._api.send_message(event['channel'], 'API error: "{}"'.format(error.error))
            else:
                self._api.send_message(event['channel'], 'API response: "{}"'.format(response))


    def _update_all_users(self, member_ids=None):
        if member_ids is None:
            member_ids = self._api.get_channel_users(self._rpg_channel_id)

        for member_id in member_ids:
            self._update_user(member_id)


    def _handle_presence_change(self, event):
        if self._active:
            self._update_user(event['user'])

    def _hello(self, channel_id):
        self._api.send_message(channel_id, 'Hello from Python! :tada:')

def set_online(users, user_id):
    """Sets a user in the given collection as active"""
    users[user_id]['active'] = True
    users[user_id]['first_seen'] = time.time()

def set_offline(users, user_id):
    """Sets a user in the given collection as inactive"""
    current_time = time.time()
    idle_time = current_time - users[user_id]['first_seen']

    users[user_id]['active'] = False
    users[user_id]['total'] += idle_time
    users[user_id]['current_level_total'] += idle_time
    users[user_id]['first_seen'] = None

    update_level(users, user_id)

def update_totals(users, user_id):
    """Updates the total time a user has been online"""
    current_time = time.time()
    idle_time = current_time - users[user_id]['first_seen']

    users[user_id]['total'] += idle_time
    users[user_id]['current_level_total'] += idle_time
    users[user_id]['first_seen'] = current_time

    update_level(users, user_id)

def update_level(users, user_id):
    """Checks whether a user has leveled up, and updates their level if so"""
    next_level = LEVEL_MULTIPLIER * (LEVEL_EXPONENTIAL_FACTOR ** users[user_id]['level'])
    if users[user_id]['current_level_total'] > next_level:
        users[user_id]['current_level_total'] -= next_level
        users[user_id]['level'] += 1
