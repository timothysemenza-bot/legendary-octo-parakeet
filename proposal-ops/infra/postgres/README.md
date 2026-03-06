# Postgres Migrations

## Migrations
- `migrations/0001_init.sql` core tenant-scoped schema and audit ledger

## Notes
- Every operational table includes `client_id` and `workspace_id`.
- RLS is enabled in `0001`; explicit policies should be added in `0002`.
