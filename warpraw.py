import subprocess
import os
import datetime
import base64
import pytz
import random
import csv
import requests

SCRIPT_DIR = os.path.dirname(__file__)
WARP_SERVER_SCANNER_PATH = os.path.join(SCRIPT_DIR, 'bin', 'warp')
SERVER_SCAN_RESULTS_PATH = os.path.join(SCRIPT_DIR, 'result.csv')
CONFIG_FILE_PATH = os.path.join(SCRIPT_DIR, 'config')

CHECK_HOST_API_URL = "https://check-host.net/check-ping"
TEHRAN_NODE = "ir-1"

def get_repository_name():
    return os.path.basename(os.path.dirname(SCRIPT_DIR)).upper()

def run_warp_server_scanner():
    if not os.path.exists(WARP_SERVER_SCANNER_PATH):
        raise RuntimeError(f"Warp binary not found at {WARP_SERVER_SCANNER_PATH}")
    os.chmod(WARP_SERVER_SCANNER_PATH, 0o755)
    process = subprocess.run([WARP_SERVER_SCANNER_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if process.returncode != 0:
        raise RuntimeError("Warp execution failed")

def extract_top_servers():
    servers = []

    try:
        with open(SERVER_SCAN_RESULTS_PATH, 'r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Skip header
            for row in reader:
                server_address = row[0].split(':')[0]  # Extract only the server address
                servers.append(server_address)

                if len(servers) == 10:
                    break
    except FileNotFoundError:
        raise RuntimeError(f"CSV file not found at {SERVER_SCAN_RESULTS_PATH}")
    except Exception as e:
        raise RuntimeError(f"Error reading CSV file: {e}")

    return servers

def check_ping(server):
    response = requests.post(CHECK_HOST_API_URL, data={'host': server, 'nodes[]': TEHRAN_NODE})
    if response.status_code == 200:
        result = response.json()
        if TEHRAN_NODE in result['nodes']:
            return result['nodes'][TEHRAN_NODE]['ping']
    return None

def get_best_servers(servers):
    ping_results = []
    for server in servers:
        ping = check_ping(server)
        if ping:
            ping_results.append((server, ping))
    
    # Debug print statement before sorting
    print("Ping results before sorting:", ping_results)
    
    ping_results.sort(key=lambda x: x[1])  # Sort by ping time
    
    # Debug print statement after sorting
    print("Ping results after sorting:", ping_results)
    
    return [server for server, _ in ping_results[:2]]

def base64_encode(data):
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')

def get_last_update_time():
    try:
        creation_time = os.path.getctime(SERVER_SCAN_RESULTS_PATH)
    except OSError as e:
        print(f"Error accessing the result CSV file: {e}")
        return None
    tehran_tz = pytz.timezone('Asia/Tehran')
    local_time = datetime.datetime.fromtimestamp(creation_time, tehran_tz)
    return local_time.strftime("%Y-%m-%d %H:%M") + " Tehran, Iran Time"

def generate_warp_config(top_servers, last_update_time):
    available_modes = ['m4', 'm5']
    mode = random.choice(available_modes)
    warp_config = f'warp://{top_servers[0]}?ifp=80-150&ifps=80-150&ifpd=20-25&ifpm={mode}#IR&&detour=warp://{top_servers[1]}#DE'
    warp_hiddify_config = (
        f"//profile-title: base64:{base64_encode(get_repository_name())}\n"
        f"//profile-update-interval: 1\n"
        f"//subscription-userinfo: upload=0; download=0; total=10737418240000000; expire=2546249531\n"
        f"//last-update: {last_update_time}\n"
        f"{warp_config}"
    )
    try:
        with open(CONFIG_FILE_PATH, 'w') as config_file:
            config_file.write(base64_encode(warp_hiddify_config))
    except IOError as e:
        print(f"Error writing to configuration file: {e}")

def clean_up():
    try:
        os.remove(SERVER_SCAN_RESULTS_PATH)
    except OSError as e:
        print(f"Error removing file {SERVER_SCAN_RESULTS_PATH}: {e}")

def main():
    run_warp_server_scanner()
    servers = extract_top_servers()
    if len(servers) < 10:
        print("Error: Not enough servers found.")
        return
    best_servers = get_best_servers(servers)
    if len(best_servers) < 2:
        print("Error: Not enough servers with ping results found.")
        return
    last_update_time = get_last_update_time()
    if last_update_time is None:
        print("Error: Unable to get last update time.")
        return
    generate_warp_config(best_servers, last_update_time)
    clean_up()
    print("Warp execution and configuration generation completed successfully.")

if __name__ == "__main__":
    main()