from gotify import Gotify
from deluge_web_client import DelugeWebClient

# Messaging Consts

GOTIFY_BASE_URL = "http://octarine:8070"
GOTIFY_APP_TOKEN = "A-hs4fkT-eSdbUD"
DELUGE_BASE_URL = "http://spike:8112"
DELUGE_PASSWORD = ""

# Desired outcomes
DESIRED_FREE_SPACE = int((1000 * 1024 * 1024 * 1024) / 4)

def sort_by_most_recent_used(n):
    return n[1]['time_since_transfer']


# Set up messaging
gotify = Gotify(base_url=GOTIFY_BASE_URL, app_token=GOTIFY_APP_TOKEN)
# gotify.create_message("TClean Called", title='TClean', priority=0)
client = DelugeWebClient(DELUGE_BASE_URL, DELUGE_PASSWORD)

client.login()
print(f"🤔 Desired Free Space: \n    {(DESIRED_FREE_SPACE / 1000000000):,.2f} Gb")
free_space = client.get_free_space().result
print(f"🤔 Current Free Space: \n    {(free_space / 1000000000):,.2f} Gb")
if free_space >= DESIRED_FREE_SPACE:
    print(f"😊  The torrent server has ample free space!")
    gotify.create_message("TClean Called, nothing to do. 😊", title="TClean", priority=0)
else:
    pass
# This all goes in the "else" above but for testing I still need to run it...
all_torrents = client.get_torrents_status(
    keys=['seeding_time', 'hash', 'is_finished', 'paused', 'total_peers', 'total_seeds', 'ratio', 'name',
          'time_since_transfer', 'label']).result
candidates = {}
for torrent in all_torrents:
    # this gives us the torrent key in the dictionary all_torrents...
    # So, is this torrent older than 60 days?
    if (all_torrents[torrent]['seeding_time'] >= 60 * 24 * 60 * 60) and (all_torrents[torrent]['label'] == ""):
        candidates[torrent] = all_torrents[torrent]
# candidates now contains a list of all torrents that have been seeded > 60 days AND has no label
# So now we need to sort them from high to low on time_since_transfer
sorted_candidates = sorted(list(candidates.items()),key=sort_by_most_recent_used,reverse=True)

print("Top 5 Candidates for removal:")
print(f"1. {sorted_candidates[0][1]['name']}")
print(f"2. {sorted_candidates[1][1]['name']}")
print(f"3. {sorted_candidates[2][1]['name']}")
print(f"4. {sorted_candidates[3][1]['name']}")
print(f"5. {sorted_candidates[4][1]['name']}")