param(
    [string]$InboxDir = "marketing-agents/data/call-capture/inbox",
    [string]$ProcessedDir = "marketing-agents/data/call-capture/processed",
    [string]$FailedDir = "marketing-agents/data/call-capture/failed",
    [string]$SourceDirsFile = "marketing-agents/data/call-capture/source-folders.txt",
    [string]$StateFile = "marketing-agents/data/call-capture/state.json",
    [string]$LogFile = "marketing-agents/data/call_capture_ingest_log.csv",
    [string]$PendingFile = "marketing-agents/data/call_capture_pending_ingest.csv",
    [string]$CompanyOsInboxDir = "marketing-agents/data/engagement-inbox/call-intake",
    [string]$EngagementIntakeScript = "marketing-agents/scripts/run-engagement-intake.ps1",
    [int]$PollSeconds = 20,
    [switch]$RunOnce,
    [switch]$SkipEngagementIntake,
    [switch]$BusinessHoursOnly,
    [string]$BusinessStart = "08:30",
    [string]$BusinessEnd = "17:30"
)

$ErrorActionPreference = "Stop"

function Resolve-RepoPath {
    param([string]$PathValue)
    if ([System.IO.Path]::IsPathRooted($PathValue)) { return $PathValue }
    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    return Join-Path $repoRoot $PathValue
}

function Ensure-Dir {
    param([string]$PathValue)
    if (-not (Test-Path $PathValue)) { New-Item -ItemType Directory -Path $PathValue -Force | Out-Null }
}

function Ensure-CsvHeader {
    param([string]$FilePath, [string[]]$Headers)
    if (-not (Test-Path $FilePath)) {
        ($Headers -join ",") | Set-Content -Path $FilePath -Encoding UTF8
    }
}

function Load-State {
    param([string]$FilePath)
    if (-not (Test-Path $FilePath)) { return @{ processed = @{}; synced = @{} } }
    try {
        $json = Get-Content -Path $FilePath -Raw -Encoding UTF8
        if ([string]::IsNullOrWhiteSpace($json)) { return @{ processed = @{}; synced = @{} } }
        $obj = $json | ConvertFrom-Json -Depth 8
        if ($null -eq $obj.processed) { $obj | Add-Member -NotePropertyName processed -NotePropertyValue @{} }
        if ($null -eq $obj.synced) { $obj | Add-Member -NotePropertyName synced -NotePropertyValue @{} }
        return $obj
    } catch {
        return @{ processed = @{}; synced = @{} }
    }
}

function Save-State {
    param([string]$FilePath, $StateObject)
    ($StateObject | ConvertTo-Json -Depth 8) | Set-Content -Path $FilePath -Encoding UTF8
}

function Get-FileFingerprint {
    param([System.IO.FileInfo]$FileInfo)
    return ("{0}|{1}|{2}" -f $FileInfo.FullName, $FileInfo.Length, $FileInfo.LastWriteTimeUtc.Ticks)
}

function Get-DefaultSourceDirs {
    $dirs = @(
        (Join-Path $env:USERPROFILE "Downloads"),
        (Join-Path $env:USERPROFILE "Documents\Zoom"),
        (Join-Path $env:USERPROFILE "Documents\Microsoft Teams Chat Files"),
        (Join-Path $env:USERPROFILE "OneDrive\Documents\Zoom"),
        (Join-Path $env:USERPROFILE "OneDrive\Documents\Recordings"),
        (Join-Path $env:USERPROFILE "Videos")
    )
    return @($dirs | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
}

function Resolve-SourceDirs {
    param([string]$ListFilePath)
    $resolved = @()
    if (Test-Path $ListFilePath) {
        $rows = Get-Content -Path $ListFilePath -Encoding UTF8
        foreach ($r in $rows) {
            $line = [string]$r
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            if ($line.TrimStart().StartsWith("#")) { continue }
            $expanded = [Environment]::ExpandEnvironmentVariables($line.Trim())
            $resolved += $expanded
        }
    } else {
        $defaults = Get-DefaultSourceDirs
        Ensure-Dir (Split-Path -Parent $ListFilePath)
        @(
            "# One folder per line. Use absolute paths.",
            "# Files found in these locations are copied into call-capture/inbox automatically.",
            "# Lines starting with # are comments.",
            ""
        ) + $defaults | Set-Content -Path $ListFilePath -Encoding UTF8
        $resolved = $defaults
    }
    return @($resolved | Select-Object -Unique)
}

function Sync-SourceFilesToInbox {
    param(
        [string[]]$SourceDirs,
        [string]$InboxPath,
        $StateObject
    )
    $allowedExt = @(".txt",".md",".json",".srt",".wav",".mp3",".m4a",".aac",".mp4",".wma")
    $copied = 0
    foreach ($dir in $SourceDirs) {
        if ([string]::IsNullOrWhiteSpace($dir)) { continue }
        if (-not (Test-Path $dir)) { continue }
        $fullDir = (Resolve-Path $dir).Path
        if ($fullDir -eq $InboxPath) { continue }

        $files = Get-ChildItem -Path $fullDir -File -ErrorAction SilentlyContinue |
            Where-Object { $allowedExt -contains $_.Extension.ToLowerInvariant() } |
            Sort-Object LastWriteTimeUtc
        foreach ($f in $files) {
            if (((Get-Date).ToUniversalTime() - $f.LastWriteTimeUtc).TotalSeconds -lt 5) { continue }
            $finger = Get-FileFingerprint $f
            if ($StateObject.synced.PSObject.Properties.Name -contains $finger) { continue }
            $safeName = ($f.BaseName -replace '[^\w\-\.\(\) ]', '_').Trim()
            if ([string]::IsNullOrWhiteSpace($safeName)) { $safeName = "call_capture" }
            $stamp = (Get-Date -Date $f.LastWriteTime).ToString("yyyyMMdd-HHmmss")
            $destName = "{0}__{1}{2}" -f $safeName, $stamp, $f.Extension.ToLowerInvariant()
            $destPath = Join-Path $InboxPath $destName
            $i = 1
            while (Test-Path $destPath) {
                $destName = "{0}__{1}-{2}{3}" -f $safeName, $stamp, $i, $f.Extension.ToLowerInvariant()
                $destPath = Join-Path $InboxPath $destName
                $i++
            }
            Copy-Item -Path $f.FullName -Destination $destPath -Force
            $StateObject.synced | Add-Member -NotePropertyName $finger -NotePropertyValue (Get-Date).ToString("s") -Force
            $copied++
        }
    }
    return $copied
}

function Is-BusinessTime {
    param([string]$StartText, [string]$EndText)
    $now = Get-Date
    $start = [datetime]::ParseExact($StartText, "HH:mm", $null)
    $end = [datetime]::ParseExact($EndText, "HH:mm", $null)
    $startToday = Get-Date -Hour $start.Hour -Minute $start.Minute -Second 0
    $endToday = Get-Date -Hour $end.Hour -Minute $end.Minute -Second 0
    return ($now -ge $startToday -and $now -le $endToday)
}

function Clean-TranscriptText {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return "" }
    $clean = $Text -replace '\r', ''
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
            if (-not [string]::IsNullOrWhiteSpace($v)) { return $v.Trim() }
        }
    }
    return ""
}

function Parse-JsonTranscript {
    param([string]$FilePath)
    try {
        $obj = Get-Content -Path $FilePath -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 20
    } catch {
        return @{ transcript = ""; summary = "" }
    }
    $summary = Get-FirstNonEmpty -Object $obj -Keys @("summary","notes","ai_summary")
    $transcript = Get-FirstNonEmpty -Object $obj -Keys @("transcript","text","body","content")
    if ([string]::IsNullOrWhiteSpace($transcript) -and $obj.PSObject.Properties.Name -contains "segments") {
        $segments = @($obj.segments | ForEach-Object { [string]($_.text) })
        $transcript = ($segments -join " ").Trim()
    }
    return @{ transcript = (Clean-TranscriptText $transcript); summary = $summary }
}

function Try-TranscribeWithWhisperCli {
    param([string]$AudioPath)
    $cmd = Get-Command whisper -ErrorAction SilentlyContinue
    if ($null -eq $cmd) { return "" }
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("bk-whisper-" + [guid]::NewGuid().ToString("N"))
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

function Infer-Outcome {
    param([string]$Text)
    $t = ([string]$Text).ToLowerInvariant()
    if ($t -match "voicemail|left message") { return "voicemail" }
    if ($t -match "no answer|could not reach|didn't answer") { return "no-answer" }
    if ($t -match "meeting booked|booked meeting|calendar invite|set a meeting") { return "meeting-booked" }
    if ($t -match "not a fit|not fit|not interested|no interest") { return "not-fit" }
    if ($t -match "do not contact|unsubscribe|remove me") { return "do-not-contact" }
    if ($t -match "call me back|follow up|send details|next week|proposal") { return "connected" }
    return "connected"
}

function Extract-ActionItems {
    param([string]$Text)
    if ([string]::IsNullOrWhiteSpace($Text)) { return @("Follow up based on call transcript.") }
    $items = @()
    $sentences = $Text -split '(?<=[\.\!\?])\s+'
    foreach ($s in $sentences) {
        $line = $s.Trim()
        if ($line.Length -lt 12) { continue }
        if ($line -match '(?i)\b(next step|action item|follow up|send|schedule|call back|email|proposal|quote|pricing|meeting)\b') {
            $items += $line
        }
        if ($items.Count -ge 5) { break }
    }
    if ($items.Count -eq 0) { $items = @("Follow up based on call transcript.") }
    return $items
}

function Parse-MetadataFromFileName {
    param([string]$BaseName)
    $company = ""
    $contact = ""
    $phone = ""
    $parts = $BaseName -split '__'
    if ($parts.Count -ge 1) { $company = ($parts[0] -replace '_', ' ').Trim() }
    if ($parts.Count -ge 2) { $contact = ($parts[1] -replace '_', ' ').Trim() }
    if ($parts.Count -ge 3) { $phone = ($parts[2] -replace '[^\d\+]', '').Trim() }
    return @{ company = $company; contact = $contact; phone = $phone }
}

function Append-CsvRow {
    param([string]$FilePath, [hashtable]$Row, [string[]]$Headers)
    $line = ($Headers | ForEach-Object { '"' + ([string]($Row[$_] -replace '"', '""')) + '"' }) -join ","
    Add-Content -Path $FilePath -Value $line -Encoding UTF8
}

function Write-CompanyOsCapture {
    param(
        [string]$OutputDir,
        [string]$Company,
        [string]$Contact,
        [string]$Phone,
        [string]$Summary,
        [string]$Transcript,
        [string]$Outcome,
        [string]$InteractionId
    )
    Ensure-Dir $OutputDir
    $dateStamp = (Get-Date).ToString("yyyy-MM-dd")
    $baseName = @($Company, $Contact, $InteractionId) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object {
        ([string]$_ -replace '[^\w\-\.\(\) ]', '_').Trim()
    }
    $slug = ($baseName -join "__")
    if ([string]::IsNullOrWhiteSpace($slug)) { $slug = "call-capture" }
    $path = Join-Path $OutputDir ("{0}__{1}.md" -f $dateStamp, $slug)

    $actionItems = Extract-ActionItems -Text $Transcript
    $content = @(
        "Subject: Call Capture Intake"
        "Direction: inbound"
        ("Date: {0}" -f $dateStamp)
        ("Company: {0}" -f $Company)
        ("Contact: {0}" -f $Contact)
        ("Phone: {0}" -f $Phone)
        ("Outcome: {0}" -f $Outcome)
        ("Interaction ID: {0}" -f $InteractionId)
        "Source: Auto call intake agent"
        ""
        "Summary:"
        $Summary
        ""
        "Action Items:"
    )

    foreach ($item in $actionItems) {
        $content += ("- {0}" -f $item)
    }

    $content += @(
        ""
        "Transcript:"
        ""
        $Transcript
    )

    $content -join "`n" | Set-Content -Path $path -Encoding UTF8
    return $path
}

function Invoke-EngagementIntake {
    param([string]$ScriptPath)
    & powershell -ExecutionPolicy Bypass -File $ScriptPath | Out-Null
}

$InboxDir = Resolve-RepoPath $InboxDir
$ProcessedDir = Resolve-RepoPath $ProcessedDir
$FailedDir = Resolve-RepoPath $FailedDir
$SourceDirsFile = Resolve-RepoPath $SourceDirsFile
$StateFile = Resolve-RepoPath $StateFile
$LogFile = Resolve-RepoPath $LogFile
$PendingFile = Resolve-RepoPath $PendingFile
$CompanyOsInboxDir = Resolve-RepoPath $CompanyOsInboxDir
$EngagementIntakeScript = Resolve-RepoPath $EngagementIntakeScript

Ensure-Dir $InboxDir
Ensure-Dir $ProcessedDir
Ensure-Dir $FailedDir
Ensure-Dir $CompanyOsInboxDir
Ensure-Dir (Split-Path -Parent $StateFile)
Ensure-Dir (Split-Path -Parent $LogFile)
Ensure-Dir (Split-Path -Parent $PendingFile)
Ensure-CsvHeader -FilePath $LogFile -Headers @("processed_at","file_name","status","company_name","contact_name","outcome","notes")
Ensure-CsvHeader -FilePath $PendingFile -Headers @("queued_at","file_name","company_name","contact_name","phone","summary","outcome","transcript")

$state = Load-State $StateFile
$sourceDirs = Resolve-SourceDirs -ListFilePath $SourceDirsFile

Write-Output ("Auto Call Intake Agent started. Inbox: {0}" -f $InboxDir)
Write-Output ("Source folders list: {0}" -f $SourceDirsFile)
Write-Output ("Company OS inbox: {0}" -f $CompanyOsInboxDir)

while ($true) {
    if ($BusinessHoursOnly -and -not (Is-BusinessTime -StartText $BusinessStart -EndText $BusinessEnd)) {
        if ($RunOnce) { break }
        Start-Sleep -Seconds $PollSeconds
        continue
    }

    $copiedCount = Sync-SourceFilesToInbox -SourceDirs $sourceDirs -InboxPath $InboxDir -StateObject $state
    if ($copiedCount -gt 0) {
        Write-Output ("Synced {0} new call file(s) into inbox." -f $copiedCount)
        Save-State -FilePath $StateFile -StateObject $state
    }

    $files = Get-ChildItem -Path $InboxDir -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc
    $capturesWritten = 0
    foreach ($f in $files) {
        if (((Get-Date).ToUniversalTime() - $f.LastWriteTimeUtc).TotalSeconds -lt 5) { continue }

        $finger = Get-FileFingerprint $f
        if ($state.processed.PSObject.Properties.Name -contains $finger) { continue }

        $meta = Parse-MetadataFromFileName -BaseName $f.BaseName
        $ext = $f.Extension.ToLowerInvariant()
        $transcript = ""
        $summary = ""
        $status = "processed"
        $notes = ""

        if ($ext -in @(".txt",".md",".srt")) {
            $transcript = Clean-TranscriptText (Get-Content -Path $f.FullName -Raw -Encoding UTF8)
        } elseif ($ext -eq ".json") {
            $parsed = Parse-JsonTranscript -FilePath $f.FullName
            $transcript = [string]$parsed.transcript
            $summary = [string]$parsed.summary
        } elseif ($ext -in @(".wav",".mp3",".m4a",".aac",".mp4",".wma")) {
            $transcript = Try-TranscribeWithPythonFasterWhisper -AudioPath $f.FullName
            if ([string]::IsNullOrWhiteSpace($transcript)) {
                $transcript = Try-TranscribeWithWhisperCli -AudioPath $f.FullName
            }
            if ([string]::IsNullOrWhiteSpace($transcript)) {
                $status = "failed"
                $notes = "No local transcription engine found (install faster-whisper or whisper CLI)."
            }
        } else {
            $status = "ignored"
            $notes = "Unsupported file type."
        }

        if ($status -eq "processed" -and [string]::IsNullOrWhiteSpace($transcript)) {
            $status = "failed"
            $notes = "Transcript content is empty."
        }

        $actionItems = if ($status -eq "processed") { Extract-ActionItems -Text $transcript } else { @() }
        if ([string]::IsNullOrWhiteSpace($summary) -and $actionItems.Count -gt 0) { $summary = $actionItems[0] }
        if ([string]::IsNullOrWhiteSpace($summary)) { $summary = "Follow up based on call transcript." }
        $outcome = if ($status -eq "processed") { Infer-Outcome -Text $transcript } else { "connected" }
        $interactionId = "auto-" + [guid]::NewGuid().ToString("N").Substring(0, 12)

        if ($status -eq "processed") {
            try {
                $capturePath = Write-CompanyOsCapture -OutputDir $CompanyOsInboxDir -Company $meta.company -Contact $meta.contact -Phone $meta.phone -Summary $summary -Transcript $transcript -Outcome $outcome -InteractionId $interactionId
                $notes = ("Captured to Company OS inbox: {0}" -f $capturePath)
                $capturesWritten++
            } catch {
                $status = "queued"
                $notes = "Company OS capture write failed, queued for retry."
                Append-CsvRow -FilePath $PendingFile -Headers @("queued_at","file_name","company_name","contact_name","phone","summary","outcome","transcript") -Row @{
                    queued_at = (Get-Date).ToString("s")
                    file_name = $f.Name
                    company_name = $meta.company
                    contact_name = $meta.contact
                    phone = $meta.phone
                    summary = $summary
                    outcome = $outcome
                    transcript = $transcript
                }
            }
        }

        Append-CsvRow -FilePath $LogFile -Headers @("processed_at","file_name","status","company_name","contact_name","outcome","notes") -Row @{
            processed_at = (Get-Date).ToString("s")
            file_name = $f.Name
            status = $status
            company_name = $meta.company
            contact_name = $meta.contact
            outcome = $outcome
            notes = $notes
        }

        $destDir = if ($status -eq "failed") { $FailedDir } else { $ProcessedDir }
        $dest = Join-Path $destDir $f.Name
        Move-Item -Path $f.FullName -Destination $dest -Force

        $state.processed | Add-Member -NotePropertyName $finger -NotePropertyValue (Get-Date).ToString("s") -Force
        Save-State -FilePath $StateFile -StateObject $state
    }

    if ($capturesWritten -gt 0 -and -not $SkipEngagementIntake) {
        try {
            Invoke-EngagementIntake -ScriptPath $EngagementIntakeScript
            Write-Output ("Ran engagement intake for {0} new call capture(s)." -f $capturesWritten)
        } catch {
            Write-Warning ("Failed to run engagement intake automatically: {0}" -f $_.Exception.Message)
        }
    }

    if ($RunOnce) { break }
    Start-Sleep -Seconds $PollSeconds
}

Write-Output "Auto Call Intake Agent stopped."
