# Annual Software Report - {{year}}

Welcome to your Annual SOTD Lather Log for {{year}}

## Annual Summary

* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during {{year}} were analyzed to produce this report.
* Data includes {{included_months}} months of the year.
{% if missing_months > 0 %}
* Note: {{missing_months}} months were missing from the data set.
{% endif %}

## Notes & Caveats

* I only show the top n results per category to keep the tables readable and avoid max post length issues.

* The unique user column shows the number of different users who used a given brand/soap/etc during the year.

* The Brand Diversity table details the number of distinct soaps used during the year from that particular brand.

* The change Δ vs columns show how an item has moved up or down the rankings since the previous year. = means no change in position, up or down arrows indicate how many positions up or down the rankings an item has moved compared to the previous year. n/a means the item was not present in the previous year.

## Soap Makers

{{tables.soap-makers}}

## Soaps

{{tables.soaps}}

## Brand Diversity

{{tables.brand-diversity}}

## Top Shavers

{{tables.top-shavers}}
