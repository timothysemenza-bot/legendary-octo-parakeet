param(
    [ValidateSet("Bootstrap", "HydrateQueues", "PersistReviewState")]
    [string]$Mode = "HydrateQueues",
    [string]$RelationshipQueueFile = "marketing-agents/data/boss_key_relationship_queue.csv",
    [string]$ConversationMemoryFile = "marketing-agents/data/boss_key_conversation_memory.csv",
    [string]$KnowledgeBaseFile = "marketing-agents/data/boss_key_competitive_kb.csv",
    [string]$ProposalQueueFile = "marketing-agents/data/boss_key_preconsult_proposals.csv"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$proposalOpsRoot = Join-Path $repoRoot "proposal-ops"
$modeValue = switch ($Mode) {
    "Bootstrap" { "bootstrap" }
    "PersistReviewState" { "persist-review-state" }
    default { "hydrate-queues" }
}

$scriptArgs = @(
    "--mode", $modeValue,
    "--relationship-file", $RelationshipQueueFile,
    "--conversation-file", $ConversationMemoryFile,
    "--knowledge-file", $KnowledgeBaseFile,
    "--proposal-file", $ProposalQueueFile
)

Push-Location $proposalOpsRoot
try {
    python -m alembic upgrade head | Out-Null
    & python ".\tools\sync_boss_key_growth_os.py" @scriptArgs
} finally {
    Pop-Location
}
