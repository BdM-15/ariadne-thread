---
auto_generated: true
entity_type: concept
source_module: workload
title: Travel Cost Estimation Patterns
updated: '2026-04-22T23:01:17'
---

> **Entity type:** `concept`

Travel estimation using government rates and frequency assumptions. Components: (1) Airfare - use GSA City Pair rates or current market (average $400-800 CONUS), (2) Lodging - GSA per diem rates by location, (3) M&IE - GSA rates ($59-$79/day typical CONUS), (4) Ground transportation - rental car or mileage, (5) Trip frequency from RFP or assumptions. Formula: Annual Travel = Trips × (Airfare + (Days × (Lodging + M&IE)) + Ground). Common assumptions: quarterly site visits, monthly PMR attendance, transition travel surge. Use actual GSA rates for proposal, update at contract execution.