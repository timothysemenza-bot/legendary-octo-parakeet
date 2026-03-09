param(
  [string]$ManifestPath,
  [string]$ResultsRoot = (Join-Path $PSScriptRoot "..\test-results"),
  [string]$OutputRoot = (Join-Path $PSScriptRoot "..\demo-artifacts"),
  [ValidateSet("auto", "openai", "windows")]
  [string]$Provider = "auto",
  [string]$OpenAIApiKey = $env:OPENAI_API_KEY
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Tool {
  param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,
    [Parameter(Mandatory = $true)]
    [string[]]$Arguments
  )

  & $FilePath @Arguments
  if ($LASTEXITCODE -ne 0) {
    throw "Command failed: $FilePath $($Arguments -join ' ')"
  }
}

function Import-OptionalEnvFile {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  if (-not (Test-Path $Path)) {
    return
  }

  Get-Content $Path | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#") -or -not $line.Contains("=")) {
      return
    }

    $parts = $line.Split("=", 2)
    $name = $parts[0].Trim()
    $value = $parts[1].Trim().Trim("'").Trim('"')
    if (-not [string]::IsNullOrWhiteSpace($name) -and -not (Test-Path "Env:$name")) {
      Set-Item -Path "Env:$name" -Value $value
    }
  }
}

function Get-LatestManifestPath {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ResultsRoot
  )

  $manifest = Get-ChildItem -Path $ResultsRoot -Recurse -Filter "narration-manifest.json" -File |
    Sort-Object LastWriteTimeUtc -Descending |
    Select-Object -First 1

  if (-not $manifest) {
    throw "No narration manifest was found under $ResultsRoot. Run a Playwright Boss Key demo first."
  }

  return $manifest.FullName
}

function Get-JsonPropertyValue {
  param(
    [Parameter(Mandatory = $true)]
    [object]$Object,
    [Parameter(Mandatory = $true)]
    [string]$Name,
    [switch]$AllowMissing
  )

  $property = $Object.PSObject.Properties[$Name]
  if (-not $property) {
    if ($AllowMissing) {
      return $null
    }
    throw "Missing JSON property '$Name'."
  }

  return $property.Value
}

function Get-StepNarration {
  param(
    [Parameter(Mandatory = $true)]
    [object]$NarrationScript,
    [Parameter(Mandatory = $true)]
    [string]$StepKey
  )

  return Get-JsonPropertyValue -Object (Get-JsonPropertyValue -Object $NarrationScript -Name "steps") -Name $StepKey
}

function Get-MediaDurationMilliseconds {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  $durationText = & ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 $Path
  if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($durationText)) {
    throw "ffprobe could not read the media duration for $Path."
  }

  $durationSeconds = [double]::Parse($durationText.Trim(), [System.Globalization.CultureInfo]::InvariantCulture)
  return [int][Math]::Round($durationSeconds * 1000)
}

function New-SilenceWav {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [Parameter(Mandatory = $true)]
    [double]$DurationSeconds
  )

  Invoke-Tool -FilePath "ffmpeg" -Arguments @(
    "-hide_banner",
    "-loglevel", "error",
    "-y",
    "-f", "lavfi",
    "-i", "anullsrc=r=44100:cl=stereo",
    "-t", ([string]::Format([System.Globalization.CultureInfo]::InvariantCulture, "{0:0.000}", $DurationSeconds)),
    "-c:a", "pcm_s16le",
    $Path
  )
}

function Pad-WavToDuration {
  param(
    [Parameter(Mandatory = $true)]
    [string]$SourcePath,
    [Parameter(Mandatory = $true)]
    [string]$TargetPath,
    [Parameter(Mandatory = $true)]
    [double]$DurationSeconds
  )

  Invoke-Tool -FilePath "ffmpeg" -Arguments @(
    "-hide_banner",
    "-loglevel", "error",
    "-y",
    "-i", $SourcePath,
    "-af", "apad",
    "-t", ([string]::Format([System.Globalization.CultureInfo]::InvariantCulture, "{0:0.000}", $DurationSeconds)),
    "-ar", "44100",
    "-ac", "2",
    "-c:a", "pcm_s16le",
    $TargetPath
  )
}

function Write-Utf8NoBomFile {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [Parameter(Mandatory = $true)]
    [string[]]$Lines
  )

  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllLines($Path, $Lines, $utf8NoBom)
}

function Resolve-PreferredProvider {
  param(
    [Parameter(Mandatory = $true)]
    [string]$RequestedProvider,
    [Parameter(Mandatory = $true)]
    [object]$NarrationScript,
    [string]$OpenAIApiKey
  )

  $ttsConfig = Get-JsonPropertyValue -Object $NarrationScript -Name "tts" -AllowMissing
  $scriptProvider = if ($ttsConfig) { Get-JsonPropertyValue -Object $ttsConfig -Name "provider" -AllowMissing } else { $null }
  $effectiveProvider = if ($RequestedProvider -ne "auto") { $RequestedProvider } elseif ($scriptProvider) { [string]$scriptProvider } else { "auto" }

  if ($effectiveProvider -eq "auto") {
    if (-not [string]::IsNullOrWhiteSpace($OpenAIApiKey)) {
      return "openai"
    }
    return "windows"
  }

  return $effectiveProvider
}

function New-OpenAiSpeechClip {
  param(
    [Parameter(Mandatory = $true)]
    [string]$ApiKey,
    [Parameter(Mandatory = $true)]
    [object]$NarrationScript,
    [Parameter(Mandatory = $true)]
    [string]$Text,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
  )

  $ttsConfig = Get-JsonPropertyValue -Object $NarrationScript -Name "tts"
  $openAiConfig = Get-JsonPropertyValue -Object $ttsConfig -Name "openai" -AllowMissing
  if (-not $openAiConfig) {
    throw "Narration script is missing a 'tts.openai' configuration block."
  }

  $payload = @{
    model = [string](Get-JsonPropertyValue -Object $openAiConfig -Name "model")
    voice = [string](Get-JsonPropertyValue -Object $openAiConfig -Name "voice")
    input = $Text
    response_format = [string](Get-JsonPropertyValue -Object $openAiConfig -Name "response_format" -AllowMissing)
  }

  if (-not $payload.response_format) {
    $payload.response_format = "wav"
  }

  $instructions = Get-JsonPropertyValue -Object $openAiConfig -Name "instructions" -AllowMissing
  if ($instructions) {
    $payload.instructions = [string]$instructions
  }

  $speed = Get-JsonPropertyValue -Object $openAiConfig -Name "speed" -AllowMissing
  if ($speed) {
    $payload.speed = $speed
  }

  $headers = @{
    Authorization = "Bearer $ApiKey"
  }

  $body = $payload | ConvertTo-Json -Depth 8 -Compress
  Invoke-WebRequest -Method Post -Uri "https://api.openai.com/v1/audio/speech" -Headers $headers -ContentType "application/json" -Body $body -OutFile $OutputPath | Out-Null
}

function Get-OrCreateSpeechSynthesizer {
  param(
    [ref]$SynthRef
  )

  if ($null -eq $SynthRef.Value) {
    Add-Type -AssemblyName System.Speech
    $SynthRef.Value = New-Object System.Speech.Synthesis.SpeechSynthesizer
  }

  return $SynthRef.Value
}

function New-WindowsSpeechClip {
  param(
    [Parameter(Mandatory = $true)]
    [ref]$SynthRef,
    [Parameter(Mandatory = $true)]
    [object]$NarrationScript,
    [Parameter(Mandatory = $true)]
    [string]$Text,
    [Parameter(Mandatory = $true)]
    [string]$OutputPath
  )

  $synth = Get-OrCreateSpeechSynthesizer -SynthRef $SynthRef
  $ttsConfig = Get-JsonPropertyValue -Object $NarrationScript -Name "tts" -AllowMissing
  $windowsConfig = if ($ttsConfig) { Get-JsonPropertyValue -Object $ttsConfig -Name "windows" -AllowMissing } else { $null }
  $preferredVoice = if ($windowsConfig) { Get-JsonPropertyValue -Object $windowsConfig -Name "voice_name" -AllowMissing } else { $null }
  $availableVoices = $synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }

  if ($preferredVoice -and ($availableVoices -contains $preferredVoice)) {
    $synth.SelectVoice($preferredVoice)
  }

  $voiceRate = 0
  if ($windowsConfig -and $windowsConfig.PSObject.Properties["voice_rate"]) {
    $voiceRate = [int]$windowsConfig.voice_rate
  }
  $synth.Rate = $voiceRate

  $synth.SetOutputToWaveFile($OutputPath)
  try {
    $synth.Speak($Text)
  }
  finally {
    $synth.SetOutputToNull()
  }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
Import-OptionalEnvFile -Path (Join-Path $repoRoot ".env")
Import-OptionalEnvFile -Path (Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")).Path ".env")

if (-not $OpenAIApiKey -and $env:OPENAI_API_KEY) {
  $OpenAIApiKey = $env:OPENAI_API_KEY
}

$resultsRootPath = (Resolve-Path $ResultsRoot).Path
if (-not $ManifestPath) {
  $ManifestPath = Get-LatestManifestPath -ResultsRoot $resultsRootPath
}

$manifestFullPath = (Resolve-Path $ManifestPath).Path
$manifest = Get-Content $manifestFullPath -Raw | ConvertFrom-Json
$narrationScriptPathValue = Get-JsonPropertyValue -Object $manifest -Name "narration_script"
$resolvedNarrationScriptPath = if ([System.IO.Path]::IsPathRooted($narrationScriptPathValue)) {
  $narrationScriptPathValue
} else {
  Join-Path $repoRoot $narrationScriptPathValue
}
$narrationScriptFullPath = (Resolve-Path $resolvedNarrationScriptPath).Path
$narrationScript = Get-Content $narrationScriptFullPath -Raw | ConvertFrom-Json
$runOutputDir = Split-Path -Parent $manifestFullPath
$videoFileName = Get-JsonPropertyValue -Object $manifest -Name "video_file"
$videoPath = Join-Path $runOutputDir $videoFileName

if (-not (Test-Path $videoPath)) {
  throw "Expected Playwright video was not found at $videoPath."
}

if (-not (Test-Path $OutputRoot)) {
  New-Item -ItemType Directory -Path $OutputRoot | Out-Null
}

$outputRootPath = (Resolve-Path $OutputRoot).Path
$outputBasename = Get-JsonPropertyValue -Object $narrationScript -Name "output_basename" -AllowMissing
if (-not $outputBasename) {
  $outputBasename = [string](Get-JsonPropertyValue -Object $manifest -Name "demo")
}

$workingRoot = Join-Path $outputRootPath "${outputBasename}-working"
$audioSegmentsRoot = Join-Path $workingRoot "segments"
$rawAudioRoot = Join-Path $workingRoot "raw"

if (Test-Path $workingRoot) {
  Remove-Item $workingRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $workingRoot | Out-Null
New-Item -ItemType Directory -Path $audioSegmentsRoot | Out-Null
New-Item -ItemType Directory -Path $rawAudioRoot | Out-Null

$segmentPaths = New-Object System.Collections.Generic.List[string]
$transcriptLines = New-Object System.Collections.Generic.List[string]
$currentTimelineMs = 0
$providerMode = Resolve-PreferredProvider -RequestedProvider $Provider -NarrationScript $narrationScript -OpenAIApiKey $OpenAIApiKey
$requestedAutoFallback = ($Provider -eq "auto")
$speechSynth = $null
$speechSynthRef = [ref]$speechSynth

foreach ($step in $manifest.steps) {
  $stepStartMs = [int]$step.start_ms
  $stepEndMs = [int]$step.end_ms
  $stepDurationMs = [Math]::Max(1, $stepEndMs - $stepStartMs)

  if (($stepStartMs - $currentTimelineMs) -ge 25) {
    $gapDurationMs = $stepStartMs - $currentTimelineMs
    $gapPath = Join-Path $audioSegmentsRoot ("gap-{0:D2}.wav" -f $segmentPaths.Count)
    New-SilenceWav -Path $gapPath -DurationSeconds ($gapDurationMs / 1000.0)
    $segmentPaths.Add($gapPath)
    $currentTimelineMs = $stepStartMs
  }

  $stepNarration = Get-StepNarration -NarrationScript $narrationScript -StepKey $step.key
  $stepText = [string](Get-JsonPropertyValue -Object $stepNarration -Name "text")
  $rawClipPath = Join-Path $rawAudioRoot ("{0:D2}-{1}.wav" -f $segmentPaths.Count, $step.key)
  $finalClipPath = Join-Path $audioSegmentsRoot ("{0:D2}-{1}.wav" -f $segmentPaths.Count, $step.key)

  try {
    if ($providerMode -eq "openai") {
      if ([string]::IsNullOrWhiteSpace($OpenAIApiKey)) {
        throw "OPENAI_API_KEY is not set."
      }
      New-OpenAiSpeechClip -ApiKey $OpenAIApiKey -NarrationScript $narrationScript -Text $stepText -OutputPath $rawClipPath
    } else {
      New-WindowsSpeechClip -SynthRef $speechSynthRef -NarrationScript $narrationScript -Text $stepText -OutputPath $rawClipPath
    }
  }
  catch {
    if ($providerMode -eq "openai" -and $requestedAutoFallback) {
      Write-Warning "OpenAI TTS failed for '$($step.key)'. Falling back to Windows TTS. $_"
      $providerMode = "windows"
      New-WindowsSpeechClip -SynthRef $speechSynthRef -NarrationScript $narrationScript -Text $stepText -OutputPath $rawClipPath
    } else {
      throw
    }
  }

  $rawDurationMs = Get-MediaDurationMilliseconds -Path $rawClipPath
  if ($rawDurationMs -gt ($stepDurationMs + 150)) {
    throw "Narration step '$($step.key)' is longer than the filmed scene. Audio ${rawDurationMs}ms exceeds scene ${stepDurationMs}ms. Increase hold_ms or shorten the narration text."
  }

  Pad-WavToDuration -SourcePath $rawClipPath -TargetPath $finalClipPath -DurationSeconds ($stepDurationMs / 1000.0)
  $segmentPaths.Add($finalClipPath)
  $transcriptLines.Add("[$($step.key)] $stepText")
  $currentTimelineMs = $stepEndMs
}

$videoDurationMs = Get-MediaDurationMilliseconds -Path $videoPath
$timelineDurationMs = [Math]::Max($videoDurationMs, [int]$manifest.total_duration_ms)

if (($timelineDurationMs - $currentTimelineMs) -ge 25) {
  $tailGapPath = Join-Path $audioSegmentsRoot ("gap-{0:D2}.wav" -f $segmentPaths.Count)
  New-SilenceWav -Path $tailGapPath -DurationSeconds (($timelineDurationMs - $currentTimelineMs) / 1000.0)
  $segmentPaths.Add($tailGapPath)
}

$concatListPath = Join-Path $workingRoot "audio-segments.txt"
$concatListLines = $segmentPaths | ForEach-Object {
  $normalizedPath = ($_ -replace "\\", "/") -replace "'", "'\''"
  "file '$normalizedPath'"
}
Write-Utf8NoBomFile -Path $concatListPath -Lines $concatListLines

$narrationAudioPath = Join-Path $outputRootPath "${outputBasename}.wav"
$narratedVideoPath = Join-Path $outputRootPath "${outputBasename}.mp4"
$transcriptPath = Join-Path $outputRootPath "${outputBasename}.txt"
$manifestCopyPath = Join-Path $outputRootPath "${outputBasename}.manifest.json"

Invoke-Tool -FilePath "ffmpeg" -Arguments @(
  "-hide_banner",
  "-loglevel", "error",
  "-y",
  "-f", "concat",
  "-safe", "0",
  "-i", $concatListPath,
  "-ar", "44100",
  "-ac", "2",
  "-c:a", "pcm_s16le",
  $narrationAudioPath
)

Invoke-Tool -FilePath "ffmpeg" -Arguments @(
  "-hide_banner",
  "-loglevel", "error",
  "-y",
  "-i", $videoPath,
  "-i", $narrationAudioPath,
  "-c:v", "libx264",
  "-preset", "medium",
  "-crf", "18",
  "-pix_fmt", "yuv420p",
  "-movflags", "+faststart",
  "-c:a", "aac",
  "-b:a", "192k",
  "-shortest",
  $narratedVideoPath
)

Set-Content -Path $transcriptPath -Value $transcriptLines -Encoding utf8
Copy-Item -Path $manifestFullPath -Destination $manifestCopyPath -Force

$streamTypes = & ffprobe -v error -show_entries stream=codec_type -of csv=p=0 $narratedVideoPath
if ($LASTEXITCODE -ne 0) {
  throw "ffprobe could not inspect the narrated video at $narratedVideoPath."
}

$streamList = $streamTypes -split "\r?\n" | Where-Object { $_ }
if ($streamList -notcontains "video" -or $streamList -notcontains "audio") {
  throw "Narrated demo output is missing an audio or video stream at $narratedVideoPath."
}

Write-Host "Narrated demo created at $narratedVideoPath"
Write-Host "Narration audio created at $narrationAudioPath"
Write-Host "Narration transcript created at $transcriptPath"
