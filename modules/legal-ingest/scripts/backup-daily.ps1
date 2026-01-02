# Daily Backup Script for Legal Ingest Data
# Performs incremental backups with 7-day retention

Write-Host "=== Legal Ingest - Daily Backup ===" -ForegroundColor Green

# Configuration
$backupRoot = "F:\legal-ingest-backups"  # Change to your backup location
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$backupDir = "$backupRoot\$timestamp"
$retentionDays = 7

# Data directories to backup
$dataServer1 = "D:\legal-ingest"
$dataServer2 = "E:\legal-ingest"

# Create backup directory
Write-Host "`nCreating backup directory: $backupDir" -ForegroundColor Yellow
New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

# Backup Server 1 data
if (Test-Path $dataServer1) {
    Write-Host "`nBacking up Server 1 data..." -ForegroundColor Yellow
    $server1Backup = "$backupDir\server1"
    
    # Use robocopy for incremental backup
    robocopy $dataServer1 $server1Backup /MIR /MT:8 /R:3 /W:5 /LOG:"$backupDir\server1_backup.log" /TEE
    
    if ($LASTEXITCODE -le 7) {
        Write-Host "Server 1 backup completed successfully" -ForegroundColor Green
    } else {
        Write-Host "Server 1 backup completed with errors (code: $LASTEXITCODE)" -ForegroundColor Yellow
    }
} else {
    Write-Host "Server 1 data directory not found: $dataServer1" -ForegroundColor Red
}

# Backup Server 2 data
if (Test-Path $dataServer2) {
    Write-Host "`nBacking up Server 2 data..." -ForegroundColor Yellow
    $server2Backup = "$backupDir\server2"
    
    robocopy $dataServer2 $server2Backup /MIR /MT:8 /R:3 /W:5 /LOG:"$backupDir\server2_backup.log" /TEE
    
    if ($LASTEXITCODE -le 7) {
        Write-Host "Server 2 backup completed successfully" -ForegroundColor Green
    } else {
        Write-Host "Server 2 backup completed with errors (code: $LASTEXITCODE)" -ForegroundColor Yellow
    }
} else {
    Write-Host "Server 2 data directory not found: $dataServer2" -ForegroundColor Red
}

# Backup Postgres databases
Write-Host "`nBacking up Postgres databases..." -ForegroundColor Yellow
$pgDumpPath = "docker"  # Assumes docker is in PATH

# Find Postgres container
$postgresContainer = docker ps --filter "name=legal_postgres" --format "{{.Names}}" 2>$null

if ($postgresContainer) {
    Write-Host "Found Postgres container: $postgresContainer" -ForegroundColor Green
    
    # Dump database
    $dbDumpFile = "$backupDir\postgres_legal_data.sql"
    docker exec $postgresContainer pg_dump -U legal_ingest legal_data > $dbDumpFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Database dump completed: $dbDumpFile" -ForegroundColor Green
        
        # Compress dump
        Write-Host "Compressing database dump..." -ForegroundColor Yellow
        Compress-Archive -Path $dbDumpFile -DestinationPath "$dbDumpFile.zip"
        Remove-Item $dbDumpFile
        Write-Host "Database dump compressed" -ForegroundColor Green
    } else {
        Write-Host "Database dump failed" -ForegroundColor Red
    }
} else {
    Write-Host "Postgres container not found, skipping database backup" -ForegroundColor Yellow
}

# Backup MinIO data (optional - usually backed up via robocopy above)
Write-Host "`nMinIO data backed up as part of Server 2 data" -ForegroundColor Gray

# Clean up old backups
Write-Host "`nCleaning up backups older than $retentionDays days..." -ForegroundColor Yellow
$cutoffDate = (Get-Date).AddDays(-$retentionDays)
$oldBackups = Get-ChildItem -Path $backupRoot -Directory | Where-Object { $_.CreationTime -lt $cutoffDate }

if ($oldBackups) {
    foreach ($oldBackup in $oldBackups) {
        Write-Host "Removing old backup: $($oldBackup.Name)" -ForegroundColor Gray
        Remove-Item -Path $oldBackup.FullName -Recurse -Force
    }
    Write-Host "Removed $($oldBackups.Count) old backup(s)" -ForegroundColor Green
} else {
    Write-Host "No old backups to remove" -ForegroundColor Gray
}

# Calculate backup size
Write-Host "`nCalculating backup size..." -ForegroundColor Yellow
$backupSize = (Get-ChildItem -Path $backupDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
Write-Host "Backup size: $($backupSize.ToString('N2')) GB" -ForegroundColor Cyan

# Create backup summary
$summary = @{
    Timestamp = $timestamp
    BackupLocation = $backupDir
    SizeGB = $backupSize
    RetentionDays = $retentionDays
    Server1Backed = (Test-Path $dataServer1)
    Server2Backed = (Test-Path $dataServer2)
    DatabaseBacked = ($postgresContainer -ne $null)
}

$summaryFile = "$backupDir\backup_summary.json"
$summary | ConvertTo-Json | Set-Content -Path $summaryFile
Write-Host "Backup summary saved: $summaryFile" -ForegroundColor Green

# Display results
Write-Host "`n=== Backup Complete ===" -ForegroundColor Green
Write-Host "`nBackup location: $backupDir" -ForegroundColor Cyan
Write-Host "Size: $($backupSize.ToString('N2')) GB" -ForegroundColor Cyan
Write-Host "Retention: $retentionDays days" -ForegroundColor Cyan

# Send notification (optional)
# TODO: Implement email or webhook notification

Write-Host "`nBackup completed successfully!" -ForegroundColor Green
