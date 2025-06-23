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


# instantiate a client
client = DelugeWebClient(url="http://spike.local:8112", password="")

# login
# once logged in the `client` will maintain the logged in state as long as you don't call
# client.disconnect()
client.login()

while(client.get_free_space().result < 1 * 1024 * 1024 * 1024 * 1024):
    print(f"\nFree Space -> {client.get_free_space().result} is less than { 1024 * 1024 * 1024 * 1024}")
    all_torrents = client.get_torrents_status(keys=['seeding_time','hash','is_finished','paused','total_peers','total_seeds','ratio','name','time_since_transfer'])
    key = next(iter(all_torrents.result))
    candidate_torrent = ""
    oldest_time = -1
    while key in all_torrents.result:
        if all_torrents.result[key]['seeding_time']/60/60/24 > 60:
            if all_torrents.result[key]['paused'] == False:
                # print(f"{key} - {all_torrents.result[key]['name']} - {all_torrents.result[key]['seeding_time']/60/60/24} - {all_torrents.result[key]['time_since_transfer']/60/60/24}")
                if all_torrents.result[key]['time_since_transfer'] > oldest_time:
                    oldest_time = all_torrents.result[key]['time_since_transfer']
                    candidate_torrent = str(key)
        key = get_next_key(all_torrents.result, key)

    print(f"\n\n Candidate for oldest: {all_torrents.result[candidate_torrent]['name']}")
    # client.pause_torrent(candidate_torrent)
    success = client.remove_torrent(torrent_id=candidate_torrent,remove_data=True)
    print(success)
    time.sleep(1)

print(f"Free Space -> {client.get_free_space().result}")
print(f"In TB terms -> {float(client.get_free_space().result /1024/1024/1024/1024)}")
