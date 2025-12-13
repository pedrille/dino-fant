import streamlit as st
from src.config import C_ACCENT

# --- UI COMPONENTS ---

def kpi_card(label, value, sub, color="#FFF", is_fixed=False):
    """
    Affiche une carte KPI avec le style 'glass-card'.
    is_fixed=True applique une hauteur fixe pour l'alignement du Dashboard.
    """
    # Si is_fixed est True (pour le haut du dashboard), on ajoute la classe spécifique
    style_class = "glass-card kpi-dashboard-fixed" if is_fixed else "glass-card"
    
    st.markdown(
        f"""
        <div class="{style_class}" style="text-align:center">
            <div class="kpi-label">{label}</div>
            <div class="kpi-num" style="color:{color}">{value}</div>
            <div class="kpi-sub" style="color:{C_ACCENT}">{sub}</div>
        </div>
        """, 
        unsafe_allow_html=True
    )

def section_title(title, subtitle):
    """
    Affiche un titre de section avec la police Rajdhani et un sous-titre.
    """
    st.markdown(f"<h1>{title}</h1><div class='sub-header'>{subtitle}</div>", unsafe_allow_html=True)

def render_gauge(label, value, color):
    """
    Génère le HTML pour une barre de progression (Jauge) simple.
    Utilisé dans les tableaux comparatifs.
    """
    return f"""
    <div class="gauge-container">
        <div class="gauge-label"><span>{label}</span><span>{int(value)}%</span></div>
        <div style="width:100%; background:#333; height:8px; border-radius:4px; overflow:hidden">
            <div style="width:{value}%; background:{color}; height:100%"></div>
        </div>
    </div>
    """
