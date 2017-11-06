# -*- coding: utf-8 -*-
"""Bot Command-Line Interface

Command-line interface for the IdleRPG Slack bot
"""

import os
import logging

from dotenv import load_dotenv

from .bot import IdleRpgBot

def main():
    """Starts IdleRPG Slack bot"""
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    load_dotenv('.env')

    slack_token = os.environ['SLACK_API_TOKEN']
    rpg_channel_name = os.environ.get('IDLE_RPG_CHANNEL', 'general')
    db_filename = os.environ.get('IDLE_RPG_DB', 'users.db')

    bot = IdleRpgBot(slack_token, rpg_channel_name, db_filename)
    bot.connect()
