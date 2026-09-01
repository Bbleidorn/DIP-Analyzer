with quelle as (
    select * from {{ source('dip_raw', 'plenarprotokoll') }}
)

select
    id as plenarprotokoll_id,
    cast(aktualisiert as timestamp) as aktualisiert,
    dokumentnummer,
    cast(datum as date) as datum,
    trim(regexp_replace(raw_json ->> '$.titel', '[\n\r]+', ' ', 'g')) as titel,
    raw_json ->> '$.herausgeber' as herausgeber,
    raw_json ->> '$.fundstelle.pdf_url' as pdf_url
from quelle
