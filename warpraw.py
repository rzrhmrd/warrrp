import ipaddress, subprocess, os, datetime, base64, pytz, random

# Define the CIDR ranges for Warp IPs
WARP_CIDR_RANGES = [
    '162.159.192.0/24',
    '162.159.193.0/24',
    '162.159.195.0/24',
    '162.159.204.0/24',
    '188.114.96.0/24',
    '188.114.97.0/24',
    '188.114.98.0/24',
    '188.114.99.0/24'
]

# Define paths to the necessary files
SCRIPT_DIR = os.path.dirname(__file__)
IP_PATH = os.path.join(SCRIPT_DIR, 'ip.txt')
RESULT_CSV_PATH = os.path.join(SCRIPT_DIR, 'result.csv')
WARP_PROGRAM_PATH = os.path.join(SCRIPT_DIR, 'bin', 'warp')

def get_repository_name():
    """Get the repository name from the script directory."""
    return os.path.basename(os.path.dirname(SCRIPT_DIR)).upper()

def generate_ip_list():
    """Generate a list of IP addresses from the given CIDR ranges and save to a file."""
    total_ips = sum(len(list(ipaddress.IPv4Network(cidr))) for cidr in WARP_CIDR_RANGES)

    with open(IP_PATH, 'w') as ip_file:
        for cidr in WARP_CIDR_RANGES:
            for i, ip_addr in enumerate(ipaddress.IPv4Network(cidr)):
                ip_file.write(str(ip_addr))
                if i != total_ips - 1:
                    ip_file.write('\n')

def run_warp_program():
    """Execute the warp program from the local bin directory."""
    if not os.path.exists(WARP_PROGRAM_PATH):
        raise RuntimeError(f"Warp binary not found at {WARP_PROGRAM_PATH}")

    process = subprocess.Popen(WARP_PROGRAM_PATH, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    process.wait()

    if process.returncode != 0:
        raise RuntimeError("Warp execution failed")

def extract_clean_ips():
    """Extract the clean IPs from the result CSV file."""
    clean_ips = []
    with open(RESULT_CSV_PATH, 'r') as csv_file:
        next(csv_file)  # Skip header
        for i, line in enumerate(csv_file):
            clean_ips.append(line.split(',')[0])
            if i == 1:
                break
    return clean_ips

def base64_encode(data):
    """Encode the data using Base64."""
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')

def get_last_update_time():
    """Get the last update time based on the creation time of RESULT_CSV_PATH."""
    try:
        creation_time = os.path.getctime(RESULT_CSV_PATH)
    except OSError as e:
        print(f"Error accessing the result CSV file: {e}")
        return None

    tehran_tz = pytz.timezone('Asia/Tehran')
    local_time = datetime.datetime.fromtimestamp(creation_time, tehran_tz)
    return local_time.strftime("%Y-%m-%d %H:%M:%S %Z")

def generate_warp_config(clean_ips, last_update_time):
    """Generate the Warp configuration file based on the clean IPs."""
    mtu = random.randint(1280, 1420)
    warp_config = (
        f'warp://{clean_ips[0]}?ifpm=m4&ifp=80-150&ifps=80-150&ifpd=20-25&mtu={mtu}#IR&&detour=warp://{clean_ips[1]}#DE'
    )

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
        print(f"Error writing to configuration files: {e}")

def clean_up():
    """Remove temporary files generated during the script execution."""
    paths = [IP_PATH, RESULT_CSV_PATH]
    for path in paths:
        try:
            os.remove(path)
        except OSError as e:
            print(f"Error removing file {path}: {e}")

def main():
    """Main function to execute the warp script logic."""
    if not os.path.exists(IP_PATH):
        print('Creating ip.txt file...')
        generate_ip_list()
        print('ip.txt file created successfully.')
    else:
        print("ip.txt file already exists.")

    print("Executing warp program...")
    run_warp_program()

    print("Extracting clean IPs and generating warp config...")
    clean_ips = extract_clean_ips()

    last_update_time = get_last_update_time()
    if last_update_time is None:
        print("Error: Unable to get last_update_time.")
        return

    generate_warp_config(clean_ips, last_update_time)

    print("Cleaning up temporary files...")
    clean_up()

    print("Warp execution and configuration generation completed successfully.")

if __name__ == "__main__":
    main()