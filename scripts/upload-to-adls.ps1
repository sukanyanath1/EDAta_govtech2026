param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [Parameter(Mandatory = $true)]
    [string]$Dest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}

function Load-DotEnv([string]$EnvFilePath) {
    $map = @{}

    if (-not (Test-Path -Path $EnvFilePath -PathType Leaf)) {
        return $map
    }

    Get-Content -Path $EnvFilePath | ForEach-Object {
        $line = $_.Trim()
        if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) {
            return
        }

        $index = $line.IndexOf('=')
        if ($index -lt 1) {
            return
        }

        $key = $line.Substring(0, $index).Trim()
        $value = $line.Substring($index + 1).Trim().Trim('"').Trim("'")
        $map[$key] = $value
    }

    return $map
}

function Get-ConfigValue([string]$Name, [hashtable]$EnvMap) {
    $fromEnv = [Environment]::GetEnvironmentVariable($Name)
    if (-not [string]::IsNullOrWhiteSpace($fromEnv)) {
        return $fromEnv
    }

    if ($EnvMap.ContainsKey($Name) -and -not [string]::IsNullOrWhiteSpace($EnvMap[$Name])) {
        return $EnvMap[$Name]
    }

    throw "Missing required configuration: $Name"
}

function Normalize-SasToken([string]$Token) {
    if ($Token.StartsWith('?')) {
        return $Token.Substring(1)
    }
    return $Token
}

if (-not (Test-Path -Path $Source -PathType Leaf)) {
    throw "Source file does not exist: $Source"
}

$repoRoot = Get-RepoRoot
$envMap = Load-DotEnv -EnvFilePath (Join-Path $repoRoot '.env')

$accountUrl = (Get-ConfigValue -Name 'STORAGE_ACCOUNT_URL' -EnvMap $envMap).TrimEnd('/')
$fileSystem = Get-ConfigValue -Name 'ADLS_FILESYSTEM' -EnvMap $envMap
$sasToken = Normalize-SasToken -Token (Get-ConfigValue -Name 'ADLS_SAS_TOKEN' -EnvMap $envMap)

$destPath = $Dest.TrimStart('/')
$encodedDestPath = (($destPath -split '/') | ForEach-Object { [System.Uri]::EscapeDataString($_) }) -join '/'
$baseUrl = "$accountUrl/$fileSystem/$encodedDestPath"

[byte[]]$fileBytes = [System.IO.File]::ReadAllBytes((Resolve-Path $Source))

$headers = @{
    'x-ms-version' = '2023-11-03'
    'x-ms-date'    = [DateTime]::UtcNow.ToString('R')
}

$createUrl = "${baseUrl}?resource=file&$sasToken"
$appendUrl = "${baseUrl}?action=append&position=0&$sasToken"
$flushUrl = "${baseUrl}?action=flush&position=$($fileBytes.Length)&$sasToken"
$deleteUrl = "${baseUrl}?$sasToken"

# Explicitly replace existing target file if present.
try {
    Invoke-RestMethod -Method Delete -Uri $deleteUrl -Headers $headers
}
catch {
    $statusCode = $null
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode) {
        if ($_.Exception.Response.StatusCode.value__) {
            $statusCode = $_.Exception.Response.StatusCode.value__
        }
        else {
            $statusCode = [int]$_.Exception.Response.StatusCode
        }
    }

    if ($statusCode -ne 404) {
        throw
    }
}

Invoke-RestMethod -Method Put -Uri $createUrl -Headers $headers
Invoke-RestMethod -Method Patch -Uri $appendUrl -Headers $headers -Body $fileBytes -ContentType 'application/octet-stream'
Invoke-RestMethod -Method Patch -Uri $flushUrl -Headers $headers

Write-Host "Uploaded '$Source' to '$Dest' in ADLS."
