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
    lb_df.insert(0, "Rank", range(1, len(lb_df) + 1))
    return lb_df

lb_df = get_leaderboard(all_at_bats)

st.subheader("🏆TOR League Leaderboard")
column_config = {
    "Rank": st.column_config.NumberColumn(
        "Rank",
        width=75,
        format="%d",
    ),
    "Player": st.column_config.TextColumn(
        "Player",
        width=250,
    ),
    "TOR": st.column_config.NumberColumn(
        "TOR",
        width=150,
        format="%.2f",
    ),
}
event = st.dataframe(
    lb_df,
    width="stretch",
    column_config=column_config,
    on_select="rerun",
    selection_mode="single-row",
    hide_index=True,
)

selection = event.get("selection", {})
selected_rows = selection.get("rows", [])

@st.dialog("Player Card", width="large")
def show_player_card(player_name, all_at_bats):
    player_map = group_by_player(all_at_bats)
    player_at_bats = [ab for ab in player_map.get(player_name, []) if ab.is_valid_ab()]

    st.subheader(player_name)
    st.metric("TOR", f"{player_tor(player_at_bats):.2f}")
    # TODO: top-left image, bottom-left tabbed tables, top-right trend chart, bottom-right panel

if selected_rows:
    selected_row = selected_rows[0]
    selected_player = lb_df.iloc[selected_row]["Player"]
    show_player_card(selected_player, all_at_bats)
