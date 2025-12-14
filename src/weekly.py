import pandas as pd
import numpy as np
import datetime

# --- CONFIGURATION ---
SEASON_START_DATE = datetime.datetime(2025, 10, 21)

def get_date_from_pick(pick_num):
    p_int = int(pick_num)
    return SEASON_START_DATE + datetime.timedelta(days=p_int - 1)

def get_winners_list(series, maximize=True):
    if series.empty: return []
    target_val = series.max() if maximize else series.min()
    winners = series[series == target_val]
    return [(player, val) for player, val in winners.items()]

def get_all_scorers(series):
    if series.empty: return []
    sorted_series = series.sort_values(ascending=False)
    return [(player, val) for player, val in sorted_series.items()]

def get_global_records(df_full):
    records = {"NoCarrot": 0, "Serie30": 0}
    for p in df_full['Player'].unique():
        scores = df_full[df_full['Player'] == p].sort_values('Pick')['Score'].values
        # No Carrot
        temp = 0
        for s in scores:
            if s >= 20: temp += 1; records["NoCarrot"] = max(records["NoCarrot"], temp)
            else: temp = 0
        # Serie 30
        temp = 0
        for s in scores:
            if s >= 30: temp += 1; records["Serie30"] = max(records["Serie30"], temp)
            else: temp = 0
    return records

def analyze_streaks_direct(df, player, current_pick_limit, global_records):
    """Analyse factuelle et directe (Format User Requested)."""
    p_df = df[(df['Player'] == player) & (df['Pick'] <= current_pick_limit)].sort_values('Pick')
    if p_df.empty: return []

    scores = p_df['Score'].values
    
    # Calculs
    curr_nc, rec_perso_nc, temp = 0, 0, 0
    for s in scores:
        if s >= 20: temp += 1; rec_perso_nc = max(rec_perso_nc, temp)
        else: temp = 0
    for s in reversed(scores):
        if s >= 20: curr_nc += 1
        else: break
        
    curr_30, rec_perso_30, temp = 0, 0, 0
    for s in scores:
        if s >= 30: temp += 1; rec_perso_30 = max(rec_perso_30, temp)
        else: temp = 0
    for s in reversed(scores):
        if s >= 30: curr_30 += 1
        else: break

    lines = []
    
    # 1. Analyse Fiabilité (> 10 matchs)
    if curr_nc >= 10:
        icon = "🔥"
        status = "[Série en cours]"
        if curr_nc >= global_records["NoCarrot"]:
            icon = "👑"; status = "[RECORD SAISON !]"
        elif curr_nc >= rec_perso_nc and curr_nc > 10:
            icon = "🚨"; status = "[Record Perso !]"
            
        txt = f"{icon} **{player}** : {curr_nc} matchs consécutifs sans carotte {status} (Rec. perso : {rec_perso_nc} | Rec. Team : {global_records['NoCarrot']})"
        lines.append(txt)

    # 2. Analyse Heavy Hitter (> 4 matchs > 30)
    if curr_30 >= 4:
        icon = "💪"
        status = "[Série en cours]"
        if curr_30 >= global_records["Serie30"]:
            icon = "👑"; status = "[RECORD SAISON !]"
        elif curr_30 >= rec_perso_30:
            icon = "🚨"; status = "[Record Perso !]"
            
        txt = f"{icon} **{player}** : {curr_30} jours consécutifs > 30 pts {status} (Rec. perso : {rec_perso_30} | Rec. Team : {global_records['Serie30']})"
        lines.append(txt)
        
    return lines

def generate_weekly_report_data(df_full, target_deck_num=None):
    if df_full.empty or 'Deck' not in df_full.columns: return None

    df = df_full.copy()
    max_deck = int(df['Deck'].max())
    target_deck = int(target_deck_num) if target_deck_num else max_deck
    if target_deck == 0: return None
    
    week_df = df[df['Deck'] == target_deck].copy()
    if week_df.empty: return None
    
    first_pick = week_df['Pick'].min()
    last_pick = week_df['Pick'].max()
    s_date = get_date_from_pick(first_pick).strftime('%d/%m')
    e_date = get_date_from_pick(last_pick).strftime('%d/%m')
    
    team_avg = week_df['Score'].mean()
    prev_deck = target_deck - 1
    diff_txt = ""
    if prev_deck > 0:
        prev_df = df[df['Deck'] == prev_deck]
        if not prev_df.empty:
            diff = team_avg - prev_df['Score'].mean()
            sign = "+" if diff > 0 else ""
            diff_txt = f"{sign}{diff:.1f} vs Deck {prev_deck}"

    discord_color = 5763719 if team_avg >= 40 else (16705372 if team_avg >= 30 else 15548997)

    stats_week = week_df.groupby('Player')['Score'].agg(['mean', 'sum', 'count']).sort_values('mean', ascending=False)
    
    rotw_history = {}
    past_decks = df[df['Deck'] < target_deck]['Deck'].unique()
    for d in past_decks:
        if d == 0: continue
        ds = df[df['Deck'] == d].groupby('Player')['Score'].sum()
        if not ds.empty:
            for p in ds[ds == ds.max()].index: rotw_history[p] = rotw_history.get(p, 0) + 1

    weekly_podium = []
    for i, (player, row) in enumerate(stats_week.head(3).iterrows()):
        nb_rotw = rotw_history.get(player, 0)
        total_leader = week_df.groupby('Player')['Score'].sum().idxmax()
        is_official_winner = (player == total_leader)
        if is_official_winner: nb_rotw += 1
        rank = i + 1
        weekly_podium.append({'rank': rank, 'player': player, 'avg': float(row['mean']), 'total': int(row['sum']), 'rotw_count': nb_rotw, 'is_winner': is_official_winner})

    bp_series = week_df.groupby('Player')['IsBP'].sum()
    snipers = get_all_scorers(bp_series[bp_series > 0])
    
    max_g = week_df.groupby('Player')['Score'].count().max()
    elig = week_df.groupby('Player')['Score'].count()
    elig = elig[elig >= (max_g - 1)].index
    murailles = []
    if not elig.empty:
        sub = week_df[week_df['Player'].isin(elig)]
        carrots = sub[sub['Score'] < 20].groupby('Player')['Score'].count()
        clean = [p for p in elig if p not in carrots.index or carrots[p] == 0]
        murailles = [(p, 0) for p in clean]

    remontada = []
    if prev_deck > 0:
        c_avg = week_df.groupby('Player')['Score'].mean()
        p_avg = df[df['Deck'] == prev_deck].groupby('Player')['Score'].mean()
        prog = (c_avg - p_avg).dropna()
        remontada = get_winners_list(prog[prog > 0], maximize=True)
        remontada = [(p, f"+{v:.1f}") for p, v in remontada]

    sunday_winners = get_winners_list(week_df[week_df['Pick'] == int(week_df['Pick'].max())].groupby('Player')['Score'].max())

    perfects = []
    for p in week_df['Player'].unique():
        scores = week_df[week_df['Player'] == p]['Score']
        if len(scores) >= 4 and scores.min() >= 30: perfects.append(p)

    daily_mvps = []
    for p_num in sorted(week_df['Pick'].unique()):
        d_data = week_df[week_df['Pick'] == p_num]
        if d_data.empty: continue
        max_s = d_data['Score'].max()
        mvps = d_data[d_data['Score'] == max_s]['Player'].tolist()
        daily_mvps.append(f"**Pick #{int(p_num)}** : {', '.join(mvps)} ({int(max_s)})")

    # DEEP ANALYSIS (Direct & Simple)
    global_recs = get_global_records(df)
    analysis_lines = []
    for p in week_df['Player'].unique():
        # On ne passe plus le préfixe joueur ici, il est géré dans la fonction
        lines = analyze_streaks_direct(df, p, int(week_df['Pick'].max()), global_recs)
        if lines:
            analysis_lines.extend(lines)

    safe_zone_count = len(week_df[week_df['Score'] >= 30])
    
    return {
        "meta": {
            "week_num": target_deck,
            "max_deck": max_deck,
            "dates": f"Du {s_date} au {e_date}",
            "color": discord_color
        },
        "podium": weekly_podium,
        "perfect": perfects,
        "daily_mvp": daily_mvps,
        "analysis": analysis_lines,
        "lists": {
            "sniper": snipers,
            "muraille": murailles,
            "remontada": remontada,
            "sunday": sunday_winners
        },
        "stats": {
            "avg": team_avg,
            "diff": diff_txt,
            "bp": week_df['IsBP'].sum(),
            "carrots": len(week_df[week_df['Score'] < 20]),
            "safe_zone": safe_zone_count
        }
    }
