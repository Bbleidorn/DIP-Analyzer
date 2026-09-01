with quelle as (
    select * from {{ source('dip_raw', 'drucksache') }}
)

select
    id as drucksache_id,
    cast(aktualisiert as timestamp) as aktualisiert,
    dokumentnummer,
    cast(datum as date) as datum,
    trim(regexp_replace(raw_json ->> '$.titel', '[\n\r]+', ' ', 'g')) as titel,
    raw_json ->> '$.drucksachetyp' as drucksachetyp,
    raw_json ->> '$.herausgeber' as herausgeber,
    cast(raw_json ->> '$.autoren_anzahl' as integer) as autoren_anzahl,
    raw_json ->> '$.fundstelle.pdf_url' as pdf_url
from quelle
