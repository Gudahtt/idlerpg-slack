from slackclient import SlackClient
import time

slack_token = 'xoxb-264743104951-b9Irpl2oKKluOT7dzZFZxTB4' #os.environ["SLACK_API_TOKEN"]
sc = SlackClient(slack_token)

sc.api_call(
  "chat.postMessage",
  channel="#general",
  text="Hello from Python! :tada:"
)

if sc.rtm_connect():
    while True:
        stuff = sc.rtm_read()

        if (len(stuff) > 0):
            print(len(stuff))
else:
    print("Connection Failed")

