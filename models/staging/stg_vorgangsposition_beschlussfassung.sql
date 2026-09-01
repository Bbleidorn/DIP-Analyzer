with quelle as (
    select id as vorgangsposition_id, vorgang_id, raw_json
    from {{ source('dip_raw', 'vorgangsposition') }}
    where (raw_json -> '$.beschlussfassung') is not null
),

entpackt as (
    select
        vorgangsposition_id,
        vorgang_id,
        unnest(cast(raw_json -> '$.beschlussfassung' as json[])) as element
    from quelle
)

select
    vorgangsposition_id,
    vorgang_id,
    element ->> '$.beschlusstenor' as beschlusstenor,
    element ->> '$.abstimmungsart' as abstimmungsart,
    element ->> '$.mehrheit' as mehrheit,
    element ->> '$.abstimm_ergebnis_bemerkung' as abstimm_ergebnis_bemerkung
from entpackt