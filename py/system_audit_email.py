import platform
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
# TPM 2.0 check (PowerShell + fallback registry)
# ===============================
def check_tpm():
    try:
        output = subprocess.check_output(
            'powershell -Command "Get-Tpm | Select-Object -Property TpmPresent, TpmReady, TpmVersion"',
            shell=True
        ).decode().strip().replace("\r","")
        lines = [line for line in output.split("\n") if line.strip()]
        if len(lines) < 2:
            raise Exception("PowerShell TPM returned no data")
        tpm_values = lines[1].split()
        tpm_present = tpm_values[0].lower() == "true"
        tpm_ready = tpm_values[1].lower() == "true"
        tpm_version_ok = len(tpm_values) > 2 and "2.0" in tpm_values[2]
        status = "✔" if tpm_present and tpm_ready and tpm_version_ok else "✖"
        return f"TpmPresent: {tpm_values[0]}, TpmReady: {tpm_values[1]}, TpmVersion: {tpm_values[2] if len(tpm_values)>2 else 'N/A'} - {status}"
    except:
        try:
            reg = subprocess.check_output(
                'reg query "HKLM\\SYSTEM\\CurrentControlSet\\Control\\DeviceGuard\\Scenarios\\TPM" /v Enabled',
                shell=True
            ).decode()
            if "0x1" in reg:
                return "TPM Present (Registry) - ✔"
            else:
                return "TPM not detected (Registry) - ✖"
        except:
            return "TPM check unavailable - ✖"

# ===============================
# Secure Boot check (PowerShell + fallback registry)
# ===============================
def check_secure_boot():
    try:
        sb = subprocess.check_output(
            'powershell -Command "Confirm-SecureBootUEFI"',
            shell=True, stderr=subprocess.DEVNULL
        ).decode().strip()
        if sb.lower() == "true":
            return "Enabled ✔"
        else:
            return "Disabled ✖"
    except:
        try:
            reg = subprocess.check_output(
                'reg query "HKLM\\SYSTEM\\CurrentControlSet\\Control\\SecureBoot\\State" /v UEFISecureBootEnabled',
                shell=True
            ).decode()
            if "0x1" in reg:
                return "Enabled (Registry) ✔"
            else:
                return "Disabled (Registry) ✖"
        except:
            return "Check unavailable - ✖"

# ===============================
# Check Windows 11 requirements
# ===============================
def check_win11_requirements():
    results = {}
    cores = psutil.cpu_count(logical=False)
    arch = platform.machine()
    cpu_ok = cores >= 2 and arch.endswith('64')
    results["CPU"] = f"{cores} cores, {arch} - {'✔' if cpu_ok else '✖'}"
    ram_gb = round(psutil.virtual_memory().total / (1024**3))
    ram_ok = ram_gb >= 4
    results["RAM"] = f"{ram_gb} GB - {'✔' if ram_ok else '✖'}"
    try:
        disk = psutil.disk_usage("C:\\")
        disk_gb = disk.total // (1024**3)
        storage_ok = disk_gb >= 64
        results["Storage"] = f"{disk_gb} GB - {'✔' if storage_ok else '✖'}"
    except:
        results["Storage"] = "Unknown - ✖"
    results["TPM 2.0"] = check_tpm()
    results["Secure Boot"] = check_secure_boot()
    return results

# ===============================
# Get system information
# ===============================
def get_system_info():
    info = {}
    info["Computer Name"] = socket.gethostname()
    info["User"] = platform.node()
    info["OS"] = platform.system() + " " + platform.release()
    info["OS Version"] = platform.version()
    info["Architecture"] = "64-bit" if platform.machine().endswith('64') else "32-bit"
    info["CPU"] = platform.processor()
    info["CPU Cores"] = psutil.cpu_count(logical=False)
    info["CPU Threads"] = psutil.cpu_count(logical=True)
    ram = psutil.virtual_memory()
    info["Total RAM"] = f"{round(ram.total / (1024**3),2)} GB"
    info["Motherboard Manufacturer"] = run_wmic("wmic baseboard get manufacturer")
    info["Motherboard Model"] = run_wmic("wmic baseboard get product")
    info["Motherboard Version"] = run_wmic("wmic baseboard get version")
    info["BIOS Version"] = run_wmic("wmic bios get smbiosbiosversion")

    # Multiple GPUs
    try:
        gpu = subprocess.check_output("wmic path win32_VideoController get name", shell=True).decode().split("\n")[1:]
        gpu_names = [g.strip() for g in gpu if g.strip()]
        info["GPU(s)"] = ", ".join(gpu_names)
    except:
        info["GPU(s)"] = "Unavailable"

    # Disks
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            free = round(usage.free / (1024**3), 2)
            disks.append(f"{part.device} : {round(usage.total / (1024**3))} GB total, {free} GB free")
        except:
            pass
    info["Disks"] = ", ".join(disks)

    # Multiple network adapters
    adapters = []
    for nic, addrs in psutil.net_if_addrs().items():
        ip_list = [a.address for a in addrs if a.family.name == 'AF_INET']
        mac_list = [a.address for a in addrs if a.family.name == 'AF_LINK']
        ip_str = ", ".join(ip_list) if ip_list else "N/A"
        mac_str = ", ".join(mac_list) if mac_list else "N/A"
        adapters.append(f"{nic} - IP: {ip_str}, MAC: {mac_str}")
    info["Network Adapters"] = "\n".join(adapters)

    boot = datetime.fromtimestamp(psutil.boot_time())
    info["System Boot Time"] = boot.strftime("%Y-%m-%d %H:%M:%S")
    return info

# ===============================
# Save to file
# ===============================
def save_to_file(info, win11_checks):
    script_folder = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(script_folder, "output")
    os.makedirs(output_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_FILE = os.path.join(output_folder, f"system_inventory_{timestamp}.txt")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("SYSTEM INVENTORY REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("=== Windows 11 Technical Requirements ===\n")
        for k, v in win11_checks.items():
            f.write(f"{k}: {v}\n")
        f.write("\n=== System Information ===\n")
        for key, value in info.items():
            f.write(f"{key}: {value}\n")
    print(f"System info saved to {OUTPUT_FILE}")

# ===============================
# Main
# ===============================
if __name__ == "__main__":
    win11_checks = check_win11_requirements()
    system_info = get_system_info()
    save_to_file(system_info, win11_checks)