# Setup script for Local Server 2
# Configures Docker, WSL2, and launches Postgres, MinIO, and Airflow

Write-Host "=== Legal Ingest - Server 2 Setup ===" -ForegroundColor Green

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
    
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
    $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
    
    Write-Host "Downloading Docker Desktop..."
    Invoke-WebRequest -Uri $dockerUrl -OutFile $dockerInstaller
    
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
$dataRoot = "E:\legal-ingest"
$directories = @(
    "$dataRoot\postgres-data",
    "$dataRoot\minio-data",
    "$dataRoot\redis-data",
    "$dataRoot\snapshots",
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
    @{Name="Legal-Postgres"; Port=5432; Protocol="TCP"},
    @{Name="Legal-MinIO-API"; Port=9000; Protocol="TCP"},
    @{Name="Legal-MinIO-Console"; Port=9001; Protocol="TCP"},
    @{Name="Legal-Airflow"; Port=8080; Protocol="TCP"},
    @{Name="Legal-Redis"; Port=6379; Protocol="TCP"}
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

# Create Docker network (shared between server 1 and 2)
Write-Host "`nCreating Docker network..." -ForegroundColor Yellow
$networkExists = docker network ls --filter name=legal-network --format "{{.Name}}" 2>$null
if (-not $networkExists) {
    docker network create legal-network
    Write-Host "Created Docker network: legal-network" -ForegroundColor Green
} else {
    Write-Host "Docker network already exists: legal-network" -ForegroundColor Gray
}

# Create Airflow directories
Write-Host "`nCreating Airflow directories..." -ForegroundColor Yellow
$airflowDirs = @(
    "$moduleRoot\airflow\dags",
    "$moduleRoot\airflow\logs",
    "$moduleRoot\airflow\plugins"
)

foreach ($dir in $airflowDirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created: $dir" -ForegroundColor Green
    }
}

# Build Docker images
Write-Host "`nBuilding Docker images..." -ForegroundColor Yellow
Set-Location $moduleRoot
docker-compose -f docker-compose-local-server2.yml build

# Start services
Write-Host "`nStarting services..." -ForegroundColor Yellow
docker-compose -f docker-compose-local-server2.yml up -d

# Wait for services to be healthy
Write-Host "`nWaiting for services to start (this may take a few minutes)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Initialize MinIO buckets
Write-Host "`nInitializing MinIO buckets..." -ForegroundColor Yellow
# This would use mc (MinIO Client) to create buckets, skipping for MVP

# Check service status
Write-Host "`nChecking service status..." -ForegroundColor Yellow
docker-compose -f docker-compose-local-server2.yml ps

# Display access information
Write-Host "`n=== Server 2 Setup Complete ===" -ForegroundColor Green
Write-Host "`nServices running:" -ForegroundColor Cyan
Write-Host "  Postgres: localhost:5432" -ForegroundColor White
Write-Host "  MinIO API: http://localhost:9000" -ForegroundColor White
Write-Host "  MinIO Console: http://localhost:9001" -ForegroundColor White
Write-Host "  Airflow: http://localhost:8080 (admin/admin)" -ForegroundColor White
Write-Host "  Redis: localhost:6379" -ForegroundColor White
Write-Host "`nData directory: $dataRoot" -ForegroundColor Cyan
Write-Host "`nTo view logs:" -ForegroundColor Cyan
Write-Host "  docker-compose -f docker-compose-local-server2.yml logs -f" -ForegroundColor White
Write-Host "`nTo stop services:" -ForegroundColor Cyan
Write-Host "  docker-compose -f docker-compose-local-server2.yml down" -ForegroundColor White

Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  1. Verify services are running correctly" -ForegroundColor White
Write-Host "  2. Access Airflow UI and configure DAGs" -ForegroundColor White
Write-Host "  3. Configure tunnel with tunnel-setup.ps1" -ForegroundColor White
Write-Host "  4. Setup backup with backup-daily.ps1" -ForegroundColor White
