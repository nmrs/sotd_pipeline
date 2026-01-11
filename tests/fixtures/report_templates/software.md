# Software Report - {{month_year}}

**Total Shaves:** {{total_shaves}}
**Unique Shavers:** {{unique_shavers}}

Welcome to your SOTD Lather Log for {{month_year}}

* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during the month of {{month_year}} were analyzed to produce this report. Collectively, these shavers used {{unique_soaps}} distinct soaps from {{unique_brands}} distinct brands.

## Observations

* [Observations will be generated based on data analysis]

## Notes & Caveats

* I only show the top n results per category to keep the tables readable and avoid max post length issues.

* The unique user column shows the number of different users who used a given brand/soap/etc in the month.

* The Brand Diversity table details the number of distinct soaps used during the month from that particular brand.

* The change Δ vs columns show how an item has moved up or down the rankings since that month. = means no change in position, up or down arrows indicate how many positions up or down the rankings an item has moved compared to that month. n/a means the item was not present in that month.

## Soap Makers

{{tables.soap_makers}}

## Soaps

{{tables.soaps}}

## Brand Diversity

{{tables.brand_diversity}}

## Top Shavers

{{tables.users}}

## Most Boring Shaver

{{tables.user-soap-brand-scent-diversity|ranks:40|columns:rank, user, unique_combinations=unique_soaps asc, shaves, avg_shaves_per_combination=avg_shaves_per_soap|deltas:true}}
