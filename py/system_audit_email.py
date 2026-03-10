import platform
import sys
import socket
import uuid
import psutil
import subprocess
from datetime import datetime
import os

# ===============================
# Helper to run WMIC commands
# ===============================
def run_wmic(command):
    try:
        output = subprocess.check_output(command, shell=True).decode().split("\n")[1].strip()
        return output
    except:
        return "Unavailable"

# ===============================
# Check Windows 11 requirements
# ===============================
def check_win11_requirements():
    results = {}

    # CPU: at least 2 cores, 64-bit
    cores = psutil.cpu_count(logical=False)
    arch = platform.machine()
    cpu_ok = cores >= 2 and arch.endswith('64')
    results["CPU"] = f"{cores} cores, {arch} - {'✔' if cpu_ok else '✖'}"

    # RAM >= 4 GB
    ram_gb = round(psutil.virtual_memory().total / (1024**3))
    ram_ok = ram_gb >= 4
    results["RAM"] = f"{ram_gb} GB - {'✔' if ram_ok else '✖'}"

    # Storage C: >= 64 GB
    try:
        disk = psutil.disk_usage("C:\\")
        disk_gb = disk.total // (1024**3)
        storage_ok = disk_gb >= 64
        results["Storage"] = f"{disk_gb} GB - {'✔' if storage_ok else '✖'}"
    except:
        results["Storage"] = "Unknown"

    # TPM 2.0
    try:
        tpm_output = subprocess.check_output(
            'powershell "get-tpm | select TpmPresent,TpmReady,TpmVersion"',
            shell=True
        ).decode()
        tpm_present = "True" in tpm_output
        tpm_version_ok = "2.0" in tpm_output
        results["TPM 2.0"] = f"{tpm_output.strip()} - {'✔' if tpm_present and tpm_version_ok else '✖'}"
    except:
        results["TPM 2.0"] = "TPM not detected - ✖"

    # Secure Boot
    try:
        sb = subprocess.check_output(
            'powershell "(Confirm-SecureBootUEFI)"',
            shell=True
        ).decode().strip()
        sb_ok = sb.lower() == 'true'
        results["Secure Boot"] = f"{sb} - {'✔' if sb_ok else '✖'}"
    except:
        results["Secure Boot"] = "Secure Boot check unavailable"

    return results

# ===============================
# Get system information
# ===============================
def get_system_info():
    info = {}

    # Basic system info
    info["Computer Name"] = socket.gethostname()
    info["User"] = platform.node()
    info["OS"] = platform.system() + " " + platform.release()
    info["OS Version"] = platform.version()
    info["Architecture"] = "64-bit" if platform.machine().endswith('64') else "32-bit"

    # CPU
    info["CPU"] = platform.processor()
    info["CPU Cores"] = psutil.cpu_count(logical=False)
    info["CPU Threads"] = psutil.cpu_count(logical=True)

    # RAM
    ram = psutil.virtual_memory()
    info["Total RAM"] = f"{round(ram.total / (1024**3),2)} GB"

    # Motherboard
    info["Motherboard Manufacturer"] = run_wmic("wmic baseboard get manufacturer")
    info["Motherboard Model"] = run_wmic("wmic baseboard get product")
    info["Motherboard Version"] = run_wmic("wmic baseboard get version")

    # BIOS
    info["BIOS Version"] = run_wmic("wmic bios get smbiosbiosversion")

    # GPU
    try:
        gpu = subprocess.check_output("wmic path win32_VideoController get name", shell=True).decode().split("\n")[1:]
        gpu_names = [g.strip() for g in gpu if g.strip()]
        info["GPU"] = ", ".join(gpu_names)
    except:
        info["GPU"] = "Unavailable"

    # Disks
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append(f"{part.device} : {round(usage.total / (1024**3))} GB")
        except:
            pass
    info["Disks"] = ", ".join(disks)

    # Network
    try:
        ip = socket.gethostbyname(socket.gethostname())
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                        for elements in range(0,2*6,8)][::-1])
        info["IP Address"] = ip
        info["MAC Address"] = mac
    except:
        info["IP Address"] = "Unavailable"
        info["MAC Address"] = "Unavailable"

    # Uptime
    boot = datetime.fromtimestamp(psutil.boot_time())
    info["System Boot Time"] = boot.strftime("%Y-%m-%d %H:%M:%S")

    return info

# ===============================
# Save info to timestamped text file in output folder
# ===============================
def save_to_file(info, win11_checks):
    script_folder = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_folder, "output")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_FILE = os.path.join(output_folder, f"system_inventory_{timestamp}.txt")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("SYSTEM INVENTORY REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Windows 11 technical requirements
        f.write("=== Windows 11 Technical Requirements ===\n")
        for k, v in win11_checks.items():
            f.write(f"{k}: {v}\n")
        f.write("\n")

        # All other system info
        f.write("=== System Information ===\n")
        for key, value in info.items():
            f.write(f"{key}: {value}\n")

    print(f"System info saved to {OUTPUT_FILE}")

# ===============================
# Main Execution
# ===============================
if __name__ == "__main__":
    win11_checks = check_win11_requirements()
    system_info = get_system_info()
    save_to_file(system_info, win11_checks)