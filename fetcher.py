import pandas as pd
from at_bat import AtBat, Pitch 
from pybaseball import statcast, playerid_reverse_lookup

def fetch_statcast_api(start_date, end_date):
    df = statcast(start_dt=start_date, end_dt=end_date)
    batter_ids = df['batter'].unique().tolist()
    batter_info = playerid_reverse_lookup(batter_ids, key_type='mlbam')
    batter_info['batter_name'] = batter_info['name_last'] + ', ' + batter_info['name_first']
    batter_info = batter_info.rename(columns={'key_mlbam': 'batter'})
    df = df.merge(batter_info[['batter', 'batter_name']], on='batter', how='left')
    
    return df

def load_statcast_csv(filepath):
    df = pd.read_csv(filepath)

    if 'batter_name' in df.columns:
        df['batter_name'] = df['batter_name'].astype(str).str.strip()
    elif 'player_name' in df.columns:
        df['batter_name'] = df['player_name'].astype(str).str.strip()
    else:
        raise ValueError("CSV file must contain either 'batter_name' or 'player_name'")

    cols_we_need = [
        'batter_name',
        'at_bat_number',
        'pitch_number',
        'launch_speed',
        'description',
        'events',
        'balls',
        'strikes',
        'game_pk',
        'bat_speed',
        'game_date'
    ]
    df = df[cols_we_need]
    return df

def build_at_bats(df, batter_name):
    player_df = df[df['batter_name'] == batter_name]
    at_bats = []
    for (game_id, ab_num), group in player_df.groupby(['game_pk', 'at_bat_number']):
        final_outcome = group['events'].dropna().iloc[-1] if not group['events'].dropna().empty else "unknown"
        game_date = group['game_date'].iloc[0]
        current_ab = AtBat(batter_name, final_outcome, game_date)
        
        # 3. Loop through every pitch in this group
        for _, row in group.iterrows():
            # Create a Pitch object (handling potential NaN for launch_speed)
            p = Pitch(
                pitch_number=row['pitch_number'],
                exit_velo=row['launch_speed'] if pd.notnull(row['launch_speed']) else 0,
                description=row['description'],
                balls=row['balls'],
                strikes=row['strikes'],
                bat_speed=row['bat_speed'] if pd.notnull(row['bat_speed']) else 0
            )
            current_ab.add_pitch(p)
            
        at_bats.append(current_ab)
        
    return at_bats