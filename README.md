# ⚾ True Batter Profile (TBP)

> *A comprehensive, pitch-level analytics engine for evaluating offensive threat, contact quality, and bat control.*

---

## 🎯 Overview & Motivation

In baseball, traditional offensive metrics evaluate plate appearances as terminal events. A hit, an out, a strikeout — each assigned a fixed value determined entirely by result. While this framework has proven analytically useful, it systematically discards the pitch-level process data from which offensive outcomes emerge.

**The True Batter Profile (TBP)** is a comprehensive analytical engine that decomposes each plate appearance into its underlying sequence of pitch-level events, evaluating offensive quality along both process and outcome dimensions.

Conventional statistics flatten plate appearances into binary results, obscuring meaningful within-at-bat variation. A 115-mph line drive caught by the shortstop, a 12-pitch strikeout featuring multiple hard fouls, and a first-pitch popup may register similarly — or identically — across OBP, OPS, and wRC+.

Simultaneously, favorable outcomes can mask process-level vulnerabilities: elevated swing-and-miss tendencies, poor pitch selection, or unsustainable contact profiles that conventional metrics are not designed to surface.

TBP currently evaluates offensive quality through two distinct, complementary frameworks:
1. **True Offensive Rating (TOR):** A process-weighted scoring system that evaluates count leverage, pitch sequence depth, and contact quality alongside a sliding scale of outcome informativeness.
2. **Bat Speed & Power Matrix:** Multidimensional trend profiles that correlate swing speed, exit velocity, and whiff rates across bat-speed tiers, separating empty power from controlled, repeatable power.

By evaluating what the hitter did across the plate appearance — not merely what resulted from it — TBP aims to more accurately estimate:
* **Offensive Threat Quality** — how dangerous the hitter actually was
* **Contact Sustainability** — whether the underlying contact profile is repeatable
* **Pitcher Pressure** — the degree to which the hitter imposed competitive difficulty
* **Bat Control** — how efficiently a player transfers bat speed into hard contact without an escalating swing-and-miss cost

---

## Development Status

**Updated October 28, 2026.** TBP is an experimental analytical framework, with TOR
as its core scoring engine and a growing suite of bat-speed/power trend analytics
alongside it. The current focus is reliable metric calculation before interactive
chart integration and later scoring calibration and predictive validation.

* **Working dashboard:** FastAPI/Jinja2 leaderboard and interactive player cards
  with CSV-backed summary metrics. The trend chart and color legend are illustrative;
  metric and date controls are not yet connected to the trend backend.
* **Implemented trend backend:** Date-filtered daily TOR, qualifying exit velocity
  and bat speed, and swing/whiff counts and rates for all offers, explicitly
  non-bunt offers, and speed-qualified offers. Cumulative power-contact rates
  include fouls: hard (EV >=95 mph), very hard (>=105), and elite (>=115).
* **Scoring checkpoint:** Hard-foul bonuses survive a later HBP or intentional walk.
  These appearances count toward TOR when they contain a non-bunt-description swing;
  otherwise they remain excluded. Explicit bunt attempts earn no contact/bat-speed
  bonuses but remain in the pitch/count sequence. HBP/IBB adds no outcome bonus.
* **Validation and next steps:** Scoring/trend regression tests cover
  called-strike-only strikeout eligibility, power thresholds, and HBP/IBB foul
  preservation. Expanded
  metrics, real trend charts, date-range interaction, and statistical reference
  coloring remain in development.

**Metric scope:** Descriptive trends use all loaded appearances independently of
TOR eligibility. Bat-speed averages and speed-qualified whiff rates share the
same finite, measured, above-69-mph non-bunt-description swing population, including
foul tips and blocked misses; TOR's bat-speed scoring categories remain narrower.
Speed and descriptions are proxies, not definitive indicators of swing intent.
Power-rate denominators contain non-bunt-description contact with finite bat speed
above 69 mph and finite positive EV, including EV at or below 80 mph. Missing EV
is counted separately, not treated as weak contact; zero measured eligible contacts
produces a `null` rate. Existing qualifying EV averages still use foul/in-play EV
above 80 mph independently of bat speed. TOR now gives blocked swinging strikes
the same reduced bat-speed bonus as ordinary misses.
Trend z-scores are relative to the selected window, not a league benchmark.

`get_trends` returns `daily_data` and a selected-window `summary`. The summary
pools eligible contact pairs in `bs_power_profile` across the date range, weights fouls/foul tips at
0.6 and balls in play at 1.0, and reports weighted mean bat speed and EV in
four bat-speed tiers: >69 to <75, 75 to <80, 80 to <85, and >=85 mph.
Its bat-speed/EV correlation is Pearson's r across populated tier means, with
equal influence per tier. It is `null` with fewer than three populated tiers or
no variation in either coordinate. Contact counts accompany the tier profile;
three tiers alone do not establish reliability. This is a descriptive
selected-window relationship, not a daily trend or a transfer-efficiency score.

The summary also includes `bs_whiff_profile`: unweighted swing counts,
`tiered_whiff_count`, and `tiered_whiff_rate` in the same bat-speed tiers.
It includes all recognized non-bunt swings with finite bat speed >69 mph,
regardless of EV availability. Whiffs are identified by pitch description, not
missing EV. Empty tiers report a `null` whiff rate. This profile currently
measures misses by speed.

`controlled_power_profile` combines the same tiers' swing/whiff counts with
measured contact counts, missing-contact EV counts, and cumulative hard (>=95),
very-hard (>=105), and elite (>=115 mph) contact counts. These event counts are
unweighted, including fouls. `hard_rate`, `vhard_rate`, and `elite_rate` are
recorded hard contacts per eligible swing; the corresponding `*_contact_rate`
fields use measured contacts as their denominator. Missing EV is unknown, not
known weak contact, so per-swing yields depend on measurement coverage.
The `*_contact_to_whiff_ratio` fields are recorded tier-contact counts divided
by whiff counts, not a physical efficiency or control score. Ratios are null
without whiffs; per-contact rates are null without measured contacts; all rates
are null without eligible swings. Empty tiers retain zero counts. Compare
counts, coverage, yields and whiff rates together; these observations do not
establish a player's optimal swing speed or diagnose mechanics.
The `overall_*_to_whiff_ratio` fields pool counts across all speed tiers in the
same date window. Each `*_to_whiff_relative_index` is 100 times the tier ratio
divided by that pooled ratio: 100 matches baseline, and 180 means an 80% higher
ratio, not an 80% higher per-swing yield. Indices are null for unavailable tier
ratios or zero/unavailable baselines. This reference changes with the date window.

Days without eligible TOR appearances retain their measurements and report TOR
as `null`. In trend output, `plate_appearances` is the TOR-scored count;
`total_plate_appearances` includes all appearances. Pitch-based rates currently
include automatic ball/strike records.

---

## 📐 Metric Definition & Core Components

### 1. True Offensive Rating (TOR)
TOR is a process-weighted offensive rating that evaluates the competitive quality of individual plate appearances at pitch resolution. Each At-Bat is modeled as a dynamic sequence rather than a singular result, scored across the following components:

* 📊 **Count Leverage** — progression through favorable and unfavorable count states.
* 📈 **Pitch Sequence Depth** — plate appearance length and pitcher workload imposed.
* 💥 **Contact Quality** — exit velocity and bat speed on all contacted pitches, including non-terminal fouls.
* 🎯 **Terminal Outcome Value** — result-based contribution, dynamically weighted by outcome informativeness.

#### Outcome Weighting Philosophy
TOR does not treat outcome as irrelevant — it treats outcome as variably informative.
* **High-Value Outcomes:** Certain results carry intrinsic value independent of process: a home run produces runs regardless of how it was generated, and extra-base hits eliminate base-out state uncertainty. These warrant substantial positive weighting.
* **Uninformative Outcomes:** Conversely, routine negative outcomes — the weak rollover groundout, the first-pitch popup — are largely uninformative in isolation. A sharply-hit lineout and a weak groundout register identically in conventional statistics despite representing categorically different offensive processes.

TOR therefore applies a **sliding outcome weight**: increasing emphasis for high-leverage productive events, decreasing emphasis where process-level signal dominates.

### 2. Bat Speed & Power Matrix
To evaluate bat control and power transfer independent of plate-appearance outcome, the trend engine bins every qualifying swing (bat speed >69 mph, non-bunt) into four bat-speed tiers: **69–75, 75–80, 80–85, and 85+ mph.**

* **Power Profile** (`bs_power_profile`) — weighted average exit velocity per tier, plus cumulative hard (>=95 mph), very hard (>=105), and elite (>=115 mph) contact rates. Fouls and foul tips are weighted at 0.6 relative to balls in play (1.0).
* **Whiff Profile** (`bs_whiff_profile`) — unweighted swing and whiff counts per tier, producing a tiered whiff rate.
* **Controlled Power Profile** (`controlled_power_profile`) — merges the two, producing per-tier hard-contact-to-whiff ratios and a relative index (baseline = 100) that flags the bat-speed tier where a player's control breaks down.

See **Development Status → Metric scope** above for the exact eligibility rules, weighting, and null-handling behind each field.

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.x
- Linux (Recommended environment) or equivalent 

### 1. Install Dependencies
Install the required Python libraries via pip:
```bash
pip install pandas pybaseball python-dotenv pytest
```

### 2. Data Preparation
Place your Statcast CSV files inside a local directory named `statcast_data/` in the project root:
```text
statcast_data/
└── statcast_sample.csv  # (gitignored)
```

---

## 💻 Usage

### FastAPI dashboard (in progress)

With your Python environment active, install the web dependencies if needed:

```bash
pip install fastapi uvicorn jinja2
```

The dashboard also uses the analytics dependencies listed above and requires
`statcast_data/2026_to_date.csv`, which is not included in Git.
From the repository root, start the server:

```bash
python -m uvicorn server:app --reload
```

Wait for `Application startup complete`, then open http://127.0.0.1:8000/.
Initial data preparation can take time. Stop with **Ctrl+C** in that terminal
and wait for the prompt before restarting. Python edits reload automatically;
refresh the browser for HTML/CSS/JavaScript edits (hard-refresh if assets are cached).

Click a player name to open a four-section card with TOR and contact metrics from
the loaded CSV dataset, fetched through `GET /api/player/{player_name}`.
The chart and color legend are currently illustrative, and date controls are
disabled while trend integration is developed. Player imagery and configurable
metric tables are planned. The previous Streamlit frontend remains a temporary reference.

### Console analysis

The primary execution flow is handled by `main.py`. The script relies on a `DATA_SOURCE` toggle at the top of the file to switch between local CSV processing and live API fetching:

```python
DATA_SOURCE = "CSV"  # Set to "API" to fetch live data via pybaseball
```

### Execution Flow
1. **Cache Initialization:** Enables `pybaseball` caching for efficient data retrieval.
2. **Data Ingestion:** Gathers data from local files (`statcast_data/*.csv`) or queries the Statcast API for specified date ranges.
3. **Reconstruction:** Parses pitch-by-pitch records into structured `AtBat` and `Pitch` objects for each player.
4. **Leaderboard Generation:** Computes aggregated TOR metrics and outputs the top-ranked players to the console.

Run the analysis pipeline with:
```bash
python main.py
```

### Scoring and trend regression tests

From the repository root, run the saved tests without downloading Statcast data:

```bash
python -B -m unittest discover -s tests -p 'test*.py' -v
```

Tests use small synthetic examples and require no Statcast download.

---

## 📂 Project Structure

```text
├── at_bat.py            # AtBat and Pitch classes (Core Data Model)
├── scorer.py            # TOR aggregation and player-level rating logic
├── trends.py            # Date-filtered daily TOR, bat-speed/power matrices, and whiff-tier trends
├── fetcher.py           # Statcast pitch-level data ingestion and At-Bat construction
├── main.py              # Entry point for running TOR analysis and leaderboard output
├── server.py            # FastAPI leaderboard and player-details routes
├── templates/
│   └── leaderboard.html # Leaderboard and preliminary player-card layout
├── static/
│   ├── style.css        # Dashboard styling and responsive dialog layout
│   └── script.js        # Player-detail requests and dialog interactions
├── tests/
│   ├── test_at_bat.py   # Scoring eligibility and foul-credit regression tests
│   └── test_trends.py   # Synthetic trend regression tests
├── download_data.py     # Statcast data acquisition and local CSV management
└── statcast_data/       # Local pitch-level data storage (gitignored)
```

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Backend:** FastAPI, Jinja2, Uvicorn, Pandas, PyBaseball
* **Frontend:** HTML, CSS, vanilla JavaScript
* **Data:** Local Statcast CSV snapshot; console API-fetching option
* **Environment:** Linux or equivalent environment - VS Code / WSL

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check out the issues page or open a pull request if you'd like to suggest improvements to the weighting algorithms or data pipeline.

---

## 📄 License

This project is licensed under the MIT License. See LICENSE for details.
