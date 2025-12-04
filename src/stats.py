import pandas as pd
import numpy as np
import streamlit as st

# OPTIMISATION : CACHING STATS CALCULATION
@st.cache_data(ttl=300, show_spinner=False)
def compute_stats(df, bp_map, daily_max_map):
    stats = []
    if df.empty: return pd.DataFrame()
    latest_pick = df['Pick'].max()
    season_avgs = df.groupby('Player')['Score'].mean()
    season_avgs_raw = df.groupby('Player')['ScoreVal'].mean()
    df_15 = df[df['Pick'] > (latest_pick - 15)]
    avg_15 = df_15.groupby('Player')['Score'].mean()
    df_10 = df[df['Pick'] > (latest_pick - 10)]
    avg_10 = df_10.groupby('Player')['Score'].mean()
    trend_data = {}
    for p, d in df.sort_values('Pick').groupby('Player'): trend_data[p] = d['Score'].tail(20).tolist()

    for p in df['Player'].unique():
        d = df[df['Player'] == p].sort_values('Pick')
        scores = d['Score'].values
        scores_raw = d['ScoreVal'].values
        picks = d['Pick'].values
        bonuses = d['IsBonus'].values
        z_scores = d['ZScore'].values

        bonus_data = d[d['IsBonus'] == True]
        scores_with_bonus = bonus_data['Score'].values
        scores_without_bonus = d[d['IsBonus'] == False]['Score'].values
        avg_with_bonus = scores_with_bonus.mean() if len(scores_with_bonus) > 0 else 0
        avg_without_bonus = scores_without_bonus.mean() if len(scores_without_bonus) > 0 else 0
        best_with_bonus = scores_with_bonus.max() if len(scores_with_bonus) > 0 else 0
        best_without_bonus = scores_without_bonus.max() if len(scores_without_bonus) > 0 else 0

        current_no_carrot_streak = 0
        for s in reversed(scores):
            if s >= 20: current_no_carrot_streak += 1
            else: break

        max_no_carrot = 0
        current_count = 0
        for s in scores:
            if s >= 20:
                current_count += 1
                if current_count > max_no_carrot: max_no_carrot = current_count
            else:
                current_count = 0

        max_alien_streak = 0
        current_alien = 0
        for s in scores:
            if s >= 60:
                current_alien += 1
                if current_alien > max_alien_streak: max_alien_streak = current_alien
            else:
                current_alien = 0

        try:
            vals, counts = np.unique(scores, return_counts=True)
            max_count_idx = np.argmax(counts)
            mode_score = vals[max_count_idx]
            mode_count = counts[max_count_idx]
        except:
            mode_score = 0
            mode_count = 0

        spread = scores.max() - scores.min()

        # ... après spread = ...

        # CALCUL TENDANCE 7 DERNIERS MATCHS
        scores_last_7 = d['Score'].tail(7)
        avg_last_7 = scores_last_7.mean() if len(scores_last_7) > 0 else 0
        diff_7 = avg_last_7 - scores.mean()

        if diff_7 >= 1: trend_icon = "↗️"
        elif diff_7 <= -1: trend_icon = "↘️"
        else: trend_icon = "➡️"

        # ... continue vers stats.append ...

        streak_30 = 0
        for s in reversed(scores):
            if s >= 30: streak_30 += 1
            else: break
        last_5 = scores[-5:]
        last5_avg = last_5.mean() if len(scores) >= 5 else scores.mean()
        momentum = last5_avg - scores.mean()

        # OPTIMISATION : Calcul automatique des BP depuis les '!'
        bp_count = d['IsBP'].sum()

        alpha_count = 0; bonus_points_gained = 0; bonus_scores_list = []

        for i, (pick_num, score) in enumerate(zip(picks, scores)):
            if pick_num in daily_max_map and score >= daily_max_map[pick_num] and score > 0: alpha_count += 1
            if bonuses[i]:
                gain = score - scores_raw[i]
                bonus_points_gained += gain
                bonus_scores_list.append(score)

        best_bonus = max(bonus_scores_list) if bonus_scores_list else 0
        worst_bonus = min(bonus_scores_list) if bonus_scores_list else 0
        avg_bonus_score = np.mean(bonus_scores_list) if bonus_scores_list else 0
        s_avg = season_avgs.get(p, 0)
        s_avg_raw = season_avgs_raw.get(p, 0)
        l15_avg = avg_15.get(p, s_avg)
        l10_avg = avg_10.get(p, s_avg)
        progression_pct = ((l15_avg - s_avg) / s_avg) * 100 if s_avg > 0 else 0
        reliability_pct = ((len(scores) - len(scores[scores < 20])) / len(scores)) * 100
        avg_z = np.mean(z_scores) if len(z_scores) > 0 else 0

        count_20_30 = len(scores[(scores >= 20) & (scores <= 30)])

        stats.append({
            'Player': p, 'Total': scores.sum(), 'Moyenne': scores.mean(), 'Moyenne_Raw': s_avg_raw,
            'StdDev': scores.std(), 'Best': scores.max(), 'Best_Raw': scores_raw.max(),
            'Worst': scores.min(), 'Worst_Raw': scores_raw.min(), 'Last': scores[-1],
            'LastIsBonus': bonuses[-1] if len(bonuses) > 0 else False, 'Last5': last5_avg, 'Last10': l10_avg, 'Last15': l15_avg,
            'Streak30': streak_30, 'Count30': len(scores[scores >= 30]), 'Count40': len(scores[scores >= 40]),
            'Count35': len(scores[scores > 35]), 'Count2030': count_20_30,
            'Carottes': len(scores[scores < 20]), 'Nukes': len(scores[scores >= 50]),
            'BP_Count': bp_count, 'Alpha_Count': alpha_count,
            'Bonus_Gained': bonus_points_gained, 'Best_Bonus': best_bonus, 'Worst_Bonus': worst_bonus,
            'Avg_Bonus': avg_bonus_score, 'Momentum': momentum, 'Games': len(scores),
            'ProgressionPct': progression_pct, 'ReliabilityPct': reliability_pct, 'AvgZ': avg_z,
            'Trend': trend_data.get(p, []), 'AvgWithBonus': avg_with_bonus, 'AvgWithoutBonus': avg_without_bonus, 'BonusPlayed': len(scores_with_bonus),
            'CurrentNoCarrot': current_no_carrot_streak, 'MaxNoCarrot': max_no_carrot, 'ModeScore': mode_score, 'ModeCount': mode_count, 'Spread': spread,
            'Trend7Icon': trend_icon,
            'MaxAlien': max_alien_streak
        })
    return pd.DataFrame(stats)

def get_comparative_stats(df, current_pick, lookback=15):
    start_pick = max(1, current_pick - lookback)
    current_stats = df.groupby('Player')['Score'].agg(['sum', 'mean'])
    current_stats['rank'] = current_stats['sum'].rank(ascending=False)
    df_past = df[df['Pick'] <= start_pick]
    if df_past.empty: return pd.DataFrame()
    past_stats = df_past.groupby('Player')['Score'].agg(['sum', 'mean'])
    past_stats['rank'] = past_stats['sum'].rank(ascending=False)
    stats_delta = pd.DataFrame(index=current_stats.index)
    stats_delta['mean_diff'] = current_stats['mean'] - past_stats['mean']
    stats_delta['rank_diff'] = past_stats['rank'] - current_stats['rank']
    return stats_delta
