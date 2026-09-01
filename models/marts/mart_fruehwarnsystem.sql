{{ config(materialized='view') }}

with letzte_positionen as (
    select *
    from {{ ref('stg_vorgangsposition') }}
    where aktualisiert >= current_date - interval 3 day
),

urheber_aggregiert as (
    select
        vorgangsposition_id,
        string_agg(distinct bezeichnung, ', ') as urheber
    from {{ ref('stg_vorgangsposition_urheber') }}
    group by vorgangsposition_id
),

beschluesse_aggregiert as (
    select
        vorgangsposition_id,
        string_agg(
            distinct beschlusstenor || coalesce(' (' || mehrheit || ')', ''), '; '
        ) as beschluesse
    from {{ ref('stg_vorgangsposition_beschlussfassung') }}
    group by vorgangsposition_id
)

select
    v.vorgang_id,
    v.titel as vorgang_titel,
    v.vorgangstyp,
    v.beratungsstand,
    v.wahlperiode,
    lp.vorgangsposition_id,
    lp.vorgangsposition_titel,
    lp.datum as position_datum,
    lp.aktualisiert as position_aktualisiert,
    lp.zuordnung,
    ua.urheber,
    ba.beschluesse
from letzte_positionen as lp
inner join {{ ref('stg_vorgang') }} as v on lp.vorgang_id = v.vorgang_id
left join urheber_aggregiert as ua on lp.vorgangsposition_id = ua.vorgangsposition_id
left join beschluesse_aggregiert as ba on lp.vorgangsposition_id = ba.vorgangsposition_id
order by lp.aktualisiert desc