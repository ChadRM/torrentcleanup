import time
import os
import logging
import sys
from dotenv import load_dotenv

from gotify import Gotify, GotifyError
from deluge_web_client import DelugeWebClient, DelugeWebClientError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Messaging Consts
GOTIFY_BASE_URL = os.getenv("GOTIFY_BASE_URL", "http://octarine:8070")
GOTIFY_APP_TOKEN = os.getenv("GOTIFY_APP_TOKEN")
DELUGE_BASE_URL = os.getenv("DELUGE_BASE_URL", "http://spike:8112")
DELUGE_PASSWORD = os.getenv("DELUGE_PASSWORD", "")

GB = 1073741824

# Desired outcomes
DESIRED_FREE_SPACE_GB = int(os.getenv("DESIRED_FREE_SPACE_GB", 250))
DESIRED_FREE_SPACE = DESIRED_FREE_SPACE_GB * GB

def sort_by_most_recent_used(n):
    return n[1]['time_since_transfer']

def send_notification(gotify_client, message, title="TClean", priority=5):
    try:
        gotify_client.create_message(message, title=title, priority=priority)
    except GotifyError as e:
        logger.error(f"Failed to send Gotify notification: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while sending Gotify notification: {e}")

def main():
    # Set up messaging
    gotify = Gotify(base_url=GOTIFY_BASE_URL, app_token=GOTIFY_APP_TOKEN)
    client = DelugeWebClient(DELUGE_BASE_URL, DELUGE_PASSWORD)

    try:
        logger.info("Logging into Deluge...")
        client.login()
        
        logger.info(f"Desired Free Space: {(DESIRED_FREE_SPACE / GB):,.2f} GB")
        free_space = client.get_free_space().result
        logger.info(f"Current Free Space: {(free_space / GB):,.2f} GB")

        if free_space >= DESIRED_FREE_SPACE:
            logger.info("The torrent server has ample free space!")
            send_notification(gotify, f"Desired: {DESIRED_FREE_SPACE / GB:,.2f} GB\nFree space: {(free_space / GB):,.2f} GB\nNothing to do. 😊")
            return

        send_notification(gotify, f"Desired: {DESIRED_FREE_SPACE / GB:,.2f} GB\nFree space: {(free_space / GB):,.2f} GB\nSearching for torrents to delete...", priority=5)
        
        all_torrents = client.get_torrents_status(
           keys=['seeding_time', 'hash', 'is_finished', 'paused', 'total_peers', 'total_seeds', 'ratio', 'name',
                 'time_since_transfer', 'label','total_size']
        ).result

        candidates = {}
        for torrent_id, status in all_torrents.items():
            # Torrent older than 60 days and has no label?
            if (status['seeding_time'] >= 60 * 24 * 60 * 60) and (status['label'] == ""):
                candidates[torrent_id] = status

        sorted_candidates = sorted(list(candidates.items()), key=sort_by_most_recent_used, reverse=True)
        logger.info(f"Found {len(sorted_candidates)} torrents eligible for removal.")
        send_notification(gotify, f"{len(sorted_candidates)} torrents eligible.", priority=5)

        for index, (torrent_id, status) in enumerate(sorted_candidates):
            logger.info(f"{index + 1}. {status['name']} -- Size: {status['total_size'] / GB:,.2f} GB -- ID: {torrent_id}")
            
            # Delete torrent
            try:
                client.remove_torrent(torrent_id=torrent_id, remove_data=True)
                logger.info(f"Deleted torrent: {status['name']}")
                send_notification(gotify, f"Torrent Deleted:\n{status['name']}\nFreed space: {status['total_size'] / GB:,.2f} GB")
            except DelugeWebClientError as e:
                logger.error(f"Failed to remove torrent {status['name']}: {e}")
                continue

            # Wait for space to stabilize
            max_stabilization_checks = 12 # 1 minute total
            for check in range(max_stabilization_checks):
                time.sleep(5)
                new_free_space = client.get_free_space().result
                if new_free_space != free_space:
                    free_space = new_free_space
                    logger.info(f"Space stabilized. Current free space: {free_space / GB:,.2f} GB")
                    break
                logger.info(f"Waiting for space to stabilize (check {check + 1}/{max_stabilization_checks})...")
            else:
                logger.warning("Space stabilization timed out. Proceeding with last known space.")
                free_space = client.get_free_space().result

            if free_space >= DESIRED_FREE_SPACE:
                logger.info("Reached desired free space.")
                break

        send_notification(gotify, f"TClean complete.\nFree space: {free_space / GB:,.2f} GB")

    except DelugeWebClientError as e:
        logger.error(f"Deluge Client Error: {e}")
        send_notification(gotify, f"Deluge Client Error: {e}", priority=10)
    except KeyboardInterrupt:
        logger.info("Cleanup interrupted by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        send_notification(gotify, f"Unexpected Error: {e}", priority=10)

if __name__ == "__main__":
    main()

