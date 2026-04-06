param(
    [ValidateSet("up", "down", "status", "logs", "reset")]
    [string]$Action = "status"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ComposeFile = Join-Path $ProjectRoot "docker-compose.local-postgres.yml"
$ComposeArgs = @("-f", $ComposeFile)
$ContainerName = "mdams-local-postgres"
$VolumeName = "mdams-local-postgres-data"
$PostgresPassword = "meam_secret"
$TestDbName = "meam_db_test"
$PsqlBase = @("exec", "-e", "PGPASSWORD=$PostgresPassword", $ContainerName, "psql", "-U", "postgres", "-d", "postgres", "-v", "ON_ERROR_STOP=1")

function Invoke-Compose {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & docker compose @ComposeArgs @Arguments
}

function Wait-PostgresReady {
    $attempt = 0
    while ($attempt -lt 30) {
        try {
            $output = & docker exec -e "PGPASSWORD=$PostgresPassword" $ContainerName pg_isready -U meam -d meam_db 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host $output
                return
            }
        } catch {
        }

        Start-Sleep -Seconds 2
        $attempt += 1
    }

    throw "PostgreSQL did not become ready in time."
}

function Get-ContainerState {
    $state = & docker ps -a --filter "name=^/$ContainerName$" --format "{{.State}}"
    return ($state | Out-String).Trim()
}

function Ensure-TestDatabase {
    $exists = & docker @PsqlBase "-tAc" "SELECT 1 FROM pg_database WHERE datname='$TestDbName'"
    if (($exists | Out-String).Trim() -ne "1") {
        & docker @PsqlBase "-c" "CREATE DATABASE $TestDbName OWNER meam;"
    }
}

switch ($Action) {
    "up" {
        $state = Get-ContainerState
        if (-not $state) {
            Invoke-Compose up -d
        } elseif ($state -ne "running") {
            & docker start $ContainerName | Out-Null
        }
        Wait-PostgresReady
        & docker @PsqlBase "-c" "ALTER ROLE meam WITH LOGIN CREATEDB PASSWORD '$PostgresPassword';"
        Ensure-TestDatabase
        Write-Host "Local PostgreSQL is ready on localhost:5432"
        Write-Host "Business DB: meam_db"
        Write-Host "Test DB: $TestDbName"
    }
    "down" {
        $state = Get-ContainerState
        if ($state) {
            & docker stop $ContainerName
        }
    }
    "status" {
        & docker ps -a --filter "name=^/$ContainerName$" --format "table {{.Names}}`t{{.Status}}`t{{.Ports}}"
    }
    "logs" {
        $state = Get-ContainerState
        if ($state) {
            & docker logs --tail 100 $ContainerName
        }
    }
    "reset" {
        $state = Get-ContainerState
        if ($state) {
            & docker rm -f $ContainerName
        }
        $volumeExists = (& docker volume ls --filter "name=^$VolumeName$" --format "{{.Name}}" | Out-String).Trim()
        if ($volumeExists -eq $VolumeName) {
            & docker volume rm $VolumeName
        }
    }
}
