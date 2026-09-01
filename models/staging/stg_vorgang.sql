with quelle as (
    select * from {{ source('dip_raw', 'vorgang') }}
)

select
    id as vorgang_id,
    cast(aktualisiert as timestamp) as aktualisiert,
    cast(datum as date) as letztes_dokument_datum,
    trim(regexp_replace(titel, '[\n\r]+', ' ', 'g')) as titel,
    trim(regexp_replace(raw_json ->> '$.abstract', '[\n\r]+', ' ', 'g')) as abstract,
    raw_json ->> '$.vorgangstyp' as vorgangstyp,
    cast(raw_json ->> '$.wahlperiode' as integer) as wahlperiode,
    raw_json ->> '$.beratungsstand' as beratungsstand,
    raw_json ->> '$.gesta' as gesta_nummer
from quelle
