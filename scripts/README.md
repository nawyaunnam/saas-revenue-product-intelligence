Operational commands are provided through the installed `saas` CLI. No embedded credentials are needed.

- `saas generate`: deterministic source extraction, validation, deduplication and immutable landing.
- `saas load`: transactionally load the newest batch; `--batch` chooses an explicit manifest directory.
- `saas build`: run dbt models and tests.
- `saas export`: export BI input CSVs and executive HTML.
- `saas demo`: all four steps for local development.
