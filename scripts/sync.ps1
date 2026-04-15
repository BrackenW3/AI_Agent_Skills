param(
    [string]$Root = 'C:\Users\User',
    [string]$Profile = "windows-full"
)

$ErrorActionPreference = 'Stop'

# PS5.1 compat: ConvertFrom-Json | ConvertTo-Hashtable only exists in PS7+
function ConvertTo-Hashtable {
    param([Parameter(ValueFromPipeline)]$InputObject)
    process {
        if ($null -eq $InputObject) { return $null }
        if ($InputObject -is [System.Collections.IDictionary]) { return $InputObject }
        if ($InputObject -is [System.Collections.IEnumerable] -and $InputObject -isnot [string]) {
            return @($InputObject | ForEach-Object { ConvertTo-Hashtable $_ })
        }
        if ($InputObject.GetType().Name -eq 'PSCustomObject') {
            $hash = @{}
            foreach ($prop in $InputObject.PSObject.Properties) {
                $hash[$prop.Name] = ConvertTo-Hashtable $prop.Value
            }
            return $hash
        }
        return $InputObject
    }
}

function Get-EnvMap {
    param([string]$Path)

    $map = @{}
    foreach ($line in Get-Content -Path $Path) {
        if ($line -match '^\s*#' -or [string]::IsNullOrWhiteSpace($line)) {
            continue
        }
        if ($line -match '^([^=]+)=(.*)$') {
            $map[$matches[1].Trim()] = $matches[2]
        }
    }

    if ($map['GITHUB_MCP_PAT']) {
        $map['GITHUB_PERSONAL_ACCESS_TOKEN'] = $map['GITHUB_MCP_PAT']
        $map['GITHUB_TOKEN'] = $map['GITHUB_MCP_PAT']
    }
    if (-not $map['FILESYSTEM_ALLOWED_PATH']) {
        $map['FILESYSTEM_ALLOWED_PATH'] = 'C:/Users/User/VSCodespace'
    }
    if (-not $map['CLAUDE_AZURE_PATH']) {
        $map['CLAUDE_AZURE_PATH'] = '/c/Program Files/Microsoft SDKs/Azure/CLI2/wbin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    }

    return $map
}

function Resolve-TemplateValue {
    param(
        [Parameter(Mandatory = $true)]$Value,
        [hashtable]$EnvMap
    )

    if ($Value -is [string]) {
        return ([regex]::Replace($Value, '\$\{([A-Z0-9_]+)\}', {
            param($match)
            $key = $match.Groups[1].Value
            if ($EnvMap.ContainsKey($key)) { return [string]$EnvMap[$key] }
            return ''
        }))
    }

    if ($Value -is [System.Collections.IDictionary]) {
        $result = [ordered]@{}
        foreach ($key in $Value.Keys) {
            $result[$key] = Resolve-TemplateValue -Value $Value[$key] -EnvMap $EnvMap
        }
        return $result
    }

    if ($Value -is [System.Collections.IEnumerable] -and -not ($Value -is [string])) {
        $items = @()
        foreach ($item in $Value) {
            $items += Resolve-TemplateValue -Value $item -EnvMap $EnvMap
        }
        return $items
    }

    return $Value
}

function Write-JsonFile {
    param(
        [string]$Path,
        $Object
    )

    $parent = Split-Path -Parent $Path
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    $json = $Object | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

function Resolve-TemplateText {
    param(
        [string]$Text,
        [hashtable]$EnvMap
    )

    return ([regex]::Replace($Text, '\$\{([A-Z0-9_]+)\}', {
        param($match)
        $key = $match.Groups[1].Value
        if ($EnvMap.ContainsKey($key)) { return [string]$EnvMap[$key] }
        return ''
    }))
}

$registryRoot = Split-Path -Parent $PSScriptRoot

# Load MCP profile
$profileFile = Join-Path $registryRoot "mcp\profiles\$Profile.mcp.json"
if (-not (Test-Path $profileFile)) {
    Write-Warning "Profile '$Profile' not found at $profileFile, falling back to shared.mcp.json"
    $profileFile = Join-Path $registryRoot 'mcp\shared.mcp.json'
}
Write-Host "-> Using MCP profile: $profileFile"

$vsCodeRoot = Join-Path $Root 'VSCodespace'
$envPath = Join-Path $vsCodeRoot '.env'
$envMap = Get-EnvMap -Path $envPath

$claudePath = Join-Path $Root '.claude.json'
if (Test-Path $claudePath) {
    $claudeCurrent = Get-Content -Raw -Path $claudePath | ConvertFrom-Json | ConvertTo-Hashtable
    if ($claudeCurrent.ContainsKey('mcpServers') -and $claudeCurrent['mcpServers'].ContainsKey('azure')) {
        $azureEnv = $claudeCurrent['mcpServers']['azure']['env']
        if ($azureEnv -and $azureEnv['PATH']) {
            $envMap['CLAUDE_AZURE_PATH'] = $azureEnv['PATH']
        }
    }
}

$copilotTemplatePath = Join-Path $registryRoot 'agents\copilot\mcp.template.json'
$copilotTemplate = Get-Content -Raw -Path $copilotTemplatePath | ConvertFrom-Json | ConvertTo-Hashtable
$copilotResolved = Resolve-TemplateValue -Value $copilotTemplate -EnvMap $envMap
Write-JsonFile -Path (Join-Path $vsCodeRoot '.mcp.json') -Object $copilotResolved
Write-JsonFile -Path (Join-Path $vsCodeRoot '.vscode\mcp.json') -Object $copilotResolved

$claudeTemplate = Get-Content -Raw -Path (Join-Path $registryRoot 'agents\claude\global-mcps.template.json') | ConvertFrom-Json | ConvertTo-Hashtable
$claudeResolvedServers = (Resolve-TemplateValue -Value $claudeTemplate['mcpServers'] -EnvMap $envMap)
if (Test-Path $claudePath) {
    $claudeCurrent = Get-Content -Raw -Path $claudePath | ConvertFrom-Json | ConvertTo-Hashtable
} else {
    $claudeCurrent = @{}
}
$claudeCurrent['mcpServers'] = $claudeResolvedServers
Write-JsonFile -Path $claudePath -Object $claudeCurrent

$geminiPath = Join-Path $Root '.gemini\settings.json'
$geminiTemplate = Get-Content -Raw -Path (Join-Path $registryRoot 'agents\gemini\settings.patch.template.json') | ConvertFrom-Json | ConvertTo-Hashtable
$geminiResolvedServers = (Resolve-TemplateValue -Value $geminiTemplate['mcpServers'] -EnvMap $envMap)
if (Test-Path $geminiPath) {
    $geminiCurrent = Get-Content -Raw -Path $geminiPath | ConvertFrom-Json | ConvertTo-Hashtable
} else {
    $geminiCurrent = @{ theme = 'Default' }
}
$geminiCurrent['mcpServers'] = $geminiResolvedServers
Write-JsonFile -Path $geminiPath -Object $geminiCurrent

$jetbrainsTemplateText = Get-Content -Raw -Path (Join-Path $registryRoot 'agents\jetbrains\llm.mcpServers.template.xml')
$jetbrainsResolved = Resolve-TemplateText -Text $jetbrainsTemplateText -EnvMap $envMap
$jetbrainsBase = Join-Path $Root 'AppData\Roaming\JetBrains'
if (Test-Path $jetbrainsBase) {
    foreach ($dir in Get-ChildItem -Path $jetbrainsBase -Directory -Filter 'PyCharm*') {
        $target = Join-Path $dir.FullName 'options\llm.mcpServers.xml'
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
        [System.IO.File]::WriteAllText($target, $jetbrainsResolved, [System.Text.UTF8Encoding]::new($false))
    }
} else {
    Write-Host "No JetBrains directory found at $jetbrainsBase, skipping JetBrains sync."
}

Write-Host 'MCP templates synced to local configs.'
