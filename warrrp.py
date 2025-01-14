import os
import csv
import base64
import pytz
import datetime
import subprocess

# Constants for paths
SCRIPT_DIR = os.path.dirname(__file__)
WARP_SERVER_SCANNER_PATH = os.path.join(SCRIPT_DIR, 'bin', 'warp')
SERVER_SCAN_RESULTS_PATH = os.path.join(SCRIPT_DIR, 'result.csv')
CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, 'config')

def get_repository_name():
    """Returns the uppercase name of the repository."""
    return os.path.basename(os.path.dirname(SCRIPT_DIR)).upper()

def run_warp_server_scanner():
    """Runs the Warp server scanner binary."""
    if not os.path.exists(WARP_SERVER_SCANNER_PATH):
        raise RuntimeError(f"Warp binary not found at {WARP_SERVER_SCANNER_PATH}")

    os.chmod(WARP_SERVER_SCANNER_PATH, 0o755)
    process = subprocess.run([WARP_SERVER_SCANNER_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)

    if process.returncode != 0:
        raise RuntimeError("Warp execution failed")

def extract_top_two_servers():
    """Extracts the top two server addresses from the CSV results."""
    top_servers = []

    try:
        with open(SERVER_SCAN_RESULTS_PATH, 'r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Skip header

            for row in reader:
                server_address = row[0]
                top_servers.append(server_address)

                if len(top_servers) == 2:
                    break

    except FileNotFoundError:
        raise RuntimeError(f"CSV file not found at {SERVER_SCAN_RESULTS_PATH}")
    except Exception as e:
        raise RuntimeError(f"Error reading CSV file: {e}")

    return top_servers

def base64_encode(data):
    """Encodes the given data in Base64."""
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')

def get_last_update_time():
    """Returns the last update time of the result CSV file in Tehran time."""
    try:
        creation_time = os.path.getctime(SERVER_SCAN_RESULTS_PATH)
    except OSError as e:
        print(f"Error accessing the result CSV file: {e}")
        return None

    tehran_tz = pytz.timezone('Asia/Tehran')
    local_time = datetime.datetime.fromtimestamp(creation_time, tehran_tz)
    return local_time.strftime("%Y-%m-%d %H:%M") + " Tehran, Iran Time"

def generate_warp_config(top_servers, last_update_time):
    """Generates and writes the Warp configuration based on the top servers and last update time."""
    plus_key = os.getenv('PLUS_KEY')

    warp_config = (
        f"warp://{top_servers[0]}?ifp=50-100&ifps=50-100&ifpd=3-6&ifpm=m4#IR&&detour=warp://{top_servers[1]}#DE"
    )

    warp_hiddify_config = (
        f"#profile-title: base64:{base64_encode(get_repository_name())}\n"
        f"#profile-update-interval: 1\n"
        f"#subscription-userinfo: upload=0; download=0; total=10737418240000000; expire=2546249531\n"
        f"#profile-web-page-url: https://github.com/rzrhmrd/warrrp\n"
        f"#last-update: {last_update_time}\n"
        f"{warp_config}"
    )

    try:
        with open(CONFIG_FILE_PATH, 'w') as config_file:
            config_file.write(base64_encode(warp_hiddify_config))
    except IOError as e:
        print(f"Error writing to configuration file: {e}")

def clean_up():
    """Cleans up by removing the result CSV file."""
    try:
        os.remove(SERVER_SCAN_RESULTS_PATH)
    except OSError as e:
        print(f"Error removing file {SERVER_SCAN_RESULTS_PATH}: {e}")

def main():
    """Main function to run the warp server scanner and generate the config."""
    run_warp_server_scanner()
    top_servers = extract_top_two_servers()

    if len(top_servers) < 2:
        print("Error: Not enough servers found.")
        return

    last_update_time = get_last_update_time()

    if last_update_time is None:
        print("Error: Unable to get last update time.")
        return

    generate_warp_config(top_servers, last_update_time)
    clean_up()
    print("Warp execution and configuration generation completed successfully.")

if __name__ == "__main__":
    main()