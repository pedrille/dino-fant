import pandas as pd
import streamlit as st
import unicodedata

# Mapping des mois pour la conversion
MONTH_MAPPING = {
    'janvier': 'January', 'fevrier': 'February', 'mars': 'March', 'avril': 'April',
    'mai': 'May', 'juin': 'June', 'juillet': 'July', 'aout': 'August',
    'septembre': 'September', 'octobre': 'October', 'novembre': 'November', 'decembre': 'December'
}

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

@st.cache_data
def load_data(csv_url):
    """
    Charge les données depuis une URL CSV Google Sheets.
    Gère le parsing des dates en français et la conversion numérique.
    """
    try:
        # Lecture du CSV
        df = pd.read_csv(csv_url)

        # Nettoyage des noms de colonnes (strip espaces)
        df.columns = df.columns.str.strip()

        # Conversion de la colonne 'Date' en datetime
        if 'Date' in df.columns:
            # On s'assure que tout est string
            df['Date_str'] = df['Date'].astype(str)

            # Fonction locale pour parser la date "24 octobre 2024"
            def parse_french_date(date_str):
                try:
                    parts = date_str.split() # ['24', 'octobre', '2024']
                    if len(parts) >= 3:
                        day = parts[0]
                        month_raw = parts[1]
                        year = parts[2]

                        # Normalisation du mois (ex: 'décembre' -> 'decembre')
                        month_norm = normalize_month(month_raw)

                        # Traduction
                        month_en = MONTH_MAPPING.get(month_norm, month_norm)

                        date_en = f"{day} {month_en} {year}"
                        return pd.to_datetime(date_en, format='%d %B %Y', errors='coerce')
                    return pd.NaT
                except:
                    return pd.NaT

            df['Date'] = df['Date_str'].apply(parse_french_date)

            # Extraction du mois (nom complet en français pour l'affichage si besoin, ou on garde le timestamp)
            # Pour l'app, on utilise souvent df['Mois'] qui est une string 'octobre', 'novembre', etc.
            # Si la colonne 'Mois' n'existe pas ou est vide, on peut la recréer depuis la date.
            # Mais ici, le CSV semble déjà avoir une colonne 'Mois' ?
            # Vérifions. Si 'Mois' existe, on la garde. Sinon on la déduit.
            # Le code original utilisait la colonne 'Mois' du CSV.
            pass

        # Conversion des colonnes numériques
        # Les colonnes de stats TTFL sont : 'Score TTFL', 'Moyenne', 'Best Pick', 'Rank', etc.
        # Identifions les colonnes qui doivent être numériques
        numeric_cols = ['Score TTFL', 'Moyenne', 'Best Pick', 'Rank', 'Total', 'Matchs joués']

        for col in df.columns:
            # Si la colonne est censée être numérique ou contient des nombres
            # On tente une conversion
            if col in numeric_cols or df[col].dtype == object:
                # On remplace les virgules par des points si c'est du string
                if df[col].dtype == object:
                     # On force en string d'abord pour éviter les erreurs sur des mixed types
                     df[col] = df[col].astype(str).str.replace(',', '.', regex=False)

                # On convertit en numeric
                df[col] = pd.to_numeric(df[col], errors='ignore')

        return df

    except Exception as e:
        st.error(f"Erreur lors du chargement des données : {e}")
        return pd.DataFrame()
