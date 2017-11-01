from slackclient import SlackClient
import time, os

from dotenv import load_dotenv

load_dotenv('.env')

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

