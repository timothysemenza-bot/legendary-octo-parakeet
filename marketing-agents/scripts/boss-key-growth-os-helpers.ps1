Set-StrictMode -Version Latest

function Resolve-BossKeyGrowthPath {
    param([string]$PathValue)

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return ""
    }

    if ([System.IO.Path]::IsPathRooted($PathValue)) {
        return $PathValue
    }

    $repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
    return Join-Path $repoRoot $PathValue
}

function Ensure-BossKeyGrowthDirectory {
    param([string]$PathValue)

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return
    }

    if (-not (Test-Path $PathValue)) {
        New-Item -ItemType Directory -Path $PathValue -Force | Out-Null
    }
}

function Import-BossKeyCsv {
    param([string]$PathValue)

    $resolved = Resolve-BossKeyGrowthPath $PathValue
    if (-not (Test-Path $resolved)) {
        return @()
    }

    return @(Import-Csv -Path $resolved)
}

function ConvertTo-BossKeySchemaRow {
    param(
        [object]$Row,
        [string[]]$PropertyOrder
    )

    $out = [ordered]@{}
    foreach ($property in $PropertyOrder) {
        $out[$property] = ""
        if ($null -ne $Row -and $Row.PSObject.Properties.Name -contains $property) {
            $out[$property] = [string]$Row.$property
        }
    }
    return [pscustomobject]$out
}

function Import-BossKeyCsvWithSchema {
    param(
        [string]$PathValue,
        [string[]]$PropertyOrder
    )

    return @(
        Import-BossKeyCsv -PathValue $PathValue |
            ForEach-Object { ConvertTo-BossKeySchemaRow -Row $_ -PropertyOrder $PropertyOrder }
    )
}

function Export-BossKeyCsv {
    param(
        [object]$Rows,
        [string]$PathValue,
        [string[]]$PropertyOrder
    )

    $resolved = Resolve-BossKeyGrowthPath $PathValue
    $directory = Split-Path -Parent $resolved
    Ensure-BossKeyGrowthDirectory -PathValue $directory

    $rowList = New-Object System.Collections.Generic.List[object]
    if ($null -ne $Rows) {
        if (($Rows -is [System.Collections.IEnumerable]) -and -not ($Rows -is [string]) -and -not ($Rows -is [pscustomobject])) {
            foreach ($item in $Rows) {
                $rowList.Add($item)
            }
        } else {
            $rowList.Add($Rows)
        }
    }

    if ($rowList.Count -eq 0) {
        if ($PropertyOrder.Count -eq 0) {
            @() | Export-Csv -Path $resolved -NoTypeInformation
            return
        }

        $blank = [ordered]@{}
        foreach ($property in $PropertyOrder) {
            $blank[$property] = ""
        }
        @([pscustomobject]$blank) | Select-Object -First 0 | Export-Csv -Path $resolved -NoTypeInformation
        return
    }

    $normalized = foreach ($row in $rowList) {
        ConvertTo-BossKeySchemaRow -Row $row -PropertyOrder $PropertyOrder
    }

    $normalized | Export-Csv -Path $resolved -NoTypeInformation
}

function ConvertTo-BossKeySlug {
    param([string]$Value)

    $slug = ([string]$Value).ToLowerInvariant() -replace '[^a-z0-9]+', '-'
    $slug = $slug.Trim('-')
    if ([string]::IsNullOrWhiteSpace($slug)) {
        return "boss-key-item"
    }
    return $slug
}

function New-BossKeyId {
    param(
        [string]$Prefix,
        [string]$Seed
    )

    $token = ConvertTo-BossKeySlug -Value $Seed
    if ($token.Length -gt 24) {
        $token = $token.Substring(0, 24).Trim('-')
    }
    $dateToken = (Get-Date).ToString("yyyyMMdd")
    return "{0}-{1}-{2}" -f $Prefix, $dateToken, $token
}

function Escape-BossKeyHtml {
    param([string]$Value)

    if ($null -eq $Value) {
        return ""
    }

    $escaped = $Value.Replace('&', '&amp;')
    $escaped = $escaped.Replace('<', '&lt;')
    $escaped = $escaped.Replace('>', '&gt;')
    $escaped = $escaped.Replace('"', '&quot;')
    return $escaped
}

function Escape-BossKeyXml {
    param([string]$Value)

    if ($null -eq $Value) {
        return ""
    }

    $escaped = $Value.Replace('&', '&amp;')
    $escaped = $escaped.Replace('<', '&lt;')
    $escaped = $escaped.Replace('>', '&gt;')
    $escaped = $escaped.Replace('"', '&quot;')
    $escaped = $escaped.Replace("'", '&apos;')
    return $escaped
}

function Parse-BossKeyOperatorPacket {
    param([string]$PathValue)

    $resolved = Resolve-BossKeyGrowthPath $PathValue
    if (-not (Test-Path $resolved)) {
        throw "Operator packet not found: $resolved"
    }

    $knownHeadings = @(
        "Source Angle",
        "LinkedIn Post",
        "Short Video Caption",
        "Document / Carousel Outline",
        "Comment Reply Options",
        "DM Follow-Up Drafts",
        "Operator Notes"
    )

    $sections = [ordered]@{}
    foreach ($heading in $knownHeadings) {
        $sections[$heading] = ""
    }

    $currentHeading = ""
    $buffer = New-Object System.Collections.Generic.List[string]

    foreach ($line in (Get-Content -Path $resolved -Encoding UTF8)) {
        $trimmed = [string]$line
        if ($knownHeadings -contains $trimmed.Trim()) {
            if (-not [string]::IsNullOrWhiteSpace($currentHeading)) {
                $sections[$currentHeading] = ($buffer -join "`n").Trim()
            }
            $currentHeading = $trimmed.Trim()
            $buffer = New-Object System.Collections.Generic.List[string]
            continue
        }

        if ($trimmed.Trim() -eq "Status: Pending owner approval before publish/send.") {
            continue
        }

        if (-not [string]::IsNullOrWhiteSpace($currentHeading)) {
            $buffer.Add($trimmed)
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($currentHeading)) {
        $sections[$currentHeading] = ($buffer -join "`n").Trim()
    }

    return [pscustomobject]$sections
}

function Convert-BossKeyMarkdownToHtml {
    param([string]$Markdown)

    if ([string]::IsNullOrWhiteSpace($Markdown)) {
        return ""
    }

    $lines = $Markdown -split "`r?`n"
    $html = New-Object System.Collections.Generic.List[string]
    $paragraph = New-Object System.Collections.Generic.List[string]
    $inList = $false

    function Flush-Paragraph {
        param(
            [System.Collections.Generic.List[string]]$ParagraphBuffer,
            [System.Collections.Generic.List[string]]$OutputBuffer
        )

        if ($ParagraphBuffer.Count -eq 0) {
            return
        }

        $text = ($ParagraphBuffer -join " ").Trim()
        if (-not [string]::IsNullOrWhiteSpace($text)) {
            $OutputBuffer.Add("<p>$([string](Escape-BossKeyHtml -Value $text))</p>")
        }
        $ParagraphBuffer.Clear()
    }

    foreach ($rawLine in $lines) {
        $line = [string]$rawLine
        $trimmed = $line.Trim()

        if ([string]::IsNullOrWhiteSpace($trimmed)) {
            Flush-Paragraph -ParagraphBuffer $paragraph -OutputBuffer $html
            if ($inList) {
                $html.Add("</ul>")
                $inList = $false
            }
            continue
        }

        if ($trimmed -match '^###\s+(.+)$') {
            Flush-Paragraph -ParagraphBuffer $paragraph -OutputBuffer $html
            if ($inList) {
                $html.Add("</ul>")
                $inList = $false
            }
            $html.Add("<h3>$([string](Escape-BossKeyHtml -Value $matches[1].Trim()))</h3>")
            continue
        }

        if ($trimmed -match '^##\s+(.+)$') {
            Flush-Paragraph -ParagraphBuffer $paragraph -OutputBuffer $html
            if ($inList) {
                $html.Add("</ul>")
                $inList = $false
            }
            $html.Add("<h2>$([string](Escape-BossKeyHtml -Value $matches[1].Trim()))</h2>")
            continue
        }

        if ($trimmed -match '^#\s+(.+)$') {
            Flush-Paragraph -ParagraphBuffer $paragraph -OutputBuffer $html
            if ($inList) {
                $html.Add("</ul>")
                $inList = $false
            }
            $html.Add("<h1>$([string](Escape-BossKeyHtml -Value $matches[1].Trim()))</h1>")
            continue
        }

        if ($trimmed -match '^[-*]\s+(.+)$') {
            Flush-Paragraph -ParagraphBuffer $paragraph -OutputBuffer $html
            if (-not $inList) {
                $html.Add("<ul>")
                $inList = $true
            }
            $html.Add("<li>$([string](Escape-BossKeyHtml -Value $matches[1].Trim()))</li>")
            continue
        }

        if ($trimmed -match '^\d+\.\s+(.+)$') {
            Flush-Paragraph -ParagraphBuffer $paragraph -OutputBuffer $html
            if (-not $inList) {
                $html.Add("<ul>")
                $inList = $true
            }
            $html.Add("<li>$([string](Escape-BossKeyHtml -Value $matches[1].Trim()))</li>")
            continue
        }

        $paragraph.Add($trimmed)
    }

    Flush-Paragraph -ParagraphBuffer $paragraph -OutputBuffer $html
    if ($inList) {
        $html.Add("</ul>")
    }

    return ($html -join "`n").Trim()
}

function Normalize-BossKeyDecision {
    param([string]$Value)

    $normalized = ([string]$Value).Trim().ToLowerInvariant()
    switch ($normalized) {
        "approve" { return "approve" }
        "approved" { return "approve" }
        "revise" { return "revise" }
        "revision" { return "revise" }
        "hold" { return "hold" }
        "reject" { return "reject" }
        default { return "hold" }
    }
}

function Round-BossKeyPrice {
    param([decimal]$Value)

    if ($Value -le 0) {
        return 0
    }

    return [math]::Round(($Value / 250), 0, [System.MidpointRounding]::AwayFromZero) * 250
}

function Format-BossKeyDisplayDate {
    param([datetime]$Value)

    return $Value.ToString("dddd, MMMM d, yyyy h:mm tt")
}

function Get-BossKeyBusyIntervals {
    param([string]$BusyCsvFile)

    $busyRows = Import-BossKeyCsv -PathValue $BusyCsvFile
    $intervals = New-Object System.Collections.Generic.List[object]

    foreach ($row in $busyRows) {
        $start = $null
        $end = $null
        try { $start = [datetime]$row.start } catch { $start = $null }
        try { $end = [datetime]$row.end } catch { $end = $null }

        if ($null -eq $start -or $null -eq $end) {
            continue
        }
        if ($end -le $start) {
            continue
        }

        $intervals.Add([pscustomobject]@{
            start = $start
            end = $end
            title = [string]$row.title
        })
    }

    return $intervals.ToArray()
}

function Get-BossKeyOpenSlots {
    param(
        [datetime]$StartDate,
        [object[]]$BusyIntervals,
        [int]$DaysAhead = 7,
        [int]$SlotMinutes = 30,
        [int]$SlotCount = 3,
        [string]$DayStart = "09:30",
        [string]$DayEnd = "15:30"
    )

    $results = New-Object System.Collections.Generic.List[object]
    $slotSpan = [TimeSpan]::FromMinutes($SlotMinutes)
    $scanDate = $StartDate.Date

    for ($dayIndex = 0; $dayIndex -lt $DaysAhead -and $results.Count -lt $SlotCount; $dayIndex++) {
        $candidateDay = $scanDate.AddDays($dayIndex)
        if ($candidateDay.DayOfWeek -in @([System.DayOfWeek]::Saturday, [System.DayOfWeek]::Sunday)) {
            continue
        }

        $windowStart = [datetime]::ParseExact(
            ("{0} {1}" -f $candidateDay.ToString("yyyy-MM-dd"), $DayStart),
            "yyyy-MM-dd HH:mm",
            $null
        )
        $windowEnd = [datetime]::ParseExact(
            ("{0} {1}" -f $candidateDay.ToString("yyyy-MM-dd"), $DayEnd),
            "yyyy-MM-dd HH:mm",
            $null
        )

        $cursor = $windowStart
        while ($cursor.Add($slotSpan) -le $windowEnd -and $results.Count -lt $SlotCount) {
            if ($cursor -lt $StartDate) {
                $cursor = $cursor.AddMinutes(15)
                continue
            }

            $candidateEnd = $cursor.Add($slotSpan)
            $overlap = $BusyIntervals | Where-Object {
                $_.start -lt $candidateEnd -and $_.end -gt $cursor
            } | Sort-Object end | Select-Object -First 1

            if ($null -eq $overlap) {
                $results.Add([pscustomobject]@{
                    start = $cursor
                    end = $candidateEnd
                })
                $cursor = $candidateEnd.AddMinutes(15)
            } else {
                $cursor = ([datetime]$overlap.end).AddMinutes(15)
            }
        }
    }

    return $results.ToArray()
}
