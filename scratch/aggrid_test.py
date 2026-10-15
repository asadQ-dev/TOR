import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, ColumnsAutoSizeMode

st.set_page_config(layout="wide")

df = pd.DataFrame({
    "Rank": range(1, 11),
    "Player": [f"Test Player {i}" for i in range(1, 11)],
    "TOR": [85.5 - i * 0.4 for i in range(10)],
    "PA": [600 - i * 20 for i in range(10)],
})

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_column("Rank", width=70)
gb.configure_column("Player", flex=1, minWidth=160)
gb.configure_column("TOR", width=90)
gb.configure_column("PA", width=90)
gb.configure_selection("single")

grid = AgGrid(
    df,
    gridOptions=gb.build(),
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    columns_auto_size_mode=ColumnsAutoSizeMode.NO_AUTOSIZE,
    fit_columns_on_grid_load=False,
    theme="streamlit",
)
st.write(grid["selected_rows"])
