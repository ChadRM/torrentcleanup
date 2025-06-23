from deluge_web_client import DelugeWebClient
import time
def get_next_key(dictionary, current_key):
    keys_iterator = iter(dictionary)
    found_current = False
    for key in keys_iterator:
        if found_current:
            return key  # This is the next key
        if key == current_key:
            found_current = True
    return None

DESIRED_FREE_SPACE = 1 * 1000 * 1000 * 1000 * 1000


# instantiate a client
client = DelugeWebClient(url="http://spike.local:8112", password="")

# login
# once logged in the `client` will maintain the logged in state as long as you don't call
# client.disconnect()
client.login()
print(f"Desired Free Space: \n{DESIRED_FREE_SPACE}")
while(client.get_free_space().result < DESIRED_FREE_SPACE):
    print(f"\nFree Space -> {client.get_free_space().result} is less than {DESIRED_FREE_SPACE}, finding one to delete....")
    all_torrents = client.get_torrents_status(keys=['seeding_time','hash','is_finished','paused','total_peers','total_seeds','ratio','name','time_since_transfer','label'])
    # print(all_torrents.result)
    key = next(iter(all_torrents.result))
    candidate_torrent = ""
    oldest_time = -1
    while key in all_torrents.result:
        if all_torrents.result[key]['label'] != "":
            print(f"{all_torrents.result[key]['name']} -- label: {all_torrents.result[key]['label']}")
        if all_torrents.result[key]['seeding_time']/60/60/24 > 60:
            if all_torrents.result[key]['paused'] == False:
                # print(f"{key} - {all_torrents.result[key]['name']} - {all_torrents.result[key]['seeding_time']/60/60/24} - {all_torrents.result[key]['time_since_transfer']/60/60/24}")
                if all_torrents.result[key]['time_since_transfer'] > oldest_time:
                    if all_torrents.result[key]['label'] != "":
                        pass
                    else:
                        oldest_time = all_torrents.result[key]['time_since_transfer']
                        candidate_torrent = str(key)
        key = get_next_key(all_torrents.result, key)

    print(f"\n\n Candidate for oldest: {all_torrents.result[candidate_torrent]['name']}")
    # client.pause_torrent(candidate_torrent)
    success = client.remove_torrent(torrent_id=candidate_torrent,remove_data=True)
    # print(success)
    time.sleep(1)

print(f"The torrent server has ample free space -> \n{client.get_free_space().result}")
client.disconnect()
