import platform
import socket
import psutil
import subprocess
from datetime import datetime
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# ===============================
# Helper
# ===============================
def run_wmic(command):
    try:
        output = subprocess.check_output(command, shell=True).decode().split("\n")[1].strip()
        return output
    except:
        return "Unavailable"

# ===============================
# TPM Check
# ===============================
def check_tpm():
    try:
        output = subprocess.check_output(
            'powershell -Command "Get-Tpm | Select-Object TpmPresent,TpmReady,TpmVersion"',
            shell=True
        ).decode()

        lines = [l for l in output.split("\n") if l.strip()]
        if len(lines) >= 2:
            values = lines[1].split()
            present = values[0]
            ready = values[1]
            version = values[2] if len(values) > 2 else "N/A"

            if present.lower() == "true" and "2.0" in version:
                return f"{version} ✔"
            else:
                return f"{version} ✖"

    except:
        pass

    return "Unavailable ✖"

# ===============================
# Secure Boot
# ===============================
def check_secure_boot():
    try:
        sb = subprocess.check_output(
            'powershell -Command "Confirm-SecureBootUEFI"',
            shell=True,
            stderr=subprocess.DEVNULL
        ).decode().strip()

        if sb.lower() == "true":
            return "Enabled ✔"
        else:
            return "Disabled ✖"

    except:
        return "Unavailable ✖"

# ===============================
# Windows 11 Requirements
# ===============================
def check_win11_requirements():
    results = {}
    cores = psutil.cpu_count(logical=False)
    arch = platform.machine()
    results["CPU"] = f"{cores} cores ({arch})"
    ram = round(psutil.virtual_memory().total / (1024**3))
    results["RAM"] = f"{ram} GB"
    disk = psutil.disk_usage("C:\\")
    disk_gb = disk.total // (1024**3)
    results["Storage"] = f"{disk_gb} GB"
    results["TPM 2.0"] = check_tpm()
    results["Secure Boot"] = check_secure_boot()
    return results

# ===============================
# System Information
# ===============================
def get_system_info():
    info = {}
    boot = datetime.fromtimestamp(psutil.boot_time())
    info["OS & Uptime"] = {
        "Computer Name": socket.gethostname(),
        "OS": platform.system(),
        "Version": platform.version(),
        "Architecture": platform.machine(),
        "Boot Time": boot.strftime("%Y-%m-%d %H:%M:%S")
    }
    info["CPU"] = {
        "Processor": platform.processor(),
        "Cores": psutil.cpu_count(logical=False),
        "Threads": psutil.cpu_count(logical=True)
    }
    ram = psutil.virtual_memory()
    info["Memory"] = {"Total RAM": f"{round(ram.total/(1024**3),2)} GB"}
    info["Motherboard"] = {
        "Manufacturer": run_wmic("wmic baseboard get manufacturer"),
        "Model": run_wmic("wmic baseboard get product"),
        "Version": run_wmic("wmic baseboard get version")
    }
    info["BIOS"] = {"BIOS Version": run_wmic("wmic bios get smbiosbiosversion")}
    # GPU
    try:
        gpu = subprocess.check_output(
            "wmic path win32_VideoController get name",
            shell=True
        ).decode().split("\n")[1:]
        gpu_names = [g.strip() for g in gpu if g.strip()]
        info["GPU"] = {"Devices": ", ".join(gpu_names)}
    except:
        info["GPU"] = {"Devices": "Unavailable"}
    # Storage
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append(f"{part.device} {round(usage.total/(1024**3))}GB (Free {round(usage.free/(1024**3))}GB)")
        except:
            pass
    info["Storage"] = {"Disks": ", ".join(disks)}
    # Network
    adapters = []
    for nic, addrs in psutil.net_if_addrs().items():
        ip = "N/A"
        mac = "N/A"
        for addr in addrs:
            if addr.family.name == "AF_INET":
                ip = addr.address
            if addr.family.name == "AF_LINK":
                mac = addr.address
        adapters.append(f"{nic}  IP:{ip}  MAC:{mac}")
    info["Network"] = {"Adapters": " | ".join(adapters)}
    return info

# ===============================
# Save Reports
# ===============================
def save_report(path, format_type):
    win11 = check_win11_requirements()
    sysinfo = get_system_info()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data = []
    for section, items in sysinfo.items():
        for k, v in items.items():
            data.append([section, k, v])
    for k, v in win11.items():
        data.append(["Windows11 Requirements", k, v])
    df = pd.DataFrame(data, columns=["Section","Item","Value"])
    filename = os.path.join(path, f"system_report_{timestamp}")
    if format_type == "TXT":
        with open(filename+".txt","w",encoding="utf-8") as f:
            f.write("SYSTEM REPORT\n\n")
            for row in data:
                f.write(f"{row[0]} | {row[1]} : {row[2]}\n")
    elif format_type == "CSV":
        df.to_csv(filename+".csv", index=False)
    elif format_type == "Excel":
        # Old Excel format (.xls)
        df.to_excel(filename+".xls", index=False, engine='xlwt')
    messagebox.showinfo("Complete","Report Generated")

# ===============================
# GUI
# ===============================
def browse_folder():
    folder = filedialog.askdirectory()
    path_var.set(folder)

def run_scan():
    path = path_var.get()
    format_type = format_var.get()
    if not path:
        messagebox.showerror("Error","Please choose an output folder")
        return
    save_report(path, format_type)

root = tk.Tk()
root.title("RD3 System Scanner")
root.geometry("450x240")
path_var = tk.StringVar()
format_var = tk.StringVar(value="TXT")
tk.Label(root,text="Output Folder").pack(pady=5)
frame = tk.Frame(root)
frame.pack()
tk.Entry(frame,textvariable=path_var,width=35).pack(side="left")
tk.Button(frame,text="Browse",command=browse_folder).pack(side="left")
tk.Label(root,text="Output Format").pack(pady=10)
ttk.Combobox(
    root,
    textvariable=format_var,
    values=["TXT","CSV","Excel"],
    state="readonly"
).pack()
tk.Button(
    root,
    text="Run System Scan",
    command=run_scan,
    height=2,
    width=25
).pack(pady=20)
root.mainloop()