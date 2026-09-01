with vorgang as (
    select * from {{ ref('stg_vorgang') }}
),

positionen as (
    select
        vorgang_id,
        count(*) as anzahl_vorgangspositionen,
        max(datum) as letzte_position_datum
    from {{ ref('stg_vorgangsposition') }}
    group by vorgang_id
),

verknuepfte_drucksachen as (
    select
        vorgang_id,
        count(distinct fundstelle_id) as anzahl_drucksachen
    from {{ ref('stg_vorgangsposition') }}
    where fundstelle_dokumentart = 'Drucksache'
    group by vorgang_id
),

verknuepfte_plenarprotokolle as (
    select
        vorgang_id,
        count(distinct fundstelle_id) as anzahl_plenarprotokolle
    from {{ ref('stg_vorgangsposition') }}
    where fundstelle_dokumentart = 'Plenarprotokoll'
    group by vorgang_id
),

deskriptoren as (
    select
        vorgang_id,
        string_agg(distinct deskriptor_name, ', ') as deskriptoren
    from {{ ref('stg_vorgang_deskriptor') }}
    group by vorgang_id
),

sachgebiete as (
    select
        vorgang_id,
        string_agg(distinct sachgebiet, ', ') as sachgebiete
    from {{ ref('stg_vorgang_sachgebiet') }}
    group by vorgang_id
)

select
    vorgang.vorgang_id,
    vorgang.titel,
    vorgang.vorgangstyp,
    vorgang.wahlperiode,
    vorgang.beratungsstand,
    vorgang.letztes_dokument_datum,
    vorgang.aktualisiert,
    coalesce(positionen.anzahl_vorgangspositionen, 0) as anzahl_vorgangspositionen,
    positionen.letzte_position_datum,
    coalesce(verknuepfte_drucksachen.anzahl_drucksachen, 0) as anzahl_drucksachen,
    coalesce(verknuepfte_plenarprotokolle.anzahl_plenarprotokolle, 0) as anzahl_plenarprotokolle,
    deskriptoren.deskriptoren,
    sachgebiete.sachgebiete
from vorgang
left join positionen on vorgang.vorgang_id = positionen.vorgang_id
left join verknuepfte_drucksachen on vorgang.vorgang_id = verknuepfte_drucksachen.vorgang_id
left join verknuepfte_plenarprotokolle on vorgang.vorgang_id = verknuepfte_plenarprotokolle.vorgang_id
left join deskriptoren on vorgang.vorgang_id = deskriptoren.vorgang_id
left join sachgebiete on vorgang.vorgang_id = sachgebiete.vorgang_id
