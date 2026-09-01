with quelle as (
    select id as vorgang_id, raw_json
    from {{ source('dip_raw', 'vorgang') }}
    where raw_json -> '$.sachgebiet' is not null
)

select
    vorgang_id,
    unnest(cast(raw_json -> '$.sachgebiet' as varchar[])) as sachgebiet
from quelle
