with quelle as (
    select id as vorgangsposition_id, vorgang_id, raw_json
    from {{ source('dip_raw', 'vorgangsposition') }}
    where (raw_json -> '$.urheber') is not null
),

entpackt as (
    select
        vorgangsposition_id,
        vorgang_id,
        unnest(cast(raw_json -> '$.urheber' as json[])) as element
    from quelle
)

select
    vorgangsposition_id,
    vorgang_id,
    element ->> '$.bezeichnung' as bezeichnung,
    element ->> '$.titel' as titel,
    element ->> '$.rolle' as rolle,
    cast(element ->> '$.einbringer' as boolean) as ist_einbringer
from entpackt