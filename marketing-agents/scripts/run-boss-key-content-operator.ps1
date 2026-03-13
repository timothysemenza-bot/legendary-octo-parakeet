param(
    [string]$InputFile = "",
    [string]$Text = "",
    [string]$Topic = "",
    [string]$Audience = "Owner-led janitorial and facilities-service firms",
    [string]$PrimaryCta = 'Comment "diagnostic" and I will send it.',
    [string]$Model = "gpt-5-mini",
    [string]$PromptFile = "marketing-agents/prompts/15_boss_key_content_operator.md",
    [string]$OutputDir = "marketing-agents/briefs/generated/content-operator",
    [switch]$PromptOnly,
    [switch]$OpenInNotepad
)

$ErrorActionPreference = "Stop"

if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw "Run this script in PowerShell 7 (pwsh) or from the current shell with: & .\marketing-agents\scripts\run-boss-key-content-operator.ps1 ..."
}

function Resolve-RepoPath {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) { return "" }
    if ([System.IO.Path]::IsPathRooted($PathValue)) { return $PathValue }
    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    return Join-Path $repoRoot $PathValue
}

function Ensure-Dir {
    param([string]$PathValue)
    if (-not (Test-Path $PathValue)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
    }
}

function Load-EnvFile {
    param([string]$FilePath)
    if (-not (Test-Path $FilePath)) { return }
    foreach ($line in Get-Content -Path $FilePath -Encoding UTF8) {
        $trimmed = [string]$line
        if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }
        $trimmed = $trimmed.Trim()
        if ($trimmed.StartsWith("#")) { continue }
        $idx = $trimmed.IndexOf("=")
        if ($idx -le 0) { continue }
        $key = $trimmed.Substring(0, $idx).Trim()
        $value = $trimmed.Substring($idx + 1).Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            $value = $value.Substring(1, $value.Length - 2)
        }
        if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($key))) {
            [Environment]::SetEnvironmentVariable($key, $value)
        }
    }
}

function Clean-TranscriptText {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return "" }
    $clean = $Value -replace '\r', ''
    $clean = $clean -replace '(?m)^\d+\s*$', ''
    $clean = $clean -replace '(?m)^\d{2}:\d{2}:\d{2}[,\.]\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*$', ''
    $clean = $clean -replace '\n{3,}', "`n`n"
    return $clean.Trim()
}

function Get-FirstNonEmpty {
    param($Object, [string[]]$Keys)
    foreach ($k in $Keys) {
        if ($Object.PSObject.Properties.Name -contains $k) {
            $v = [string]$Object.$k
            if (-not [string]::IsNullOrWhiteSpace($v)) {
                return $v.Trim()
            }
        }
    }
    return ""
}

function Parse-JsonTranscript {
    param([string]$FilePath)
    try {
        $obj = Get-Content -Path $FilePath -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 20
    } catch {
        return ""
    }
    $summary = Get-FirstNonEmpty -Object $obj -Keys @("summary", "notes", "ai_summary")
    $transcript = Get-FirstNonEmpty -Object $obj -Keys @("transcript", "text", "body", "content")
    if ([string]::IsNullOrWhiteSpace($transcript) -and $obj.PSObject.Properties.Name -contains "segments") {
        $segments = @($obj.segments | ForEach-Object { [string]$_.text })
        $transcript = ($segments -join " ").Trim()
    }
    return (Clean-TranscriptText (@($summary, $transcript) -join "`n`n"))
}

function Try-TranscribeWithWhisperCli {
    param([string]$AudioPath)
    $cmd = Get-Command whisper -ErrorAction SilentlyContinue
    if ($null -eq $cmd) { return "" }
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("bk-content-whisper-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $tmp -Force | Out-Null
    try {
        & whisper $AudioPath --model base --language en --task transcribe --output_format txt --output_dir $tmp | Out-Null
        $txt = Get-ChildItem -Path $tmp -Filter *.txt -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($txt) {
            return (Clean-TranscriptText (Get-Content -Path $txt.FullName -Raw -Encoding UTF8))
        }
        return ""
    } finally {
        Remove-Item -Path $tmp -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Try-TranscribeWithPythonFasterWhisper {
    param([string]$AudioPath)
    $py = Get-Command python -ErrorAction SilentlyContinue
    if ($null -eq $py) { return "" }
    $script = @'
import sys
try:
    from faster_whisper import WhisperModel
except Exception:
    print("__NO_FASTER_WHISPER__")
    sys.exit(0)
path = sys.argv[1]
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, _ = model.transcribe(path, vad_filter=True)
text = " ".join([s.text.strip() for s in segments]).strip()
print(text)
'@
    try {
        $out = & python -c $script $AudioPath 2>$null
        $txt = ([string]($out -join " ")).Trim()
        if ($txt -eq "__NO_FASTER_WHISPER__") { return "" }
        return (Clean-TranscriptText $txt)
    } catch {
        return ""
    }
}

function Get-SourceText {
    param([string]$InputFilePath, [string]$InlineText)
    if (-not [string]::IsNullOrWhiteSpace($InlineText)) {
        return @{
            text = (Clean-TranscriptText $InlineText)
            source_type = "inline-text"
        }
    }

    if ([string]::IsNullOrWhiteSpace($InputFilePath)) {
        throw "Provide -InputFile or -Text."
    }

    $resolved = Resolve-RepoPath $InputFilePath
    if (-not (Test-Path $resolved)) {
        throw "Input file not found: $resolved"
    }

    $ext = [System.IO.Path]::GetExtension($resolved)
    if ($null -eq $ext) { $ext = "" }
    $ext = $ext.ToLowerInvariant()
    if (@(".txt", ".md", ".srt") -contains $ext) {
        return @{
            text = (Clean-TranscriptText (Get-Content -Path $resolved -Raw -Encoding UTF8))
            source_type = "text-file"
        }
    }

    if ($ext -eq ".json") {
        return @{
            text = (Parse-JsonTranscript -FilePath $resolved)
            source_type = "json-transcript"
        }
    }

    if (@(".wav", ".mp3", ".m4a", ".aac", ".mp4", ".mov", ".mkv", ".wma") -contains $ext) {
        $transcript = Try-TranscribeWithPythonFasterWhisper -AudioPath $resolved
        if ([string]::IsNullOrWhiteSpace($transcript)) {
            $transcript = Try-TranscribeWithWhisperCli -AudioPath $resolved
        }
        if ([string]::IsNullOrWhiteSpace($transcript)) {
            throw "No transcript available. Install faster-whisper or whisper CLI, or provide a text transcript."
        }
        return @{
            text = $transcript
            source_type = "audio-video-transcribed"
        }
    }

    throw "Unsupported input extension: $ext"
}

function Get-FileText {
    param([string]$PathValue)
    $resolved = Resolve-RepoPath $PathValue
    if (-not (Test-Path $resolved)) { return "" }
    return Get-Content -Path $resolved -Raw -Encoding UTF8
}

function Slugify {
    param([string]$Value)
    $slug = ([string]$Value).ToLowerInvariant() -replace '[^a-z0-9]+', '-'
    $slug = $slug.Trim('-')
    if ([string]::IsNullOrWhiteSpace($slug)) { return "content-operator" }
    if ($slug.Length -gt 48) { return $slug.Substring(0, 48).Trim('-') }
    return $slug
}

function Extract-OutputText {
    param($ResponseObject)
    if ($null -ne $ResponseObject.output_text -and -not [string]::IsNullOrWhiteSpace([string]$ResponseObject.output_text)) {
        return [string]$ResponseObject.output_text
    }

    $chunks = New-Object System.Collections.Generic.List[string]
    foreach ($item in @($ResponseObject.output)) {
        foreach ($content in @($item.content)) {
            if ($content.type -eq "output_text" -and -not [string]::IsNullOrWhiteSpace([string]$content.text)) {
                $chunks.Add([string]$content.text)
            }
        }
    }
    return ($chunks -join "`n`n").Trim()
}

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Ensure-Dir (Resolve-RepoPath $OutputDir)

Load-EnvFile (Join-Path $repoRoot ".env")
Load-EnvFile (Join-Path $repoRoot ".env.local")

$source = Get-SourceText -InputFilePath $InputFile -InlineText $Text
if ([string]::IsNullOrWhiteSpace($source.text)) {
    throw "The source material is empty after parsing/transcription."
}

$promptText = Get-FileText $PromptFile
if ([string]::IsNullOrWhiteSpace($promptText)) {
    throw "Missing prompt file: $(Resolve-RepoPath $PromptFile)"
}

$contextBlock = @"
## Boss Key Reference Context

### Positioning
- Timmy is the visible expert behind Boss Key.
- Boss Key helps janitorial and facilities-service firms tighten public-sector pursuit discipline.
- Core problems: late opportunity visibility, weak bid-no-bid discipline, owner dependency, poor pricing/staffing/compliance handoffs, rushed proposal coordination.

### Approved Proof
- 12+ years in proposal management and writing.
- 200+ compliant proposals developed at SBM Management Services.
- Facilities-services proposal leadership at The Facilities Group.
- Experience across healthcare, regulated, and public-facing proposal environments.

### Writing Rules
- Use direct, plain language.
- Sound like an operator, not a creator coach.
- No invented metrics or inflated claims.
- Keep the writing useful before promotional.
- Use first-person voice for Timmy.

### Preferred Content Angles
- Why good facilities firms still lose bids.
- The owner should not be the proposal manager.
- Timing beats volume.
- Proposal writing is usually not the first bottleneck.
- The capture-to-proposal handoff is where many pursuits break.

### Approved CTAs
- Comment "diagnostic" and I will send it.
- DM me "radar" if you want the brief.
- Comment "handoff" and I will send the checklist.
- If this is your situation, message me and I will tell you what I would fix first.

### Asset Mapping
- diagnostic -> Facilities Pursuit Diagnostic
- radar -> Mid-Atlantic Facilities Rebid Radar
- handoff -> Facilities Capture-to-Proposal Handoff Checklist
### Output Goal
- Generate one coherent idea expressed as a LinkedIn post, a short video caption, a document/carousel outline, comment replies, DM follow-ups, and operator notes.
"@

$topicLabel = if ([string]::IsNullOrWhiteSpace($Topic)) { "Derived from source" } else { $Topic.Trim() }
$runStamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$baseName = "boss-key-content-operator-{0}-{1}" -f $runStamp, (Slugify $topicLabel)
$outputDirResolved = Resolve-RepoPath $OutputDir
$packetPath = Join-Path $outputDirResolved ("{0}.md" -f $baseName)
$jsonPath = Join-Path $outputDirResolved ("{0}.json" -f $baseName)

$userInput = @"
Topic hint: $topicLabel
Audience: $Audience
Preferred CTA: $PrimaryCta
Source type: $($source.source_type)

## Source Material
$($source.text)

$contextBlock
"@

$apiKey = [Environment]::GetEnvironmentVariable("OPENAI_API_KEY")

if ($PromptOnly -or [string]::IsNullOrWhiteSpace($apiKey)) {
    $modeNote = if ($PromptOnly) { "Prompt-only run requested." } else { "OPENAI_API_KEY not found. Generated prompt packet instead of live model output." }
    $packet = @"
# Boss Key Content Operator Packet
Date: $(Get-Date -Format "yyyy-MM-dd HH:mm")
Model: $Model
Mode: Prompt packet

$modeNote

## System Prompt

$promptText

## User Input

$userInput
"@
    $packet | Set-Content -Path $packetPath -Encoding UTF8
    Write-Output ("Generated prompt packet: {0}" -f $packetPath)
    if ($OpenInNotepad) {
        Start-Process notepad.exe $packetPath | Out-Null
    }
    return
}

$payload = @{
    model = $Model
    instructions = $promptText
    input = $userInput
    max_output_tokens = 1600
    reasoning = @{
        effort = "low"
    }
    text = @{
        verbosity = "low"
    }
} | ConvertTo-Json -Depth 10

$headers = @{
    Authorization = "Bearer $apiKey"
    "Content-Type" = "application/json"
}

try {
    $rawResponse = Invoke-WebRequest -Method Post -Uri "https://api.openai.com/v1/responses" -Headers $headers -Body $payload -TimeoutSec 180
    $responseText = [string]$rawResponse.Content
    $response = $responseText | ConvertFrom-Json -Depth 50
} catch {
    throw "OpenAI request failed: $($_.Exception.Message)"
}

$outputText = Extract-OutputText -ResponseObject $response
if ([string]::IsNullOrWhiteSpace($outputText)) {
    throw "The model response did not contain output text."
}

$outputText | Set-Content -Path $packetPath -Encoding UTF8
$responseText | Set-Content -Path $jsonPath -Encoding UTF8

Write-Output ("Generated content packet: {0}" -f $packetPath)
Write-Output ("Saved raw response: {0}" -f $jsonPath)

if ($OpenInNotepad) {
    Start-Process notepad.exe $packetPath | Out-Null
}
