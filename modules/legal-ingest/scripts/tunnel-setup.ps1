# VPN/SSH Tunnel Setup for PlanetHoster <-> Local Servers
# Configures secure tunnel between cloud and local infrastructure

Write-Host "=== Legal Ingest - Tunnel Setup ===" -ForegroundColor Green

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    exit 1
}

# Configuration
$tunnelType = Read-Host "Select tunnel type (1=WireGuard, 2=SSH): "
$remoteHost = Read-Host "Enter PlanetHoster server hostname/IP"
$remotePort = Read-Host "Enter remote SSH port (default 22)"
if ([string]::IsNullOrWhiteSpace($remotePort)) { $remotePort = "22" }

Write-Host "`nConfiguring $tunnelType tunnel to $remoteHost..." -ForegroundColor Yellow

if ($tunnelType -eq "1") {
    # WireGuard setup
    Write-Host "`n=== WireGuard Configuration ===" -ForegroundColor Cyan
    
    # Check if WireGuard is installed
    $wireguardPath = "C:\Program Files\WireGuard\wireguard.exe"
    if (-not (Test-Path $wireguardPath)) {
        Write-Host "WireGuard not found. Please install from: https://www.wireguard.com/install/" -ForegroundColor Yellow
        Write-Host "After installation, run this script again." -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "WireGuard is installed" -ForegroundColor Green
    
    # Generate keys
    Write-Host "`nGenerating WireGuard keys..." -ForegroundColor Yellow
    $configDir = "$env:ProgramFiles\WireGuard\Configs"
    if (-not (Test-Path $configDir)) {
        New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    }
    
    # Generate private key
    $privateKey = & wg genkey
    $publicKey = $privateKey | & wg pubkey
    
    Write-Host "Private key generated (keep secret!)" -ForegroundColor Green
    Write-Host "Public key: $publicKey" -ForegroundColor Cyan
    
    # Create WireGuard config
    $configPath = "$configDir\legal-ingest.conf"
    $wgConfig = @"
[Interface]
PrivateKey = $privateKey
Address = 10.0.0.2/24
ListenPort = 51820

[Peer]
PublicKey = <REPLACE_WITH_SERVER_PUBLIC_KEY>
Endpoint = ${remoteHost}:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
"@
    
    Set-Content -Path $configPath -Value $wgConfig
    Write-Host "`nWireGuard config created: $configPath" -ForegroundColor Green
    Write-Host "Please replace <REPLACE_WITH_SERVER_PUBLIC_KEY> with the server's public key" -ForegroundColor Yellow
    
    # Configure firewall
    Write-Host "`nConfiguring firewall for WireGuard..." -ForegroundColor Yellow
    $existingRule = Get-NetFirewallRule -DisplayName "Legal-WireGuard" -ErrorAction SilentlyContinue
    if (-not $existingRule) {
        New-NetFirewallRule -DisplayName "Legal-WireGuard" -Direction Inbound -Protocol UDP -LocalPort 51820 -Action Allow | Out-Null
        Write-Host "Firewall rule created" -ForegroundColor Green
    }
    
    Write-Host "`nTo activate the tunnel:" -ForegroundColor Cyan
    Write-Host "  1. Edit $configPath and add server's public key" -ForegroundColor White
    Write-Host "  2. Open WireGuard GUI" -ForegroundColor White
    Write-Host "  3. Import tunnel configuration from $configPath" -ForegroundColor White
    Write-Host "  4. Activate the tunnel" -ForegroundColor White
    
} elseif ($tunnelType -eq "2") {
    # SSH tunnel setup
    Write-Host "`n=== SSH Tunnel Configuration ===" -ForegroundColor Cyan
    
    # Check if OpenSSH is installed
    $sshPath = "C:\Windows\System32\OpenSSH\ssh.exe"
    if (-not (Test-Path $sshPath)) {
        Write-Host "Installing OpenSSH..." -ForegroundColor Yellow
        Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
        Write-Host "OpenSSH installed" -ForegroundColor Green
    } else {
        Write-Host "OpenSSH is installed" -ForegroundColor Green
    }
    
    # Generate SSH key if needed
    $sshKeyPath = "$env:USERPROFILE\.ssh\legal_ingest_rsa"
    if (-not (Test-Path $sshKeyPath)) {
        Write-Host "`nGenerating SSH key..." -ForegroundColor Yellow
        ssh-keygen -t rsa -b 4096 -f $sshKeyPath -N '""' -C "legal-ingest-tunnel"
        Write-Host "SSH key generated: $sshKeyPath" -ForegroundColor Green
        Write-Host "Public key:" -ForegroundColor Cyan
        Get-Content "$sshKeyPath.pub"
        Write-Host "`nCopy the public key above and add it to ~/.ssh/authorized_keys on the server" -ForegroundColor Yellow
    }
    
    # Create tunnel script
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $tunnelScript = "$scriptDir\start-ssh-tunnel.ps1"
    
    $tunnelScriptContent = @"
# SSH Tunnel Startup Script
# Establishes reverse SSH tunnel from local servers to PlanetHoster

`$remoteHost = "$remoteHost"
`$remotePort = $remotePort
`$sshKey = "$sshKeyPath"

Write-Host "Starting SSH tunnel to `$remoteHost..." -ForegroundColor Yellow

# Tunnel configuration:
# - Forward local Postgres (5432) to remote 15432
# - Forward local OpenSearch (9200) to remote 19200
# - Forward local Milvus (19530) to remote 29530

`$tunnelArgs = @(
    "-i", `$sshKey,
    "-N",
    "-R", "15432:localhost:5432",
    "-R", "19200:localhost:9200",
    "-R", "29530:localhost:19530",
    "-o", "ServerAliveInterval=60",
    "-o", "ServerAliveCountMax=3",
    "-p", `$remotePort,
    "root@`$remoteHost"
)

Write-Host "Tunnel ports:" -ForegroundColor Cyan
Write-Host "  Local Postgres:5432 -> Remote:15432" -ForegroundColor White
Write-Host "  Local OpenSearch:9200 -> Remote:19200" -ForegroundColor White
Write-Host "  Local Milvus:19530 -> Remote:29530" -ForegroundColor White

Write-Host "`nStarting tunnel (press Ctrl+C to stop)..." -ForegroundColor Yellow
& ssh `$tunnelArgs
"@
    
    Set-Content -Path $tunnelScript -Value $tunnelScriptContent
    Write-Host "`nTunnel script created: $tunnelScript" -ForegroundColor Green
    
    # Create Windows service wrapper
    Write-Host "`nCreating Windows service for tunnel..." -ForegroundColor Yellow
    $serviceName = "LegalIngestTunnel"
    
    # Check if service exists
    $service = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
    if (-not $service) {
        # Create scheduled task (alternative to service)
        $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$tunnelScript`""
        $trigger = New-ScheduledTaskTrigger -AtStartup
        $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
        
        Register-ScheduledTask -TaskName "Legal Ingest SSH Tunnel" -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force
        Write-Host "Scheduled task created: Legal Ingest SSH Tunnel" -ForegroundColor Green
    }
    
    Write-Host "`nTo start the tunnel:" -ForegroundColor Cyan
    Write-Host "  1. Ensure SSH key is added to server's authorized_keys" -ForegroundColor White
    Write-Host "  2. Run: $tunnelScript" -ForegroundColor White
    Write-Host "  OR" -ForegroundColor White
    Write-Host "  3. Start scheduled task 'Legal Ingest SSH Tunnel'" -ForegroundColor White
    
} else {
    Write-Host "Invalid selection" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Tunnel Setup Complete ===" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Configure the server side of the tunnel" -ForegroundColor White
Write-Host "  2. Test connectivity from both sides" -ForegroundColor White
Write-Host "  3. Update .env files with tunnel endpoints" -ForegroundColor White
Write-Host "  4. Test data synchronization" -ForegroundColor White
