[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Executable,
    [string]$ProxyUri = 'http://127.0.0.1:10808',
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'
$iloaderFile = Get-Item -LiteralPath $Executable -ErrorAction Stop
if ($iloaderFile.PSIsContainer -or $iloaderFile.Extension -ne '.exe') {
    throw 'Select the installed iloader executable.'
}
$proxyAddress = [uri]$ProxyUri
if ($proxyAddress.Scheme -ne 'http' -or
    $proxyAddress.Host -notin @('127.0.0.1', 'localhost', '::1', '[::1]') -or
    $proxyAddress.UserInfo -ne '' -or $proxyAddress.Port -lt 1) {
    throw 'Use an unauthenticated local HTTP proxy endpoint.'
}

if ($CheckOnly) {
    [pscustomobject]@{
        Status = 'Validated'
        Executable = $iloaderFile.FullName
        ProcessProxy = $proxyAddress.AbsoluteUri
    } | ConvertTo-Json -Compress
    exit 0
}

if (@(Get-Process -Name iloader -ErrorAction SilentlyContinue).Count -gt 0) {
    throw 'Exit iloader completely before using this launcher.'
}

$launchInfo = New-Object System.Diagnostics.ProcessStartInfo
$launchInfo.FileName = $iloaderFile.FullName
$launchInfo.WorkingDirectory = $iloaderFile.DirectoryName
$launchInfo.UseShellExecute = $false
foreach ($proxyVariable in @('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY')) {
    $launchInfo.EnvironmentVariables[$proxyVariable] = $proxyAddress.AbsoluteUri
}
$launchInfo.EnvironmentVariables['NO_PROXY'] = 'localhost,127.0.0.1,::1'
[void][System.Diagnostics.Process]::Start($launchInfo)
