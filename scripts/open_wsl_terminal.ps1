param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function ConvertTo-WindowsProcessArgument {
    param(
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Argument
    )

    if ($Argument.Length -gt 0 -and $Argument -notmatch '[\s"]') {
        return $Argument
    }

    $result = '"'
    $backslashes = 0

    foreach ($char in $Argument.ToCharArray()) {
        if ($char -eq '\') {
            $backslashes += 1
            continue
        }

        if ($char -eq '"') {
            if ($backslashes -gt 0) {
                $result += ('\' * ($backslashes * 2))
                $backslashes = 0
            }
            $result += '\"'
            continue
        }

        if ($backslashes -gt 0) {
            $result += ('\' * $backslashes)
            $backslashes = 0
        }
        $result += $char
    }

    if ($backslashes -gt 0) {
        $result += ('\' * ($backslashes * 2))
    }

    $result += '"'
    return $result
}

function ConvertTo-WslPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $resolved = (Resolve-Path -LiteralPath $Path).Path
    if ($resolved -notmatch '^([A-Za-z]):\\(.*)$') {
        throw "Only local drive paths can be converted to WSL paths: $resolved"
    }

    $drive = $Matches[1].ToLowerInvariant()
    $tail = $Matches[2] -replace '\\', '/'
    return "/mnt/$drive/$tail"
}

if (-not (Get-Command wt.exe -ErrorAction SilentlyContinue)) {
    throw "Windows Terminal (wt.exe) was not found on PATH."
}

if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
    throw "WSL (wsl.exe) was not found on PATH."
}

$startupScript = Join-Path $PSScriptRoot "start_wsl_shell.sh"
if (-not (Test-Path $startupScript)) {
    throw "WSL startup script was not found: $startupScript"
}

$wslStartupScript = ConvertTo-WslPath $startupScript

$processInfo = [System.Diagnostics.ProcessStartInfo]::new()
$processInfo.FileName = "wt.exe"

$arguments = @(
    "new-tab",
    "--title",
    "MiniTokamak WSL",
    "cmd.exe",
    "/d",
    "/k",
    "wsl.exe",
    "-d",
    "Ubuntu",
    "--",
    "bash",
    $wslStartupScript
)

$processInfo.Arguments = ($arguments | ForEach-Object { ConvertTo-WindowsProcessArgument $_ }) -join " "

if ($DryRun) {
    $processInfo.FileName
    $processInfo.Arguments
    exit 0
}

[void][System.Diagnostics.Process]::Start($processInfo)
