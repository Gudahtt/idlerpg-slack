from slackclient import SlackClient
import time, os

from os.path import join, dirname
from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

slack_token = os.environ["SLACK_API_TOKEN"]
sc = SlackClient(slack_token)

sc.api_call(
  "chat.postMessage",
  channel="#general",
  text="Hello from Python! :tada:"
)

if sc.rtm_connect():
    while True:
        event = sc.rtm_read()
        print(event)

        time.sleep(1)
else:
    print("Connection Failed")

