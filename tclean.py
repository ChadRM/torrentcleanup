from gotify import Gotify
from deluge_web_client import DelugeWebClient

# Messaging Consts

GOTIFY_BASE_URL="http://octarine:8070"
GOTIFY_APP_TOKEN="A-hs4fkT-eSdbUD"
DELUGE_BASE_URL="http://spike:8112"
DELUGE_PASSWORD=""

# Desired outcomes
DESIRED_FREE_SPACE = int((1000 * 1024 * 1024 * 1024)/4)

# Set up messaging
gotify = Gotify(base_url=GOTIFY_BASE_URL,app_token=GOTIFY_APP_TOKEN)
# gotify.create_message("TClean Called", title='TClean', priority=0)
client = DelugeWebClient(DELUGE_BASE_URL,DELUGE_PASSWORD)

client.login()
print(f"🤔 Desired Free Space: \n    {(DESIRED_FREE_SPACE/1000000000):,.2f} Gb")
free_space = client.get_free_space().result
print(f"🤔 Current Free Space: \n    {(free_space/1000000000):,.2f} Gb")
if free_space >= DESIRED_FREE_SPACE:
    print(f"😊  The torrent server has ample free space!")
    gotify.create_message("TClean Called, nothing to do. 😊",title="TClean",priority=0)



