# Annual Software Report - {{year}}

Welcome to your Annual SOTD Lather Log for {{year}}

## Annual Summary

* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during {{year}} were analyzed to produce this report.
* Data includes {{included_months}} months of the year.
{{missing_months_note}}

## Notes & Caveats

* Tables show all entries with 5 or more shaves to provide comprehensive coverage without artificial row limits.

* The unique user column shows the number of different users who used a given brand/soap/etc during the year.

* The Brand Diversity table details the number of distinct soaps used during the year from that particular brand, showing all brands with 5+ unique soaps.

* The change Δ vs columns show how an item has moved up or down the rankings since the previous year. = means no change in position, up or down arrows indicate how many positions up or down the rankings an item has moved compared to the previous year. n/a means the item was not present in the previous year.

## Soap Brands

{{tables.soap-makers|shaves:50|columns:rank, name=brand, shaves, unique_users|deltas:true|deltas:true}}

## Soaps

{{tables.soaps|ranks:100|columns:rank, name=soap, shaves, unique_users|deltas:true|wsdb:true}}

## Brand Diversity

{{tables.brand-diversity|unique_soaps:10|deltas:true}}

## Soap Diversity by User

{{tables.user-soap-brand-scent-diversity|ranks:20|columns:rank, user, unique_combinations=unique_soaps, shaves, avg_shaves_per_combination=avg_shaves_per_soap|deltas:true}}

## Most Boring Shaver

{{tables.user-soap-brand-scent-diversity|ranks:20|columns:rank, user, hhi=boring score desc, effective_soaps, unique_combinations=unique_soaps, shaves|deltas:true|shaves:50}}
