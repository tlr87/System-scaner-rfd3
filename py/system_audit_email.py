import platform
import sys
import socket
import uuid
import psutil
import subprocess
from datetime import datetime
import os

# ===============================
# Compatibility Check for Windows 11
# ===============================
def check_compatibility():
    os_name = platform.system()
    
    if os_name != "Windows":
        print(f"Unsupported OS: {os_name}. This tool requires Windows 11.")
        sys.exit(1)
    
    try:
        build_number = int(subprocess.check_output(
            'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion" /v CurrentBuildNumber',
            shell=True
        ).decode().split()[-1])
    except Exception as e:
        print(f"Could not determine Windows build number: {e}")
        sys.exit(1)
    
    if build_number < 22000:
        print(f"Unsupported Windows version: build {build_number}. Requires Windows 11 (build 22000+).")
        sys.exit(1)
    
    print(f"OS compatibility check passed: Windows 11 build {build_number}\n")

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
# Save info to timestamped text file in the script's folder
# ===============================
def save_to_file(info):
    # Get folder where the script is located
    script_folder = os.path.dirname(os.path.abspath(__file__))
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_FILE = os.path.join(script_folder, f"system_inventory_{timestamp}.txt")
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("SYSTEM INVENTORY REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for key, value in info.items():
            f.write(f"{key}: {value}\n")
    
    print(f"System info saved to {OUTPUT_FILE}")

# ===============================
# Main Execution
# ===============================
if __name__ == "__main__":
    check_compatibility()
    system_info = get_system_info()
    save_to_file(system_info)