<#
.SYNOPSIS
    Run the NexusAI workspace from one organized PowerShell entrypoint.

.DESCRIPTION
    This script keeps the common local workflows in one place:
    - `up` starts the full Docker Compose stack
    - `down` stops the stack
    - `logs` streams combined service logs
    - `check` runs the reliable validation bundle used by this repo

.EXAMPLE
    .\scripts\nexusai.ps1
    Starts the full local stack.

.EXAMPLE
    .\scripts\nexusai.ps1 check
    Runs backend tests, frontend typecheck/build, and Docker Compose config validation.
#>

[CmdletBinding()]
param(
    [ValidateSet("up", "down", "logs", "check")]
    [string]$Action = "up"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $RepoRoot

function Assert-CommandExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command '$Name' was not found in PATH."
    }
}

function Invoke-ExternalCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Executable,

        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )

    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage (exit code $LASTEXITCODE)."
    }
}

function Invoke-FrontendCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,

        [Parameter(Mandatory = $true)]
        [string]$FailureMessage
    )

    Push-Location (Join-Path $RepoRoot "frontend")
    try {
        $NpmExecutable = if ($env:OS -eq "Windows_NT") { "npm.cmd" } else { "npm" }
        Invoke-ExternalCommand -Executable $NpmExecutable -Arguments $Arguments -FailureMessage $FailureMessage
    } finally {
        Pop-Location
    }
}

switch ($Action) {
    "up" {
        Assert-CommandExists -Name "docker"
        Write-Host "Starting the full NexusAI stack with Docker Compose..."
        Invoke-ExternalCommand -Executable "docker" -Arguments @("compose", "up", "--build", "--remove-orphans") -FailureMessage "Docker Compose startup failed"
    }

    "down" {
        Assert-CommandExists -Name "docker"
        Write-Host "Stopping the NexusAI stack..."
        Invoke-ExternalCommand -Executable "docker" -Arguments @("compose", "down", "--remove-orphans") -FailureMessage "Docker Compose shutdown failed"
    }

    "logs" {
        Assert-CommandExists -Name "docker"
        Write-Host "Streaming NexusAI logs..."
        Invoke-ExternalCommand -Executable "docker" -Arguments @("compose", "logs", "-f", "backend", "frontend", "postgres") -FailureMessage "Docker Compose logs failed"
    }

    "check" {
        Assert-CommandExists -Name "python"
        Assert-CommandExists -Name "npm"
        Assert-CommandExists -Name "docker"

        Write-Host "Running backend tests..."
        Invoke-ExternalCommand -Executable "python" -Arguments @("-m", "pytest") -FailureMessage "Backend tests failed"

        Write-Host "Running frontend type checking..."
        Invoke-FrontendCommand -Arguments @("run", "typecheck") -FailureMessage "Frontend typecheck failed"

        Write-Host "Validating Docker Compose configuration..."
        Invoke-ExternalCommand -Executable "docker" -Arguments @("compose", "config") -FailureMessage "Docker Compose config validation failed"

        Write-Host "Validation complete."
    }
}
