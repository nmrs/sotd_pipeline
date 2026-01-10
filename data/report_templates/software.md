# Lather Log {{month_year}}

**Total Shaves:** {{total_shaves}}
**Unique Shavers:** {{unique_shavers}}

Welcome to your SOTD Lather Log for {{month_year}}

* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during the month of {{month_year}} were analyzed to produce this report. Collectively, these shavers used {{unique_soaps}} distinct soaps from {{unique_brands}} distinct brands. {{total_samples}} of those shaves used samples of {{unique_sample_soaps}} unique soaps.

## Observations

* [Observations will be generated based on data analysis]

## Notes & Caveats

* Tables show all entries with 5 or more shaves to provide comprehensive coverage without artificial row limits.

* The unique user column shows the number of different users who used a given brand/soap/etc in the month.

* The Brand Diversity table details the number of distinct soaps used during the month from that particular brand, showing all brands with 5+ unique soaps.

* The change Δ vs columns show how an item has moved up or down the rankings since that month. = means no change in position, up or down arrows indicate how many positions up or down the rankings an item has moved compared to that month. n/a means the item was not present in that month.

## Soap Brands

{{tables.soap-makers|shaves:5|deltas:true}}

## Soaps

{{tables.soaps|shaves:5|columns:rank, name=soap, shaves, unique_users|deltas:true|wsdb:true}}

## Brand Diversity

{{tables.brand-diversity|unique_soaps:5|deltas:true}}

## Soap Diversity by User

{{tables.user-soap-brand-scent-diversity|ranks:40|columns:rank, user, unique_combinations=unique_soaps, shaves, avg_shaves_per_combination=avg_shaves_per_soap|deltas:true}}

## Top Shavers

{{tables.users|ranks:30|columns:rank, user, shaves, missed_days|deltas:true}}
