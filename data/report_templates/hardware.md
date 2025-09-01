# Hardware Report - {{month_year}}

**Total Shaves:** {{total_shaves}}
**Unique Shavers:** {{unique_shavers}}

Welcome to your SOTD Hardware Report for {{month_year}}

* {{total_shaves}} shave reports from {{unique_shavers}} distinct shavers during the month of {{month_year}} were analyzed to produce this report, for an average of {{avg_shaves_per_user}} (median {{median_shaves_per_user}}) shaves per user.

## Observations

* [Observations will be generated based on data analysis]

## Notes & Caveats

* I only show the top n results per category to keep the tables readable and avoid max post length issues.

* Blade Format stats now differentiate between DE and half DE razors.

* "Other" in the Blade Format table includes vintage reusable blades (including Rolls, Valet Auto Strop, and old-style lather catchers with wedge blades) as well as other antique proprietary blade formats (e.g. Enders Speed Blade)

* Blades recorded as just 'GEM' will be matched to 'Personna GEM PTFE' per guidance [here](https://www.reddit.com/r/Wetshaving/comments/19a43q7/comment/kil95r8/)

* The Personna name is [going away](https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://www.badgerandblade.com/forum/threads/what-do-you-know-about-this-personna-no-longer-exists.647703/&ved=2ahUKEwiyi4n7pPKFAxXeLtAFHfNVDz8QFnoECAQQAQ&usg=AOvVaw38QYgjzknuIIIV94b6VDP5) for blades manufactured in the USA, but the majority of entries are still coming in under Personna, so I am sticking to that for this report. Once more than 50% of the entries come in under the new names, I will reverse this and map any old Personna entries to the new name.

    * Personna GEM PTFE is now Accutec Pro Premium (GEM)
  
    * Personna Lab Blue is now Accuforge Super Stainless MicroCoat
  
    * Personna Med Prep is now Accuthrive Super Med Prep

    * The German-made Personna Platinums (aka "Personna Reds") will continue to use the Personna brand

* In the case of most brush makers (eg Maggard) - knots are split into synthetic / badger / boar and attributed to the maker - eg 'Maggard Synthetic', though for particularly popular brush models (e.g. specific models from Semogue and Omega) or knots (e.g. DG, Chisel & Hound, or AP Shave Co.) they are reported on indvidually.

* The unique user column shows the number of different users who used a given razor / brush etc in the month. We can combine this with the total number of shaves to get the average number of times a user used a razor / brush etc

* The change Δ vs columns show how an item has moved up or down the rankings since that month. = means no change in position, up or down arrows indicate how many positions up or down the rankings an item has moved compared to that month. n/a means the item was not present in that month.

## Razor Formats

{{tables.razor-formats|deltas:true}}

## Razors

{{tables.razors|ranks:50|deltas:true}}

## Razor Manufacturers

{{tables.razor-manufacturers|ranks:30|deltas:true}}

## Blades

{{tables.blades|ranks:50|deltas:true}}

## Brushes

{{tables.brushes|ranks:50|deltas:true}}

## Brush Handle Makers

{{tables.brush-handle-makers|ranks:30|deltas:true}}

## Brush Knot Makers

{{tables.brush-knot-makers|ranks:30|deltas:true}}

## Knot Fibers

{{tables.brush-fibers|deltas:true}}

## Knot Sizes

{{tables.brush-knot-sizes|deltas:true}}

## Blackbird Plates

{{tables.blackbird-plates|deltas:true}}

## Christopher Bradley Plates

{{tables.christopher-bradley-plates|deltas:true}}

## Game Changer Plates

{{tables.game-changer-plates|deltas:true}}

## Straight Widths

{{tables.straight-widths|deltas:true}}

## Straight Grinds

{{tables.straight-grinds|deltas:true}}

## Straight Points

{{tables.straight-points|deltas:true}}

## Most Used Blades in Most Used Razors

{{tables.razor-blade-combinations|shaves:20}}

## Highest Use Count per Blade

{{tables.highest-use-count-per-blade|uses:20}}

## Top Shavers

{{tables.users|ranks:30|columns:rank, user, shaves, missed_days|deltas:true}}
