param(
    [string]$QueueFile = "marketing-agents/data/boss_key_content_queue.csv",
    [string]$SiteRoot = "boss-key-website",
    [string]$InsightsIndex = "boss-key-website/insights/index.html",
    [string]$FeedFile = "boss-key-website/insights/feed.xml",
    [string]$BaseUrl = "https://bosskeyops.com"
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "boss-key-growth-os-helpers.ps1")

$queuePropertyOrder = @(
    "content_id",
    "created_date",
    "cadence_type",
    "source_id",
    "source_type",
    "source_path",
    "source_title",
    "title",
    "slug",
    "summary",
    "article_draft_path",
    "article_output_path",
    "company_linkedin_draft_path",
    "personal_linkedin_draft_path",
    "scheduled_publish_date",
    "owner_decision",
    "review_status",
    "website_status",
    "rss_status",
    "linkedin_company_status",
    "linkedin_personal_status",
    "published_date",
    "notes"
)

function Get-BossKeyArticleMetaDate {
    param([pscustomobject]$Row)

    foreach ($field in @("published_date", "scheduled_publish_date", "created_date")) {
        $value = [string]$Row.$field
        if ([string]::IsNullOrWhiteSpace($value)) {
            continue
        }
        try {
            return [datetime]$value
        } catch {
            continue
        }
    }

    return Get-Date
}

function Get-BossKeyArticlePageHtml {
    param(
        [pscustomobject]$Row,
        [string]$BodyHtml
    )

    $publishDate = Get-BossKeyArticleMetaDate -Row $Row
    $label = if ([string]::IsNullOrWhiteSpace($Row.cadence_type)) { "Insight" } else { ([string]$Row.cadence_type).Replace("_", " ") }
    $summaryHtml = Escape-BossKeyHtml -Value ([string]$Row.summary)
    $titleHtml = Escape-BossKeyHtml -Value ([string]$Row.title)

    return @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>$titleHtml | Boss Key LLC</title>
  <meta name="description" content="$summaryHtml">
  <link rel="icon" type="image/svg+xml" href="../assets/logos/brand/boss-key-logo-refined.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --ink: #f4f6f8;
      --paper: #091018;
      --line: #263445;
      --soft: #c4cdd8;
      --muted: #94a2b3;
      --signal: #0f8b7c;
      --accent: #d4a35f;
      --panel: #101924;
      --panel-2: #0d141d;
      --max: 960px;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 15% 5%, rgba(15, 139, 124, 0.22) 0%, rgba(15, 139, 124, 0) 34%),
        linear-gradient(155deg, #111923 0%, #061018 100%);
      font-family: "Manrope", "Segoe UI", sans-serif;
      line-height: 1.65;
    }
    a { color: inherit; text-decoration: none; }
    .wrap { width: min(var(--max), 92vw); margin: 0 auto; }
    header {
      position: sticky;
      top: 0;
      z-index: 20;
      border-bottom: 1px solid #1c2834;
      background: rgba(9, 16, 24, 0.86);
      backdrop-filter: blur(8px);
      padding: 16px 0;
    }
    .nav {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }
    .brand {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
    }
    .brand img { width: 32px; height: 32px; display: block; }
    .links {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .links a {
      border: 1px solid #304152;
      border-radius: 999px;
      padding: 6px 11px;
      background: #111a24;
      color: var(--soft);
      font-size: 0.84rem;
      font-weight: 700;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 11px 15px;
      border-radius: 12px;
      border: 1px solid transparent;
      font-weight: 700;
    }
    .btn-primary {
      background: linear-gradient(145deg, var(--signal), #0a6f63);
      color: #f8fffe;
    }
    .btn-secondary {
      background: #121c26;
      color: #ebf1f6;
      border-color: #324153;
    }
    main { padding: 26px 0 42px; }
    section {
      margin: 14px 0;
      border: 1px solid var(--line);
      border-radius: 20px;
      background: linear-gradient(165deg, rgba(16, 25, 36, 0.98), rgba(10, 15, 22, 0.98));
      padding: 26px;
    }
    h1, h2, h3 {
      font-family: "Fraunces", Georgia, serif;
      line-height: 1.1;
      letter-spacing: -0.02em;
      margin: 0 0 12px;
    }
    h1 { font-size: clamp(2.2rem, 4.7vw, 3.8rem); }
    h2 { font-size: clamp(1.4rem, 2.8vw, 2rem); margin-top: 28px; }
    h3 { font-size: 1.1rem; margin-top: 22px; }
    p { margin: 0 0 14px; color: var(--soft); }
    ul { margin: 0 0 16px; padding-left: 20px; color: #dbe2eb; }
    li { margin: 8px 0; }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 14px;
      padding: 6px 10px;
      border: 1px solid rgba(15, 139, 124, 0.36);
      border-radius: 999px;
      background: rgba(15, 139, 124, 0.12);
      color: #d9fff9;
      font-size: 0.76rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .lede {
      font-size: 1.08rem;
      color: #eaf0f5;
      max-width: 52rem;
    }
    .meta {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 18px;
    }
    .meta-card {
      border: 1px solid #2f4051;
      border-radius: 14px;
      background: #101821;
      padding: 14px;
    }
    .meta-card strong {
      display: block;
      margin-bottom: 4px;
      font-size: 0.82rem;
      color: #fff;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .content h1 { display: none; }
    .cta {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 18px;
    }
    footer {
      border-top: 1px solid var(--line);
      color: #9eabb9;
      font-size: 0.88rem;
      padding: 16px 0 26px;
    }
    @media (max-width: 880px) {
      .meta { grid-template-columns: 1fr; }
      .cta .btn { width: 100%; }
    }
  </style>
</head>
<body>
<header>
  <div class="wrap nav">
    <a class="brand" href="../index.html"><img src="../assets/logos/brand/boss-key-logo-refined.svg" alt=""><span>Boss Key LLC</span></a>
    <nav class="links" aria-label="Main navigation">
      <a href="../services.html">Services</a>
      <a href="../facilities.html">Facilities</a>
      <a href="./index.html">Insights</a>
      <a href="../proof.html">Proof</a>
      <a href="../contact.html">Contact</a>
    </nav>
    <a class="btn btn-primary schedule-cta" href="#">Book briefing</a>
  </div>
</header>
<main class="wrap">
  <section>
    <span class="eyebrow">$([string](Escape-BossKeyHtml -Value $label))</span>
    <h1>$titleHtml</h1>
    <p class="lede">$summaryHtml</p>
    <div class="meta">
      <div class="meta-card">
        <strong>Published</strong>
        <span>$($publishDate.ToString("MMMM d, yyyy"))</span>
      </div>
      <div class="meta-card">
        <strong>Workflow</strong>
        <span>Review-first website publishing with LinkedIn company sharing handled through RSS after approval.</span>
      </div>
    </div>
    <div class="cta">
      <a class="btn btn-primary schedule-cta" href="#">Book briefing</a>
      <a class="btn btn-secondary" href="../facilities-diagnostic.html">Request the diagnostic</a>
      <a class="btn btn-secondary" href="./feed.xml">Open RSS feed</a>
    </div>
  </section>
  <section class="content">
$BodyHtml
  </section>
</main>
<footer>
  <div class="wrap">Boss Key LLC | Review-first publishing | Insights hub | LinkedIn company sharing via approved RSS</div>
</footer>
<script>
(function(){
  const scheduleFallback='https://calendar.app.google/XXQaukj4evMTLq4E7';
  const calendarScheduleUrl=window.BOSSKEY_SCHEDULE_URL||scheduleFallback;
  document.querySelectorAll('.schedule-cta').forEach(function(link){
    link.href=calendarScheduleUrl;
    link.target='_blank';
    link.rel='noopener noreferrer';
  });
})();
</script>
</body>
</html>
"@
}

$siteRootResolved = Resolve-BossKeyGrowthPath $SiteRoot
$insightsDirResolved = Resolve-BossKeyGrowthPath "boss-key-website/insights"
Ensure-BossKeyGrowthDirectory -PathValue $siteRootResolved
Ensure-BossKeyGrowthDirectory -PathValue $insightsDirResolved

$rows = New-Object System.Collections.Generic.List[object]
foreach ($row in (Import-BossKeyCsv -PathValue $QueueFile)) {
    $working = [ordered]@{}
    foreach ($property in $queuePropertyOrder) {
        $working[$property] = if ($row.PSObject.Properties.Name -contains $property) { [string]$row.$property } else { "" }
    }

    if ($working.website_status -eq "approved") {
        $working.website_status = "published"
        if ([string]::IsNullOrWhiteSpace($working.published_date)) {
            $working.published_date = (Get-Date).ToString("yyyy-MM-dd")
        }
    }

    if ($working.rss_status -eq "approved") {
        $working.rss_status = "published"
    }

    $rows.Add([pscustomobject]$working)
}

$published = @(
    $rows | Where-Object {
        $_.website_status -eq "published" -or $_.rss_status -eq "published"
    } | Sort-Object {
        (Get-BossKeyArticleMetaDate -Row $_)
    } -Descending
)

foreach ($row in $published) {
    if ([string]::IsNullOrWhiteSpace($row.article_draft_path)) {
        continue
    }

    $draftResolved = Resolve-BossKeyGrowthPath $row.article_draft_path
    if (-not (Test-Path $draftResolved)) {
        continue
    }

    $outputResolved = Resolve-BossKeyGrowthPath $row.article_output_path
    $outputDir = Split-Path -Parent $outputResolved
    Ensure-BossKeyGrowthDirectory -PathValue $outputDir

    $markdown = Get-Content -Path $draftResolved -Raw -Encoding UTF8
    $bodyHtml = Convert-BossKeyMarkdownToHtml -Markdown $markdown
    $pageHtml = Get-BossKeyArticlePageHtml -Row $row -BodyHtml $bodyHtml
    $pageHtml | Set-Content -Path $outputResolved -Encoding UTF8
}

$cards = @()
foreach ($row in $published) {
    $publishDate = Get-BossKeyArticleMetaDate -Row $row
    $title = Escape-BossKeyHtml -Value ([string]$row.title)
    $summary = Escape-BossKeyHtml -Value ([string]$row.summary)
    $urlPath = ([string]$row.article_output_path).Replace("boss-key-website\", "").Replace("\", "/")
    $cards += @"
      <article class="card">
        <span class="eyebrow">$([string](Escape-BossKeyHtml -Value (([string]$row.cadence_type).Replace("_", " "))))</span>
        <h2><a href="./$([string](Escape-BossKeyHtml -Value ($row.slug + ".html")))" data-existing-path="$([string](Escape-BossKeyHtml -Value $urlPath))">$title</a></h2>
        <p>$summary</p>
        <div class="meta">
          <span>$($publishDate.ToString("MMMM d, yyyy"))</span>
          <span>Review-first workflow approved</span>
        </div>
      </article>
"@
    if ($urlPath -ne ("insights/" + $row.slug + ".html") -and $urlPath -ne ("insights/" + $row.slug)) {
        $cards[$cards.Count - 1] = $cards[$cards.Count - 1].Replace("./" + $row.slug + ".html", "../" + ($urlPath.Substring("insights/".Length)))
    }
}

$indexHtml = @"
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Insights | Boss Key LLC</title>
  <meta name="description" content="Approved Boss Key insights that can feed the company RSS workflow after owner review.">
  <link rel="icon" type="image/svg+xml" href="../assets/logos/brand/boss-key-logo-refined.svg">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=Manrope:wght@400;500;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --ink: #f5f6f8;
      --paper: #0b1018;
      --line: #253344;
      --soft: #c6cfdb;
      --muted: #97a4b5;
      --signal: #0f8b7c;
      --accent: #d4a35f;
      --max: 1080px;
    }
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      padding: 0;
      color: var(--ink);
      background:
        radial-gradient(circle at 18% 0%, rgba(15, 139, 124, 0.2) 0%, rgba(15, 139, 124, 0) 32%),
        linear-gradient(155deg, #111925 0%, #061018 100%);
      font-family: "Manrope", "Segoe UI", sans-serif;
      line-height: 1.6;
    }
    a { color: inherit; text-decoration: none; }
    .wrap { width: min(var(--max), 92vw); margin: 0 auto; }
    header {
      position: sticky;
      top: 0;
      z-index: 20;
      padding: 16px 0;
      background: rgba(11, 16, 24, 0.84);
      backdrop-filter: blur(8px);
      border-bottom: 1px solid #1c2732;
    }
    .nav {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .brand {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
    }
    .brand img { width: 32px; height: 32px; display: block; }
    .links {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .links a {
      border: 1px solid #304153;
      border-radius: 999px;
      padding: 6px 11px;
      background: #121b25;
      color: var(--soft);
      font-size: 0.85rem;
      font-weight: 700;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 11px 15px;
      border-radius: 12px;
      border: 1px solid transparent;
      font-weight: 700;
    }
    .btn-primary {
      background: linear-gradient(145deg, var(--signal), #0a6f63);
      color: #f7fffe;
    }
    .btn-secondary {
      background: #131c27;
      color: #ebf0f6;
      border-color: #304153;
    }
    main { padding: 26px 0 42px; }
    section {
      margin: 14px 0;
      padding: 24px;
      border: 1px solid var(--line);
      border-radius: 20px;
      background: linear-gradient(165deg, rgba(17, 25, 36, 0.98), rgba(10, 15, 22, 0.98));
    }
    h1, h2 {
      font-family: "Fraunces", Georgia, serif;
      line-height: 1.08;
      letter-spacing: -0.02em;
      margin: 0 0 12px;
    }
    h1 { font-size: clamp(2.3rem, 4.8vw, 4rem); }
    h2 { font-size: clamp(1.35rem, 2.7vw, 2rem); }
    p { margin: 0 0 12px; color: var(--soft); }
    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;
      padding: 6px 10px;
      border-radius: 999px;
      border: 1px solid rgba(15, 139, 124, 0.34);
      background: rgba(15, 139, 124, 0.12);
      color: #ddfff9;
      font-size: 0.76rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }
    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 16px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    .card {
      border: 1px solid #304152;
      border-radius: 16px;
      background: #101822;
      padding: 18px;
    }
    .card h2 a { color: #fff; }
    .meta {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 0.9rem;
    }
    footer {
      border-top: 1px solid var(--line);
      color: #9eadbc;
      font-size: 0.88rem;
      padding: 16px 0 26px;
    }
    @media (max-width: 900px) {
      .grid { grid-template-columns: 1fr; }
      .actions .btn { width: 100%; }
    }
  </style>
</head>
<body>
<header>
  <div class="wrap nav">
    <a class="brand" href="../index.html"><img src="../assets/logos/brand/boss-key-logo-refined.svg" alt=""><span>Boss Key LLC</span></a>
    <nav class="links" aria-label="Main navigation">
      <a href="../services.html">Services</a>
      <a href="../facilities.html">Facilities</a>
      <a href="./index.html">Insights</a>
      <a href="../proof.html">Proof</a>
      <a href="../contact.html">Contact</a>
    </nav>
    <a class="btn btn-primary schedule-cta" href="#">Book briefing</a>
  </div>
</header>
<main class="wrap">
  <section>
    <span class="eyebrow">Boss Key Insights Hub</span>
    <h1>Approved insights that drive the website first and the LinkedIn company feed second.</h1>
    <p>This page only lists content that has cleared owner review. Drafts stay in the internal review packet until you approve them. Once an insight is approved and deployed here, the company-page RSS workflow can share it automatically.</p>
    <div class="actions">
      <a class="btn btn-primary schedule-cta" href="#">Book briefing</a>
      <a class="btn btn-secondary" href="./feed.xml">Open RSS feed</a>
      <a class="btn btn-secondary" href="../contact.html">Request a diagnostic</a>
    </div>
  </section>
  <section>
    <h2>Published insights</h2>
    <div class="grid">
$($cards -join "`n")
    </div>
  </section>
</main>
<footer>
  <div class="wrap">Boss Key LLC | Public insights hub | RSS-driven company sharing after owner-approved publishing</div>
</footer>
<script>
(function(){
  const scheduleFallback='https://calendar.app.google/XXQaukj4evMTLq4E7';
  const calendarScheduleUrl=window.BOSSKEY_SCHEDULE_URL||scheduleFallback;
  document.querySelectorAll('.schedule-cta').forEach(function(link){
    link.href=calendarScheduleUrl;
    link.target='_blank';
    link.rel='noopener noreferrer';
  });
})();
</script>
</body>
</html>
"@

$indexResolved = Resolve-BossKeyGrowthPath $InsightsIndex
$feedResolved = Resolve-BossKeyGrowthPath $FeedFile
$indexDir = Split-Path -Parent $indexResolved
$feedDir = Split-Path -Parent $feedResolved
Ensure-BossKeyGrowthDirectory -PathValue $indexDir
Ensure-BossKeyGrowthDirectory -PathValue $feedDir

$indexHtml | Set-Content -Path $indexResolved -Encoding UTF8

$feedItems = foreach ($row in $published) {
    $publishDate = (Get-BossKeyArticleMetaDate -Row $row).ToUniversalTime().ToString("r")
    $pathValue = ([string]$row.article_output_path).Replace("boss-key-website\", "").Replace("\", "/")
    $linkPath = if ($pathValue.StartsWith("insights/")) { $pathValue } else { "insights/{0}.html" -f $row.slug }
    $fullLink = "{0}/{1}" -f $BaseUrl.TrimEnd('/'), $linkPath.TrimStart('/')
@"
  <item>
    <title>$([string](Escape-BossKeyXml -Value $row.title))</title>
    <link>$([string](Escape-BossKeyXml -Value $fullLink))</link>
    <guid isPermaLink="true">$([string](Escape-BossKeyXml -Value $fullLink))</guid>
    <pubDate>$publishDate</pubDate>
    <description>$([string](Escape-BossKeyXml -Value $row.summary))</description>
  </item>
"@
}

$feedXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Boss Key Insights</title>
    <link>$([string](Escape-BossKeyXml -Value ($BaseUrl.TrimEnd('/') + "/insights/")))</link>
    <description>Owner-approved Boss Key insights for website publishing and LinkedIn company-page RSS sharing.</description>
    <lastBuildDate>$((Get-Date).ToUniversalTime().ToString("r"))</lastBuildDate>
    <language>en-us</language>
$($feedItems -join "`n")
  </channel>
</rss>
"@

$feedXml | Set-Content -Path $feedResolved -Encoding UTF8
Export-BossKeyCsv -Rows ($rows.ToArray()) -PathValue $QueueFile -PropertyOrder $queuePropertyOrder

Write-Output ("Built Boss Key insights site. Published items: {0}. Index: {1}. Feed: {2}" -f $published.Count, $InsightsIndex, $FeedFile)
