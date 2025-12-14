import pandas as pd
import numpy as np
import datetime
import random

# --- MOTEUR NARRATIF SPORTIF ---
CONTEXT_PHRASES = {
    "reliability_high": [
        "🛡️ **La Muraille :**", "🧱 **Intraitable :**", "🤖 **Le Métronome :**", "🔒 **Sécurité Totale :**"
    ],
    "scoring_high": [
        "💪 **En mode MVP :**", "🔥 **Main chaude :**", "🚀 **Stratosphérique :**", "⚔️ **Heavy Hitter :**"
    ],
    "record_break": [
        "👑 **HISTORIQUE !**", "🚨 **ALERTE RECORD !**", "🌟 **LÉGENDAIRE :**"
    ],
    "clutch": [
        "🧊 **Sang froid :**", "⚡ **Clutch Player :**"
    ]
}

def get_random_intro(category):
    return random.choice(CONTEXT_PHRASES.get(category, ["Analysis :"]))

def get_winners_list(series, maximize=True):
    if series.empty: return []
    target_val = series.max() if maximize else series.min()
    winners = series[series == target_val]
    return [(player, val) for player, val in winners.items()]

def get_global_records(df_full):
    records = {"NoCarrot": 0, "Serie30": 0}
    for p in df_full['Player'].unique():
        scores = df_full[df_full['Player'] == p].sort_values('Pick')['Score'].values
        temp = 0
        for s in scores:
            if s >= 20: temp += 1; records["NoCarrot"] = max(records["NoCarrot"], temp)
            else: temp = 0
        temp = 0
        for s in scores:
            if s >= 30: temp += 1; records["Serie30"] = max(records["Serie30"], temp)
            else: temp = 0
    return records

def analyze_streaks_deep(df, player, current_pick_limit, global_records):
    p_df = df[(df['Player'] == player) & (df['Pick'] <= current_pick_limit)].sort_values('Pick')
    if p_df.empty: return []

    scores = p_df['Score'].values
    curr_nc, record_perso_nc, temp = 0, 0, 0
    for s in scores:
        if s >= 20: temp += 1; record_perso_nc = max(record_perso_nc, temp)
        else: temp = 0
    for s in reversed(scores):
        if s >= 20: curr_nc += 1
        else: break
        
    curr_30, record_perso_30, temp = 0, 0, 0
    for s in scores:
        if s >= 30: temp += 1; record_perso_30 = max(record_perso_30, temp)
        else: temp = 0
    for s in reversed(scores):
        if s >= 30: curr_30 += 1
        else: break

    infos = []
    if curr_nc >= 8:
        if curr_nc >= global_records["NoCarrot"]:
            intro = get_random_intro("record_break")
            detail = f"{intro} **{curr_nc} matchs sans carotte** (Record Team Battu !)"
        elif curr_nc >= record_perso_nc and curr_nc > 5:
            intro = get_random_intro("record_break")
            detail = f"{intro} **{curr_nc} matchs sans carotte** (Nouveau record personnel)"
        else:
            intro = get_random_intro("reliability_high")
            detail = f"{intro} {curr_nc} matchs de suite > 20 pts (Série en cours)"
        infos.append(detail)

    if curr_30 >= 4:
        if curr_30 >= global_records["Serie30"]:
            intro = get_random_intro("record_break")
            detail = f"{intro} **{curr_30} cartons > 30 pts** (Record Team All-Time !)"
        else:
            intro = get_random_intro("scoring_high")
            detail = f"{intro} {curr_30} matchs consécutifs > 30 pts"
        infos.append(detail)
    return infos

def generate_weekly_report_data(df_full, target_deck_num=None):
    if df_full.empty or 'Deck' not in df_full.columns: return None

    df = df_full.copy()
    max_deck = int(df['Deck'].max())
    target_deck = int(target_deck_num) if target_deck_num else max_deck
    if target_deck == 0: return None
    
    week_df = df[df['Deck'] == target_deck].copy()
    if week_df.empty: return None
    
    s_date = week_df['Date'].min().strftime('%d/%m')
    e_date = week_df['Date'].max().strftime('%d/%m')
    
    # 1. TEAM
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

    # 2. PODIUM
    weekly_scores = week_df.groupby('Player')['Score'].sum().sort_values(ascending=False)
    rotw_history = {}
    past_decks = df[df['Deck'] < target_deck]['Deck'].unique()
    for d in past_decks:
        if d == 0: continue
        ds = df[df['Deck'] == d].groupby('Player')['Score'].sum()
        if not ds.empty:
            for p in ds[ds == ds.max()].index: rotw_history[p] = rotw_history.get(p, 0) + 1

    weekly_podium = []
    for i, (player, score) in enumerate(weekly_scores.head(3).items()):
        nb_rotw = rotw_history.get(player, 0)
        rank = i + 1
        if i == 0 and score == weekly_scores.iloc[0]: nb_rotw += 1
        elif i > 0 and score == weekly_scores.iloc[i-1]: rank = weekly_podium[-1]['rank']
        weekly_podium.append({'rank': rank, 'player': player, 'score': int(score), 'rotw_count': nb_rotw})

    # 3. STATS
    perfects = []
    for p in week_df['Player'].unique():
        scores = week_df[week_df['Player'] == p]['Score']
        if len(scores) >= 4 and scores.min() >= 30: perfects.append(p)

    daily_mvps = []
    for p_num in sorted(week_df['Pick'].unique()):
        d_data = week_df[week_df['Pick'] == p_num]
        max_s = d_data['Score'].max()
        mvps = d_data[d_data['Score'] == max_s]['Player'].tolist()
        daily_mvps.append(f"`Pick #{p_num}` {', '.join(mvps)} ({int(max_s)})")

    bp_sum = week_df.groupby('Player')['IsBP'].sum()
    snipers = get_winners_list(bp_sum[bp_sum > 0], maximize=True)
    
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
        prog = prog[prog > 0]
        remontada = get_winners_list(prog, maximize=True)
        remontada = [(p, f"+{v:.1f}") for p, v in remontada]

    last_pick = week_df['Pick'].max()
    sunday_winners = get_winners_list(week_df[week_df['Pick'] == last_pick].groupby('Player')['Score'].max())

    global_recs = get_global_records(df)
    analysis_lines = []
    for p in week_df['Player'].unique():
        lines = analyze_streaks_deep(df, p, week_df['Pick'].max(), global_recs)
        if lines:
            for l in lines: analysis_lines.append(f"👤 **{p}** : {l}")

    # 5. NEW KPI POSITIF : SAFE ZONE (Scores > 30)
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
            "safe_zone": safe_zone_count # Remplaçant du Clean Sheet/Floor
        }
    }
