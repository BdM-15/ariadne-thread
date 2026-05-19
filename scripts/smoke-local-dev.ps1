[CmdletBinding()]
param(
    [string]$AriadneBaseUrl = "http://127.0.0.1:9622",
    [string]$Crawl4AIBaseUrl = "",
    [string]$SearXNGBaseUrl = "",
    [string]$SmokeTarget = "example"
)

$ErrorActionPreference = "Stop"

if (-not $Crawl4AIBaseUrl) {
    $Crawl4AIBaseUrl = if ($env:CRAWL4AI_BASE_URL) { $env:CRAWL4AI_BASE_URL } else { "http://localhost:11235" }
}
if (-not $SearXNGBaseUrl) {
    $SearXNGBaseUrl = if ($env:SEARXNG_BASE_URL) { $env:SEARXNG_BASE_URL } else { "http://localhost:8080" }
}

function Convert-ResponseJson {
    param([object]$Response)
    return $Response.Content | ConvertFrom-Json
}

function Invoke-JsonGet {
    param([string]$Uri)
    $response = Invoke-WebRequest -UseBasicParsing -Uri $Uri -TimeoutSec 60
    return Convert-ResponseJson $response
}

function Invoke-JsonPost {
    param([string]$Uri, [object]$Body)
    $jsonBody = $Body | ConvertTo-Json -Depth 6
    $response = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -ContentType "application/json" -Body $jsonBody -TimeoutSec 60
    return Convert-ResponseJson $response
}

function Assert-Condition {
    param([bool]$Condition, [string]$Message)
    if (-not $Condition) {
        throw $Message
    }
}

Write-Host "Checking Crawl4AI at $Crawl4AIBaseUrl"
try {
    Invoke-JsonGet "$Crawl4AIBaseUrl/health" | Out-Null
}
catch {
    Invoke-JsonGet "$Crawl4AIBaseUrl/openapi.json" | Out-Null
}

Write-Host "Checking SearXNG JSON search at $SearXNGBaseUrl"
$encodedTarget = [System.Uri]::EscapeDataString($SmokeTarget)
$searxngResponse = Invoke-JsonGet "$SearXNGBaseUrl/search?q=$encodedTarget&format=json"
$searxngResults = @()
if ($null -ne $searxngResponse.results) {
    $searxngResults = @($searxngResponse.results)
}
Assert-Condition ($searxngResults.Count -gt 0) "SearXNG returned no JSON results for smoke target '$SmokeTarget'."

Write-Host "Checking Ariadne source-provider registry at $AriadneBaseUrl"
$registryResponse = Invoke-JsonGet "$AriadneBaseUrl/api/capture-research/source-providers"
Assert-Condition ($registryResponse.registry.quality_status -eq "full_ready") "Ariadne source-provider registry is not full_ready."

$smokeBody = @{ approved = $true; smoke_target = $SmokeTarget }
foreach ($providerId in @("crawl4ai_local", "searxng_local")) {
    Write-Host "Checking Ariadne smoke endpoint for $providerId"
    $smokeResponse = Invoke-JsonPost "$AriadneBaseUrl/api/capture-research/source-providers/$providerId/smoke-check" $smokeBody
    Assert-Condition ($smokeResponse.result.status -eq "success") "Ariadne smoke check failed for $providerId`: $($smokeResponse.result.diagnostic_summary)"
}

Write-Host "Local dev stack smoke checks passed."