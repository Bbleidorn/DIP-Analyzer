with quelle as (
    select * from {{ source('dip_raw', 'vorgangsposition') }}
)

select
    id as vorgangsposition_id,
    vorgang_id,
    cast(aktualisiert as timestamp) as aktualisiert,
    cast(datum as date) as datum,
    raw_json ->> '$.vorgangsposition' as vorgangsposition_titel,
    raw_json ->> '$.zuordnung' as zuordnung,
    cast(raw_json ->> '$.gang' as boolean) as ist_wichtiger_schritt,
    raw_json ->> '$.fundstelle.id' as fundstelle_id,
    raw_json ->> '$.fundstelle.dokumentart' as fundstelle_dokumentart,
    cast(raw_json ->> '$.aktivitaet_anzahl' as integer) as aktivitaeten_anzahl
from quelle
