import streamlit as st
from src.config import (
    C_BG, C_TEXT, C_ACCENT, C_BLUE, C_BONUS,
    C_GREEN, C_RED, C_GOLD, C_PURPLE, C_ORANGE
)

# --- FONCTION COULEUR UNIFIÉE ---
def get_uniform_color(score):
    if score < 20: return "#EF4444"   # C_RED (< 20)
    elif score < 40: return "#374151" # GRIS-MID  (20-39)
    else: return "#10B981"            # C_GREEN (40+)

# --- UI COMPONENTS ---
def render_gauge(label, value, color):
    return f"""
    <div class="gauge-container">
        <div class="gauge-label"><span>{label}</span><span>{int(value)}%</span></div>
        <div style="width:100%; background:#333; height:8px; border-radius:4px; overflow:hidden">
            <div style="width:{value}%; background:{color}; height:100%"></div>
        </div>
    </div>
    """

def kpi_card(label, value, sub, color="#FFF", is_fixed=False):
    # Si is_fixed est True (pour le haut du dashboard), on ajoute la classe spécifique
    style_class = "glass-card kpi-dashboard-fixed" if is_fixed else "glass-card"
    st.markdown(f"""<div class="{style_class}" style="text-align:center"><div class="kpi-label">{label}</div><div class="kpi-num" style="color:{color}">{value}</div><div class="kpi-sub" style="color:{C_ACCENT}">{sub}</div></div>""", unsafe_allow_html=True)

def section_title(title, subtitle):
    st.markdown(f"<h1>{title}</h1><div class='sub-header'>{subtitle}</div>", unsafe_allow_html=True)

def inject_custom_css():
    st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Rajdhani:wght@500;600;700;800&display=swap');
    .stApp {{ background-color: {C_BG}; color: {C_TEXT}; font-family: 'Inter', sans-serif; }}
    section[data-testid="stSidebar"] {{ background-color: #000000 !important; border-right: 1px solid #222; }}
    section[data-testid="stSidebar"] img {{ pointer-events: none; }}
    div[data-testid="stSidebarNav"] {{ display: none; }}
    .nav-link {{ font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 1px !important; }}
    h1, h2, h3 {{ font-family: 'Rajdhani', sans-serif; text-transform: uppercase; margin: 0; }}
    h1 {{ font-size: 3rem; font-weight: 800; background: linear-gradient(90deg, #FFF, #888); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .sub-header {{ font-size: 0.9rem; color: #666; letter-spacing: 1.5px; margin-bottom: 25px; font-weight: 500; }}

    /* --- FIX SELECTBOX LABEL COLOR --- */
    .stSelectbox label {{ color: #E5E7EB !important; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; font-size: 0.8rem; }}

    /* --- FIX UI DASHBOARD : CLASSE GENERIQUE --- */
    .glass-card {{
        background: linear-gradient(145deg, rgba(25,25,25,0.6) 0%, rgba(10,10,10,0.8) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.3);
    }}

    /* --- NOUVELLE CLASSE SPECIFIQUE POUR LE HAUT DU DASHBOARD --- */
    .kpi-dashboard-fixed {{
        height: 190px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }}

    .trend-section-title {{ font-family: 'Rajdhani'; font-size: 1.2rem; font-weight: 700; color: #FFF; margin-bottom: 5px; border-left: 4px solid #555; padding-left: 10px; }}
    .trend-section-desc {{ font-size: 0.8rem; color: #888; margin-bottom: 15px; padding-left: 14px; font-style: italic; }}
    .trend-box {{ background: rgba(255,255,255,0.03); border-radius: 12px; padding: 15px; border: 1px solid rgba(255,255,255,0.05); height: 100%; }}
    .hot-header {{ color: {C_ACCENT}; border-bottom: 1px solid rgba(206, 17, 65, 0.3); padding-bottom: 8px; margin-bottom: 10px; font-weight: 700; font-family: 'Rajdhani'; font-size: 1.1rem; display:flex; align-items:center; gap:8px; }}
    .cold-header {{ color: {C_BLUE}; border-bottom: 1px solid rgba(59, 130, 246, 0.3); padding-bottom: 8px; margin-bottom: 10px; font-weight: 700; font-family: 'Rajdhani'; font-size: 1.1rem; display:flex; align-items:center; gap:8px; }}
    .t-row {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.03); }}
    .t-row:last-child {{ border-bottom: none; }}
    .t-val {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.2rem; text-align: right; }}
    .t-sub {{ font-size: 0.7rem; color: #666; display: block; margin-top: 2px; text-align: right; }}
    .t-name {{ font-weight: 500; color: #DDD; font-size: 0.95rem; }}
    .hof-badge {{ display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 0.7rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; background: rgba(255,255,255,0.05); }}
    .hof-player {{ font-family: 'Rajdhani'; font-size: 1.6rem; font-weight: 700; color: #FFF; }}
    .hof-stat {{ font-family: 'Rajdhani'; font-size: 2.2rem; font-weight: 800; text-align: right; line-height: 1; }}
    .hof-unit {{ font-size: 0.7rem; color: #666; text-align: right; font-weight: 600; text-transform: uppercase; }}
    .kpi-label {{ color: #888; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }}
    /* CORRECTION TAILLE DE POLICE ADAPTATIVE */
    .kpi-num {{
        font-family: 'Rajdhani';
        font-weight: 800;
        /* Avant : 2.8rem (trop gros) */
        /* Maintenant : s'adapte entre 1.6rem et 2.2rem selon l'écran */
        font-size: clamp(1.6rem, 2vw, 2.2rem);
        line-height: 1.1;
        color: #FFF;
        /* Empêche les césures moches au milieu des mots */
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    /* --- TOOLTIP INFO SAISON --- */
    .season-info-icon {{
        position: absolute;
        top: 10px;
        right: 10px;
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.3);
        cursor: help;
        z-index: 10;
        transition: color 0.3s;
    }}
    .season-info-icon:hover {{
        color: #FFF;
    }}

    .season-tooltip {{
        visibility: hidden;
        width: 220px;
        background-color: rgba(10, 10, 10, 0.95);
        color: #EEE;
        text-align: left;
        border-radius: 8px;
        padding: 12px;
        position: absolute;
        z-index: 100;
        top: 35px; /* Apparaît sous l'icône */
        right: 0;
        border: 1px solid #444;
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        line-height: 1.4;
        box-shadow: 0 4px 20px rgba(0,0,0,0.8);
        opacity: 0;
        transition: opacity 0.3s;
        pointer-events: none; /* Evite de cliquer dessus par erreur */
    }}

    .season-info-icon:hover .season-tooltip {{
        visibility: visible;
        opacity: 1;
    }}

    .st-label {{ color: #CCC; font-weight:700; display:block; margin-bottom:2px; }}

    /* TEAM HQ & GRILLES */
    .stat-box-mini {{
        background: rgba(255,255,255,0.03);
        border:1px solid rgba(255,255,255,0.05);
        border-radius:12px;
        padding: 20px 10px;
        text-align:center;
        height:100%;
        display:flex;
        flex-direction:column;
        justify-content:center;
        margin-bottom: 0px;
    }}
    .stat-mini-val {{ font-family:'Rajdhani'; font-weight:700; font-size:1.8rem; color:#FFF; line-height:1; }}
    .stat-mini-lbl {{ font-size:0.75rem; color:#888; text-transform:uppercase; margin-top:8px; letter-spacing:1px; }}
    .stat-mini-sub {{ font-size:0.7rem; font-weight:600; margin-top:4px; color:#555; }}

    /* Player Lab - Match Pills FIXED CENTERING WITH TARGET BELOW */
    .match-pill {{
        flex: 0 0 auto;
        min-width: 40px;
        height: 48px;
        border-radius: 6px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        font-family: 'Rajdhani';
        font-weight: 700;
        font-size: 0.9rem;
        color: #FFF;
        margin: 0 2px;
        line-height: 1;
        padding-top: 2px;
    }}
    .mp-score {{ font-size: 1rem; }}
    .mp-icon {{ font-size: 0.6rem; margin-top: 2px; opacity: 0.9; }}

    .match-row {{
        display: flex;
        flex-direction: row-reverse;
        overflow-x: auto;
        gap: 4px;
        padding-bottom: 8px;
        width: 100%;
        justify-content: flex-start;
    }}

    /* Boutons Streamlit Fix */
    .stButton button {{
        background-color: #1F2937 !important;
        color: #FFFFFF !important;
        border: 1px solid #374151 !important;
        font-weight: 600 !important;
        font-family: 'Rajdhani', sans-serif !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    .stButton button:hover {{
        border-color: {C_ACCENT} !important;
        color: {C_ACCENT} !important;
        background-color: #111 !important;
    }}

    .stPlotlyChart {{ width: 100% !important; }}
    div[data-testid="stDataFrame"] {{ border: none !important; }}
    [data-testid="stSidebarUserContent"] {{ padding-top: 2rem; }}

    /* Records Card Adjustment */
    .hq-card-row {{ display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid rgba(255,255,255,0.1); }}
    .hq-card-row:last-child {{ border-bottom:none; }}
    .hq-val {{ font-family:'Rajdhani'; font-weight:800; font-size:1.8rem; color:#FFF; }}
    .hq-lbl {{ font-size:0.8rem; color:#AAA; text-transform:uppercase; display:flex; align-items:center; gap:8px; }}

    .chart-desc {{ font-size:0.8rem; color:#888; margin-bottom:10px; font-style:italic; }}
    .gauge-container {{ width: 100%; background-color: #222; border-radius: 10px; margin-bottom: 15px; }}
    .gauge-fill {{ height: 10px; border-radius: 10px; transition: width 1s ease-in-out; }}
    .gauge-label {{ display: flex; justify-content: space-between; font-size: 0.8rem; margin-bottom: 4px; color: #DDD; }}

    /* TOP 5 PICKS STYLING - NEW V2 DESIGN FIXED */
    .top-pick-card {{
        display: flex;
        align-items: center;
        background: linear-gradient(90deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255,255,255,0.05);
        padding: 10px 15px;
        margin-bottom: 8px;
        border-radius: 8px;
        transition: all 0.2s;
    }}
    .top-pick-card:hover {{ background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.1); transform: translateX(5px); }}

    .tp-rank-badge {{
        font-family: 'Rajdhani'; font-weight: 800; font-size: 1rem;
        width: 30px; height: 30px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 50%;
        background: #222; border: 2px solid #444; color: #FFF;
        margin-right: 12px;
        flex-shrink: 0;
    }}

    .tp-content {{ flex-grow: 1; overflow: hidden; }}
    .tp-date {{ font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }}
    .tp-tags {{ font-size: 0.7rem; color: {C_BONUS}; font-weight: 600; }}

    /* Correction ici : flex-shrink: 0 et margin-left pour forcer l'affichage */
    .tp-score-big {{
        font-family: 'Rajdhani';
        font-weight: 800;
        font-size: 1.8rem;
        color: #FFF;
        line-height: 1;
        margin-left: 15px;
        flex-shrink: 0;
        min-width: 60px;
        text-align: right;
    }}

    /* RADAR LEGEND CUSTOM */
    .legend-box {{
        display: flex; flex-direction: column; justify-content: center; height: 100%;
        padding-left: 20px; border-left: 1px solid #333;
    }}
    .legend-item {{ margin-bottom: 15px; }}
    .legend-title {{ color: {C_ACCENT}; font-family: 'Rajdhani'; font-weight: 700; font-size: 1rem; margin-bottom: 2px; }}
    .legend-desc {{ color: #888; font-size: 0.8rem; line-height: 1.3; }}

    /* Widget Title Custom */
    .widget-title {{ font-family: 'Rajdhani'; font-weight: 700; text-transform: uppercase; color: #AAA; letter-spacing: 1px; margin-bottom: 5px; }}

    /* TRENDS PAGE STYLING */
    .trend-card-row {{
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.05);
    }}
    .trend-card-row:last-child {{ border: none; }}
    .trend-name {{ font-weight: 500; color: #DDD; }}
    .trend-val {{ font-family: 'Rajdhani'; font-weight: 700; font-size: 1.1rem; }}
    .trend-delta {{ font-size: 0.8rem; margin-left: 8px; font-weight: 600; }}
</style>
""", unsafe_allow_html=True)
