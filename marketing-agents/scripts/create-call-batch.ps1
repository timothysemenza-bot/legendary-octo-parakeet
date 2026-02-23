param(
    [string]$BatchQueueFile = "marketing-agents/data/call_batch_queue.csv",
    [string]$CallPlanFile = "marketing-agents/data/daily_call_plan.csv",
    [string]$BatchId = "",
    [string]$DialerProvider = "manual",
    [string]$OwnerApproved = "no",
    [string]$BusinessStart = "09:00",
    [string]$BusinessEnd = "17:00",
    [bool]$WeekdaysOnly = $true
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BatchQueueFile)) { throw "Missing file: $BatchQueueFile" }
if (-not (Test-Path $CallPlanFile)) { throw "Missing file: $CallPlanFile" }

$plan = Import-Csv -Path $CallPlanFile
if ($plan.Count -eq 0) { throw "Call plan is empty." }

$callDate = $plan[0].call_date
$start = ($plan | Select-Object -First 1).start_time
$end = ($plan | Select-Object -Last 1).end_time
$id = if ([string]::IsNullOrWhiteSpace($BatchId)) { "batch-" + (Get-Date -Format "yyyyMMdd-HHmmss") } else { $BatchId }

$callDateDt = [datetime]::ParseExact($callDate, "yyyy-MM-dd", $null)
if ($WeekdaysOnly -and ($callDateDt.DayOfWeek -eq [DayOfWeek]::Saturday -or $callDateDt.DayOfWeek -eq [DayOfWeek]::Sunday)) {
    throw ("Call date {0} is {1}. Weekday-only policy blocks batch creation." -f $callDate, $callDateDt.DayOfWeek)
}

$batchStartDt = [datetime]::ParseExact(("{0} {1}" -f $callDate, $start), "yyyy-MM-dd HH:mm", $null)
$batchEndDt = [datetime]::ParseExact(("{0} {1}" -f $callDate, $end), "yyyy-MM-dd HH:mm", $null)
$businessStartDt = [datetime]::ParseExact(("{0} {1}" -f $callDate, $BusinessStart), "yyyy-MM-dd HH:mm", $null)
$businessEndDt = [datetime]::ParseExact(("{0} {1}" -f $callDate, $BusinessEnd), "yyyy-MM-dd HH:mm", $null)

if ($batchStartDt -lt $businessStartDt -or $batchEndDt -gt $businessEndDt) {
    throw ("Batch window ({0}-{1}) is outside allowed business hours ({2}-{3})." -f $start, $end, $BusinessStart, $BusinessEnd)
}

$rows = @(Import-Csv -Path $BatchQueueFile)
$exists = $rows | Where-Object { $_.batch_id -eq $id } | Select-Object -First 1
if ($null -ne $exists) { throw "Batch id already exists: $id" }

$new = [pscustomobject]@{
    batch_id = $id
    created_date = (Get-Date).ToString("yyyy-MM-dd")
    call_date = $callDate
    start_time = $start
    end_time = $end
    dialer_provider = $DialerProvider
    owner_approved = $OwnerApproved
    record_count = "$($plan.Count)"
    status = "queued"
    notes = "Created from daily_call_plan.csv"
}

(@($rows) + $new) | Export-Csv -Path $BatchQueueFile -NoTypeInformation
Write-Output ("Created batch {0} with {1} calls (owner_approved={2})." -f $id, $plan.Count, $OwnerApproved)
