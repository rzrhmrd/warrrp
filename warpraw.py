import subprocess, os, datetime, base64, pytz, random

SCRIPT_DIR = os.path.dirname(__file__)
RESULT_CSV_PATH = os.path.join(SCRIPT_DIR, 'result.csv')
WARP_PROGRAM_PATH = os.path.join(SCRIPT_DIR, 'bin', 'warp')

def get_repository_name():
    return os.path.basename(os.path.dirname(SCRIPT_DIR)).upper()

def run_warp_program():
    if not os.path.exists(WARP_PROGRAM_PATH):
        raise RuntimeError(f"Warp binary not found at {WARP_PROGRAM_PATH}")
    os.chmod(WARP_PROGRAM_PATH, 0o755)
    process = subprocess.run([WARP_PROGRAM_PATH], stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
    if process.returncode != 0:
        raise RuntimeError("Warp execution failed")

def extract_clean_ips():
    clean_ips = []
    with open(RESULT_CSV_PATH, 'r') as csv_file:
        next(csv_file)  # Skip header
        for i, line in enumerate(csv_file):
            clean_ips.append(line.split(',')[0])
            if i == 1:
                break
    return clean_ips

def base64_encode(data):
    return base64.b64encode(data.encode('utf-8')).decode('utf-8')

def get_last_update_time():
    try:
        creation_time = os.path.getctime(RESULT_CSV_PATH)
    except OSError as e:
        print(f"Error accessing the result CSV file: {e}")
        return None
    tehran_tz = pytz.timezone('Asia/Tehran')
    local_time = datetime.datetime.fromtimestamp(creation_time, tehran_tz)
    return local_time.strftime("%Y-%m-%d %H:%M:%S %Z")

def generate_warp_config(clean_ips, last_update_time):
    mtu = random.randint(1280, 1420)
    warp_config = f'warp://{clean_ips[0]}?ifpm=m4&ifp=80-150&ifps=80-150&ifpd=20-25&mtu={mtu}#IR&&detour=warp://{clean_ips[1]}#DE'
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
        os.remove(RESULT_CSV_PATH)
    except OSError as e:
        print(f"Error removing file {RESULT_CSV_PATH}: {e}")

def main():
    run_warp_program()
    clean_ips = extract_clean_ips()
    last_update_time = get_last_update_time()
    if last_update_time is None:
        print("Error: Unable to get last update time.")
        return
    generate_warp_config(clean_ips, last_update_time)
    clean_up()
    print("Warp execution and configuration generation completed successfully.")

if __name__ == "__main__":
    main()