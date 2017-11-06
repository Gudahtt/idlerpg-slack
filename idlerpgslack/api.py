# -*- coding: utf-8 -*-
"""Slack API Client

Acts as a wrapper around the slack client library.
"""

import logging
import re
from json.decoder import JSONDecodeError

from slackclient import SlackClient

LINK_REGEX = re.compile(r'''<https?:.+?\|(.+?)>''')

class SlackApiClient():
    """Slack API client"""

    def __init__(self, slack_token):
        """Returns a Slack Web API client"""
        self._sc = SlackClient(slack_token)

    def _safe_web_call(self, method, *args, **kwargs):
        link_match = LINK_REGEX.match(method)
        if link_match:
            method = link_match.group(1)

        logging.debug(
            'API method %s, args: "%s"',
            method,
            kwargs
        )
        try:
            response = self._sc.api_call(method, *args, **kwargs)
        except JSONDecodeError:
            raise SlackApiError(method, args, kwargs, 'Possible invalid method (JSONDecodeError)')

        if not response['ok']:
            raise SlackApiError(method, args, kwargs, response['error'])

        if 'warning' in response:
            logging.warning(
                'API method %s, args: "%s", warning: "%s"',
                method,
                kwargs,
                response['warning']
            )
        return response

    def connect(self):
        """Initiate a connection with Slack """
        if not self._sc.rtm_connect():
            raise RuntimeError('Connection Failed')

    def read(self):
        """Read from the Websocket connection"""
        return self._sc.rtm_read()

    def custom_api_call(self, method, *args, **kwargs):
        """Custom API call specified at runtime"""
        response = self._safe_web_call(method, *args, **kwargs)

        del response['ok']
        if 'args' in response:
            if 'token' in response['args']:
                del response['args']['token']
            if not response['args']:
                del response['args']

        return response

    def get_channel(self, name):
        """Return the Slack channel with the given name."""
        response = self._safe_web_call(
            'channels.list'
        )

        channels = response['channels']

        try:
            return next(channel for channel in channels if channel['name'] == name)
        except StopIteration:
            raise RuntimeError('Channel {} not found'.format(name))

    def get_channel_users(self, channel_id):
        """Return the list of users in the channel with the id given"""
        response = self._safe_web_call(
            'conversations.members',
            channel=channel_id
        )

        return response['members']

    def get_user_info(self, user_id):
        """Get user information from Slack"""
        response = self._safe_web_call(
            'users.info',
            user=user_id
        )

        return response['user']

    def is_user_active(self, user_id):
        """Returns whether the user is active or not"""
        response = self._safe_web_call(
            'users.getPresence',
            user=user_id
        )

        return response['presence'] == 'active'

    def send_message(self, channel_id, message, attachments=None):
        """Sends a message to a Slack channel"""
        self._safe_web_call(
            'chat.postMessage',
            channel=channel_id,
            text=message,
            attachments=attachments
        )

    def get_self(self):
        """Returns information about the connected user"""
        return self._sc.server.login_data['self']

class SlackApiError(Exception):
    """Raise when a Slack API call results in an error response"""
    def __init__(self, method, api_args, api_kwargs, error, *args):
        self.method = method
        self.api_args = api_args
        self.api_kwargs = api_kwargs
        self.error = error

        super(SlackApiError, self).__init__(
            'Error calling \'{}\', message: "{}"'.format(method, error),
            method,
            api_args,
            api_kwargs,
            error,
            *args
        )
