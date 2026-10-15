from at_bat import AtBat, Pitch
from fetcher import load_statcast_csv, build_at_bats, fetch_statcast_api
from scorer import player_tor, rank_players
from pybaseball import cache
import glob
import pandas as pd

DATA_SOURCE = "CSV"

def main():
    cache.enable()
    
    print("Welcome to TOR: True Offensive Rating")
    if DATA_SOURCE == "CSV":
        all_files = glob.glob("statcast_data/*.csv")
        df_list = [load_statcast_csv(f) for f in all_files]    
        df = pd.concat(df_list, ignore_index=True)
    
    elif DATA_SOURCE == "API":
        print("Fetching data from Statcast API (this may take a minute)...")
        df = fetch_statcast_api('2026-04-20', '2026-05-06')
        
    else:
        print(f"Error: Invalid DATA_SOURCE '{DATA_SOURCE}'")
        return 
    print(f"Total rows in CSV: {len(df)}")

    print("Top players by pitch count:")
    print(df['batter_name'].value_counts().head(5))
    print("Example names from the file:")
    print(df['batter_name'].unique()[:10])
    players = df['batter_name'].unique()
    
    all_at_bats = []
    for player in players:
        at_bats = build_at_bats(df, player)
        all_at_bats.extend(at_bats)

    print("\n--- PLAYER RANKINGS ---")
    leaderboard = rank_players(all_at_bats)
    
    for i, (name, score) in enumerate(leaderboard[:50], 1):
        print(f"{i}. {name}: {score:.2f}")

if __name__ == "__main__":
    main()