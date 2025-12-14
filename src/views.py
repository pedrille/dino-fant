import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Imports internes
from src.config import *
from src.ui import kpi_card, section_title, render_gauge
from src.utils import get_uniform_color, send_weekly_report_discord, format_winners_list
from src.stats import compute_stats, get_head_to_head_stats
from src.weekly import generate_weekly_report_data

# --- 1. DASHBOARD ---
def render_dashboard(day_df, full_stats, latest_pick, team_avg_per_pick, team_streak_nc, df):
    section_title("RAPTORS <span class='highlight'>DASHBOARD</span>", f"Daily Briefing • Pick #{int(latest_pick)}")
    top = day_df.iloc[0]

    # ALIGNEMENT CORRECT DU SCORE ET DES BADGES
    val_suffix = ""
    if 'IsBonus' in top and top['IsBonus']: val_suffix += " 🌟x2"
    if 'IsBP' in top and top['IsBP']: val_suffix += " 🎯BP"

    sub_html = f"<div><span style='font-size:1.6rem; font-weight:800'>{int(top['Score'])} PTS</span> <span style='font-size:1rem; color:{C_GOLD}; font-weight:700'>{val_suffix}</span></div>"

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="glass-card kpi-dashboard-fixed" style="text-align:center"><div class="kpi-label">MVP DU SOIR</div><div class="kpi-num" style="color:{C_GOLD}">{top['Player']}</div><div class="kpi-sub" style="color:{C_ACCENT}">{sub_html}</div></div>""", unsafe_allow_html=True)

    total_day = day_df['Score'].sum()
    with c2: kpi_card("TOTAL TEAM SOIR", int(total_day), "POINTS", is_fixed=True)

    team_daily_avg = day_df['Score'].mean()
    diff_perf = ((team_daily_avg - team_avg_per_pick) / team_avg_per_pick) * 100
    perf_col = C_GREEN if diff_perf > 0 else "#F87171"
    with c3: kpi_card("PERF. TEAM SOIR", f"{diff_perf:+.1f}%", "VS MOY. PÉRIODE", perf_col, is_fixed=True)

    col_streak = C_GREEN if team_streak_nc > 0 else C_RED
    with c4: kpi_card("SÉRIE TEAM NO-CARROT", f"{team_streak_nc}", "JOURS CONSÉCUTIFS", col_streak, is_fixed=True)

    leader = full_stats.sort_values('Total', ascending=False).iloc[0]
    with c5: kpi_card("LEADER PÉRIODE", leader['Player'], f"TOTAL: {int(leader['Total'])}", C_ACCENT, is_fixed=True)

    day_merged = pd.merge(day_df, full_stats[['Player', 'Moyenne']], on='Player')
    day_merged['Delta'] = day_merged['Score'] - day_merged['Moyenne']
    top_clutch = day_merged.sort_values('Delta', ascending=False).head(3)

    c_perf, c_clutch = st.columns([2, 1])
    with c_perf:
        st.markdown("<h3 style='margin-bottom:10px; margin-top:0; color:#FFF; font-family:Rajdhani; font-weight:700'>📊 SCORES DU SOIR</h3>", unsafe_allow_html=True)
        
        # --- RESTAURATION DES COULEURS ---
        # On applique la fonction get_uniform_color (qui est dans src.utils et renvoie Rouge/Gris/Vert)
        day_df['BarColor'] = day_df['Score'].apply(get_uniform_color)
        
        # On utilise color_discrete_map="identity" pour dire à Plotly d'utiliser les codes hexadécimaux de la colonne BarColor
        fig = px.bar(day_df, x='Player', y='Score', text='Score', color='BarColor', color_discrete_map="identity")
        
        fig.update_traces(textposition='outside', marker_line_width=0, textfont_size=14, textfont_family="Rajdhani", cliponaxis=False)
        fig.add_hline(y=team_avg_per_pick, line_dash="dot", line_color=C_TEXT, annotation_text="Moy. Team", annotation_position="top right")
        
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA', 'family': 'Inter'}, yaxis=dict(showgrid=False, visible=False), xaxis=dict(title=None, tickfont=dict(size=14, family='Rajdhani', weight=600)), height=350, showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    with c_clutch:
        st.markdown("<h3 style='margin-bottom:10px; margin-top:0; color:#FFF; font-family:Rajdhani; font-weight:700'>⚡ CLUTCH DU SOIR</h3>", unsafe_allow_html=True)
        st.markdown("<div class='chart-desc'>Joueurs ayant le plus dépassé leur moyenne habituelle ce soir.</div>", unsafe_allow_html=True)
        for i, row in enumerate(top_clutch.itertuples()):
            st.markdown(f"""<div class='glass-card' style='margin-bottom:10px; padding:12px'><div style='display:flex; justify-content:space-between; align-items:center'><div><div style='font-weight:700; color:{C_TEXT}'>{row.Player}</div><div style='font-size:0.75rem; color:#666'>Moy: {row.Moyenne:.1f}</div></div><div style='text-align:right'><div style='font-size:1.2rem; font-weight:800; color:{C_GREEN}'>+{row.Delta:.1f}</div><div style='font-size:0.8rem; color:#888'>{int(row.Score)} pts</div></div></div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:30px'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#FFF; font-family:Rajdhani; font-weight:700; margin-bottom:20px'>🏆 ANALYSE & CLASSEMENTS</h3>", unsafe_allow_html=True)
    c_gen, c_form, c_text = st.columns(3)
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}

    df_minus_last = df[df['Pick'] < latest_pick].groupby('Player')['Score'].sum().rank(ascending=False)
    current_ranks = full_stats.set_index('Player')['Total'].rank(ascending=False)

    with c_gen:
        st.markdown(f"<div class='glass-card' style='height:100%'><div style='color:{C_ACCENT}; font-family:Rajdhani; font-weight:700; margin-bottom:5px'>🏆 TOP 5 PÉRIODE</div><div class='chart-desc'>Classement de la période sélectionnée.</div>", unsafe_allow_html=True)
        top_5_season = full_stats.sort_values('Total', ascending=False).head(5).reset_index()
        for i, r in top_5_season.iterrows():
            medal = medals.get(i, f"{i+1}")
            prev_rank = df_minus_last.get(r['Player'], i+1)
            curr_rank = current_ranks.get(r['Player'], i+1)
            diff = prev_rank - curr_rank
            evo = f"<span style='color:{C_GREEN}; font-size:0.8rem'>▲{int(diff)}</span>" if diff > 0 else (f"<span style='color:{C_RED}; font-size:0.8rem'>▼{int(abs(diff))}</span>" if diff < 0 else "<span style='color:#444; font-size:0.8rem'>=</span>")
            st.markdown(f"<div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px'><div style='display:flex; align-items:center; gap:10px'><div style='font-size:1.2rem; width:20px'>{medal}</div><div style='font-family:Rajdhani; font-weight:600; font-size:1rem; color:#FFF'>{r['Player']}</div></div><div style='text-align:right'><span style='font-family:Rajdhani; font-weight:700; color:{C_ACCENT}'>{int(r['Total'])}</span> {evo}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_form:
        st.markdown(f"<div class='glass-card' style='height:100%'><div style='color:{C_GREEN}; font-family:Rajdhani; font-weight:700; margin-bottom:5px'>🔥 TOP 5 FORME (15J)</div><div class='chart-desc'>Meilleures moyennes sur les 15 derniers picks.</div>", unsafe_allow_html=True)
        top_5_form = full_stats.sort_values('Last15', ascending=False).head(5).reset_index()
        for i, r in top_5_form.iterrows():
            medal = medals.get(i, f"{i+1}")
            st.markdown(f"<div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:8px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:6px'><div style='display:flex; align-items:center; gap:10px'><div style='font-size:1.2rem; width:20px'>{medal}</div><div style='font-family:Rajdhani; font-weight:600; font-size:1rem; color:#FFF'>{r['Player']}</div></div><div style='font-family:Rajdhani; font-weight:700; color:{C_GREEN}'>{r['Last15']:.1f}</div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_text:
        st.markdown(f"""
        <div class='glass-card' style='height:100%'>
            <div style='color:{C_TEXT}; font-family:Rajdhani; font-weight:700; margin-bottom:5px'>🎨 TEXTURE DES PICKS</div>
            <div class='chart-desc'>Rouge < 20 | Gris 20-39 | Vert 40+.</div>
        """ , unsafe_allow_html=True)

        bins = [-1, 19, 39, 200]
        labels = ['< 20', '20-39', '40+']
        day_df['Range'] = pd.cut(day_df['Score'], bins=bins, labels=labels)
        dist_counts = day_df['Range'].value_counts().reset_index()
        dist_counts.columns = ['Range', 'Count']

        color_map = {'< 20': C_RED, '20-39': "#374151", '40+': C_GREEN}

        fig_donut = px.pie(dist_counts, values='Count', names='Range', hole=0.4, color='Range', color_discrete_map=color_map)
        fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=220, paper_bgcolor='rgba(0,0,0,0)')
        fig_donut.update_traces(textposition='inside', textinfo='label+value', textfont_size=14)
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- 2. TEAM HQ ---
def render_team_hq(df, latest_pick, team_rank, team_history, team_avg_per_pick, total_bp_team, full_stats):
    section_title("TEAM <span class='highlight'>HQ</span>", "Vue d'ensemble de l'effectif")
    total_pts_season = df['Score'].sum()
    daily_agg = df.groupby('Pick')['Score'].sum()
    best_night = daily_agg.max(); worst_night = daily_agg.min(); avg_night = daily_agg.mean()

    total_nukes_team = len(df[df['Score'] >= 50])
    total_carrots_team = len(df[df['Score'] < 20])
    safe_zone_team = len(df[df['Score'] > 35])

    total_bonus_played = len(df[df['IsBonus'] == True])
    current_rank_disp = f"#{int(team_rank)}" if team_rank > 0 else "-"
    best_rank_ever = f"#{min(team_history)}" if len(team_history) > 0 else "-"
    bonus_df = df[df['IsBonus'] == True]
    avg_bonus_team = bonus_df['Score'].mean() if not bonus_df.empty else 0
    daily_totals = df.groupby('Pick')['Score'].sum()
    avg_team_15 = daily_totals[daily_totals.index > (latest_pick - 15)].mean() if len(daily_totals) > 15 else daily_totals.mean()

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("TOTAL PÉRIODE", int(total_pts_season), "POINTS CUMULÉS", C_GOLD)
    with k2: kpi_card("MOYENNE / PICK", f"{team_avg_per_pick:.1f}", "PAR JOUEUR", "#FFF")
    with k3: kpi_card("MOYENNE ÉQUIPE / SOIR", f"{int(avg_night)}", "TOTAL COLLECTIF", C_BLUE)

    diff_dyn_team = ((avg_team_15 - avg_night) / avg_night) * 100
    col_dyn_team = C_GREEN if diff_dyn_team > 0 else C_RED
    with k4: kpi_card("DYNAMIQUE 15J", f"{diff_dyn_team:+.1f}%", "VS MOY. PÉRIODE", col_dyn_team)

    st.markdown("<br>", unsafe_allow_html=True)

    c_grid, c_rec = st.columns([3, 1], gap="medium")
    with c_grid:
        g1, g2, g3 = st.columns(3, gap="medium")
        with g1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(latest_pick)}</div><div class='stat-mini-lbl'>MATCHS JOUÉS</div></div>", unsafe_allow_html=True)
        with g2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_ACCENT}'>{current_rank_disp}</div><div class='stat-mini-lbl'>CLASSEMENT ACTUEL</div></div>", unsafe_allow_html=True)
        with g3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GOLD}'>{best_rank_ever}</div><div class='stat-mini-lbl'>BEST RANK EVER</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

        g4, g5, g6 = st.columns(3, gap="medium")
        with g4: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BLUE}'>{safe_zone_team}</div><div class='stat-mini-lbl'>SAFE ZONE (> 35 PTS)</div></div>", unsafe_allow_html=True)
        with g5: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GREEN}'>{total_nukes_team}</div><div class='stat-mini-lbl'>NUKES (> 50 PTS)</div></div>", unsafe_allow_html=True)
        with g6: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_RED}'>{total_carrots_team}</div><div class='stat-mini-lbl'>CAROTTES (< 20 PTS)</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)

        g7, g8, g9 = st.columns(3, gap="medium")
        with g7: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_PURPLE}'>{total_bp_team}</div><div class='stat-mini-lbl'>TOTAL BEST PICKS 🎯</div></div>", unsafe_allow_html=True)
        with g8: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BONUS}'>{total_bonus_played}</div><div class='stat-mini-lbl'>BONUS JOUÉS 🌟</div></div>", unsafe_allow_html=True)
        with g9: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{avg_bonus_team:.1f}</div><div class='stat-mini-lbl'>MOYENNE SOUS BONUS</div></div>", unsafe_allow_html=True)

    with c_rec:
        st.markdown(f"""<div class="glass-card" style="height:100%; display:flex; flex-direction:column; justify-content:center; padding:25px;"><div style="text-align:center; margin-bottom:20px; font-family:Rajdhani; font-weight:700; font-size:1.1rem; color:#AAA; letter-spacing:1px; border-bottom:1px solid #333; padding-bottom:10px;">RECORDS & MOYENNE</div><div class="hq-card-row"><div class="hq-lbl">🚀 RECORD</div><div class="hq-val" style="color:{C_GREEN}">{int(best_night)}</div></div><div class="hq-card-row"><div class="hq-lbl">⚖️ MOYENNE</div><div class="hq-val">{int(avg_night)}</div></div><div class="hq-card-row"><div class="hq-lbl">🧱 PLANCHER</div><div class="hq-val" style="color:{C_ACCENT}">{int(worst_night)}</div></div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-bottom:30px'></div>", unsafe_allow_html=True)

    st.markdown("### 🏁 LA COURSE AU TITRE (EVOLUTION)")
    st.markdown("<div class='chart-desc'>Cliquez sur ▶️ pour lancer la course. L'animation est fluide et gérée par le navigateur.</div>", unsafe_allow_html=True)

    if not df.empty:
        pivoted = df.pivot_table(index='Pick', columns='Player', values='Score', aggfunc='sum').fillna(0)
        cum_df = pivoted.cumsum()
        race_df = cum_df.reset_index().melt(id_vars='Pick', var_name='Player', value_name='Total')
        race_df = race_df.sort_values('Pick')
        global_max = race_df['Total'].max() * 1.1

        fig_race = px.bar(
            race_df,
            x="Total",
            y="Player",
            color="Player",
            text="Total",
            orientation='h',
            animation_frame="Pick",
            animation_group="Player",
            range_x=[0, global_max],
            color_discrete_map=PLAYER_COLORS
        )

        fig_race.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font={'color': '#AAA', 'family': 'Rajdhani'},
            xaxis=dict(visible=False, range=[0, global_max]),
            yaxis=dict(title=None, tickfont=dict(size=14, weight=700)),
            height=500,
            margin=dict(l=0, r=50, t=0, b=0),
            showlegend=False,
            yaxis_categoryorder='total ascending'
        )
        try:
            fig_race.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 150
            fig_race.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 100
            fig_race.layout.sliders[0].currentvalue = {"prefix": "PICK #", "font": {"size": 20, "color": C_ACCENT}}
            fig_race.layout.sliders[0].pad = {"t": 50}
        except: pass

        fig_race.update_traces(textposition='outside', marker_line_width=0, textfont_size=14, textfont_color="#FFF")
        st.plotly_chart(fig_race, use_container_width=True)

    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)

    st.markdown("### 🔥 HEATMAP")
    st.markdown(f"<div class='chart-desc'>Rouge < 35 | Gris 35-45 (Neutre) | Vert > 45.</div>", unsafe_allow_html=True)

    heat_filter = st.selectbox("📅 Filtrer la Heatmap", ["VUE GLOBALE"] + list(df['Month'].unique()), key='heat_filter')

    if heat_filter == "VUE GLOBALE": df_heat = df
    else: df_heat = df[df['Month'] == heat_filter]

    heatmap_data = df_heat.pivot_table(index='Player', columns='Pick', values='Score', aggfunc='sum')
    custom_colors = [[0.0, '#EF4444'], [0.43, '#1F2937'], [0.56, '#1F2937'], [1.0, '#10B981']]

    fig_heat = px.imshow(heatmap_data, labels=dict(x="Pick", y="Player", color="Score"), x=heatmap_data.columns, y=heatmap_data.index, color_continuous_scale=custom_colors, zmin=0, zmax=80, aspect="auto")
    fig_heat.update_traces(xgap=1, ygap=1)
    fig_heat.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=500, xaxis={'showgrid': False}, yaxis={'showgrid': False})
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("### 📊 DATA ROOM")
    st.dataframe(
        full_stats[['Player', 'Trend7Icon', 'Trend', 'Total', 'Moyenne', 'BP_Count', 'Nukes', 'Carottes', 'Bonus_Gained']].sort_values('Total', ascending=False),
        hide_index=True, 
        use_container_width=True, 
        column_config={
            "Player": st.column_config.TextColumn("Joueur", width="medium"),
            "Trend7Icon": st.column_config.TextColumn("7J", width="small", help="Tendance 7 derniers matchs"),
            "Trend": st.column_config.LineChartColumn("Forme (20j)", width="medium", y_min=0, y_max=80),
            "Total": st.column_config.ProgressColumn("Total Pts", format="%d", min_value=0, max_value=full_stats['Total'].max()),
            "Moyenne": st.column_config.NumberColumn("Moyenne", format="%.1f"),
            "Carottes": st.column_config.NumberColumn("🥕", help="Scores < 20"),
            "Nukes": st.column_config.NumberColumn("☢️", help="Scores > 50"),
            "BP_Count": st.column_config.NumberColumn("🎯", help="Best Picks"),
            "Bonus_Gained": st.column_config.NumberColumn("⚗️", help="Pts Bonus Gagnés")
        }
    )

# --- 3. PLAYER LAB ---
def render_player_lab(df, full_stats):
    section_title("PLAYER <span class='highlight'>LAB</span>", "Deep Dive Analytics")
    st.markdown("<div class='widget-title'>👤 SÉLECTION DU JOUEUR</div>", unsafe_allow_html=True)
    sel_player = st.selectbox("Recherche", sorted(df['Player'].unique()), label_visibility="collapsed")

    p_color = PLAYER_COLORS.get(sel_player, "#333")
    st.markdown(f"""
    <div style="background-color: {p_color}; padding: 15px; border-radius: 12px; margin-bottom: 25px; text-align: center; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 15px rgba(0,0,0,0.3);">
        <h2 style="color: white; margin:0; font-family:'Rajdhani'; font-weight:800; font-size:2rem; text-shadow: 0 2px 4px rgba(0,0,0,0.5); text-transform:uppercase; letter-spacing:2px;">🔭 ZOOM SUR {sel_player}</h2>
    </div>
    """, unsafe_allow_html=True)

    p_data = full_stats[full_stats['Player'] == sel_player].iloc[0]
    p_hist_all = df[df['Player'] == sel_player]

    sorted_team = full_stats.sort_values('Total', ascending=False).reset_index(drop=True)
    internal_rank = sorted_team[sorted_team['Player'] == sel_player].index[0] + 1
    nb_players = len(sorted_team)
    form_15 = p_data['Last15']
    diff_form = ((form_15 - p_data['Moyenne']) / p_data['Moyenne']) * 100
    sign = "+" if diff_form > 0 else ""
    color_diff = C_GREEN if diff_form > 0 else "#F87171"
    z_val = p_data['CurrentNoCarrot']
    z_col = C_GREEN if z_val > 3 else (C_RED if z_val == 0 else "#FFF")
    rank_col = C_GOLD if internal_rank == 1 else (C_SILVER if internal_rank == 2 else (C_BRONZE if internal_rank == 3 else "#FFF"))

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi_card("TOTAL POINTS", int(p_data['Total']), "PÉRIODE")
    with c2: kpi_card("MOYENNE", f"{p_data['Moyenne']:.1f}", "PTS / PICK")
    with c3: kpi_card("SÉRIE NO-CAROTTE", f"{int(z_val)}", "MATCHS (>20 PTS)", z_col)
    with c4: kpi_card("CLASSEMENT", f"#{internal_rank}", f"SUR {nb_players}", rank_col)
    with c5: kpi_card("BEST SCORE", int(p_data['Best']), "RECORD PÉRIODE", C_GOLD)

    st.markdown("<div style='margin-top:20px; margin-bottom:5px; color:#888; font-size:0.8rem; text-transform:uppercase; letter-spacing:1px; text-align:center'>HISTORIQUE MATCHS</div>", unsafe_allow_html=True)
    all_season_picks = p_hist_all.sort_values('Pick', ascending=True)

    if not all_season_picks.empty:
        html_picks = "<div class='match-row' style='width:100%'>"
        desc_picks = p_hist_all.sort_values('Pick', ascending=False)
        for _, r in desc_picks.iterrows():
            sc = r['Score']
            if r['IsBonus']:
                bg = C_GOLD; txt_col = "#000000"; border = f"2px solid {C_GOLD}"
            else:
                # RETABLISSEMENT DE LA COULEUR CONDITIONNELLE
                bg = get_uniform_color(r['Score'])
                txt_col = "#FFF"; border = "1px solid rgba(255,255,255,0.1)"

            pill_content = f"<div class='mp-score'>{int(sc)}</div>"
            if r.get('IsBP', False):
                pill_content += "<div class='mp-icon'>🎯</div>"

            html_picks += f"<div class='match-pill' style='background:{bg}; color:{txt_col}; border:{border}' title='Pick #{r['Pick']}'>{pill_content}</div>"
        html_picks += "</div>"
        st.markdown(html_picks, unsafe_allow_html=True)
    else:
        st.info("Pas encore assez de matchs joués.")

    st.markdown("<br>", unsafe_allow_html=True)

    col_grid, col_top5 = st.columns([3, 1], gap="medium")

    with col_grid:
        r1c1, r1c2, r1c3 = st.columns(3, gap="small")
        with r1c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['ReliabilityPct'])}%</div><div class='stat-mini-lbl'>FIABILITÉ (> 20 PTS)</div></div>", unsafe_allow_html=True)
        with r1c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{p_data['Last15']:.1f}</div><div class='stat-mini-lbl'>MOYENNE 15 JOURS</div></div>", unsafe_allow_html=True)
        with r1c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{color_diff}'>{sign}{diff_form:.1f}%</div><div class='stat-mini-lbl'>DYNAMIQUE 15J</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        r2c1, r2c2, r2c3 = st.columns(3, gap="small")
        with r2c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{p_data['Moyenne_Raw']:.1f}</div><div class='stat-mini-lbl'>MOYENNE PURE</div></div>", unsafe_allow_html=True)
        with r2c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['Best_Raw'])}</div><div class='stat-mini-lbl'>MEILLEUR SCORE SEC</div></div>", unsafe_allow_html=True)
        with r2c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val'>{int(p_data['Worst'])}</div><div class='stat-mini-lbl'>PIRE SCORE</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        r3c1, r3c2, r3c3 = st.columns(3, gap="small")
        with r3c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BLUE}'>{int(p_data['Count35'])}</div><div class='stat-mini-lbl'>SAFE ZONE (> 35 PTS)</div></div>", unsafe_allow_html=True)
        with r3c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GREEN}'>{int(p_data['Nukes'])}</div><div class='stat-mini-lbl'>NUKES (> 50 PTS)</div></div>", unsafe_allow_html=True)
        with r3c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_RED}'>{int(p_data['Carottes'])}</div><div class='stat-mini-lbl'>CAROTTES (< 20 PTS)</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        r4c1, r4c2, r4c3 = st.columns(3, gap="small")
        with r4c1: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_PURPLE}'>{int(p_data['BP_Count'])}</div><div class='stat-mini-lbl'>TOTAL BEST PICKS 🎯</div></div>", unsafe_allow_html=True)
        with r4c2: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_GOLD}'>{int(p_data['Alpha_Count'])}</div><div class='stat-mini-lbl'>MVP DU SOIR</div></div>", unsafe_allow_html=True)
        with r4c3: st.markdown(f"<div class='stat-box-mini'><div class='stat-mini-val' style='color:{C_BONUS}'>{p_data['Avg_Bonus']:.1f}</div><div class='stat-mini-lbl'>MOYENNE SOUS BONUS 🌟</div></div>", unsafe_allow_html=True)

    with col_top5:
        st.markdown("#### 🌟 TOP 5 PICKS")
        st.markdown("<div class='chart-desc'>Meilleurs scores de la période.</div>", unsafe_allow_html=True)
        top_5 = p_hist_all.sort_values('Score', ascending=False).head(5)
        for i, r in top_5.reset_index().iterrows():
            rank_num = i + 1
            border_col = C_GOLD if rank_num == 1 else (C_SILVER if rank_num == 2 else (C_BRONZE if rank_num == 3 else "#444"))
            tags = []
            if r['IsBonus']: tags.append("🌟 x2")
            if r.get('IsBP', False): tags.append("🎯 BP")
            tags_html = f"<div class='tp-tags'>{' '.join(tags)}</div>" if tags else ""
            html_card = f"""<div class="top-pick-card" style="border-left: 4px solid {border_col}"><div class="tp-rank-badge" style="border-color:{border_col}; color:{border_col}">{rank_num}</div><div class="tp-content"><div class="tp-date">Pick #{r['Pick']}</div>{tags_html}</div><div class="tp-score-big">{int(r['Score'])}</div></div>"""
            st.markdown(html_card, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:10px'>📡 PROFIL ATHLÉTIQUE</h3>", unsafe_allow_html=True)

    c_radar_graph, c_radar_legend = st.columns([2, 1], gap="large")
    with c_radar_graph:
        max_avg = full_stats['Moyenne'].max(); max_best = full_stats['Best'].max(); max_last10 = full_stats['Last10'].max(); max_nukes = full_stats['Nukes'].max()
        reg_score = 100 - ((p_data['StdDev'] / full_stats['StdDev'].max()) * 100)
        r_vals = [(p_data['Moyenne'] / max_avg) * 100, (p_data['Best'] / max_best) * 100, (p_data['Last10'] / max_last10) * 100, reg_score, (p_data['Nukes'] / (max_nukes if max_nukes > 0 else 1)) * 100]
        r_cats = ['SCORING', 'CEILING', 'FORME', 'RÉGULARITÉ', 'CLUTCH']
        fig_radar = go.Figure(data=go.Scatterpolar(r=r_vals + [r_vals[0]], theta=r_cats + [r_cats[0]], fill='toself', line_color=C_ACCENT, fillcolor="rgba(206, 17, 65, 0.3)"))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100], showticklabels=False, linecolor='#333'), bgcolor='rgba(0,0,0,0)'), paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white', size=14, family="Rajdhani"), margin=dict(t=20, b=20, l=40, r=40), height=400)
        st.plotly_chart(fig_radar, use_container_width=True)

    with c_radar_legend:
        st.markdown("""<div class='legend-box'><div class='legend-item'><div class='legend-title'>SCORING</div><div class='legend-desc'>Volume de points moyen sur la période.</div></div><div class='legend-item'><div class='legend-title'>CEILING (PLAFOND)</div><div class='legend-desc'>Record personnel (Potentiel max sur un match).</div></div><div class='legend-item'><div class='legend-title'>FORME</div><div class='legend-desc'>Dynamique actuelle sur les 10 derniers matchs.</div></div><div class='legend-item'><div class='legend-title'>RÉGULARITÉ</div><div class='legend-desc'>Capacité à éviter les gros écarts de score.</div></div><div class='legend-item'><div class='legend-title'>CLUTCH</div><div class='legend-desc'>Fréquence des très gros scores (> 50 points).</div></div></div>""", unsafe_allow_html=True)

    c_dist, c_trend = st.columns(2, gap="medium")
    with c_dist:
        if not p_hist_all.empty:
            st.markdown("#### 📊 DISTRIBUTION DES SCORES", unsafe_allow_html=True)
            fig_hist = px.histogram(p_hist_all, x="Score", nbins=15, color_discrete_sequence=[C_ACCENT], text_auto=True)
            fig_hist.update_traces(marker_line_color='white', marker_line_width=1, opacity=0.8)
            fig_hist.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=10, b=0), height=250, xaxis_title=None, yaxis_title=None, bargap=0.1)
            st.plotly_chart(fig_hist, use_container_width=True)

    with c_trend:
        if not p_hist_all.empty:
            st.markdown("#### 📈 TENDANCE (15 DERNIERS MATCHS)", unsafe_allow_html=True)
            last_15_data = p_hist_all.sort_values('Pick').tail(15)
            if not last_15_data.empty:
                fig_trend = px.line(last_15_data, x="Pick", y="Score", markers=True)
                fig_trend.update_traces(line_color=C_GOLD, marker_color=C_ACCENT, marker_size=8)
                fig_trend.add_hline(y=p_data['Moyenne'], line_dash="dot", line_color=C_TEXT, annotation_text="Moy. Période", annotation_position="bottom right")
                fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=10, b=0), height=250, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_trend, use_container_width=True)

    if not p_hist_all.empty:
        st.markdown("#### 🏔️ PARCOURS PÉRIODE", unsafe_allow_html=True)
        team_season_avg = df['Score'].mean()
        fig_evol = px.line(p_hist_all, x="Pick", y="Score", markers=True)
        fig_evol.update_traces(line_color=C_BLUE, line_width=2, marker_size=4)
        fig_evol.add_hline(y=p_data['Moyenne'], line_dash="dot", line_color=C_TEXT, annotation_text="Moy. Joueur", annotation_position="top left")
        fig_evol.add_hline(y=team_season_avg, line_dash="dash", line_color=C_ORANGE, annotation_text="Moy. Team", annotation_position="bottom right", annotation_font_color=C_ORANGE)
        fig_evol.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, margin=dict(l=0, r=0, t=30, b=0), height=300, xaxis_title="Pick #", yaxis_title="Points TTFL", legend=dict(font=dict(color="#E5E7EB")))
        st.plotly_chart(fig_evol, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:15px'>⚔️ DUEL : LE COMPARATEUR</h3>", unsafe_allow_html=True)

    dc1, dc2 = st.columns(2)
    with dc1: p1_sel = st.selectbox("Joueur A", sorted(df['Player'].unique()), index=0, key="p1_comp")
    with dc2: p2_sel = st.selectbox("Joueur B", sorted(df['Player'].unique()), index=1, key="p2_comp")

    if p1_sel and p2_sel:
        stat1 = full_stats[full_stats['Player'] == p1_sel].iloc[0]
        stat2 = full_stats[full_stats['Player'] == p2_sel].iloc[0]
        
        # CALCUL DIRECT DES DUELS
        wins_p1, wins_p2 = get_head_to_head_stats(df, p1_sel, p2_sel)
        
        def comp_row(label, v1, v2, format_str="{}", inverse=False):
            color1, color2 = "#FFF", "#FFF"
            if v1 != v2:
                better_v1 = (v1 > v2) if not inverse else (v1 < v2)
                if better_v1: color1 = C_GREEN; color2 = "#666"
                else: color1 = "#666"; color2 = C_GREEN
            
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.05); padding:8px 0;">
                <div style="width:30%; text-align:left; font-family:Rajdhani; font-weight:700; color:{color1}">{format_str.format(v1)}</div>
                <div style="width:40%; text-align:center; font-size:0.8rem; color:#AAA; letter-spacing:1px;">{label}</div>
                <div style="width:30%; text-align:right; font-family:Rajdhani; font-weight:700; color:{color2}">{format_str.format(v2)}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown(f"<div class='glass-card'>", unsafe_allow_html=True)
        # LIGNE SPECIALE DUEL (MISE EN AVANT)
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.1); padding:12px 0; margin-bottom:5px; background:rgba(255,255,255,0.02);">
            <div style="width:30%; text-align:left; font-family:Rajdhani; font-weight:800; font-size:1.4rem; color:{C_GOLD if wins_p1 > wins_p2 else '#FFF'}">{wins_p1}</div>
            <div style="width:40%; text-align:center; font-size:0.9rem; font-weight:700; color:{C_GOLD}; letter-spacing:1px; display:flex; flex-direction:column; justify-content:center;">VICTOIRES<br><span style="font-size:0.7rem; color:#888; font-weight:400">FACE À FACE</span></div>
            <div style="width:30%; text-align:right; font-family:Rajdhani; font-weight:800; font-size:1.4rem; color:{C_GOLD if wins_p2 > wins_p1 else '#FFF'}">{wins_p2}</div>
        </div>
        """, unsafe_allow_html=True)

        comp_row("POINTS TOTAL", stat1['Total'], stat2['Total'], "{:.0f}")
        comp_row("MOYENNE", stat1['Moyenne'], stat2['Moyenne'], "{:.1f}")
        comp_row("FORME (15J)", stat1['Last15'], stat2['Last15'], "{:.1f}")
        comp_row("RECORD SAISON", stat1['Best'], stat2['Best'], "{:.0f}")
        comp_row("BEST PICKS", stat1['BP_Count'], stat2['BP_Count'], "{:.0f}")
        comp_row("NUKES (>50)", stat1['Nukes'], stat2['Nukes'], "{:.0f}")
        comp_row("CAROTTES (<20)", stat1['Carottes'], stat2['Carottes'], "{:.0f}", inverse=True)
        comp_row("FIABILITÉ", stat1['ReliabilityPct'], stat2['ReliabilityPct'], "{:.0f}%")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 4. BONUS X2 ---
def render_bonus_x2(df):
    # MODIFICATION: On force l'utilisation de df_full_history passé en argument depuis app.py
    # (Note: ici df est déjà df_full_history grâce au câblage dans app.py)
    section_title("BONUS <span class='highlight'>ZONE</span>", "Analyse de Rentabilité")
    
    df_bonus = df[df['IsBonus'] == True].copy()
    
    # Calcul du Gain Réel
    df_bonus['RealGain'] = df_bonus['Score'] - df_bonus['ScoreVal']
    
    # Indicateur visuel de rentabilité (Rentable si score de base >= 40, donc score total >= 80)
    df_bonus['Rentable'] = df_bonus['ScoreVal'].apply(lambda x: "✅" if x >= 40 else "❌")

    available_months = df['Month'].unique().tolist()
    sel_month = st.selectbox("Filtrer par Mois", ["Tous"] + [m for m in available_months if m != "Inconnu"])
    if sel_month != "Tous": df_bonus_disp = df_bonus[df_bonus['Month'] == sel_month]
    else: df_bonus_disp = df_bonus

    if df_bonus_disp.empty:
        st.info("Aucun bonus trouvé.")
    else:
        nb_bonus = len(df_bonus_disp)
        avg_bonus = df_bonus_disp['Score'].mean()
        total_gain = df_bonus_disp['RealGain'].sum()
        success_rate = (len(df_bonus_disp[df_bonus_disp['Score'] >= 50]) / nb_bonus * 100) if nb_bonus > 0 else 0
        best_bonus = df_bonus_disp['Score'].max()

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1: kpi_card("TOTAL", nb_bonus, "BONUS JOUÉS 🌟", C_BONUS)
        with k2: kpi_card("MOYENNE", f"{avg_bonus:.1f}", "PTS / BONUS", "#FFF")
        with k3: kpi_card("GAIN RÉEL", f"+{int(total_gain)}", "PTS AJOUTÉS", C_GREEN)
        with k4: kpi_card("RENTABILITÉ", f"{int(success_rate)}%", "SCORES > 50 PTS", C_PURPLE)
        with k5: kpi_card("RECORD", int(best_bonus), "MAX SCORE", C_GOLD)

        st.markdown("<br>", unsafe_allow_html=True)
        c_chart1, c_chart2 = st.columns([2, 3], gap="medium")
        with c_chart1:
            st.markdown("#### 💰 IMPACT MENSUEL (GAINS RÉELS)")
            monthly_gain = df_bonus.groupby('Month')['RealGain'].sum().reset_index()
            # Tri chronologique sécurisé
            month_order = ['octobre', 'novembre', 'decembre', 'janvier', 'fevrier', 'mars', 'avril']
            existing_months = [m for m in month_order if m in monthly_gain['Month'].unique()]
            monthly_gain['Month'] = pd.Categorical(monthly_gain['Month'], categories=existing_months, ordered=True)
            monthly_gain = monthly_gain.sort_values('Month')
            
            # -- MODIFICATION GRAPHIQUE --
            # Utilisation de px.bar pour des couleurs distinctes par mois et suppression de la ligne de cumul.
            fig_m = px.bar(
                monthly_gain, 
                x='Month', 
                y='RealGain', 
                text='RealGain', 
                color='Month', # Une couleur différente par mois
                color_discrete_sequence=px.colors.qualitative.Prism # Palette qualitative sympa
            )
            fig_m.update_traces(textposition='outside', texttemplate='%{text:.0f}')
            fig_m.update_layout(
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)', 
                font={'color': '#AAA'}, 
                xaxis=dict(title=None), 
                yaxis=dict(showgrid=False, visible=False), 
                height=300, 
                showlegend=False # Pas besoin de légende car les barres sont explicites
            )
            st.plotly_chart(fig_m, use_container_width=True)
            
        with c_chart2:
            st.markdown("#### 🎯 SCORES BONUS PAR JOUEUR")
            fig_strip = px.strip(df_bonus_disp, x="Player", y="Score", color="Player", color_discrete_map=PLAYER_COLORS, stripmode='overlay')
            fig_strip.update_traces(marker=dict(size=12, line=dict(width=1, color='White'), opacity=0.9))
            fig_strip.add_hline(y=50, line_dash="dash", line_color="#666", annotation_text="Seuil (50)", annotation_position="bottom right")
            fig_strip.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, height=300, xaxis=dict(title=None), yaxis=dict(title="Score Total", range=[0, df_bonus_disp['Score'].max() + 10]), showlegend=False)
            st.plotly_chart(fig_strip, use_container_width=True)

        st.markdown("### 📜 HISTORIQUE DÉTAILLÉ")
        st.dataframe(
            df_bonus_disp[['Pick', 'Player', 'Month', 'ScoreVal', 'Score', 'RealGain', 'Rentable']].sort_values('Pick', ascending=False), 
            hide_index=True, 
            use_container_width=True,
            column_config={
                "Rentable": st.column_config.TextColumn("Rentable", width="small")
            }
        )

# --- 5. NO CARROT ---
# CORRECTION: Ajout de l'argument df_full_history pour calculer l'Iron Man global
def render_no_carrot(df, team_streak_nc, full_stats, df_full_history):
    section_title("ANTI <span class='highlight'>CARROTE</span>", "Objectif Fiabilité & Constance")
    
    # 1. CALCULS SUR FULL HISTORY (Saison Complète)
    max_streak_team_hist = 0
    curr_str = 0
    sorted_picks_asc = sorted(df_full_history['Pick'].unique())
    
    team_streak_active = 0
    for p_id in sorted(df_full_history['Pick'].unique(), reverse=True):
        d_min = df_full_history[df_full_history['Pick'] == p_id]['Score'].min()
        if d_min >= 20: team_streak_active += 1
        else: break
            
    for p_id in sorted_picks_asc:
        d_min = df_full_history[df_full_history['Pick'] == p_id]['Score'].min()
        if d_min >= 20: curr_str += 1
        else:
            if curr_str > max_streak_team_hist: max_streak_team_hist = curr_str
            curr_str = 0
    if curr_str > max_streak_team_hist: max_streak_team_hist = curr_str

    full_stats_global = compute_stats(df_full_history, {}, {})
    
    iron_man_curr = full_stats_global.sort_values('CurrentNoCarrot', ascending=False).iloc[0]
    iron_man_all_time = full_stats_global.sort_values('MaxNoCarrot', ascending=False).iloc[0]
    mister_clean = full_stats_global.sort_values('Carottes', ascending=True).iloc[0]

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: kpi_card("SÉRIE TEAM EN COURS", f"{team_streak_active}", "JOURS SANS CAROTTE", C_GREEN if team_streak_active > 0 else C_RED)
    with k2: kpi_card("RECORD TEAM (HISTORIQUE)", f"{max_streak_team_hist}", "JOURS CONSÉCUTIFS", C_GOLD)
    with k3: kpi_card("IRON MAN (ACTUEL)", iron_man_curr['Player'], f"{int(iron_man_curr['CurrentNoCarrot'])} MATCHS SUITE", C_BLUE)
    with k4: kpi_card("IRON MAN (HISTORIQUE)", iron_man_all_time['Player'], f"{int(iron_man_all_time['MaxNoCarrot'])} MATCHS SUITE", C_PURPLE)
    with k5: kpi_card("MISTER CLEAN", mister_clean['Player'], f"{int(mister_clean['Carottes'])} CAROTTES (TOTAL)", C_PURE)

    st.markdown("<br>", unsafe_allow_html=True)
    c_graph, c_list = st.columns([2, 1], gap="large")
    with c_graph:
        st.markdown("#### 📉 ZONE DE DANGER (CAROTTES PAR SOIR - SAISON)")
        carrot_counts = df_full_history[df_full_history['Score'] < 20].groupby('Pick').size().reset_index(name='Carottes')
        all_picks = pd.DataFrame({'Pick': sorted(df_full_history['Pick'].unique())})
        carrot_chart = pd.merge(all_picks, carrot_counts, on='Pick', how='left').fillna(0)
        carrot_chart['Color'] = carrot_chart['Carottes'].apply(lambda x: "#374151" if x == 0 else C_RED)
        
        # Trouver le pire soir pour l'annotation
        max_carrots = carrot_chart['Carottes'].max()
        worst_day = carrot_chart[carrot_chart['Carottes'] == max_carrots].iloc[0]
        
        fig_car = px.bar(carrot_chart, x='Pick', y='Carottes')
        fig_car.update_traces(marker_color=carrot_chart['Color'])
        
        # Ajout Annotation
        if max_carrots > 0:
            fig_car.add_annotation(
                x=worst_day['Pick'], y=max_carrots,
                text=f"Pire Soir: {int(max_carrots)} Carottes",
                showarrow=True, arrowhead=1, ax=0, ay=-40,
                font=dict(color="#FFF", size=12), bgcolor=C_RED
            )
            
        fig_car.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#222', title="Nb Carottes"), height=350)
        st.plotly_chart(fig_car, use_container_width=True)

    with c_list:
        st.markdown("#### 🛡️ SÉRIES EN COURS (JOUEURS)")
        sorted_reliability = full_stats_global.sort_values('CurrentNoCarrot', ascending=False)[['Player', 'CurrentNoCarrot']]
        for i, r in sorted_reliability.iterrows():
            val = int(r['CurrentNoCarrot'])
            col_bar = C_GREEN if val >= 10 else (C_BLUE if val >= 5 else C_TEXT)
            width = min(100, val * 2)
            st.markdown(f"<div style='margin-bottom:8px;'><div style='display:flex; justify-content:space-between; font-size:0.9rem; font-weight:600; color:{C_TEXT}'><span>{r['Player']}</span><span style='color:{col_bar}'>{val}</span></div><div style='width:100%; background:#222; height:6px; border-radius:3px; margin-top:2px;'><div style='width:{width}%; background:{col_bar}; height:100%; border-radius:3px;'></div></div></div>", unsafe_allow_html=True)

# --- 6. TRENDS ---
def render_trends(df, latest_pick):
    section_title("TENDANCES", "Analyse de la forme récente (15 derniers jours)")
    df_15 = df[df['Pick'] > (latest_pick - 15)]
    team_daily_15 = df_15.groupby('Pick')['Score'].sum()
    avg_15_team = team_daily_15.mean()
    team_daily_season = df.groupby('Pick')['Score'].sum()
    season_avg_team = team_daily_season.mean()
    team_trend_diff = ((avg_15_team - season_avg_team) / season_avg_team) * 100
    best_form_player = df_15.groupby('Player')['Score'].mean().idxmax()
    best_form_val = df_15.groupby('Player')['Score'].mean().max()
    avg_15_indiv = df_15['Score'].mean()
    max_team_15 = team_daily_15.max()

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: kpi_card("MOYENNE TEAM (15J)", f"{avg_15_team:.0f}", "POINTS / SOIR", C_BLUE)
    with k2: kpi_card("MOYENNE / PICK (15J)", f"{avg_15_indiv:.1f}", "INDIVIDUEL", "#FFF")
    col_trend = C_GREEN if team_trend_diff > 0 else C_RED
    with k3: kpi_card("DYNAMIQUE", f"{'+' if team_trend_diff > 0 else ''}{team_trend_diff:.1f}%", "VS PÉRIODE", col_trend)
    with k4: kpi_card("PLAFOND TEAM (15J)", int(max_team_15), "MEILLEUR SOIR", C_GOLD)
    with k5: kpi_card("MVP (15J)", best_form_player, f"{best_form_val:.1f} PTS", C_ACCENT)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("#### 📉 ÉVOLUTION DU SCORE D'ÉQUIPE (15 DERNIERS JOURS)")
    fig_team_15 = px.line(team_daily_15, markers=True)
    fig_team_15.update_traces(line_color=C_ACCENT, line_width=3, marker_size=8)
    fig_team_15.add_hline(y=season_avg_team, line_dash="dot", line_color=C_TEXT, annotation_text=f"Moyenne ({int(season_avg_team)})", annotation_position="bottom right")
    fig_team_15.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font={'color': '#AAA'}, xaxis=dict(showgrid=False, title=None), yaxis=dict(showgrid=True, gridcolor='#222', title="Points Totaux"), height=350, showlegend=False)
    st.plotly_chart(fig_team_15, use_container_width=True)

    # Calcul dynamique Top 3 / Flop 3 (SANS FILTRE STRICT)
    player_season_avg = df.groupby('Player')['Score'].mean()
    # On regarde la forme sur les 7 derniers matchs pour plus de réactivité
    player_7_avg = df[df['Pick'] > (latest_pick - 7)].groupby('Player')['Score'].mean()
    
    delta_df = pd.DataFrame({'Season': player_season_avg, 'Recent': player_7_avg})
    delta_df['Delta'] = delta_df['Recent'] - delta_df['Season']
    delta_df = delta_df.dropna().sort_values('Delta', ascending=False)
    
    # Top 3
    hot_players = delta_df.head(3)
    # Flop 3
    cold_players = delta_df.tail(3).sort_values('Delta', ascending=True)

    c_hot, c_cold = st.columns(2, gap="large")
    with c_hot:
        st.markdown(f"<div class='trend-box'><div class='hot-header'>🔥 TOP 3 PROGRESSION (7J)</div><div style='font-size:0.8rem; color:#888; margin-bottom:10px'>Joueurs avec la meilleure dynamique récente.</div>", unsafe_allow_html=True)
        if hot_players.empty: st.info("Données insuffisantes.")
        else:
            for p, row in hot_players.iterrows():
                st.markdown(f"<div class='trend-card-row'><div class='trend-name'>{p}</div><div style='text-align:right'><div class='trend-val' style='color:{C_GREEN}'>{row['Recent']:.1f}</div><div class='trend-delta' style='color:{C_GREEN}'>+{row['Delta']:.1f}</div></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c_cold:
        st.markdown(f"<div class='trend-box'><div class='cold-header'>❄️ TOP 3 REGRESSION (7J)</div><div style='font-size:0.8rem; color:#888; margin-bottom:10px'>Joueurs en baisse de régime récente.</div>", unsafe_allow_html=True)
        if cold_players.empty: st.info("Données insuffisantes.")
        else:
            for p, row in cold_players.iterrows():
                st.markdown(f"<div class='trend-card-row'><div class='trend-name'>{p}</div><div style='text-align:right'><div class='trend-val' style='color:{C_RED}'>{row['Recent']:.1f}</div><div class='trend-delta' style='color:{C_RED}'>{row['Delta']:.1f}</div></div></div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    # --- MOMENTUM CHART (ALL PLAYERS 15 DAYS) - CORRECTION GRAPH MANQUANT ---
    st.markdown("#### 📉 MOMENTUM (15 DERNIERS JOURS)")
    st.markdown("<div class='chart-desc'>Trajectoire de tous les joueurs actifs sur la période.</div>", unsafe_allow_html=True)
    
    # Filter only players who played in last 15 days
    active_players = df_15['Player'].unique()
    momentum_data = df_15[df_15['Player'].isin(active_players)].sort_values('Pick')
    
    # COLORER LA LIGNE PAR JOUEUR
    fig_mom = px.line(momentum_data, x='Pick', y='Score', color='Player', markers=True, color_discrete_map=PLAYER_COLORS)
    
    # FIX UI: LEGEND COLOR TOO DARK
    fig_mom.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='rgba(0,0,0,0)', 
        font={'color': '#AAA'}, 
        xaxis=dict(showgrid=False), 
        yaxis=dict(showgrid=True, gridcolor='#222'), 
        height=500,
        legend=dict(orientation="h", y=-0.2, font=dict(color="#E5E7EB"))
    )
    st.plotly_chart(fig_mom, use_container_width=True)

# --- 7. HALL OF FAME ---
def render_hall_of_fame(df_full_history, bp_map, daily_max_map):
    section_title("HALL OF <span class='highlight'>FAME</span>", "Records & Trophées")
    st.markdown("<h3 style='margin-bottom:15px; font-family:Rajdhani; color:#AAA;'>🏆 RAPTORS SEASON TROPHIES</h3>", unsafe_allow_html=True)
    trophy_cols = st.columns(4)
    season_keys = [k for k in SEASONS_CONFIG.keys() if "SAISON COMPLÈTE" not in k]
    real_latest_pick = df_full_history['Pick'].max() if not df_full_history.empty else 0

    for i, s_name in enumerate(season_keys):
        s_start, s_end = SEASONS_CONFIG[s_name]
        short_name = s_name.split(':')[0].replace("PART ", "P")
        full_title = s_name.split(':')[1].split('(')[0].strip()
        details = SEASONS_DETAILS[i]
        dates_txt = details["dates"]
        desc_txt = details["desc"]

        is_finished = real_latest_pick > s_end
        is_active = s_start <= real_latest_pick <= s_end
        is_future = real_latest_pick < s_start

        card_bg = "rgba(255,255,255,0.02)"
        border_col = "#333"
        title_col = "#666"
        icon = "🔒"
        player_name = "VERROUILLÉ"
        score_val = "-"

        if not is_future:
            df_part = df_full_history[(df_full_history['Pick'] >= s_start) & (df_full_history['Pick'] <= s_end)]
            if not df_part.empty:
                leader = df_part.groupby('Player')['Score'].sum().sort_values(ascending=False).head(1)
                if not leader.empty:
                    player_name = leader.index[0]
                    score_val = f"{int(leader.values[0])} pts"
            if is_finished:
                card_bg = "linear-gradient(145deg, rgba(255, 215, 0, 0.1) 0%, rgba(0,0,0,0.4) 100%)"
                border_col = C_GOLD; title_col = C_GOLD; icon = "👑"
            elif is_active:
                card_bg = "linear-gradient(145deg, rgba(59, 130, 246, 0.1) 0%, rgba(0,0,0,0.4) 100%)"
                border_col = C_BLUE; title_col = C_BLUE; icon = "🔥"

        with trophy_cols[i]:
            st.markdown(f"""<div style="background:{card_bg}; border:1px solid {border_col}; border-radius:10px; padding:15px; text-align:center; height:100%; position:relative;"><div style="font-size:0.7rem; color:#888;">{short_name}</div><div style="font-family:Rajdhani; font-weight:700; color:{title_col}; font-size:0.9rem;">{full_title}</div><div style="font-size:1.5rem; margin-bottom:5px;">{icon}</div><div style="font-family:Rajdhani; font-weight:800; color:#FFF; font-size:1.1rem;">{player_name}</div><div style="font-size:0.8rem; color:{title_col};">{score_val}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin-bottom:10px; font-family:Rajdhani; color:#AAA;'>🏛️ RECORDS GLOBAUX SAISON</h3>", unsafe_allow_html=True)

    full_stats_global = compute_stats(df_full_history, bp_map, daily_max_map)
    
    goat = full_stats_global.sort_values('Moyenne', ascending=False).iloc[0]
    mvp = full_stats_global.sort_values('Moyenne_Raw', ascending=False).iloc[0]
    sniper = full_stats_global.sort_values('BP_Count', ascending=False).iloc[0]
    alpha = full_stats_global.sort_values('Alpha_Count', ascending=False).iloc[0]
    medalist = full_stats_global.sort_values('Medalist', ascending=False).iloc[0]
    prime = full_stats_global.sort_values('PrimeTime', ascending=False).iloc[0]
    dominator = full_stats_global.sort_values('Dominator', ascending=False).iloc[0]
    savior = full_stats_global.sort_values('SaviorScore', ascending=False).iloc[0]
    
    ceiling = full_stats_global.sort_values('Best', ascending=False).iloc[0]
    pure_scorer = full_stats_global.sort_values('Best_Raw', ascending=False).iloc[0]
    alien = full_stats_global.sort_values('MaxAlien', ascending=False).iloc[0]
    nuclear = full_stats_global.sort_values('Nukes', ascending=False).iloc[0]
    heavy = full_stats_global.sort_values('Count40', ascending=False).iloc[0]
    unstoppable = full_stats_global.sort_values('MaxUnstoppable', ascending=False).iloc[0]
    
    lungs = full_stats_global.sort_values('IronLungs', ascending=False).iloc[0]
    decks = full_stats_global.sort_values('MaxDeck', ascending=False).iloc[0]
    rock = full_stats_global.sort_values('Count30', ascending=False).iloc[0]
    sixth = full_stats_global.sort_values('SixthMan', ascending=False).iloc[0]
    shield = full_stats_global.sort_values('ShieldCount', ascending=True).iloc[0]
    zen = full_stats_global.sort_values('ReliabilityPct', ascending=False).iloc[0]
    iron_man = full_stats_global.sort_values('MaxNoCarrot', ascending=False).iloc[0]
    wall = full_stats_global.sort_values('Worst', ascending=False).iloc[0]
    metronome = full_stats_global.sort_values('StdDev', ascending=True).iloc[0]
    
    torch = full_stats_global.sort_values('Last15', ascending=False).iloc[0]
    rising = full_stats_global.sort_values('ProgressionPct', ascending=False).iloc[0]
    soloist = full_stats_global.sort_values('Soloist', ascending=False).iloc[0]
    phoenix = full_stats_global.sort_values('MaxPhoenix', ascending=False).iloc[0]
    alchemist = full_stats_global.sort_values('Bonus_Gained', ascending=False).iloc[0]
    ghost = full_stats_global.sort_values('Ghost', ascending=False).iloc[0]
    maniac = full_stats_global.sort_values('ModeCount', ascending=False).iloc[0]
    albatross = full_stats_global.sort_values('Spread', ascending=False).iloc[0]
    gambler = full_stats_global.sort_values('StdDev', ascending=False).iloc[0]
    braqueur = full_stats_global.sort_values('Braqueur', ascending=True).iloc[0]
    
    bad_luck = full_stats_global.sort_values('BadLuck', ascending=False).iloc[0]
    crash = full_stats_global[full_stats_global['Worst_Bonus'] > 0].sort_values('Worst_Bonus', ascending=True).iloc[0]
    bad_biz = full_stats_global.sort_values('Bonus_Gained', ascending=True).iloc[0]
    brick = full_stats_global.sort_values('Worst_Raw', ascending=True).iloc[0]
    mister_clean = full_stats_global.sort_values('Carottes', ascending=True).iloc[0]
    farmer = full_stats_global.sort_values('Carottes', ascending=False).iloc[0]

    hof_list = [
        # I. L'ELITE
        {"title": "THE GOAT", "icon": "🏆", "color": C_GOLD, "player": goat['Player'], "val": f"{goat['Moyenne']:.1f}", "unit": "PTS MOYENNE", "desc": "Meilleure moyenne générale de la saison (Bonus inclus)."},
        {"title": "REAL MVP", "icon": "💎", "color": C_PURE, "player": mvp['Player'], "val": f"{mvp['Moyenne_Raw']:.1f}", "unit": "PTS MOYENNE (BRUT)", "desc": "Meilleure moyenne de points 'purs', sans compter les bonus."},
        {"title": "THE SNIPER", "icon": "🎯", "color": C_PURPLE, "player": sniper['Player'], "val": int(sniper['BP_Count']), "unit": "BEST PICKS", "desc": "Le plus grand nombre de Best Picks trouvés cette saison."},
        {"title": "ALPHA DOG", "icon": "🐺", "color": C_ALPHA, "player": alpha['Player'], "val": int(alpha['Alpha_Count']), "unit": "TOPS TEAM", "desc": "Le joueur ayant fini le plus souvent meilleur scoreur de l'équipe."},
        {"title": "THE MEDALIST", "icon": "🎖️", "color": "#F59E0B", "player": medalist['Player'], "val": int(medalist['Medalist']), "unit": "PODIUMS", "desc": "Le plus grand nombre d'apparitions sur le podium journalier de l'équipe."},
        {"title": "PRIME TIME", "icon": "🗓️", "color": "#EC4899", "player": prime['Player'], "val": f"{prime['PrimeTime']:.1f}", "unit": "PTS MOYENNE (MOIS)", "desc": "Meilleure moyenne de points enregistrée sur un mois civil complet."},
        {"title": "THE DOMINATOR", "icon": "🦖", "color": "#10B981", "player": dominator['Player'], "val": int(dominator['Dominator']), "unit": "MATCHS > MOYENNE", "desc": "Le plus grand nombre de fois où le joueur a scoré plus que la moyenne journalière de l'équipe."},
        {"title": "THE SAVIOR", "icon": "🙏", "color": "#FCD34D", "player": savior['Player'], "val": int(savior['SaviorScore']), "unit": "PTS (PIRE SOIR)", "desc": "Le MVP de la pire soirée collective de la saison."},

        # II. LES SCOREURS
        {"title": "THE CEILING", "icon": "🏔️", "color": "#FB7185", "player": ceiling['Player'], "val": int(ceiling['Best']), "unit": "PTS MAX", "desc": "Record absolu de points sur un match (Bonus inclus)."},
        {"title": "PURE SCORER", "icon": "🏀", "color": "#7C3AED", "player": pure_scorer['Player'], "val": int(pure_scorer['Best_Raw']), "unit": "PTS MAX (BRUT)", "desc": "Record absolu de points sur un match (Score brut)."},
        {"title": "THE ALIEN", "icon": "👽", "color": C_ALIEN, "player": alien['Player'], "val": int(alien['MaxAlien']), "unit": "MATCHS", "desc": "Plus longue série de matchs consécutifs au-dessus de 60 pts."},
        {"title": "NUCLEAR", "icon": "☢️", "color": C_ACCENT, "player": nuclear['Player'], "val": int(nuclear['Nukes']), "unit": "BOMBS", "desc": "Le plus grand nombre de scores explosifs (> 50 pts)."},
        {"title": "HEAVY HITTER", "icon": "🥊", "color": "#DC2626", "player": heavy['Player'], "val": int(heavy['Count40']), "unit": "PICKS > 40", "desc": "Le plus grand nombre de scores très élevés (> 40 pts)."},
        {"title": "UNSTOPPABLE", "icon": "⚡", "color": "#F59E0B", "player": unstoppable['Player'], "val": int(unstoppable['MaxUnstoppable']), "unit": "SERIE > 40", "desc": "Plus longue série historique de matchs consécutifs au-dessus de 40 pts."},

        # III. LES FIABLES
        {"title": "IRON LUNGS", "icon": "🫁", "color": "#06B6D4", "player": lungs['Player'], "val": int(lungs['IronLungs']), "unit": "PTS TOTAL (BRUT)", "desc": "Plus gros volume total de points marqués à la sueur du front (sans bonus)."},
        {"title": "KING OF DECKS", "icon": "🃏", "color": "#8B5CF6", "player": decks['Player'], "val": int(decks['MaxDeck']), "unit": "PTS (7 MATCHS)", "desc": "Meilleur cumul de points sur 7 matchs consécutifs."},
        {"title": "THE ROCK", "icon": "🛡️", "color": C_GREEN, "player": rock['Player'], "val": int(rock['Count30']), "unit": "MATCHS", "desc": "Le plus grand nombre de matchs dans la Safe Zone (> 30 pts)."},
        {"title": "THE 6TH MAN", "icon": "🏀", "color": "#6366F1", "player": sixth['Player'], "val": int(sixth['SixthMan']), "unit": "MATCHS (30-40)", "desc": "Le plus grand nombre de scores solides situés dans la zone 30-40 pts."},
        {"title": "THE SHIELD", "icon": "🛡️", "color": "#3B82F6", "player": shield['Player'], "val": int(shield['ShieldCount']), "unit": "DERNIERES PLACES", "desc": "Le joueur ayant fini le moins souvent à la dernière place du classement journalier."},
        {"title": "IRON MAN", "icon": "🤖", "color": "#4F46E5", "player": iron_man['Player'], "val": int(iron_man['MaxNoCarrot']), "unit": "MATCHS", "desc": "Plus longue série historique de matchs sans aucune carotte."},
        {"title": "IRON WALL", "icon": "🧱", "color": "#78350F", "player": wall['Player'], "val": int(wall['Worst']), "unit": "PIRE SCORE", "desc": "Le 'Pire score' le plus élevé de la saison (Plancher haut)."},
        {"title": "THE METRONOME", "icon": "⏰", "color": C_IRON, "player": metronome['Player'], "val": f"{metronome['StdDev']:.1f}", "unit": "ECART TYPE", "desc": "Le joueur le plus régulier (Plus faible écart-type)."},

        # IV. LE STYLE
        {"title": "HUMAN TORCH", "icon": "🔥", "color": "#BE123C", "player": torch['Player'], "val": f"{torch['Last15']:.1f}", "unit": "PTS / 15J", "desc": "Meilleure forme du moment (Moyenne sur les 15 derniers matchs)."},
        {"title": "RISING STAR", "icon": "🚀", "color": "#34D399", "player": rising['Player'], "val": f"+{rising['ProgressionPct']:.1f}%", "unit": "PROGRESSION", "desc": "Plus grosse progression de forme (Moyenne 15j vs Moyenne Saison)."},
        {"title": "THE SOLOIST", "icon": "🎸", "color": "#A855F7", "player": soloist['Player'], "val": int(soloist['Soloist']), "unit": "SOLOS > 40", "desc": "Le plus grand nombre de soirs où il a été le seul de l'équipe à franchir la barre des 40 pts."},
        {"title": "THE PHOENIX", "icon": "🐣", "color": "#F97316", "player": phoenix['Player'], "val": int(phoenix['MaxPhoenix']), "unit": "PTS REBOND", "desc": "Meilleur score réalisé le lendemain d'une carotte (< 20 pts)."},
        {"title": "THE ALCHEMIST", "icon": "⚗️", "color": C_BONUS, "player": alchemist['Player'], "val": int(alchemist['Bonus_Gained']), "unit": "PTS BONUS", "desc": "Le plus grand volume de points gagnés grâce aux multiplicateurs."},
        {"title": "THE GHOST", "icon": "👻", "color": "#CBD5E1", "player": ghost['Player'], "val": int(ghost['Ghost']), "unit": "SCORES > 35 (NO MVP)", "desc": "Le plus grand nombre de gros scores (> 35 pts) sans jamais décrocher le titre de MVP du soir."},
        {"title": "THE MANIAC", "icon": "🤪", "color": "#D946EF", "player": maniac['Player'], "val": f"{maniac['ModeScore']}", "unit": f"{maniac['ModeCount']} FOIS", "desc": "Le score précis le plus souvent répété par ce joueur."},
        {"title": "THE ALBATROSS", "icon": "🦅", "color": "#2DD4BF", "player": albatross['Player'], "val": int(albatross['Spread']), "unit": "AMPLITUDE", "desc": "Plus grand écart constaté entre le record et le pire score."},
        {"title": "THE GAMBLER", "icon": "🎰", "color": "#E11D48", "player": gambler['Player'], "val": f"{gambler['StdDev']:.1f}", "unit": "VOLATILITÉ", "desc": "Le joueur le plus instable (Plus forte variation de performance)."},
        {"title": "THE BRAQUEUR", "icon": "🥷", "color": "#334155", "player": braqueur['Player'], "val": int(braqueur['Braqueur']), "unit": "PTS (MIN BP)", "desc": "Le score le plus faible ayant suffi pour décrocher un Best Pick."},

        # V. LE MUR DE LA HONTE
        {"title": "BAD LUCK", "icon": "🍀❌", "color": "#99F6E4", "player": bad_luck['Player'], "val": int(bad_luck['BadLuck']), "unit": "PTS (NO BP)", "desc": "Le plus gros score réalisé sans obtenir le Best Pick ce soir-là (Score Brut)."},
        {"title": "CRASH TEST", "icon": "💥", "color": C_RED, "player": crash['Player'], "val": int(crash['Worst_Bonus']), "unit": "PTS MIN (X2)", "desc": "Le pire score réalisé alors qu'un bonus était actif."},
        {"title": "BAD BUSINESS", "icon": "💸", "color": "#9CA3AF", "player": bad_biz['Player'], "val": int(bad_biz['Bonus_Gained']), "unit": "PTS BONUS", "desc": "Le moins de points gagnés grâce aux bonus (Manque de rentabilité)."},
        {"title": "THE BRICK", "icon": "🏗️", "color": "#6B7280", "player": brick['Player'], "val": int(brick['Worst_Raw']), "unit": "PTS MIN (BRUT)", "desc": "Le pire score brut enregistré cette saison."},
        {"title": "MISTER CLEAN", "icon": "🧼", "color": "#E0F2FE", "player": mister_clean['Player'], "val": int(mister_clean['Carottes']), "unit": "CAROTTES (TOTAL)", "desc": "Le plus petit nombre de carottes récoltées sur la saison."},
        {"title": "THE FARMER", "icon": "🥕", "color": C_ORANGE, "player": farmer['Player'], "val": int(farmer['Carottes']), "unit": "CAROTTES", "desc": "Le plus grand nombre de carottes récoltées (< 20 pts)."}
    ]

    rows = [hof_list[i:i+2] for i in range(0, len(hof_list), 2)]
    for row_cards in rows:
        cols = st.columns(2)
        for i, card in enumerate(row_cards):
            with cols[i]:
                st.markdown(f"""<div class="glass-card" style="position:relative; overflow:hidden; margin-bottom:10px"><div style="position:absolute; right:-10px; top:-10px; font-size:5rem; opacity:0.05; pointer-events:none">{card['icon']}</div><div class="hof-badge" style="color:{card['color']}; border:1px solid {card['color']}">{card['icon']} {card['title']}</div><div style="display:flex; justify-content:space-between; align-items:flex-end;"><div><div class="hof-player">{card['player']}</div><div style="font-size:0.8rem; color:#888; margin-top:4px">{card['desc']}</div></div><div><div class="hof-stat" style="color:{card['color']}">{card['val']}</div><div class="hof-unit">{card['unit']}</div></div></div></div>""", unsafe_allow_html=True)

# --- 8. WEEKLY REPORT (NOUVEAU) ---
def render_weekly_report(df_full_history):
    section_title("WEEKLY <span class='highlight'>REPORT</span>", "Générateur du Rapport Hebdomadaire")
    
    # Génération des données via le moteur weekly.py
    data = generate_weekly_report_data(df_full_history)
    
    if not data:
        st.error("Impossible de générer le rapport (Données insuffisantes ou format de date incorrect).")
        return

    meta = data['meta']
    
    # --- ALERTE SI DIMANCHE MANQUANT ---
    if not meta['has_sunday']:
        st.error("⚠️ ATTENTION : Les données du Dimanche semblent manquantes pour cette semaine !")
        st.warning("Le rapport risque d'être incomplet. Assurez-vous d'avoir saisi les scores de la nuit dernière dans le GSheet avant d'envoyer.")
    
    c1, c2 = st.columns([2, 1])
    
    with c1:
        st.markdown(f"### 📄 APERÇU DU RAPPORT (Semaine #{meta['week_num']})")
        st.markdown(f"<div style='color:#888; font-size:0.9rem; margin-bottom:20px'>Période : {meta['start_date']} au {meta['end_date']}</div>", unsafe_allow_html=True)
        
        # Simulation Visuelle de l'Embed Discord (Style CSS proche de Discord)
        rotw_display = ', '.join([f"**{p}** ({nb})" for p, nb in data['rotw_leaderboard']])
        
        st.markdown(f"""
        <div style="background:#2f3136; border-left: 4px solid #CE1141; padding:15px; border-radius:4px; font-family:'Inter', sans-serif; color:#dcddde; font-size: 0.9rem; line-height: 1.5;">
            <div style="font-weight:700; color:#FFF; font-size:1.1rem; margin-bottom:10px">🦖 RAPTORS WEEKLY REPORT • SEMAINE #{meta['week_num']}</div>
            <div style="font-style:italic; color:#b9bbbe; margin-bottom:15px">*Bilan du Lundi {meta['start_date']} au Dimanche {meta['end_date']}*</div>
            
            <div style="font-weight:700; color:#FFF; margin-top:10px">🏆 LE PODIUM HEBDOMADAIRE</div>
            {format_winners_list([(p['player'], p['score']) for p in data['podium']])} (format complet sur Discord)
            
            <div style="font-weight:700; color:#FFF; margin-top:10px">👑 COURSE AU TRÔNE (Total Titres)</div>
            {rotw_display if rotw_display else "Aucun historique."}
            
            <div style="display:flex; margin-top:15px; gap:20px; flex-wrap:wrap;">
                <div style="flex:1; min-width:150px;">
                    <div style="font-weight:700; color:#FFF">🎯 SNIPER HEBDO</div>
                    {format_winners_list(data['sniper'], " BP")}
                </div>
                <div style="flex:1; min-width:150px;">
                    <div style="font-weight:700; color:#FFF">🛡️ LA MURAILLE</div>
                    {format_winners_list(data['muraille'], " 🥕")}
                </div>
                <div style="flex:1; min-width:150px;">
                    <div style="font-weight:700; color:#FFF">🧗 LA REMONTADA</div>
                    {format_winners_list(data['remontada'], " pts prog.")}
                </div>
            </div>
            
            <div style="font-weight:700; color:#FFF; margin-top:15px">🔥 SÉRIES & DYNAMIQUES</div>
            {'<br>'.join([f"{s['msg']} **{s['player']}** : {s['val']} {s['type']} (Record : {s['record']})" for s in data['streaks']]) if data['streaks'] else "Aucune série significative cette semaine."}
            
            <div style="font-weight:700; color:#FFF; margin-top:15px">📊 TEAM PULSE</div>
            📈 Moyenne : <b>{data['team_stats']['avg']:.1f}</b> ({"+" if data['team_stats']['diff']>0 else ""}{data['team_stats']['diff']:.1f})<br>
            🎯 Best Picks : {data['team_stats']['bp']}<br>
            🛡️ Carottes : {data['team_stats']['carrots']}<br>
            { "✨ <b>CLEAN SHEET SEMAINE !</b> (Aucun score < 25)" if data['team_stats']['clean_sheet'] else ""}
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("### 🚀 ACTIONS")
        st.info("Vérifiez l'aperçu ci-contre. Si tout est bon, cliquez sur le bouton pour envoyer sur Discord.")
        
        if st.button("ENVOYER LE RAPPORT", type="primary", use_container_width=True):
            with st.spinner("Envoi en cours..."):
                res = send_weekly_report_discord(data, "https://raptorsttfl-dashboard.streamlit.app/")
                if res == "success":
                    st.success("✅ Rapport envoyé avec succès !")
                    st.balloons()
                else:
                    st.error(f"Erreur lors de l'envoi : {res}")
