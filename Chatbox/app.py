import streamlit as st
import pandas as pd
import spacy
from datetime import datetime

# 📌 Charger spaCy et ton fichier météo
nlp = spacy.load("fr_core_news_sm")  # ou md si tu préfères
df_meteo = pd.read_csv("ton_fichier.csv")  # remplace par le bon nom
df_meteo["date"] = pd.to_datetime(df_meteo["date"], format="%Y%m%d")

import spacy
nlp = spacy.load("fr_core_news_sm")

def lemmatize_list(word_list):
    """Transforme une liste de mots en leurs lemmes."""
    lemmes = []
    for word in word_list:
        doc = nlp(word.lower())
        lemmes.extend([token.lemma_ for token in doc])
    return lemmes

# Mots-clés bruts
raw_keywords = {
    "weather_stat": ["chaud","averse","orage","froid","climat","précipitation","température", "pluie", "humidité", "vent", "ensoleillement"],
    "time_compare": ["plus", "moins", "comparer", "évolution", "augmentation", "baisse"],
    "location_data_lieux": ["houma", "thibodaux", "zone", "secteur", "région", "localité"],
    "location_data_donnees": ["qualité", "niveau", "pollution", "ozone", "température", "air", "eau"],
    "biodiversity_check": ["raton-laveur","écureuil","daim","loutre","serpent","castor","opossum","héron","pélican","tortue","espèce", "animal", "faune", "oiseau", "alligator", "biodiversité", "observer", "présence"],
    "pollution_check": ["pollution", "contamination", "polluer", "seuil"],
    "extreme_event": ["inondation", "ouragan", "tempête", "événement", "pic"],
    "alert_check": ["alerte", "signal", "anomalie", "détection"],
}

# On lemmatise les listes une bonne fois pour toutes
keywords = {key: lemmatize_list(val) for key, val in raw_keywords.items()}

def analyser_intention(question):
    """Analyse la question utilisateur et retourne l’intention détectée."""

    # Lemmatisation de la question
    doc = nlp(question.lower())
    lemmes_question = [token.lemma_ for token in doc]

    # weather_stat + time_compare
    if any(kw in lemmes_question for kw in keywords["weather_stat"]):
        if any(kw in lemmes_question for kw in keywords["time_compare"]):
            return "time_compare"
        return "weather_stat"

    # trend_check (même logique que time_compare mais sans météo)
    if any(kw in lemmes_question for kw in keywords["time_compare"]):
        return "trend_check"

    # location_data : lieu + donnée
    if any(kw in lemmes_question for kw in keywords["location_data_lieux"]) and \
       any(kw in lemmes_question for kw in keywords["location_data_donnees"]):
        return "location_data"

    # biodiversity_check
    if any(kw in lemmes_question for kw in keywords["biodiversity_check"]):
        return "biodiversity_check"

    # pollution_check
    if any(kw in lemmes_question for kw in keywords["pollution_check"]):
        return "pollution_check"

    # extreme_event
    if any(kw in lemmes_question for kw in keywords["extreme_event"]):
        return "extreme_event"

    # alert_check
    if any(kw in lemmes_question for kw in keywords["alert_check"]):
        return "alert_check"

    return "inconnu"

import pandas as pd

# On charge les données météo
df_meteo = pd.read_csv("../donnees_meteo_final.csv")

# Vérification rapide
df_meteo.head()

raw_meteo_keywords = {
    "T2M": ["température", "chaud", "froid", "degrés", "climatique"],
    "T2M_MIN": ["minimale", "minima", "plus froide", "température minimale", "froid"],
    "T2M_MAX_x": ["maximale", "maxima", "plus chaude", "température maximale", "chaleur"],
    "PRECTOTCORR": ["pluie", "précipitation", "averse", "pluvieux", "arrosage"],
    "RH2M": ["humidité", "moiteur", "taux d'humidité"],
    "WS2M": ["vent", "rafale", "vents", "brise", "bourrasque"],
    "ALLSKY_SFC_SW_DWN": ["ensoleillement", "lumière", "rayonnement", "soleil"]
}

keywords_meteo_lemmatized = {
    col: lemmatize_list(mots) for col, mots in raw_meteo_keywords.items()
}

def repondre_weather_stat(question):
    # 1. Lemmatisation
    doc = nlp(question.lower())
    lemmes_question = [token.lemma_ for token in doc]

    # 2. Identifier la colonne météo
    colonne = None
    unite = ""
    for col, mots_lemmes in keywords_meteo_lemmatized.items():
        if any(mot in lemmes_question for mot in mots_lemmes):
            colonne = col
            if "T2M" in col:
                unite = "°C"
            elif col == "PRECTOTCORR":
                unite = "mm"
            elif col == "RH2M":
                unite = "%"
            elif col == "WS2M":
                unite = "m/s"
            elif col == "ALLSKY_SFC_SW_DWN":
                unite = "W/m²"
            break

    if colonne is None:
        return "Je ne sais pas quelle variable météo tu veux analyser."

    # 3. Extraire la période
    periode = extraire_periode(question)
    date_debut = periode["start_date"]
    date_fin = periode["end_date"]
    df_meteo["date"] = pd.to_datetime(df_meteo["date"], format="%Y%m%d")


    # 4. S’assurer que la colonne 'date' est bien de type datetime
    df_meteo["date"] = pd.to_datetime(df_meteo["date"])

    # 5. Filtrer les données sur la période
    donnees_filtrees = df_meteo[
        (df_meteo["date"] >= date_debut) & 
        (df_meteo["date"] <= date_fin)
    ]

    if donnees_filtrees.empty:
        return "Je n’ai trouvé aucune donnée météo pour cette période."

    # 6. Calcul de la moyenne
    moyenne = donnees_filtrees[colonne].mean()
    moyenne_arrondie = round(moyenne, 2)

    # 7. Réponse finale
    return f"La valeur moyenne de {colonne} entre le {date_debut.date()} et le {date_fin.date()} est de {moyenne_arrondie} {unite}."

def extraire_periode(question):
    import re
    from datetime import datetime
    question = question.lower()
    
    mois_dict = {
        "janvier": 1, "février": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6,
        "juillet": 7, "août": 8, "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
    }

    saisons_dict = {
        "printemps": [3, 4, 5],
        "été": [6, 7, 8],
        "automne": [9, 10, 11],
        "hiver": [12, 1, 2]
    }

    # ➤ 1. Jour précis : "le 15 avril 2023"
    jour_match = re.search(r"le (\d{1,2}) (\w+) (\d{4})", question)
    if jour_match:
        jour = int(jour_match.group(1))
        mois = mois_dict.get(jour_match.group(2))
        annee = int(jour_match.group(3))
        if mois:
            date = datetime(annee, mois, jour)
            return {"start_date": date, "end_date": date}

    # ➤ 2. Plage de jours : "du 12 au 30 juin 2023"
    plage_match = re.search(r"du (\d{1,2}) au (\d{1,2}) (\w+) (\d{4})", question)
    if plage_match:
        jour1 = int(plage_match.group(1))
        jour2 = int(plage_match.group(2))
        mois = mois_dict.get(plage_match.group(3))
        annee = int(plage_match.group(4))
        if mois:
            date1 = datetime(annee, mois, jour1)
            date2 = datetime(annee, mois, jour2)
            return {"start_date": date1, "end_date": date2}

    # ➤ 3. Plage de mois : "entre mars et mai 2023"
    mois_range = re.search(r"entre (\w+) et (\w+) (\d{4})", question)
    if mois_range:
        mois1 = mois_dict.get(mois_range.group(1))
        mois2 = mois_dict.get(mois_range.group(2))
        annee = int(mois_range.group(3))
        if mois1 and mois2:
            start_date = datetime(annee, mois1, 1)
            end_date = datetime(annee, mois2, 28)  # simple par défaut
            return {"start_date": start_date, "end_date": end_date}

    # ➤ 4. Mois + année : "en mai 2023"
    mois_annee = re.search(r"en (\w+) (\d{4})", question)
    if mois_annee:
        mois = mois_dict.get(mois_annee.group(1))
        annee = int(mois_annee.group(2))
        if mois:
            start_date = datetime(annee, mois, 1)
            end_date = datetime(annee, mois, 28)  # simple
            return {"start_date": start_date, "end_date": end_date}

    # ➤ 5. Saison + année : "en été 2023"
    saison_annee = re.search(r"(printemps|été|automne|hiver) (\d{4})", question)
    if saison_annee:
        saison = saison_annee.group(1)
        annee = int(saison_annee.group(2))
        mois_saison = saisons_dict.get(saison)
        if saison == "hiver":
            start_date = datetime(annee - 1, 12, 1)
            end_date = datetime(annee, 2, 28)
        else:
            start_date = datetime(annee, mois_saison[0], 1)
            end_date = datetime(annee, mois_saison[-1], 28)
        return {"start_date": start_date, "end_date": end_date}

    # ➤ 6. Année seule : "en 2023"
        # ➤ 6.1 Plage d'années : "de 2020 à 2023" ou "entre 2019 et 2022"
    range_annees = re.search(r"(?:de|entre)\s+(20\d{2})\s+(?:à|et|-)\s+(20\d{2})", question)
    if range_annees:
        annee1 = int(range_annees.group(1))
        annee2 = int(range_annees.group(2))
        if annee1 <= annee2:
            start_date = datetime(annee1, 1, 1)
            end_date = datetime(annee2, 12, 31)
            return {"start_date": start_date, "end_date": end_date}


    annee_match = re.search(r"(20\d{2})", question)
    if annee_match:
        annee = int(annee_match.group(1))
        start_date = datetime(annee, 1, 1)
        end_date = datetime(annee, 12, 31)
        return {"start_date": start_date, "end_date": end_date}

    # ➤ 7. Mois seul sans année → on suppose année courante
    mois_trouve = [m for m in mois_dict if m in question]
    if mois_trouve:
        mois = mois_dict[mois_trouve[0]]
        annee = datetime.now().year
        return {
            "start_date": datetime(annee, mois, 1),
            "end_date": datetime(annee, mois, 28)
        }

    # ➤ 8. Rien trouvé → retour année en cours complète
    annee = datetime.now().year
    return {
        "start_date": datetime(annee, 1, 1),
        "end_date": datetime(annee, 12, 31)
    }



def repondre(question):
    intention = analyser_intention(question)

    if intention == "weather_stat":
        return repondre_weather_stat(question)

    # D’autres intentions à gérer plus tard
    elif intention == "biodiversity_check":
        return "Je vais bientôt répondre aux questions sur la biodiversité !"

    elif intention == "pollution_check":
        return "Je vais bientôt répondre aux questions sur la pollution !"

    else:
        return "Désolé, je ne comprends pas encore ce type de question."


# 🎯 Interface utilisateur
st.title("Agent météo intelligent ☀️🌧️")
question = st.text_input("Pose ta question météo ici :", placeholder="Ex : Quelle était la température en été 2021 ?")

if st.button("Répondre"):
    if question:
        reponse = repondre(question)
        st.success(reponse)
    else:
        st.warning("Pose une question pour que je puisse te répondre.")
