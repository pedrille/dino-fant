import pandas as pd
import numpy as np
import datetime

# --- CONFIGURATION TEXTE ---
COMMENTS = {
    "increase": ["en nette progression", "sur une pente ascendante", "qui accélère la cadence"],
    "stable": ["solide sur ses appuis", "d'une régularité métronomique", "toujours présent"],
    "decrease": ["en léger repli", "qui doit se relancer", "un peu court cette semaine"],
    "fire": ["INARRÊTABLE", "EN FEU", "STRATOSPHÉRIQUE", "IMPÉRIAL"]
}

def get_winners_list(series, maximize=True):
    if series.empty: return []
    target_val = series.max() if maximize else series.min()
    winners = series[series == target_val]
    return [(player, val) for player, val in winners.items()]

def get_global_records(df_full):
    """Calcule les records absolus de l'équipe (toute la saison) pour la comparaison."""
    max_nc_global = 0
    max_30_global = 0
    
    # On scanne chaque joueur pour trouver le record absolu de l'équipe
    for p in df_full['Player'].unique():
        scores = df_full[df_full['Player'] == p].sort_values('Pick')['Score'].values
        
        # No Carrot
        temp = 0
        for s in scores:
            if s >= 20: temp += 1; max_nc_global = max(max_nc_global, temp)
            else: temp = 0
            
        # Série 30+
        temp = 0
        for s in scores:
            if s >= 30: temp += 1; max_30_global = max(max_30_global, temp)
            else: temp = 0
            
    return {"NoCarrot": max_nc_global, "Serie30": max_30_global}

def calculate_advanced_streaks(df, player, current_pick_limit, global_records):
    """Analyse profonde des dynamiques joueur vs histoire."""
    p_df = df[(df['Player'] == player) & (df['Pick'] <= current_pick_limit)].sort_values('Pick')
    if p_df.empty: return None

    scores = p_df['Score'].values
    
    # 1. Analyse Série No-Carrot
    curr_nc, record_perso_nc, temp = 0, 0, 0
    for s in scores:
        if s >= 20: temp += 1; record_perso_nc = max(record_perso_nc, temp)
        else: temp = 0
    for s in reversed(scores):
        if s >= 20: curr_nc += 1
        else: break
        
    # 2. Analyse Série > 30 (La "Safe Zone")
    curr_30, record_perso_30, temp = 0, 0, 0
    for s in scores:
        if s >= 30: temp += 1; record_perso_30 = max(record_perso_30, temp)
        else: temp = 0
    for s in reversed(scores):
        if s >= 30: curr_30 += 1
        else: break

    # Rédaction du commentaire "Intelligent"
    infos = []
    
    # Seuil d'affichage pour ne pas spammer (10 pour NC, 4 pour 30+)
    if curr_nc >= 10:
        status = "🔥"
        if curr_nc >= global_records["NoCarrot"]: status = "👑 RECORD ALL-TIME !"
        elif curr_nc >= record_perso_nc: status = "🚨 RECORD PERSO !"
        
        txt = f"**{status} Série Fiabilité :** {curr_nc} matchs sans carotte (Record Team: {global_records['NoCarrot']})"
        infos.append(txt)

    if curr_30 >= 4:
        status = "🔥"
        if curr_30 >= global_records["Serie30"]: status = "👑 RECORD ALL-TIME !"
        elif curr_30 >= record_perso_30: status = "🚨 RECORD PERSO !"
        
        txt = f"**{status} Série 'Heavy Hitter' :** {curr_30} matchs > 30 pts (Record Team: {global_records['Serie30']})"
        infos.append(txt)
        
    return infos

def generate_weekly_report_data(df_full, target_deck_num=None):
    """
    Génère le rapport pour un Deck spécifique (ou le dernier par défaut).
    """
    if df_full.empty or 'Deck' not in df_full.columns: return None

    df = df_full.copy()
    
    # GESTION DU SELECTEUR
    max_deck = int(df['Deck'].max())
    if target_deck_num is None:
        target_deck = max_deck
    else:
        target_deck = int(target_deck_num)
    
    if target_deck == 0: return None
    
    # Données de la semaine (Deck)
    week_df = df[df['Deck'] == target_deck].copy()
    if week_df.empty: return None
    
    # Dates & Metadata
    start_date_obj = week_df['Date'].min()
    end_date_obj = start_date_obj + datetime.timedelta(days=6)
    start_date = start_date_obj.strftime('%d/%m')
    end_date = end_date_obj.strftime('%d/%m')
    
    # --- 1. TEAM PULSE & N-1 ---
    team_avg_curr = week_df['Score'].mean()
    
    # Comparatif N-1
    prev_deck = target_deck - 1
    diff_txt = ""
    pulse_color = 13504833 # Rouge par défaut
    
    if prev_deck > 0:
        prev_df = df[df['Deck'] == prev_deck]
        if not prev_df.empty:
            prev_avg = prev_df['Score'].mean()
            diff = team_avg_curr - prev_avg
            sign = "+" if diff > 0 else ""
            diff_txt = f"({sign}{diff:.1f} vs Deck {prev_deck})"
    
    # Détermination Couleur Dynamique Discord
    if team_avg_curr >= 40: pulse_color = 5763719 # Vert (#57F287)
    elif team_avg_curr >= 30: pulse_color = 16705372 # Jaune (#FEE75C)
    else: pulse_color = 15548997 # Rouge (#ED4245)

    # --- 2. PODIUM & ANALYSE ROTW ---
    weekly_scores = week_df.groupby('Player')['Score'].sum().sort_values(ascending=False)
    weekly_podium = []
    
    # Calcul historique pour le ROTW
    rotw_history = {}
    all_past_decks = df[df['Deck'] < target_deck]['Deck'].unique()
    for d in all_past_decks:
        if d == 0: continue
        d_scores = df[df['Deck'] == d].groupby('Player')['Score'].sum()
        if not d_scores.empty:
            winners = d_scores[d_scores == d_scores.max()].index.tolist()
            for p in winners: rotw_history[p] = rotw_history.get(p, 0) + 1

    for i, (player, score) in enumerate(weekly_scores.head(3).items()):
        nb_titles = rotw_history.get(player, 0)
        rank = i + 1
        if i == 0 and score == weekly_scores.iloc[0]: nb_titles += 1 # Ajout du titre virtuel
        weekly_podium.append({'rank': rank, 'player': player, 'score': int(score), 'titles': nb_titles})

    # --- 3. LE PERFECT (Nouveauté) ---
    # Joueurs ayant joué au moins 4 matchs et n'ayant JAMAIS fait moins de 30
    perfect_players = []
    for p in week_df['Player'].unique():
        p_scores = week_df[week_df['Player'] == p]['Score']
        if len(p_scores) >= 4 and p_scores.min() >= 30:
            perfect_players.append(p)

    # --- 4. MVP QUOTIDIEN (Nouveauté) ---
    daily_mvps = []
    picks_in_deck = sorted(week_df['Pick'].unique())
    for p_num in picks_in_deck:
        day_data = week_df[week_df['Pick'] == p_num]
        if not day_data.empty:
            max_s = day_data['Score'].max()
            mvps = day_data[day_data['Score'] == max_s]['Player'].tolist()
            # On formate la date (ex: Lun, Mar...)
            day_name = day_data['Date'].iloc[0].strftime('%a')
            daily_mvps.append(f"`{day_name}` {', '.join(mvps)} ({int(max_s)})")

    # --- 5. ANALYSE PROFONDE (Deep Stats) ---
    global_records = get_global_records(df) # On calcule les records de l'année
    streaks_analysis = []
    current_limit = week_df['Pick'].max()
    
    for p in week_df['Player'].unique():
        lines = calculate_advanced_streaks(df, p, current_limit, global_records)
        if lines:
            for l in lines:
                streaks_analysis.append(f"👤 **{p}** : {l}")

    # --- 6. AUTRES STATS ---
    # Sniper
    weekly_bp = week_df.groupby('Player')['IsBP'].sum()
    snipers = get_winners_list(weekly_bp[weekly_bp > 0], maximize=True)
    
    # Muraille (Ceux qui ont 0 carotte et joué le max de matchs)
    max_games = week_df.groupby('Player')['Score'].count().max()
    eligible = week_df.groupby('Player')['Score'].count()
    eligible = eligible[eligible >= (max_games - 1)].index # Tolérance 1 match
    
    murailles = []
    if not eligible.empty:
        sub = week_df[week_df['Player'].isin(eligible)]
        carrots = sub[sub['Score'] < 20].groupby('Player')['Score'].count()
        # On ne garde que ceux qui ont 0
        clean_players = carrots[carrots == 0].index.tolist()
        # On ajoute ceux qui ne sont pas dans la liste des carottes (donc 0)
        others = [p for p in eligible if p not in carrots.index]
        all_clean = list(set(clean_players + others))
        murailles = [(p, "0") for p in all_clean]

    # Remontada
    remontada_winners = []
    if prev_deck > 0:
        curr_avg = week_df.groupby('Player')['Score'].mean()
        prev_avg = df[df['Deck'] == prev_deck].groupby('Player')['Score'].mean()
        progression = (curr_avg - prev_avg).dropna()
        progression = progression[progression > 0]
        remontada_winners = get_winners_list(progression, maximize=True)
        remontada_winners = [(p, f"+{v:.1f}") for p, v in remontada_winners]

    # Sunday Clutch
    last_pick = week_df['Pick'].max()
    sunday_df = week_df[week_df['Pick'] == last_pick]
    sunday_winners = get_winners_list(sunday_df.groupby('Player')['Score'].max(), maximize=True)

    return {
        "meta": {
            "week_num": target_deck,
            "max_deck": max_deck, # Pour le sélecteur
            "start_date": start_date,
            "end_date": end_date,
            "discord_color": pulse_color
        },
        "podium": weekly_podium,
        "perfect": perfect_players,
        "daily_mvp": daily_mvps,
        "streaks_analysis": streaks_analysis,
        "sniper": snipers,
        "muraille": murailles,
        "remontada": remontada_winners,
        "sunday_clutch": sunday_winners,
        "team_stats": {
            "avg": team_avg_curr,
            "diff_txt": diff_txt,
            "bp": week_df['IsBP'].sum(),
            "carrots": len(week_df[week_df['Score'] < 20]),
            "clean_sheet": week_df['Score'].min() >= 25
        }
    }
