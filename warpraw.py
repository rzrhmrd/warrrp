import subprocess, os, datetime, base64, pytz, random, csv

SCRIPT_DIR = os.path.dirname(__file__)
WARP_BINARY_PATH = os.path.join(SCRIPT_DIR, 'bin', 'warp')
IP_SCAN_RESULTS_PATH = os.path.join(SCRIPT_DIR, 'result.csv')

def get_repository_name():
    return os.path.basename(os.path.dirname(SCRIPT_DIR)).upper()

def run_warp_program():
    if not os.path.exists(WARP_BINARY_PATH):
        raise RuntimeError(f"Warp binary not found at {WARP_BINARY_PATH}")
    os.chmod(WARP_BINARY_PATH, 0o755)
    process = subprocess.run([WARP_BINARY_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if process.returncode != 0:
        raise RuntimeError("Warp execution failed")

def extract_ips_with_lowest_latency():
    """
    Extracts IP addresses from the scan results CSV file and returns the two IPs with the lowest latency.
    """
    ip_latency_pairs = []

    try:
        with open(IP_SCAN_RESULTS_PATH, 'r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)  # Skip header
            for row in reader:
                ip_address = row[0]
                latency = float(row[1])
                ip_latency_pairs.append((ip_address, latency))
    except FileNotFoundError:
        raise RuntimeError(f"CSV file not found at {IP_SCAN_RESULTS_PATH}")
    except Exception as e:
        raise RuntimeError(f"Error reading CSV file: {e}")

    # Sort by latency and get the two IPs with the lowest latency
    ip_latency_pairs.sort(key=lambda x: x[1])
    lowest_latency_ips = [ip for ip, _ in ip_latency_pairs[:2]]

    return lowest_latency_ips

def base64_encode(data):
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')

def get_last_update_time():
    try:
        creation_time = os.path.getctime(IP_SCAN_RESULTS_PATH)
    except OSError as e:
        print(f"Error accessing the result CSV file: {e}")
        return None
    tehran_tz = pytz.timezone('Asia/Tehran')
    local_time = datetime.datetime.fromtimestamp(creation_time, tehran_tz)
    return local_time.strftime("%Y-%m-%d %H:%M:%S") + " Tehran, Iran"

def generate_warp_config(lowest_latency_ips, last_update_time):
    mtu = random.randint(1280, 1420)
    warp_config = f'warp://{lowest_latency_ips[0]}?ifpm=m4&ifp=80-150&ifps=80-150&ifpd=20-25&mtu={mtu}#IR&&detour=warp://{lowest_latency_ips[1]}#DE'
    warp_hiddify_config = (
        f"//profile-title: base64:{base64_encode(get_repository_name())}\n"
        f"//profile-update-interval: 1\n"
        f"//subscription-userinfo: upload=0; download=0; total=10737418240000000; expire=2546249531\n"
        f"//last-update: {last_update_time}\n"
        f"{warp_config}"
    )
    try:
        with open('config', 'w') as config_file:
            config_file.write(base64_encode(warp_hiddify_config))
    except IOError as e:
        print(f"Error writing to configuration file: {e}")

def clean_up():
    try:
        os.remove(IP_SCAN_RESULTS_PATH)
    except OSError as e:
        print(f"Error removing file {IP_SCAN_RESULTS_PATH}: {e}")

def main():
    run_warp_program()
    lowest_latency_ips = extract_ips_with_lowest_latency()
    if len(lowest_latency_ips) < 2:
        print("Error: Not enough IPs with low latency found.")
        return
    last_update_time = get_last_update_time()
    if last_update_time is None:
        print("Error: Unable to get last update time.")
        return
    generate_warp_config(lowest_latency_ips, last_update_time)
    clean_up()
    print("Warp execution and configuration generation completed successfully.")

if __name__ == "__main__":
    main()