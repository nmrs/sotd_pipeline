# Annual Hardware Report - {{year}}

Welcome to your Annual SOTD Hardware Report for {{year}}

## Annual Summary

* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during {{year}} were analyzed to produce this report, for an average of {{avg_shaves_per_user}} (median {{median_shaves_per_user}}) shaves per user.

## Observations

* [Observations will be generated based on data analysis]

## Notes & Caveats

* Most tables are row-limited to keep them readable and avoid max post length issues. If the final row is part of a tie, the entire tied group is included in the report.

* "Other" in the Blade Format table includes vintage reusable blades (including Rolls, Valet Auto Strop, and old-style lather catchers with wedge blades) as well as other antique proprietary blade formats (e.g. Enders Speed Blade)

* Blades recorded as just 'GEM' will be matched to 'Personna GEM PTFE' per guidance [here](https://www.reddit.com/r/Wetshaving/comments/19a43q7/comment/kil95r8/)

* The Personna name is [going away](https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://www.badgerandblade.com/forum/threads/what-do-you-know-about-this-personna-no-longer-exists.647703/&ved=2ahUKEwiyi4n7pPKFAxXeLtAFHfNVDz8QFnoECAQQAQ&usg=AOvVaw38QYgjzknuIIIV94b6VDP5) for blades manufactured in the USA, but the majority of entries are still coming in under Personna, so I am sticking to that for the time being. Once more than 50% of the entries come in under the new names, I will reverse this and map any old Personna entries to the new name.

* The Δ vs columns show how an item has moved up or down the rankings since that month. = means no change in position, up or down arrows indicate how many positions up or down the rankings an item has moved compared to that month. n/a means the item was not present in that month.

## Razor Formats

{{tables.razor-formats|deltas:true}}

## Razors

{{tables.razors|ranks:50|columns:rank, name=razor, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Razor Manufacturers

{{tables.razor-manufacturers|ranks:30|columns:rank, name, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Blades

{{tables.blades|ranks:50|columns:rank, name=blade, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Brushes

{{tables.brushes|ranks:50|columns:rank, name=brush, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Brush Handle Makers

{{tables.brush-handle-makers|ranks:30|columns:rank, name, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Brush Knot Makers

{{tables.brush-knot-makers|ranks:30|columns:rank, name=Knot Maker, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Knot Fibers

{{tables.brush-fibers|columns:rank, name, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Knot Sizes

{{tables.brush-knot-sizes|columns:rank, name, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Blackbird Plates

{{tables.blackbird-plates|columns:rank, name, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Christopher Bradley Plates

{{tables.christopher-bradley-plates|columns:rank, name, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Game Changer Plates

{{tables.game-changer-plates|columns:rank, name, gap=plate, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Straight Widths

{{tables.straight-widths|columns:rank, name, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Straight Grinds

{{tables.straight-grinds|columns:rank, name, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Straight Points

{{tables.straight-points|columns:rank, name, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user|deltas:true}}

## Most Used Blades in Most Used Razors

{{tables.razor-blade-combinations|shaves:50|columns:rank, name, shaves, unique_users, avg_shaves_per_user, median_shaves_per_user}}

## Highest Use Count per Blade

{{tables.highest-use-count-per-blade|uses:50}}

## Top Shavers

{{tables.users|ranks:100|columns:rank, user, missed_days, shaves|deltas:true}}
