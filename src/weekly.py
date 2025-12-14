import pandas as pd
import numpy as np
import datetime
import random

# --- MOTEUR NARRATIF (V22.2) ---
# Pour rendre le rapport moins "robotique" et plus "journaliste sportif"
PHRASES = {
    "increase": ["en nette progression", "qui hausse le ton", "sur une dynamique positive"],
    "stable": ["d'une régularité métronomique", "solide sur ses appuis", "toujours au rendez-vous"],
    "clean_sheet": ["Propre. Net. Sans bavure.", "La copie parfaite.", "Une semaine de patron."],
    "mvp_prefix": ["Patron du", "King du", "Masterclass au", "Dominant au"],
    "streak_break": ["chasse le record", "ne s'arrête plus", "est en mission"]
}

def get_winners_list(series, maximize=True):
    if series.empty: return []
    target_val = series.max() if maximize else series.min()
    winners = series[series == target_val]
    return [(player, val) for player, val in winners.items()]

def get_global_records(df_full):
    """Scan l'historique complet pour trouver les records absolus de l'équipe."""
    records = {"NoCarrot": 0, "Serie30": 0}
    for p in df_full['Player'].unique():
        scores = df_full[df_full['Player'] == p].sort_values('Pick')['Score'].values
        # No Carrot
        temp = 0
        for s in scores:
            if s >= 20: temp += 1; records["NoCarrot"] = max(records["NoCarrot"], temp)
            else: temp = 0
        # Série 30+
        temp = 0
        for s in scores:
            if s >= 30: temp += 1; records["Serie30"] = max(records["Serie30"], temp)
            else: temp = 0
    return records

def analyze_streaks_deep(df, player, current_pick_limit, global_records):
    """Analyse contextuelle : Actuel vs Perso vs Team."""
    p_df = df[(df['Player'] == player) & (df['Pick'] <= current_pick_limit)].sort_values('Pick')
    if p_df.empty: return []

    scores = p_df['Score'].values
    
    # Analyse No-Carrot (Fiabilité)
    curr_nc, record_perso_nc, temp = 0, 0, 0
    for s in scores:
        if s >= 20: temp += 1; record_perso_nc = max(record_perso_nc, temp)
        else: temp = 0
    for s in reversed(scores):
        if s >= 20: curr_nc += 1
        else: break
        
    # Analyse Heavy Hitter (>30)
    curr_30, record_perso_30, temp = 0, 0, 0
    for s in scores:
        if s >= 30: temp += 1; record_perso_30 = max(record_perso_30, temp)
        else: temp = 0
    for s in reversed(scores):
        if s >= 30: curr_30 += 1
        else: break

    infos = []
    
    # LOGIQUE D'AFFICHAGE INTELLIGENTE
    # On n'affiche que si la série est significative (>8)
    if curr_nc >= 8:
        # Détermination du statut
        if curr_nc >= global_records["NoCarrot"]:
            icon = "👑"; label = "RECORD TEAM ALL-TIME !"
        elif curr_nc >= record_perso_nc:
            icon = "🚨"; label = "RECORD PERSO BATTU !"
        else:
            icon = "🔥"; label = "Série en cours"
            
        txt = f"{icon} **Fiabilité** : {curr_nc} matchs sans carotte ({label} | Rec. Perso: {record_perso_nc} | Rec. Team: {global_records['NoCarrot']})"
        infos.append(txt)

    if curr_30 >= 4:
        if curr_30 >= global_records["Serie30"]:
            icon = "👑"; label = "RECORD TEAM ALL-TIME !"
        elif curr_30 >= record_perso_30:
            icon = "🚨"; label = "RECORD PERSO BATTU !"
        else:
            icon = "💪"; label = "En forme"
            
        txt = f"{icon} **Heavy Hitter** : {curr_30} matchs > 30 pts ({label} | Rec. Perso: {record_perso_30} | Rec. Team: {global_records['Serie30']})"
        infos.append(txt)
        
    return infos

def generate_weekly_report_data(df_full, target_deck_num=None):
    if df_full.empty or 'Deck' not in df_full.columns: return None

    df = df_full.copy()
    max_deck = int(df['Deck'].max())
    target_deck = int(target_deck_num) if target_deck_num else max_deck
    
    if target_deck == 0: return None
    
    week_df = df[df['Deck'] == target_deck].copy()
    if week_df.empty: return None
    
    # Dates du Deck (pour sous-titre)
    start_date = week_df['Date'].min().strftime('%d/%m')
    end_date = week_df['Date'].max().strftime('%d/%m')
    
    # 1. ANALYSE TEAM
    team_avg = week_df['Score'].mean()
    prev_deck = target_deck - 1
    diff_txt = ""
    
    if prev_deck > 0:
        prev_df = df[df['Deck'] == prev_deck]
        if not prev_df.empty:
            diff = team_avg - prev_df['Score'].mean()
            sign = "+" if diff > 0 else ""
            diff_txt = f"{sign}{diff:.1f} vs Deck {prev_deck}"

    # Couleur Discord (Vert/Jaune/Rouge)
    discord_color = 5763719 if team_avg >= 40 else (16705372 if team_avg >= 30 else 15548997)

    # 2. ROTW & PODIUM
    weekly_scores = week_df.groupby('Player')['Score'].sum().sort_values(ascending=False)
    
    # Historique des titres ROTW
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
        # Gestion ex-aequo 1ere place pour le titre
        if i == 0: 
            if score == weekly_scores.iloc[0]: nb_rotw += 1
        elif i > 0 and score == weekly_scores.iloc[i-1]: 
            rank = weekly_podium[-1]['rank']
            
        weekly_podium.append({'rank': rank, 'player': player, 'score': int(score), 'rotw_count': nb_rotw})

    # 3. STATS SPÉCIFIQUES
    # Perfect (Tous les matchs > 30) - Min 4 matchs joués
    perfects = []
    for p in week_df['Player'].unique():
        scores = week_df[week_df['Player'] == p]['Score']
        if len(scores) >= 4 and scores.min() >= 30: perfects.append(p)

    # MVP par Pick (Correction "Jours")
    daily_mvps = []
    for p_num in sorted(week_df['Pick'].unique()):
        d_data = week_df[week_df['Pick'] == p_num]
        max_s = d_data['Score'].max()
        mvps = d_data[d_data['Score'] == max_s]['Player'].tolist()
        daily_mvps.append(f"`Pick #{p_num}` {', '.join(mvps)} ({int(max_s)})")

    # Sniper & Muraille & Remontada
    bp_sum = week_df.groupby('Player')['IsBP'].sum()
    snipers = get_winners_list(bp_sum[bp_sum > 0], maximize=True)
    
    # Muraille : ceux qui ont joué le max possible et 0 carotte
    max_g = week_df.groupby('Player')['Score'].count().max()
    elig = week_df.groupby('Player')['Score'].count()
    elig = elig[elig >= (max_g - 1)].index
    murailles = []
    if not elig.empty:
        sub = week_df[week_df['Player'].isin(elig)]
        carrots = sub[sub['Score'] < 20].groupby('Player')['Score'].count()
        clean = [p for p in elig if p not in carrots.index or carrots[p] == 0]
        murailles = [(p, 0) for p in clean]

    # Remontada
    remontada = []
    if prev_deck > 0:
        c_avg = week_df.groupby('Player')['Score'].mean()
        p_avg = df[df['Deck'] == prev_deck].groupby('Player')['Score'].mean()
        prog = (c_avg - p_avg).dropna()
        prog = prog[prog > 0]
        remontada = get_winners_list(prog, maximize=True)
        remontada = [(p, f"+{v:.1f}") for p, v in remontada]

    # Sunday Clutch (Dernier pick)
    sunday_winners = []
    if not week_df.empty:
        last_pick = week_df['Pick'].max()
        s_df = week_df[week_df['Pick'] == last_pick]
        sunday_winners = get_winners_list(s_df.groupby('Player')['Score'].max())

    # 4. DEEP ANALYSIS (Narrative)
    global_recs = get_global_records(df)
    analysis_lines = []
    for p in week_df['Player'].unique():
        lines = analyze_streaks_deep(df, p, week_df['Pick'].max(), global_recs)
        if lines:
            for l in lines: analysis_lines.append(f"👤 **{p}** : {l}")

    return {
        "meta": {
            "week_num": target_deck,
            "max_deck": max_deck,
            "dates": f"Du {start_date} au {end_date}",
            "color": discord_color
        },
        "podium": weekly_podium,
        "rotw_leaderboard": sorted(rotw_history.items(), key=lambda x: x[1], reverse=True)[:5],
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
            "clean_sheet": week_df['Score'].min() >= 25
        }
    }
