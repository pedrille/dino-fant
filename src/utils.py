
import unicodedata

# --- FONCTION COULEUR UNIFIÉE ---
def get_uniform_color(score):
    if score < 20: return "#EF4444"   # C_RED (< 20)
    elif score < 40: return "#374151" # GRIS-MID  (20-39)
    else: return "#10B981"            # C_GREEN (40+)

def normalize_month(month_str):
    """
    Normalise une chaîne de caractères représentant un mois (en français).
    Supprime les accents et met en minuscules.
    Ex: 'décembre' -> 'decembre', 'Février' -> 'fevrier'
    """
    if not isinstance(month_str, str):
        return month_str

    # Mettre en minuscule
    s = month_str.lower().strip()

    # Supprimer les accents
    # NFD décompose les caractères (ex: é -> e + accent aigu)
    # On garde ensuite seulement les caractères qui ne sont pas des marques de combinaison (Mn)
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

    return s

def render_gauge(label, value, color):
    return f"""
    <div class="gauge-container">
        <div class="gauge-label"><span>{label}</span><span>{int(value)}%</span></div>
        <div style="width:100%; background:#333; height:8px; border-radius:4px; overflow:hidden">
            <div style="width:{value}%; background:{color}; height:100%"></div>
        </div>
    </div>
    """
