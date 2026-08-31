# 🚂 RailMadat — AI & Scheduling Engine Training Data Research

> **Date:** August 31, 2026
> **Purpose:** Identify all available online data sources for training RailMadat's AI classification model and scheduling engine.

---

## Executive Summary

Research across Kaggle, data.gov.in, GitHub, Figshare, academic papers, government portals, and international open data sources identified **13 directly relevant datasets** for classification and **13 for scheduling**. The top recommendation is the **Indian Railway Failure Detection & Maintenance (100K)** dataset on Kaggle, which provides 100K realistic Indian railway sensor records specifically designed for failure prediction.

---

## PART 1: AI Classification Training Data

### 🏆 Tier 1 — Directly Relevant (Indian Railways + Maintenance/Faults)

| # | Dataset | URL | Size | Fields | Quality | Notes |
|---|---------|-----|------|--------|---------|-------|
| 1 | **Indian Railway Failure Detection & Maintenance (100K)** | [Kaggle](https://www.kaggle.com/datasets/shambhurajejagadale/indian-railway-failure-detection-and-maintenance100k) | 27 MB, 100K rows | Sensor records, failure types, maintenance actions | ⭐⭐⭐⭐⭐ | **BEST match.** 100K realistic Indian railway sensor records for failure prediction. Perfect for classification model. |
| 2 | **Indian Railways Accidents 1902–2024** | [Kaggle](https://www.kaggle.com/datasets/siddhanthkumardas/indian-railways-accidents-1902-2024) | CSV | Accident types, causes, locations, casualties, years | ⭐⭐⭐⭐ | Historical accident data with cause categories. Good for severity/priority training. |
| 3 | **Indian Railway Safety Budget & Accidents** | [Kaggle](https://www.kaggle.com/datasets/joeljosehubert/indian-railway-safety-budget-and-accidents) | 20 columns, 2004–2022 | Safety budget, accidents, deaths, year | ⭐⭐⭐ | Good for context — budget vs. accidents correlation. Not directly useful for fault classification. |
| 4 | **Indian Train Collision Dataset** | [Kaggle](https://www.kaggle.com/datasets/brijlaldhankour/indian-train-collison-dataset) | 100K rows | 10 parameters, collision causes, fault types | ⭐⭐⭐⭐ | Generated but realistic. Good for training fault-to-cause mapping. |

### 🥈 Tier 2 — International (Adaptable to Indian Context)

| # | Dataset | URL | Size | Fields | Quality | Notes |
|---|---------|-----|------|--------|---------|-------|
| 5 | **Railroad Accident & Incident Data (FRA Form 54)** | [Kaggle](https://www.kaggle.com/datasets/chrico03/railroad-accident-and-incident-data) | Huge, 1975–2022 | Cause codes, track class, equipment type, damage, injuries | ⭐⭐⭐⭐⭐ | **US Federal Railroad data** — most comprehensive railway fault dataset in the world. 50 years of data. Needs field mapping to Indian categories. |
| 6 | **FRA Safety Data Portal** | [data.transportation.gov](https://data.transportation.gov/stories/s/Form-54-Data-Downloads/pk4v-772c/) | Multiple GB | Full Form 54 data — cause codes, derailments, collisions, equipment failures | ⭐⭐⭐⭐⭐ | Direct download CSV. US data but the cause taxonomy maps well to Indian rail faults. |
| 7 | **MetroPT Dataset (Predictive Maintenance)** | [Nature Paper](https://www.nature.com/articles/s41597-022-01877-3) | ~150MB time-series | Compressor pressure, motor current, anomalies with ground truth | ⭐⭐⭐⭐ | Porto metro system. Real-world predictive maintenance data. Sensor-heavy. |
| 8 | **AI4I 2020 Predictive Maintenance** | [UCI ML Repository](https://archive-beta.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset) | 10K rows, 14 features | Machine type, failure type, tool wear, temperature, torque | ⭐⭐⭐⭐ | Synthetic but industry-realistic. Good baseline for feature engineering patterns. |

### 🥉 Tier 3 — Supplementary / Image-Based

| # | Dataset | URL | Size | Fields | Quality | Notes |
|---|---------|-----|------|--------|---------|-------|
| 9 | **Railway Track Fault Detection** | [Kaggle](https://www.kaggle.com/datasets/salmaneunus/railway-track-fault-detection) | Images | Fault/no-fault images | ⭐⭐⭐ | Image classification — useful if you add photo-based fault detection later. |
| 10 | **Railway Track Surface Faults Dataset** | [PMC/NIH](https://pmc.ncbi.nlm.nih.gov/articles/PMC10828558/) | Images + annotations | 7 fault types: Grooves, Joints, Cracks, etc. | ⭐⭐⭐⭐ | 22 citations. Real images from Indian tracks. Good for CV extension. |
| 11 | **Rail Components Dataset (RCD)** | [Kaggle](https://www.kaggle.com/datasets/elvin1233/rail-components) | 2100 images, 41K annotations | Component-level annotations | ⭐⭐⭐ | Useful for asset identification from photos. |
| 12 | **High-Speed Train Bogie Vibration & Fault Diagnosis** | [Kaggle](https://www.kaggle.com/datasets/ziya07/high-speed-train-bogie-vibration-and-fault-diagnosis) | Vibration signals | Fault types, sensor readings | ⭐⭐⭐ | Good for rolling stock fault classification. |

---

## PART 2: Scheduling Engine Training Data

### 🏆 Tier 1 — Train Schedules & Timetables (Indian)

| # | Dataset | URL | Size | Fields | Quality | Notes |
|---|---------|-----|------|--------|---------|-------|
| 1 | **Indian Railways Dataset (Sripaadsrinivasan)** | [Kaggle](https://www.kaggle.com/datasets/sripaadsrinivasan/indian-railways-dataset) | CSV | Train stops, stations, arrival/departure times, days of operation | ⭐⭐⭐⭐⭐ | **BEST for scheduling.** Each row = a train stop at a station with schedule times. Direct from data.gov.in. |
| 2 | **datameet/railways (GitHub)** | [GitHub](https://github.com/datameet/railways) | JSON (convertible to CSV) | trains.json, stations.json, schedules.json — full timetable | ⭐⭐⭐⭐⭐ | Source of the Kaggle dataset above. Direct from Indian government open data. All Indian trains. |
| 3 | **Indian Trains Schedule & Routes** | [Kaggle](https://www.kaggle.com/datasets/rohan26x/indian-express-train-dataset) | CSV | All express trains — schedules, routes, stops, timing | ⭐⭐⭐⭐ | Focus on express trains. Good for block window calculation. |
| 4 | **Indian Railways Time Table** | [Kaggle](https://www.kaggle.com/datasets/harsh16/indian-railways-time-table-for-trains-available) | 75 KB | Train timetable for available trains | ⭐⭐⭐ | Smaller but clean. Quick to use. |
| 5 | **Indian Railway Schedule-Prices-Availability** | [Kaggle](https://www.kaggle.com/datasets/bhavyarajdev/indian-railways-schedule-prices-availability-data) | 3 MB, 3 files | Schedules, pricing, availability | ⭐⭐⭐ | Web-scraped. Good supplementary data. |

### 🥈 Tier 2 — Train Delay & Performance Data

| # | Dataset | URL | Size | Fields | Quality | Notes |
|---|---------|-----|------|--------|---------|-------|
| 6 | **Indian Railway Delay Dataset** | [Kaggle](https://www.kaggle.com/datasets/vishwassrivastava1/indian-railway-delay-dataset) | CSV | Train name, number, delays 2016–2025 | ⭐⭐⭐⭐ | Manual collection across 10 years. Perfect for understanding delay patterns that affect maintenance windows. |
| 7 | **Indian Railway Express Trains Delay Datasets** | [GitHub](https://github.com/ankitaanand28/DA323_IndianRailwayTrainDelayDatasets) | CSV | Train delays for express trains (Guwahati routes) | ⭐⭐⭐ | Academic dataset. Good for zone-specific analysis. |
| 8 | **A Railway Network Dataset (Nature Scientific Data, 2025)** | [Figshare](https://figshare.com/articles/dataset/_b_A_Railway_Network_Dataset_Incorporating_Multi-Type_Train_Operation_Records_and_Train_Scheduling_b_/28891607) | 4 CSV files | Train operations, station locations, mileage, weather, scheduling | ⭐⭐⭐⭐⭐ | **Italian railway** — multi-type trains, weather, scheduling. Best-quality academic dataset. Perfect structure for adaptation. |
| 9 | **Infrabel (Belgium) Punctuality Data** | [Open Data Portal](https://opendata.infrabel.be/explore/dataset/stiptheid-gegevens-maandelijksebestanden/) | Monthly files | Hourly punctuality ratios, train sightings | ⭐⭐⭐⭐ | European railway punctuality data. Clean structure, good for modeling. |

### 🥉 Tier 3 — International Scheduling References

| # | Dataset | URL | Size | Fields | Quality | Notes |
|---|---------|-----|------|--------|---------|-------|
| 10 | **UK Network Rail TRUST Data** | [Open Rail Data Wiki](https://wiki.openraildata.com/index.php/About_the_Network_Rail_feeds) | Real-time streams | Train movements, schedule adherence, delays | ⭐⭐⭐⭐ | Live feed — useful for understanding real-time scheduling. 600 messages/minute. |
| 11 | **UK National Rail Timetable** | [Rail Delivery Group](https://www.raildeliverygroup.com/our-services/essential-services/rail-data/timetable-data.html) | Weekly CSV | Full UK timetable | ⭐⭐⭐ | Good reference structure. Free download. |
| 12 | **US BTS Rail Network Spatial Dataset** | [BTS](https://www.bts.gov/newsroom/rail-network-spatial-dataset) | Shapefiles | Track layout, nodes, rail network | ⭐⭐⭐ | US only, but good for understanding network topology modeling. |
| 13 | **Landscape Open Data Railway Europe** | [Figshare](https://figshare.com/articles/dataset/Landscape_Open_Data_Railway_Europe_by_Org_/29159780) | 1.28 MB CSV | European railway open data landscape | ⭐⭐⭐ | Catalog of what's available across European railways. |

---

## PART 3: Government & Academic Sources

### Indian Government

| Source | URL | What's There | Access |
|--------|-----|-------------|--------|
| **data.gov.in — Indian Railways** | [data.gov.in](https://www.data.gov.in/catalogs/?ministry=Ministry%20of%20Railways) | Train timetables, asset data, operational statistics | Free, API available |
| **Indian Railways Annual Statistical Statements** | [indianrailways.gov.in](https://www.indianrailways.gov.in/railwayboard/view_section.jsp?lang=0&id=0,1,304,366,554,941) | Yearly stats: accidents, track km, assets, employees | Free PDFs |
| **Safety Information Management System** | [safety.indianrail.gov.in](https://safety.indianrail.gov.in/) | Train accident records, cause analysis | Login required |
| **Indian Railways Safety Report (PIB)** | [pib.gov.in](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2202873) | 2025-26 safety stats — accidents dropped from 171 to 11 | Free |
| **RTI Database** | Via RTI requests | Any railway data via Right to Information | Application required |

### Academic / Research

| Source | URL | What's There |
|--------|-----|-------------|
| **Survey of AI for Railway Maintenance (2026)** | [PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12899784/) | Comprehensive review of models + data sources used |
| **Survey of AI Public Datasets for Railways (2021)** | [MDPI](https://www.mdpi.com/2412-3811/6/10/136) | Categorized list of all public railway datasets |
| **Predictive Maintenance for Railway Tracks** | [Springer](https://link.springer.com/article/10.1186/s44147-025-00842-2) | Time-aware framework with sparse data |
| **Autonlab PMX Data** | [GitHub](https://github.com/autonlab/pmx_data) | **20+ predictive maintenance datasets** across industries (not railway-specific but great for methodology) |
| **Kokikwbt Predictive Maintenance** | [GitHub](https://github.com/kokikwbt/predictive-maintenance) | Curated list of PM datasets |

### Live APIs (for real-time data)

| API | URL | What It Provides |
|-----|-----|-----------------|
| **Indian Rail API** | [GitHub](https://github.com/AniCrad/indian-rail-api) | Live train status, schedules |
| **RailwayAPI.com** | [railwayapi.com](https://www.railwayapi.com/) | PNR, train info, live tracking |
| **indiarailinfo.com** | [indiarailinfo.com](https://www.indiarailinfo.com/) | Comprehensive train data (scrapable) |
| **railpull (GitHub)** | [GitHub](https://github.com/shwetankg07/railpull) | Pulls current timetable from Indian Railways source |

---

## PART 4: Synthetic Data Generation Plan

Since real Indian railway maintenance data is limited (most is not publicly digitized), here's a recommended synthetic data strategy:

### For AI Classification Engine

| Table Needed | Records | Strategy |
|-------------|---------|----------|
| **Complaints** | 5,000+ | Mix real fault categories from Dataset #1 (100K Indian Railway) with Indian location names, realistic distributions |
| **Fault Categories** | Based on Indian Railways manual | Track: 40%, Signalling: 25%, Electrical: 20%, Station: 15% |
| **Severity Distribution** | — | Low: 30%, Medium: 35%, High: 25%, Critical: 10% |
| **Seasonal Patterns** | — | Monsoon (Jun-Sep): 40% more failures, Winter: signal failures, Summer: track buckling |
| **Root Causes** | Indian Railways categories | Wear & tear: 35%, Corrosion: 20%, Weather: 15%, Manufacturing defect: 10%, External: 10%, Unknown: 10% |

### For Scheduling Engine

| Table Needed | Records | Source |
|-------------|---------|--------|
| **Train Schedules** | 13,000+ trains | Download from datameet/railways GitHub |
| **Station Timetables** | All stops | Indian Railways Dataset (Kaggle) |
| **Maintenance Block History** | 500+ | Synthetic — based on real block patterns (2:00–5:00 AM windows) |
| **Delay Records** | 50,000+ | Indian Railway Delay Dataset + synthetic |

---

## PART 5: Recommended Action Plan

### Immediate (This Week)

1. **Download these 3 datasets** (free, direct download):
   - Indian Railway Failure Detection & Maintenance (100K) → Kaggle
   - Indian Railways Dataset (schedules) → Kaggle
   - Indian Railway Delay Dataset → Kaggle

2. **Download these 2 from GitHub**:
   - datameet/railways (trains.json + stations.json + schedules.json)
   - Indian Railway Express Trains Delay Datasets

3. **Download this for international benchmarking**:
   - FRA Form 54 (Railroad Accident Data) → data.transportation.gov

### Short-Term (This Month)

4. **Train your classification model** on the 100K Indian Railway dataset
5. **Train your scheduling engine** on the Indian train schedules + delay data
6. **Generate synthetic maintenance history** using the distributions above

### Medium-Term (Before Judging)

7. **Fine-tune with your own app data** — as real complaints come in, retrain
8. **Add weather data** (IMD open data) for monsoon-related prediction
9. **Consider the Nature Scientific Data railway dataset** (Italian) as a transfer learning source for scheduling optimization
