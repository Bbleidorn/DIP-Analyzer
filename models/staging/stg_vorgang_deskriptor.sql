with quelle as (
    select id as vorgang_id, raw_json
    from {{ source('dip_raw', 'vorgang') }}
    where raw_json -> '$.deskriptor' is not null
),

entpackt as (
    select
        vorgang_id,
        unnest(cast(raw_json -> '$.deskriptor' as json[])) as element
    from quelle
)

select
    vorgang_id,
    element ->> '$.name' as deskriptor_name,
    element ->> '$.typ' as deskriptor_typ,
    cast(element ->> '$.fundstelle' as boolean) as zentrale_bedeutung
from entpackt
