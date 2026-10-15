import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from fetcher import load_statcast_csv

df = load_statcast_csv("statcast_data/2026_to_date.csv")
print(df['description'].value_counts())