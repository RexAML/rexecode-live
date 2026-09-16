# Rexecode Live — version ultra premium (Streamlit)

Produit haut de gamme, **tout-Streamlit** : verdict, voix de l'économiste, moteurs,
preuve (track record fiable & sans biais), suite de baromètres, premium, alertes,
note de comité. Thème **clair/sombre automatique** (suit l'appareil). Graphiques en
**SVG sur mesure** (pas de widgets génériques). *API & widget viendront en dernier.*

Modèle & application : **Anthony Morlet-Lavidalie**, Rexecode.

## Tester en local
```
cd "C:\projets_claude\projet application prévision"
.venv\Scripts\python.exe -m streamlit run rexlive\app.py
```
Ouvre l'adresse affichée (http://localhost:8501). Navigation par les onglets en haut
(Produit / Suite / Preuve / Alertes / Premium) et bascule **Décideur / Analyste**.

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
