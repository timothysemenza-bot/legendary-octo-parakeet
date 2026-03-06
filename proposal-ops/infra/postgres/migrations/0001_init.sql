-- ProposalOps initial schema
-- Enforces tenant scoping across all core tables.

create extension if not exists "uuid-ossp";
create extension if not exists "pgcrypto";

create table if not exists clients (
  id text primary key,
  name text not null,
  status text not null default 'ACTIVE',
  isolation_tier text not null default 'SHARED',
  config_version text not null default 'v1',
  created_at timestamptz not null default now()
);

create table if not exists workspaces (
  id text primary key,
  client_id text not null references clients(id),
  name text not null,
  timezone text not null default 'UTC',
  created_at timestamptz not null default now()
);

create table if not exists opportunities (
  id text primary key,
  client_id text not null references clients(id),
  workspace_id text not null references workspaces(id),
  title text not null,
  buyer text not null,
  due_date date not null,
  stage text not null,
  status text not null default 'IN_PROGRESS',
  owner_id text not null,
  priority text not null default 'MEDIUM',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists solicitations (
  id text primary key,
  client_id text not null references clients(id),
  workspace_id text not null references workspaces(id),
  opportunity_id text not null references opportunities(id),
  source text not null,
  raw_text_ref text not null,
  version integer not null default 1,
  created_at timestamptz not null default now()
);

create table if not exists requirements (
  id text primary key,
  client_id text not null references clients(id),
  workspace_id text not null references workspaces(id),
  solicitation_id text not null references solicitations(id),
  req_code text not null,
  text text not null,
  atomic_index integer not null,
  category text not null default 'GENERAL',
  mandatory boolean not null default true,
  source_locator jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists compliance_matrix_rows (
  id text primary key,
  client_id text not null references clients(id),
  workspace_id text not null references workspaces(id),
  opportunity_id text not null references opportunities(id),
  requirement_id text not null references requirements(id),
  response_section_id text,
  status text not null default 'UNMAPPED',
  owner_id text,
  evidence_refs jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists gate_decisions (
  id text primary key,
  client_id text not null references clients(id),
  workspace_id text not null references workspaces(id),
  opportunity_id text not null references opportunities(id),
  gate_code text not null,
  decision text not null,
  decider_id text not null,
  rationale text not null,
  rework_instructions jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists submission_packages (
  id text primary key,
  client_id text not null references clients(id),
  workspace_id text not null references workspaces(id),
  opportunity_id text not null references opportunities(id),
  artifact_refs jsonb not null default '[]'::jsonb,
  checksum text not null,
  authorized_by text not null,
  submitted_at timestamptz not null default now()
);

create table if not exists lessons_learned_records (
  id text primary key,
  client_id text not null references clients(id),
  workspace_id text not null references workspaces(id),
  opportunity_id text not null references opportunities(id),
  outcome text not null,
  root_causes jsonb not null default '[]'::jsonb,
  actions jsonb not null default '[]'::jsonb,
  knowledge_promotions jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists audit_events (
  id uuid primary key default gen_random_uuid(),
  client_id text not null references clients(id),
  workspace_id text not null references workspaces(id),
  opportunity_id text,
  actor_type text not null check (actor_type in ('human', 'agent', 'system')),
  actor_id text not null,
  action text not null,
  reason_code text,
  before_state jsonb,
  after_state jsonb,
  linked_artifacts jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_opportunities_tenant on opportunities(client_id, workspace_id);
create index if not exists idx_requirements_tenant on requirements(client_id, workspace_id);
create index if not exists idx_cmr_tenant on compliance_matrix_rows(client_id, workspace_id);
create index if not exists idx_gate_tenant on gate_decisions(client_id, workspace_id);
create index if not exists idx_submission_tenant on submission_packages(client_id, workspace_id);
create index if not exists idx_llr_tenant on lessons_learned_records(client_id, workspace_id);
create index if not exists idx_audit_tenant on audit_events(client_id, workspace_id, created_at desc);

-- Placeholder policy enablement. Service role + RLS policies are added in migration 0002.
alter table opportunities enable row level security;
alter table requirements enable row level security;
alter table compliance_matrix_rows enable row level security;
alter table gate_decisions enable row level security;
alter table submission_packages enable row level security;
alter table lessons_learned_records enable row level security;
alter table audit_events enable row level security;
