import glob
import pandas as pd
import streamlit as st
from at_bat import AtBat, Pitch
from fetcher import build_at_bats, load_statcast_csv
from scorer import rank_players, group_by_player, player_tor

st.set_page_config(
    page_title="TOR: True Offensive Rating",
    page_icon="⚾",
    layout="wide",
)

st.title("TOR: True Offensive Rating Dashboard")
st.markdown("Advanced pitch-level sabermetrics engine powered by Statcast data.")
@st.cache_data
def load_data():
    return load_statcast_csv("statcast_data/2026_to_date.csv")

df = load_data()   
st.write(f"Loaded {len(df):,} pitches")

# NEW LEADERBOARD
@st.cache_data
def get_all_at_bats(df):
    players = df["batter_name"].unique()
    all_at_bats = []
    for player in players:
        at_bats = build_at_bats(df, player)
        all_at_bats.extend(at_bats)
    return all_at_bats

all_at_bats = get_all_at_bats(df)

def get_leaderboard(all_at_bats):
    leaderboard = rank_players(all_at_bats, min_pas=100)
    lb_df = pd.DataFrame(leaderboard, columns=["Player", "TOR"])
    return lb_df

lb_df = get_leaderboard(all_at_bats)

st.subheader("🏆TOR League Leaderboard")
st.dataframe(lb_df, width="stretch")
