param(
    [string]$QueueFile = "marketing-agents/data/photoshop_jobs.csv",
    [int]$MaxJobs = 10,
    [switch]$Visible
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $QueueFile)) { throw "Missing queue file: $QueueFile" }

$queue = @(Import-Csv -Path $QueueFile)
if ($queue.Count -eq 0) {
    Write-Output "No jobs in queue."
    exit 0
}

try {
    $psApp = New-Object -ComObject Photoshop.Application
    if ($Visible) {
        $psApp.Visible = $true
        try { $psApp.BringToFront() | Out-Null } catch {}
    }
} catch {
    throw "Photoshop COM automation unavailable. Open Photoshop once and retry. Error: $($_.Exception.Message)"
}

function New-JobJsx {
    param(
        [string]$SourcePath,
        [string]$OutputPath,
        [int]$MaxLongEdge,
        [int]$JpgQuality,
        [bool]$Enhance
)
    $enhanceLiteral = if ($Enhance) { "true" } else { "false" }
@"
var inFile = new File("$($SourcePath.Replace('\','\\'))");
if (!inFile.exists) { throw new Error("Missing source: " + inFile.fsName); }
var outFile = new File("$($OutputPath.Replace('\','\\'))");
if (!outFile.parent.exists) { outFile.parent.create(); }

var doc = app.open(inFile);
var w = doc.width.as("px");
var h = doc.height.as("px");
var maxEdge = $MaxLongEdge;
if (w >= h) {
    if (w > maxEdge) { doc.resizeImage(UnitValue(maxEdge, "px"), null, null, ResampleMethod.BICUBICSHARPER); }
} else {
    if (h > maxEdge) { doc.resizeImage(null, UnitValue(maxEdge, "px"), null, ResampleMethod.BICUBICSHARPER); }
}

if ($enhanceLiteral) {
    try { doc.activeLayer.adjustBrightnessContrast(6, 10); } catch (e1) {}
    try { doc.activeLayer.adjustHueSaturation(0, 5, 0); } catch (e2) {}
    try { doc.activeLayer.applyUnSharpMask(55, 0.8, 2); } catch (e3) {}
}

var opts = new JPEGSaveOptions();
opts.quality = $JpgQuality;
opts.embedColorProfile = true;
opts.formatOptions = FormatOptions.STANDARDBASELINE;
doc.saveAs(outFile, opts, true, Extension.LOWERCASE);
doc.close(SaveOptions.DONOTSAVECHANGES);
"@
}

$processed = 0

foreach ($row in $queue) {
    if ($processed -ge $MaxJobs) { break }
    if ($row.status -ne "queued") { continue }

    try {
        $source = $row.source_path
        $output = $row.output_path
        $edge = [int]$row.max_long_edge
        $quality = [int]$row.jpg_quality
        $enhance = ($row.job_type -eq "headshot_enhanced_web" -or $row.job_type -eq "headshot_enhanced_mobile")

        if (-not (Test-Path $source)) { throw "Source not found: $source" }
        $outDir = Split-Path -Parent $output
        if (-not [string]::IsNullOrWhiteSpace($outDir) -and -not (Test-Path $outDir)) {
            New-Item -ItemType Directory -Force -Path $outDir | Out-Null
        }

        $jsx = New-JobJsx -SourcePath $source -OutputPath $output -MaxLongEdge $edge -JpgQuality $quality -Enhance $enhance
        $psApp.DoJavaScript($jsx) | Out-Null

        $row.status = "completed"
        $row.last_error = ""
        $row.completed_at = (Get-Date).ToString("s")
        $processed++
        Write-Output ("Completed {0} -> {1}" -f $row.job_id, $output)
    } catch {
        $row.status = "failed"
        $row.last_error = $_.Exception.Message
        Write-Warning ("Failed {0}: {1}" -f $row.job_id, $row.last_error)
    }
}

$queue | Export-Csv -Path $QueueFile -NoTypeInformation
Write-Output ("Processed {0} job(s)." -f $processed)
