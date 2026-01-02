# Setup script for Local Server 1
# Configures Docker, WSL2, and launches the ingestion pipeline

Write-Host "=== Legal Ingest - Server 1 Setup ===" -ForegroundColor Green

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator" -ForegroundColor Red
    exit 1
}

# Check Docker installation
Write-Host "`nChecking Docker installation..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>$null
if (-not $dockerVersion) {
    Write-Host "Docker not found. Installing Docker Desktop..." -ForegroundColor Yellow
    
    # Download Docker Desktop
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
    
    Write-Host "Downloading Docker Desktop..."
    Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerInstaller
    
    # Install Docker Desktop
    Write-Host "Installing Docker Desktop (this may take several minutes)..."
    Start-Process -FilePath $dockerInstaller -ArgumentList "install", "--quiet" -Wait
    
    Write-Host "Docker Desktop installed. Please restart your computer and run this script again." -ForegroundColor Green
    exit 0
} else {
    Write-Host "Docker found: $dockerVersion" -ForegroundColor Green
}

# Check WSL2
Write-Host "`nChecking WSL2..." -ForegroundColor Yellow
$wslVersion = wsl --status 2>$null
if (-not $wslVersion) {
    Write-Host "Installing WSL2..." -ForegroundColor Yellow
    wsl --install
    Write-Host "WSL2 installed. Please restart your computer and run this script again." -ForegroundColor Green
    exit 0
} else {
    Write-Host "WSL2 is configured" -ForegroundColor Green
}

# Create data directories
Write-Host "`nCreating data directories..." -ForegroundColor Yellow
$dataRoot = "D:\legal-ingest"
$directories = @(
    "$dataRoot\opensearch-data",
    "$dataRoot\milvus-data",
    "$dataRoot\etcd",
    "$dataRoot\milvus-minio",
    "$dataRoot\raw-data",
    "$dataRoot\logs"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Green
    } else {
        Write-Host "Exists: $dir" -ForegroundColor Gray
    }
}

# Set permissions
Write-Host "`nSetting directory permissions..." -ForegroundColor Yellow
foreach ($dir in $directories) {
    $acl = Get-Acl $dir
    $permission = "Everyone", "FullControl", "ContainerInherit,ObjectInherit", "None", "Allow"
    $accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
    $acl.SetAccessRule($accessRule)
    Set-Acl $dir $acl
}

# Configure firewall
Write-Host "`nConfiguring Windows Firewall..." -ForegroundColor Yellow
$firewallRules = @(
    @{Name="Legal-OpenSearch"; Port=9200; Protocol="TCP"},
    @{Name="Legal-Milvus"; Port=19530; Protocol="TCP"},
    @{Name="Legal-Prometheus"; Port=9090; Protocol="TCP"}
)

foreach ($rule in $firewallRules) {
    $existingRule = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue
    if (-not $existingRule) {
        New-NetFirewallRule -DisplayName $rule.Name -Direction Inbound -Protocol $rule.Protocol -LocalPort $rule.Port -Action Allow | Out-Null
        Write-Host "Created firewall rule: $($rule.Name)" -ForegroundColor Green
    } else {
        Write-Host "Firewall rule exists: $($rule.Name)" -ForegroundColor Gray
    }
}

# Copy environment file if not exists
Write-Host "`nConfiguring environment..." -ForegroundColor Yellow
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$moduleRoot = Split-Path -Parent $scriptDir

if (-not (Test-Path "$moduleRoot\.env")) {
    Copy-Item "$moduleRoot\.env.example" "$moduleRoot\.env"
    Write-Host "Created .env file. Please edit it with your configuration." -ForegroundColor Yellow
    Write-Host "Path: $moduleRoot\.env" -ForegroundColor Cyan
} else {
    Write-Host ".env file already exists" -ForegroundColor Green
}

# Build Docker images
Write-Host "`nBuilding Docker images..." -ForegroundColor Yellow
Set-Location $moduleRoot
docker-compose -f docker-compose-local-server1.yml build

# Start services
Write-Host "`nStarting services..." -ForegroundColor Yellow
docker-compose -f docker-compose-local-server1.yml up -d

# Wait for services to be healthy
Write-Host "`nWaiting for services to start (this may take a few minutes)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check service status
Write-Host "`nChecking service status..." -ForegroundColor Yellow
docker-compose -f docker-compose-local-server1.yml ps

# Display access information
Write-Host "`n=== Server 1 Setup Complete ===" -ForegroundColor Green
Write-Host "`nServices running:" -ForegroundColor Cyan
Write-Host "  OpenSearch: http://localhost:9200" -ForegroundColor White
Write-Host "  Milvus: localhost:19530" -ForegroundColor White
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "`nData directory: $dataRoot" -ForegroundColor Cyan
Write-Host "`nTo view logs:" -ForegroundColor Cyan
Write-Host "  docker-compose -f docker-compose-local-server1.yml logs -f" -ForegroundColor White
Write-Host "`nTo stop services:" -ForegroundColor Cyan
Write-Host "  docker-compose -f docker-compose-local-server1.yml down" -ForegroundColor White

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Verify services are running correctly" -ForegroundColor White
Write-Host "  2. Check logs for any errors" -ForegroundColor White
Write-Host "  3. Run setup-server2.ps1 on the second server" -ForegroundColor White
Write-Host "  4. Configure tunnel with tunnel-setup.ps1" -ForegroundColor White
