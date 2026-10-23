# ⚾ True Offensive Rating (TOR)

> *Decomposing plate appearances from terminal results into dynamic, pitch-level processes.*

---

## Development Status

**As of October 23, 2026: active development / pre-beta.**
The project is transitioning from Streamlit to a custom FastAPI + Jinja2 +
HTML/CSS/JavaScript dashboard. The scoring engine and basic player-card flow work;
the multi-metric trend analysis and its frontend integration are still being built.
TOR is an experimental metric; predictive performance has not been established.

### Working now
- Pitch-level TOR scoring and player rankings.
- CSV-backed FastAPI leaderboard and player-details JSON endpoint.
- Clickable player names opening a responsive, blurred-backdrop dialog with
  API-fetched TOR and contact metrics, plus loading and retry states.
- Preliminary four-section player-card layout.
- Standalone trend calculations in [trends.py](./trends.py): inclusive date-range
  filtering, daily valid-appearance grouping, daily TOR, and qualifying contact EV
  averages with qualifying/excluded/missing measurement counts.
- Qualifying trend EV includes recorded fouls and balls in play strictly above
  the lowest quality-contact scoring threshold (currently 80 mph). It is not an
  unfiltered or standard balls-in-play-only EV average.
- Seven saved regression tests for date filtering, grouping, TOR averages/counts,
  and current window-relative TOR statistics. EV boundary/missing-data behavior
  has also been checked with temporary examples; dedicated saved EV tests are pending.

### In progress / not connected
- Trend calculations are **not yet exposed through a trend endpoint or drawn by
  the chart**. The displayed chart is illustrative, date controls are disabled,
  and the gradient legend is a design preview, not calculated player coloring.
- Current trend z-scores are experimental and relative to the selected player's
  date window, not a fixed league reference. TOR uses PA-weighted daily means;
  EV compares daily means with qualifying individual measurements. These are
  different reference distributions, not finalized comparable color scales.
- Bat-speed trends, EV consistency measures, launch-angle ingestion, and TOR
  component trends are next. Launch angle exists in the source CSV but is not
  retained by the current loader or pitch model.
- Player headshots/team metadata, configurable metric tables, interactive date
  controls, and additional chart types remain planned.
- The web server loads the 2026 CSV once at startup. CSV/API source selection
  exists in the console scripts, not the web startup path; automatic refresh is
  not implemented.
- CI/CD is not configured yet. Dependency consolidation and API edge-case review
  remain pending; the Streamlit implementation is retained as a temporary reference.

---

## 🎯 Overview & Motivation

In baseball, traditional offensive metrics evaluate plate appearances as terminal events. A hit, an out, a strikeout — each assigned a fixed value determined entirely by result. While this framework has proven analytically useful, it systematically discards the pitch-level process data from which offensive outcomes emerge.

**TOR** proposes a complementary framework: decomposing each plate appearance into its underlying sequence of pitch-level events and evaluating offensive quality along both process and outcome dimensions.

Conventional statistics flatten plate appearances into binary results, obscuring meaningful within-at-bat variation. A 115-mph line drive caught by the shortstop, a 12-pitch strikeout featuring multiple hard fouls, and a first-pitch popup may register similarly — or identically — across OBP, OPS, and wRC+.

Simultaneously, favorable outcomes can mask process-level vulnerabilities: elevated swing-and-miss tendencies, poor pitch selection, or unsustainable contact profiles that conventional metrics are not designed to surface.

TOR addresses this by evaluating what the hitter did across the plate appearance — not merely what resulted from it — with the goal of more accurately estimating:
* **Offensive Threat Quality** — how dangerous the hitter actually was
* **Contact Sustainability** — whether the underlying contact profile is repeatable
* **Pitcher Pressure** — the degree to which the hitter imposed competitive difficulty

---

## 📐 Metric Definition & Core Components

TOR is a process-weighted offensive rating that evaluates the competitive quality of individual plate appearances at pitch resolution. Each At-Bat is modeled as a dynamic sequence rather than a singular result, scored across the following components:

* 📊 **Count Leverage** — progression through favorable and unfavorable count states.
* 📈 **Pitch Sequence Depth** — plate appearance length and pitcher workload imposed.
* 💥 **Contact Quality** — exit velocity and bat speed on all contacted pitches, including non-terminal fouls.
* 🎯 **Terminal Outcome Value** — result-based contribution, dynamically weighted by outcome informativeness.

### Outcome Weighting Philosophy
TOR does not treat outcome as irrelevant — it treats outcome as variably informative.
* **High-Value Outcomes:** Certain results carry intrinsic value independent of process: a home run produces runs regardless of how it was generated, and extra-base hits eliminate base-out state uncertainty. These warrant substantial positive weighting.
* **Uninformative Outcomes:** Conversely, routine negative outcomes — the weak rollover groundout, the first-pitch popup — are largely uninformative in isolation. A sharply-hit lineout and a weak groundout register identically in conventional statistics despite representing categorically different offensive processes.

TOR therefore applies a **sliding outcome weight**: increasing emphasis for high-leverage productive events, decreasing emphasis where process-level signal dominates.

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

Click a player name to open a modal with TOR and contact metrics fetched from
`GET /api/player/{player_name}`. A preliminary four-section card shows identity
placeholders, API-backed metrics from the startup CSV snapshot, an illustrative trend chart, disabled
date controls, and a low-to-high gradient legend. The sample chart and colors are identical for every
player and are not statistical results. Real images, configurable metric tables,
date-filtered trends, and reference-relative coloring are not connected yet.
The endpoint currently returns an error object with HTTP 200 for unknown names,
uses zero for missing measurements, and calculates hard-hit rate over all positive
recorded exit velocities rather than only balls in play. These behaviors need
review before treating the API as finalized. The Streamlit frontend remains as
a temporary reference.

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

### Trend regression tests

From the repository root, run the saved tests without downloading Statcast data:

```bash
python -B -m unittest discover -s tests -p test_trends.py -v
```

These use small synthetic examples. They verify calculation behavior, not TOR's
predictive validity or completed frontend integration.

---

## 📂 Project Structure

```text
├── at_bat.py            # AtBat and Pitch classes (Core Data Model)
├── scorer.py            # TOR aggregation and player-level rating logic
├── trends.py            # Date-filtered daily TOR and qualifying-EV analysis
├── fetcher.py           # Statcast pitch-level data ingestion and At-Bat construction
├── main.py              # Entry point for running TOR analysis and leaderboard output
├── server.py            # FastAPI leaderboard and player-details routes
├── templates/
│   └── leaderboard.html # Leaderboard and preliminary player-card layout
├── static/
│   ├── style.css        # Dashboard styling and responsive dialog layout
│   └── script.js        # Player-detail requests and dialog interactions
├── tests/
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
