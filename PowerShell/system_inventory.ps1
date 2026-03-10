# Output file
$OutputFile = "C:\Temp\system_inventory.txt"

# Ensure folder exists
$folder = Split-Path $OutputFile
if (-not (Test-Path $folder)) {
    New-Item -ItemType Directory -Path $folder | Out-Null
}

# Start building report
$report = @()
$report += "SYSTEM INVENTORY REPORT"
$report += "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$report += ""

# Computer info
$report += "Computer Name: $env:COMPUTERNAME"
$report += "User: $env:USERNAME"
$report += "OS: $(Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Caption)"
$report += "OS Version: $(Get-CimInstance Win32_OperatingSystem | Select-Object -ExpandProperty Version)"
$report += "Architecture: $([Environment]::Is64BitOperatingSystem -as [string])"

# CPU
$cpu = Get-CimInstance Win32_Processor
$report += "CPU: $($cpu.Name)"
$report += "CPU Cores: $($cpu.NumberOfCores)"
$report += "CPU Threads: $($cpu.NumberOfLogicalProcessors)"

# RAM
$ram = Get-CimInstance Win32_PhysicalMemory
$ramTotal = [Math]::Round(($ram.Capacity | Measure-Object -Sum).Sum / 1GB,2)
$ramSlots = $ram.Count
$report += "Total RAM: $ramTotal GB"
$report += "RAM Slots Used: $ramSlots"

# Motherboard
$board = Get-CimInstance Win32_BaseBoard
$report += "Motherboard Manufacturer: $($board.Manufacturer)"
$report += "Motherboard Model: $($board.Product)"
$report += "Motherboard Version: $($board.Version)"

# BIOS
$bios = Get-CimInstance Win32_BIOS
$report += "BIOS Version: $($bios.SMBIOSBIOSVersion)"

# GPU
$gpu = Get-CimInstance Win32_VideoController
$gpuNames = $gpu | ForEach-Object { $_.Name }
$report += "GPU: $($gpuNames -join ', ')"

# Disks
$disks = Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3"
$diskInfo = $disks | ForEach-Object { "$($_.DeviceID) : $([Math]::Round($_.Size/1GB)) GB" }
$report += "Disks: $($diskInfo -join ', ')"

# Network
$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "Loopback*"} | Select-Object -First 1 -ExpandProperty IPAddress)
$mac = (Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object -First 1 -ExpandProperty MacAddress)
$report += "IP Address: $ip"
$report += "MAC Address: $mac"

# Uptime
$bootTime = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
$report += "System Boot Time: $bootTime"

# Save to file
$report | Out-File -FilePath $OutputFile -Encoding UTF8

Write-Host "System info saved to $OutputFile"