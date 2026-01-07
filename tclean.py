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
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
GOTIFY_BASE_URL = os.getenv("GOTIFY_BASE_URL", "http://octarine:8070")
GOTIFY_APP_TOKEN = os.getenv("GOTIFY_APP_TOKEN")
DELUGE_BASE_URL = os.getenv("DELUGE_BASE_URL", "http://spike:8112")
DELUGE_PASSWORD = os.getenv("DELUGE_PASSWORD", "")
GB = 1073741824
SIXTY_DAYS_IN_SECONDS = 60 * 24 * 60 * 60

# Desired outcomes
DESIRED_FREE_SPACE_GB = int(os.getenv("DESIRED_FREE_SPACE_GB", 250))
DESIRED_FREE_SPACE = DESIRED_FREE_SPACE_GB * GB


def bytes_to_gb(byte_count):
    """Converts bytes to a formatted GB string."""
    return f"{(byte_count / GB):,.2f} GB"


def send_notification(gotify_client, message, title="TClean", priority=5):
    """Sends a notification using the Gotify client."""
    try:
        gotify_client.create_message(message, title=title, priority=priority)
    except Exception as e:
        logger.error(f"Failed to send Gotify notification: {e}")


def find_eligible_torrents(all_torrents):
    """Filters torrents older than 60 days with no label."""
    return {
        tid: status for tid, status in all_torrents.items()
        if status['seeding_time'] >= SIXTY_DAYS_IN_SECONDS and status['label'] == ""
    }


def wait_for_space_stabilization(deluge_client, initial_space):
    """Waits for disk space reported by Deluge to change after deletion."""
    max_checks = 12
    for check in range(max_checks):
        time.sleep(5)
        new_free_space = deluge_client.get_free_space().result
        if new_free_space != initial_space:
            logger.info(f"Space stabilized. Current free space: {bytes_to_gb(new_free_space)}")
            return new_free_space
        logger.info(f"Waiting for space to stabilize (check {check + 1}/{max_checks})...")

    logger.warning("Space stabilization timed out.")
    return deluge_client.get_free_space().result


def main():
    gotify_client = Gotify(base_url=GOTIFY_BASE_URL, app_token=GOTIFY_APP_TOKEN)
    deluge_client = DelugeWebClient(DELUGE_BASE_URL, DELUGE_PASSWORD)

    try:
        logger.info("Logging into Deluge...")
        deluge_client.login()

        free_space = deluge_client.get_free_space().result
        status_msg = f"Desired: {bytes_to_gb(DESIRED_FREE_SPACE)}\nFree space: {bytes_to_gb(free_space)}"
        logger.info(f"Current Free Space: {bytes_to_gb(free_space)}")

        if free_space >= DESIRED_FREE_SPACE:
            logger.info("The torrent server has ample free space!")
            send_notification(gotify_client, f"{status_msg}\nNothing to do. 😊")
            return

        send_notification(gotify_client, f"{status_msg}\nSearching for torrents to delete...")

        all_torrents = deluge_client.get_torrents_status(
            keys=['seeding_time', 'hash', 'is_finished', 'paused', 'total_peers',
                  'total_seeds', 'ratio', 'name', 'time_since_transfer', 'label', 'total_size']
        ).result

        candidates = find_eligible_torrents(all_torrents)
        sorted_candidates = sorted(candidates.items(), key=lambda x: x[1]['time_since_transfer'], reverse=True)

        logger.info(f"Found {len(sorted_candidates)} torrents eligible for removal.")
        send_notification(gotify_client, f"{len(sorted_candidates)} torrents eligible.")

        for index, (torrent_id, status) in enumerate(sorted_candidates):
            logger.info(
                f"{index + 1}. {status['name']} -- Size: {bytes_to_gb(status['total_size'])} -- ID: {torrent_id}")

            try:
                deluge_client.remove_torrent(torrent_id=torrent_id, remove_data=True)
                logger.info(f"Deleted torrent: {status['name']}")
                send_notification(gotify_client,
                                  f"Torrent Deleted:\n{status['name']}\nFreed: {bytes_to_gb(status['total_size'])}")
            except DelugeWebClientError as e:
                logger.error(f"Failed to remove torrent {status['name']}: {e}")
                continue

            free_space = wait_for_space_stabilization(deluge_client, free_space)

            if free_space >= DESIRED_FREE_SPACE:
                logger.info("Reached desired free space.")
                break

        send_notification(gotify_client, f"TClean complete.\nFree space: {bytes_to_gb(free_space)}")

    except DelugeWebClientError as e:
        logger.error(f"Deluge Client Error: {e}")
        send_notification(gotify_client, f"Deluge Client Error: {e}", priority=10)
    except KeyboardInterrupt:
        logger.info("Cleanup interrupted by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        send_notification(gotify_client, f"Unexpected Error: {e}", priority=10)


if __name__ == "__main__":
    main()