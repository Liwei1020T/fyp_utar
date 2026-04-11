# Admin Inventory Alignment

## 1. Purpose

This module treats admin inventory as an operations surface, not a player catalog.

The admin inventory flow should help the shop team:

- identify strings quickly from thumbnail media
- spot low-stock and missing-price issues early
- separate catalog master data from shop-specific inventory data
- edit recommendation-facing scores without losing backend alignment
- keep price handling truthful with `pending` and `quoted_at_shop` states instead of fake zero pricing

## 2. Admin Inventory List Proposal

### Page intent

- Make the list feel like a compact stock-control workbench.
- Prioritize fast scanning over large product storytelling.
- Surface action-needed items before the full list.

### Page structure

1. Header
   `Inventory`
   `Manage stock, pricing, and shop readiness.`
2. Summary strip
   Example: `18 items · 3 low stock · 2 price pending`
3. Search and filter row
   Search by string or brand, filter toggle, sort toggle
4. Status chips
   `All`, `In Stock`, `Low Stock`, `Out of Stock`, `Price Missing`
5. Advanced filters
   Brand chips plus explicit sort options
6. Needs attention section
   Show low stock, out of stock, hidden, and price-missing items first
7. All inventory section
   Show the full filtered list below the attention stack

### Behavior notes

- Use thumbnail-first compact cards.
- Never show `RM 0.00` as a placeholder for missing price.
- Drive attention through chip color, summary counts, and section ordering.

## 3. Admin String Detail Proposal

### Page intent

- Treat the screen as a master-detail editor for one string.
- Separate string catalog fields from shop-facing inventory fields.
- Keep the preview card operational and compact.

### Page structure

1. Header
   String name
   `Edit string data, media, scores, and shop inventory.`
2. Optional backend sync scope note
   Explains current live backend persistence limits
3. String preview card
   Image, full name, gauge, main trait, stock, and price state
4. Catalog information section
   Brand, model, localized name, gauges, material, tension, main trait, category, description, visibility
5. Performance scores section
   Power, control, durability, comfort, sound on a 1-10 scale
6. Media section
   Current image preview plus upload, replace, remove actions
7. Shop data section
   Price state, price, stock level, availability, shop note
8. Actions
   `Save string changes`
   `Back to inventory`

### Backend truthfulness

- Current backend integration can persist shop data today.
- Catalog, score, media, and visibility edits are aligned in the frontend model and UI, but they need dedicated backend master-data endpoints for full server persistence.

## 4. Unified Inventory Card Design

### Component shape

Three information layers:

1. Header line
   Thumbnail, model name, brand, availability badge
2. Metadata line
   Gauge range, main trait, optional category tag, stock badge, price badge, attention badge
3. Quick actions
   Restock or edit stock, edit price, edit details or notes

### Component rules

- Thumbnail is a fixed square with rounded corners and neutral shelf background.
- Image uses `contain` to keep product packs recognizable.
- Fallback uses brand initials plus `No photo`.
- Cards stay dense and do not exceed the height of a typical operations list row by much.
- Attention cards reuse the same component with stronger emphasis rather than switching into a different layout.

## 5. Backend Field Mapping

| Frontend section | Domain boundary | Backend fields | Notes |
| --- | --- | --- | --- |
| String preview card | Mixed read model | `brand`, `model_name`, `localized_name`, `gauge_min_mm`, `gauge_max_mm`, `main_trait`, `image_url`, `stock_qty`, `price`, `price_status`, `availability_status` | Combines catalog and inventory for operational preview only |
| Catalog information | String master data | `id`, `brand`, `model_name`, `localized_name`, `gauge_min_mm`, `gauge_max_mm`, `material`, `description`, `main_trait`, `category`, `tension_min_lbs`, `tension_max_lbs`, `is_active`, `updated_at` | Belongs in a string catalog or `strings` table |
| Performance scores | String master data | `power_score`, `control_score`, `durability_score`, `comfort_score`, `sound_score` | Must stay consistent with recommendation and compare surfaces |
| Media | String master data | `image_url` or image asset reference | Upload, replace, and remove should target master data, not shop inventory |
| Shop data | Vendor inventory | `id`, `vendor_id`, `string_id`, `stock_qty`, `price`, `price_status`, `availability_status`, `shop_note`, `updated_at` | Belongs in a vendor inventory table |

### Frontend domain model

The frontend now treats `StringItem` as a hybrid display model with two explicit sub-records:

- `catalog`
- `inventory`

Legacy top-level fields remain for compatibility with existing player flows, but admin inventory screens should treat `catalog` and `inventory` as the source of truth.

## 6. Admin Microcopy

### List page

- `Manage stock, pricing, and shop readiness.`
- `No urgent stock or pricing issues in this view.`
- `Inventory is currently ready for bookings based on the selected filters.`
- `Clear the search, status, or brand filters to widen the list again.`

### Card actions

- `Restock`
- `Edit stock`
- `Add price`
- `Edit price`
- `Edit details`
- `Notes`

### Detail page

- `Core string data shared across recommendation, comparison, and admin views.`
- `These 1 to 10 scores should stay aligned with radar charts and recommendation logic.`
- `Use a clean pack or spool image so the counter team can identify the item quickly.`
- `Use pending or quoted at shop instead of storing a fake RM 0.00.`
- `Hidden strings stay in the catalog editor but can be excluded from live recommendation and shelf views.`

## 7. ASCII Wireframes

### Inventory list

```text
┌────────────────────────────────────────────────────┐
│ Inventory                                          │
│ Manage stock, pricing, and shop readiness.         │
├────────────────────────────────────────────────────┤
│ 18 items · 3 low stock · 2 price pending           │
│                                                    │
│ [ Search string or brand.............. ] [Filter]  │
│ [ All ] [ In Stock ] [ Low Stock ] [ Out ] [ Price │
│ Missing ]                                          │
│                                                    │
│ NEEDS ATTENTION                         3 items     │
│ ┌────────────────────────────────────────────────┐ │
│ │ [img] Victor VBS-68 Power       [Low Stock]   │ │
│ │       0.68 mm · Power · Balanced              │ │
│ │       [Stock 2] [RM 32.00] [Low stock watch]  │ │
│ │       [Restock] [Edit price]                  │ │
│ └────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────┐ │
│ │ [img] Li-Ning No.1            [In Stock]       │ │
│ │       0.65 mm · Control · Balanced            │ │
│ │       [Stock 9] [Price pending] [Add price]   │ │
│ │       [Edit stock] [Add price]                │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│ ALL INVENTORY                           18 shown   │
│ ┌────────────────────────────────────────────────┐ │
│ │ [img] Gosen G-Tone 5            [In Stock]     │ │
│ │       0.65 mm · Control                       │ │
│ │       [Stock 11] [Quoted at shop]             │ │
│ │       [Edit stock] [Edit details] [Notes]     │ │
│ └────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────┘
```

### Detail editor

```text
┌────────────────────────────────────────────────────┐
│ ← Gosen G-Tone 5                                   │
│   Edit string data, media, scores, and shop        │
│   inventory.                                       │
├────────────────────────────────────────────────────┤
│ BACKEND SYNC SCOPE                                 │
│ Live backend currently saves price, stock level,   │
│ and shop note. Catalog, media, and score edits     │
│ stay local until master-data endpoints exist.      │
│                                                    │
│ STRING PREVIEW                                     │
│ ┌────────────────────────────────────────────────┐ │
│ │ [ image ] Gosen G-Tone 5                       │ │
│ │ Brand: Gosen                                   │ │
│ │ 0.65 mm · Control                              │ │
│ │ [ In Stock ] [ Stock 11 ] [ Quoted at shop ]   │ │
│ └────────────────────────────────────────────────┘ │
│                                                    │
│ CATALOG INFORMATION                                │
│ [ Brand                  Gosen                  ]  │
│ [ Model name             G-Tone 5              ]  │
│ [ Localized name         高神 G-Tone 5         ]  │
│ [ Gauge min              0.65 ] [ Gauge max 0.65] │
│ [ Material               High polymer nylon     ] │
│ [ Tension min            23   ] [ Tension max 29] │
│ [ Main trait             Control                ] │
│ [ Category     Control / Balanced / Durable ... ] │
│ [ Visible ] [ Hidden ]                            │
│ [ Description.................................. ] │
│                                                    │
│ PERFORMANCE SCORES                                 │
│ Power        [ 7 ]                                 │
│ Control      [ 9 ]                                 │
│ Durability   [ 6 ]                                 │
│ Comfort      [ 7 ]                                 │
│ Sound        [ 9 ]                                 │
│                                                    │
│ MEDIA                                              │
│ [ Current image preview ]                          │
│ [ Upload image ] [ Replace image ] [ Remove image ]│
│                                                    │
│ SHOP DATA                                          │
│ [ Fixed price ] [ Price pending ] [ Quoted at shop]│
│ [ Price RM              35.00                   ]  │
│ [ Stock level           11                      ]  │
│ [ In Stock ] [ Low Stock ] [ Out of Stock ]       │
│ [ Shop note.................................... ]  │
│                                                    │
│ [ Save string changes ]                            │
│ [ Back to inventory ]                              │
└────────────────────────────────────────────────────┘
```

## 8. Implementation Checklist

- [x] Add explicit frontend separation between string catalog data and shop inventory data
- [x] Preserve compatibility with existing player-facing string screens through legacy top-level fields
- [x] Redesign admin inventory list into a denser workbench layout
- [x] Add thumbnail-aware reusable admin inventory cards
- [x] Add truthful price states: fixed price, pending, quoted at shop
- [x] Prioritize attention items above the full list
- [x] Expand inventory detail into catalog, scores, media, and shop-data sections
- [x] Support upload, replace, and remove image actions in the frontend
- [x] Document backend mapping and persistence boundaries
- [ ] Add backend endpoints for catalog master-data updates
- [ ] Add backend media upload or asset-reference handling for `image_url`
- [ ] Add backend persistence for performance scores and visibility state
- [ ] Add server-side validation for price status versus price value combinations
