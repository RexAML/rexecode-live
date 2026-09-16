# Rexecode Live — version premium (Streamlit)

Produit haut de gamme, **tout-Streamlit**. Menu **nommé par le contenu**, lisible par
tous les profils (dirigeants, fédérations, financiers, experts comme généralistes) :

1. **Prévision de croissance** — le chiffre du trimestre en cours + le suivant, le
   commentaire de l'économiste, ce qui fait bouger la prévision, sa trajectoire épurée.
2. **Notre méthode** — comment nous prévoyons (les trois modèles + la combinaison, en clair).
3. **Notre fiabilité** — notre historique de précision, fiable & sans biais (nous uniquement).
4. **Nos autres prévisions** — les baromètres à venir (inflation, emploi, industrie…).

Thème **clair/sombre automatique** (suit l'appareil), **pleine largeur adaptative**
(remplit les grands écrans, lisible sur mobile), graphiques en **SVG sur mesure**.
Note de synthèse téléchargeable. *API & widget viendront en dernier.*

Modèle & application : **Anthony Morlet-Lavidalie**, Rexecode.

## Tester en local
```
cd "C:\projets_claude\projet application prévision"
.venv\Scripts\python.exe -m streamlit run rexlive\app.py
```
Ouvre l'adresse affichée (http://localhost:8501). Navigation par les onglets en haut :
**Prévision de croissance / Notre méthode / Notre fiabilité / Nos autres prévisions**.

**Avec des collègues (même réseau)** :
```
cd "C:\projets_claude\projet application prévision"
.venv\Scripts\python.exe -m streamlit run rexlive\app.py --server.address 0.0.0.0
```
Transmets l'adresse « Network URL ». (Ouvre le port 8501 au pare-feu si besoin.)

## Déployer sur Streamlit Cloud (comme RexNow)
Le dossier `rexlive/` est **autonome** : les données du modèle sont embarquées dans
`rexlive/data/` (donc pas besoin de `results/pib` sur le cloud).

1. Crée un dépôt GitHub (privé), dépose **le contenu de `rexlive/`** à la racine
   (fichiers `app.py`, `requirements.txt`, dossiers `data/` et `.streamlit/`).
2. https://share.streamlit.io → **Create app** → **Main file path : `app.py`** → Deploy.
3. *(optionnel)* Pour protéger l'accès en phase privée : **⋮ → Settings → Secrets** →
   ```
   app_password = "choisis-un-mot-de-passe"
   ```
   Tant qu'aucun `app_password` n'est défini, l'app est ouverte.

## Mettre à jour les chiffres
Après un recalcul du modèle, recopie dans `rexlive/data/` :
```
horizon_summary.json   cats_importance.json   nowcast_evolution.json
```
(depuis `..\results\pib\`) puis re-commit → Streamlit redéploie tout seul.

## Ce qui reste (dernières briques, hors Streamlit)
- **API JSON** (données pour partenaires) et **widget embarquable** : à faire en dernier,
  via un petit serveur dédié (le `rexecode_live/` en Flask du dépôt en montre déjà une
  version locale). Streamlit ne les fait pas proprement.
- Mise en ligne publique sur rexecode.fr, alertes e-mail/Teams réelles : infrastructure Rexecode.

## Contenu
- `app.py` — l'application (un seul fichier, SVG généré, thème adaptatif).
- `data/` — sorties pré-calculées du modèle.
- `.streamlit/config.toml` — thème (suit l'appareil).
- `requirements.txt` — `streamlit` (aucune autre dépendance).
