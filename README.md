# ⚾ True Offensive Rating (TOR)

> *Decomposing plate appearances from terminal results into dynamic, pitch-level processes.*

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
- VS Code / WSL (Recommended environment)

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

---

## 📂 Project Structure

```text
├── at_bat.py            # AtBat and Pitch classes (Core Data Model)
├── scorer.py            # TOR aggregation and player-level rating logic
├── fetcher.py           # Statcast pitch-level data ingestion and At-Bat construction
├── main.py              # Entry point for running TOR analysis and leaderboard output
├── download_data.py     # Statcast data acquisition and local CSV management
└── statcast_data/       # Local pitch-level data storage (gitignored)
```

---

## 🛠️ Tech Stack

* **Language:** Python 3.x
* **Libraries:** Pandas, PyBaseball, Glob, OS
* **Environment:** VS Code / WSL

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check out the issues page or open a pull request if you'd like to suggest improvements to the weighting algorithms or data pipeline.

---

## 📄 License

This project is licensed under the MIT License. See LICENSE for details.
