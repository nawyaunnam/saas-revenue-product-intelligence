-- Defensive deduplication also protects cloud CDC replays.
select event_id, user_id, account_id, occurred_at, event_name, ingested_at
from (
    select *, row_number() over (partition by event_id order by ingested_at desc) as arrival_rank
    from {{ source('raw', 'events') }}
) ranked where arrival_rank = 1
