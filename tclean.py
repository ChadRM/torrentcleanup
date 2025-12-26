import time

from gotify import Gotify
from deluge_web_client import DelugeWebClient

# Messaging Consts

GOTIFY_BASE_URL = "http://octarine:8070"
GOTIFY_APP_TOKEN = "A-hs4fkT-eSdbUD"
DELUGE_BASE_URL = "http://spike:8112"
DELUGE_PASSWORD = ""
GB = 1073741824

# Desired outcomes
DESIRED_FREE_SPACE = 250 * GB

def sort_by_most_recent_used(n):
    return n[1]['time_since_transfer']


# Set up messaging
gotify = Gotify(base_url=GOTIFY_BASE_URL, app_token=GOTIFY_APP_TOKEN)
# gotify.create_message("TClean Called", title='TClean', priority=0)
client = DelugeWebClient(DELUGE_BASE_URL, DELUGE_PASSWORD)

client.login()
print(f"🤔 Desired Free Space: \n    {(DESIRED_FREE_SPACE / GB):,.2f} Gb")
free_space = client.get_free_space().result
print(f"🤔 Current Free Space: \n    {(free_space / GB):,.2f} Gb")
if free_space >= DESIRED_FREE_SPACE:
    print(f"😊  The torrent server has ample free space!")
    gotify.create_message(f"Desired: {DESIRED_FREE_SPACE / GB:,.2f}\nFree space: {(free_space / GB):,.2f} Gb,\nNothing to do. 😊", title="TClean", priority=0)
else:
    gotify.create_message(f"Desired: {DESIRED_FREE_SPACE / GB:,.2f}\nFree space: {(free_space / GB):,.2f} Gb,\nSearching for torrents to delete...", title="TClean", priority=0)
    all_torrents = client.get_torrents_status(
       keys=['seeding_time', 'hash', 'is_finished', 'paused', 'total_peers', 'total_seeds', 'ratio', 'name',
             'time_since_transfer', 'label','total_size']
    ).result
    candidates = {}
    for torrent in all_torrents:
        # this gives us the torrent key in the dictionary all_torrents...
        # So, is this torrent older than 60 days?
        if (all_torrents[torrent]['seeding_time'] >= 60 * 24 * 60 * 60) and (all_torrents[torrent]['label'] == ""):
            candidates[torrent] = all_torrents[torrent]
    # candidates now contains a list of all torrents that have been seeded > 60 days AND has no label
    # So now we need to sort them from high to low on time_since_transfer
    sorted_candidates = sorted(list(candidates.items()),key=sort_by_most_recent_used,reverse=True)
    print(f"There are {len(sorted_candidates)} torrents eligible for removal:")
    gotify.create_message(f"{len(sorted_candidates)} torrents eligible.", title="TClean", priority=0)
    for index in range(0, len(sorted_candidates)):
        print(f"{index + 1}. {sorted_candidates[index][1]['name']} -- Size: {sorted_candidates[index][1]['total_size'] / GB:,.2f} Gb -- Torrent ID: {sorted_candidates[index][0]}")
        # Code to delete a torrent:
        success = client.remove_torrent(torrent_id=sorted_candidates[index][0], remove_data=True)
        gotify.create_message(f"Torrent Deleted:\n{sorted_candidates[index][1]['name']}\nFreed space: {sorted_candidates[index][1]['total_size'] / GB:,.2f} Gb")
        while free_space != client.get_free_space().result:
            free_space = client.get_free_space().result
            time.sleep(5) # wait for free space to stabilize -- it might've been a huge torrent.  If there are active torrents, this might take a while.  That's okay.
        if free_space >= DESIRED_FREE_SPACE:
            break
    gotify.create_message(f"TClean complete.\nFree space: {free_space:,.2f} Gb", title="TClean", priority=0)

