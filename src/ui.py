
import streamlit as st
from src.config import C_ACCENT, C_GOLD, C_BLUE, C_GREEN, C_RED, C_TEXT, C_BONUS

def kpi_card(label, value, sub, color="#FFF", is_fixed=False):
    # Si is_fixed est True (pour le haut du dashboard), on ajoute la classe spécifique
    style_class = "glass-card kpi-dashboard-fixed" if is_fixed else "glass-card"
    st.markdown(f"""<div class="{style_class}" style="text-align:center"><div class="kpi-label">{label}</div><div class="kpi-num" style="color:{color}">{value}</div><div class="kpi-sub" style="color:{C_ACCENT}">{sub}</div></div>""", unsafe_allow_html=True)

def section_title(title, subtitle):
    st.markdown(f"<h1>{title}</h1><div class='sub-header'>{subtitle}</div>", unsafe_allow_html=True)
