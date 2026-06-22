param(
    [string]$AdapterName = ""
)

$ErrorActionPreference = "Stop"

$principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw "Administrator privileges are required. Re-run PowerShell as Administrator."
}

function Set-AdapterPropertyIfPresent {
    param(
        [string]$Name,
        [string]$RegistryKeyword,
        [int]$RegistryValue
    )
    $prop = Get-NetAdapterAdvancedProperty -Name $Name -RegistryKeyword $RegistryKeyword -ErrorAction SilentlyContinue
    if ($null -eq $prop) {
        Write-Host "[SKIP] missing property $RegistryKeyword"
        return
    }
    Set-NetAdapterAdvancedProperty -Name $Name -RegistryKeyword $RegistryKeyword -RegistryValue $RegistryValue
    Write-Host "[OK] $RegistryKeyword=$RegistryValue"
}

if ($AdapterName.Trim() -eq "") {
    $adapter = Get-NetAdapter | Where-Object { $_.InterfaceDescription -like "*Realtek*GbE*" -and $_.Status -ne "Disabled" } | Select-Object -First 1
    if ($null -eq $adapter) {
        $adapter = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Select-Object -First 1
    }
    if ($null -eq $adapter) {
        throw "No active network adapter found."
    }
    $AdapterName = $adapter.Name
}

Set-AdapterPropertyIfPresent -Name $AdapterName -RegistryKeyword "*WakeOnMagicPacket" -RegistryValue 1
Set-AdapterPropertyIfPresent -Name $AdapterName -RegistryKeyword "S5WakeOnLan" -RegistryValue 1
Set-AdapterPropertyIfPresent -Name $AdapterName -RegistryKeyword "*WakeOnPattern" -RegistryValue 0
Set-AdapterPropertyIfPresent -Name $AdapterName -RegistryKeyword "*EEE" -RegistryValue 0
Set-AdapterPropertyIfPresent -Name $AdapterName -RegistryKeyword "AdvancedEEE" -RegistryValue 0
Set-AdapterPropertyIfPresent -Name $AdapterName -RegistryKeyword "EnableGreenEthernet" -RegistryValue 0
Set-AdapterPropertyIfPresent -Name $AdapterName -RegistryKeyword "WolShutdownLinkSpeed" -RegistryValue 2

powercfg /deviceenablewake "Realtek PCIe GbE Family Controller" | Out-Null

Write-Host "[VERIFY] wake_armed"
powercfg /devicequery wake_armed

Write-Host "[VERIFY] WoL advanced properties"
Get-NetAdapterAdvancedProperty -Name $AdapterName |
    Where-Object { $_.RegistryKeyword -match "Wake|WOL|Magic|Shutdown|EEE|Green" } |
    Select-Object Name, DisplayName, DisplayValue, RegistryKeyword |
    Format-Table -AutoSize
