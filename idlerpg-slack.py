import os
import logging

from dotenv import load_dotenv
from bot import IdleRpgBot

def main():
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    load_dotenv('.env')

    slack_token = os.environ['SLACK_API_TOKEN']
    rpg_channel_name = os.environ.get('IDLE_RPG_CHANNEL', 'general')
    db_filename = os.environ.get('IDLE_RPG_DB', 'users.db')

    bot = IdleRpgBot(slack_token, rpg_channel_name, db_filename)
    bot.connect()

if __name__ == '__main__':
    main()
