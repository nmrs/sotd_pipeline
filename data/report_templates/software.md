# Software Report - {{month_year}}

**Total Shaves:** {{total_shaves}}
**Unique Shavers:** {{unique_shavers}}

Welcome to your SOTD Lather Log for {{month_year}}

* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during the month of {{month_year}} were analyzed to produce this report. Collectively, these shavers used {{unique_soaps}} distinct soaps from {{unique_brands}} distinct brands. {{total_samples}} of those shaves were marked (sample).

## Observations

* [Observations will be generated based on data analysis]

## Notes & Caveats

* Tables show all entries with 5 or more shaves to provide comprehensive coverage without artificial row limits.

* The unique user column shows the number of different users who used a given brand/soap/etc in the month.

* The Brand Diversity table details the number of distinct soaps used during the month from that particular brand, showing all brands with 5+ unique soaps.

* The change Δ vs columns show how an item has moved up or down the rankings since that month. = means no change in position, up or down arrows indicate how many positions up or down the rankings an item has moved compared to that month. n/a means the item was not present in that month.

## Soap Brands

{{tables.soap-makers|ranks:50|deltas:true}}

## Soaps

{{tables.soaps|ranks:50|columns:rank, name=soap, shaves, unique_users}}

## Brand Diversity

{{tables.brand-diversity|rows:30|deltas:true}}

### Soap Diversity by User
{{tables.user-soap-brand-scent-diversity|rows:50}}

## Top Shavers

{{tables.users|rows:50|deltas:true}}

### Soap Brand Diversity by User
{{tables.user-soap-brand-diversity|rows:50}}
