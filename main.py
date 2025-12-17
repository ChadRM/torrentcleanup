import time

from deluge_web_client import DelugeWebClient


def get_next_key(dictionary, current_key):
    keys = dictionary.keys()
    found_current = False
    for key in keys:
        if found_current:
            return key  # This is the next key
        if key == current_key:
            found_current = True
    return None


DESIRED_FREE_SPACE = int((1000 * 1024 * 1024 * 1024)/4)

client = DelugeWebClient(url="http://spike:8112", password="")

client.login()
print(f"🤔 Desired Free Space: \n{DESIRED_FREE_SPACE}")
while client.get_free_space().result < DESIRED_FREE_SPACE:
    all_torrents = client.get_torrents_status(
        keys=['seeding_time', 'hash', 'is_finished', 'paused', 'total_peers', 'total_seeds', 'ratio', 'name',
              'time_since_transfer', 'label'])
    key = next(iter(all_torrents.result))
    candidate_torrent = ""
    oldest_time = -1
    while key in all_torrents.result:
        if all_torrents.result[key]["label"] != "":
            pass
            # This torrent has a label on it and is therefore ineligible for deletion.  Skip it.
            # print(f"{all_torrents.result[key]['name']} -- label: {all_torrents.result[key]['label']}")
        elif int(all_torrents.result[key]['seeding_time']) / 60 / 60 / 24 > 60:
            if not all_torrents.result[key]['paused']:
                if all_torrents.result[key]['time_since_transfer'] > oldest_time:
                    if all_torrents.result[key]['label'] != "":
                        pass
                    else:
                        oldest_time = all_torrents.result[key]['time_since_transfer']
                        candidate_torrent = str(key)
        key = get_next_key(all_torrents.result, key)

    print(f"🚫 Deleting: {all_torrents.result[candidate_torrent]['name']}")
    # client.pause_torrent(candidate_torrent)
    success = client.remove_torrent(torrent_id=candidate_torrent, remove_data=True)
    time.sleep(1)

print(f"😊  The torrent server has ample free space -> \n{client.get_free_space().result}")

