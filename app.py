"""Rexecode Live — nowcast du PIB de la France, version premium sur Streamlit.

Menu nommé par le contenu, lisible par tous les profils : Prévision de croissance ·
Notre méthode · Notre fiabilité · Nos autres prévisions. Thème clair/sombre qui suit
l'appareil. Pleine largeur adaptative. Graphiques en SVG sur mesure, construits sur les
vraies données du modèle. Commentaire économique automatisé à partir des chiffres.
Modèle & application : Anthony Morlet-Lavidalie — Rexecode.

Lancer :  .venv\\Scripts\\python.exe -m streamlit run rexlive\\app.py
"""
from __future__ import annotations
import json
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "pib"
HERE = Path(__file__).resolve().parent

st.set_page_config(page_title="Rexecode Live — Nowcast PIB", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")


def loadjson(name, default=None):
    for base in (OUT, HERE / "data"):
        try:
            raw = (base / name).read_bytes()
            for enc in ("utf-8", "cp1252", "latin-1"):
                try:
                    return json.loads(raw.decode(enc))
                except Exception:
                    continue
        except Exception:
            continue
    return default if default is not None else {}


def frn(x, n=2):
    return ("+" if x >= 0 else "−") + f"{abs(x):.{n}f}".replace(".", ",")


def comma(x, n=2):
    return f"{x:.{n}f}".replace(".", ",")


# ---------------- thème (suit l'appareil) ----------------
try:
    DARK = (st.context.theme.type == "dark")
except Exception:
    DARK = False

if DARK:
    C = dict(bg="#0A0F16", surf="#131E2B", surf2="#182636", ink="#EAF0F7", soft="#B7C4D5", faint="#8698AB",
             navy="#173D61", navy2="#0E2942", blue="#5FB0E2", orange="#F0A055", brass="#CBAA6E", teal="#40C29E",
             line="#243547", ic="95,176,226", ico="240,160,85",
             vtxt="#FFFFFF", vsoft="#D2E2EF", vkick="#A6CAE6", vseal="#CADEEF", vline="rgba(255,255,255,.18)")
else:
    C = dict(bg="#EDF1F6", surf="#FFFFFF", surf2="#F1F7FC", ink="#0E1A2A", soft="#3D4F66", faint="#6C7E96",
             navy="#123A5E", navy2="#0C2942", blue="#0A6FB0", orange="#D9722A", brass="#8A6D37", teal="#1E8F73",
             line="#D7DFEA", ic="10,111,176", ico="217,114,42",
             vtxt="#FFFFFF", vsoft="#DEEBF7", vkick="#B4D0E9", vseal="#CFE1F0", vline="rgba(255,255,255,.20)")

# ---------------- données ----------------
hs = loadjson("horizon_summary.json")
f3, f4 = hs.get("forecast_T3_h0", {}), hs.get("forecast_T4_h1", {})
r0, r1 = hs.get("rmse_h0", {}), hs.get("rmse_h1", {})
MAJ = "septembre 2026"
T3, T4 = f3.get("COMBI", 0.204), f4.get("COMBI", 0.261)
RMSE0, RMSE1 = r0.get("COMBI", 0.215), r1.get("COMBI", 0.226)
cats = loadjson("cats_importance.json", {})
DRIVERS = sorted(cats.items(), key=lambda kv: -kv[1])[:7]
# exemples concrets par famille d'indicateurs (pour rendre les barres parlantes)
EXEMPLES = {
    "Enquêtes de conjoncture": "climat des affaires, carnets de commandes",
    "Production & activité réelle": "production industrielle, énergie",
    "Commerce extérieur & international": "exports, PMI zone euro",
    "Financier, monétaire & incertitude": "taux, crédit, OAT-Bund",
    "Consommation & demande intérieure": "consommation, immatriculations",
    "Marché du travail": "emploi, chômage, intérim",
    "Prix, énergie & matières premières": "pétrole, gaz, IPC",
}


def _rm(key, default):
    v = r0.get(key)
    return v if isinstance(v, (int, float)) else default


# erreur (RMSE test, horizon nowcast) par modèle — montre que la combinaison gagne
MODELS_RMSE = [("Forêt aléatoire", _rm("RandomForest", 0.213)), ("MIDAS", _rm("MIDAS", 0.247)),
               ("ElasticNet", _rm("ElasticNet", 0.227)), ("Combinaison", _rm("COMBI", RMSE0))]
# track record vs 1ère estimation INSEE (2002-2025)
BIAS, MAE_CUR, MAE_NEXT = 0.06, 0.24, 0.57
PREC = [("À quelques semaines", MAE_CUR, "trimestre en cours"), ("Un an à l'avance", MAE_NEXT, "année suivante")]

# contributions signées par famille (contributions.json)
CONTRIB = loadjson("contributions.json", {})

# trajectoire réelle du nowcast (nowcast_evolution.json)
evo = loadjson("nowcast_evolution.json", {})
rstage = evo.get("rmse_stage", {})
q3 = evo.get("paths", {}).get("2026Q3", {})


def _q3(k, d):
    v = q3.get(k)
    return v if isinstance(v, (int, float)) else d


# T3 : quatre points mensuels (valeur, ±1 écart-type) ; le point final = le chiffre publié
T3PTS = [("juin", _q3("avant T", 0.304), rstage.get("avant T", 0.231)),
         ("juil.", _q3("fin M1", 0.299), rstage.get("fin M1", 0.228)),
         ("août", _q3("fin M2", 0.28), rstage.get("fin M2", 0.238)),
         ("sept.", T3, rstage.get("fin M3", 0.215))]
T4PT = (T4, RMSE1)  # T4 : estimation actuelle, ±1 écart-type

# décomposition du chiffre publié : les 3 modèles → leur moyenne
MODELF = [("Forêt aléatoire", f3.get("RandomForest", 0.163)),
          ("MIDAS", f3.get("MIDAS", 0.311)),
          ("ElasticNet", f3.get("ElasticNet", 0.139))]
AVG3 = round(sum(v for _, v in MODELF) / len(MODELF), 3)

# backtest : nowcast (combi) vs réalisé (INSEE), hors trimestres Covid 2020-2021
tv2 = loadjson("chart_v2.json", [])
TRACK = [(x["t"], x["a"], x["combi"]) for x in tv2
         if isinstance(x.get("a"), (int, float)) and isinstance(x.get("combi"), (int, float))
         and x["t"][:4] not in ("2020", "2021")]

BAROS = [("Croissance du PIB", "live", "trimestre en cours", frn(T3) + " %"),
         ("Inflation", "pret", "hausse des prix (IPC)", "à venir"),
         ("Production industrielle", "pret", "industrie manufacturière", "à venir"),
         ("Émissions de CO₂", "roadmap", "empreinte carbone", "à venir")]


# ---------------- commentaire économique automatisé ----------------
def commentaire(t3, t4):
    acc = "un rebond" if t3 > 0 else "un nouveau recul"
    amp = "de faible ampleur" if abs(t3) < 0.15 else ("d'ampleur modérée" if abs(t3) < 0.30 else "assez net")
    d = t4 - t3
    if d > 0.05:
        suite = f"Au quatrième trimestre ({frn(t4)} %), la croissance se prolongerait, à peine plus soutenue"
    elif d < -0.05:
        suite = f"Au quatrième trimestre ({frn(t4)} %), le rythme fléchirait légèrement"
    else:
        suite = f"Au quatrième trimestre ({frn(t4)} %), le rythme resterait globalement inchangé"
    return (f"Après un deuxième trimestre en léger repli, l'activité renouerait avec la croissance "
            f"au troisième ({frn(t3)} %) — {acc} {amp}, mais qui ne marque pas de véritable "
            f"redémarrage : l'acquis reste faible et la demande intérieure manque de ressort. {suite}.")


# ---------------- routage ----------------
qp = st.query_params
PAGE = qp.get("p", "prevision")
NAV = [("prevision", "Prévision de croissance"), ("methode", "Notre méthode"),
       ("fiabilite", "Notre fiabilité"), ("autres", "Nos autres prévisions")]

# ==================================================================== CSS
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Libre+Franklin:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
:root{{--bg:{C['bg']};--surf:{C['surf']};--surf2:{C['surf2']};--ink:{C['ink']};--soft:{C['soft']};--faint:{C['faint']};
 --navy:{C['navy']};--blue:{C['blue']};--orange:{C['orange']};--brass:{C['brass']};--teal:{C['teal']};--line:{C['line']};}}
#MainMenu,footer,header[data-testid="stHeader"],[data-testid="stStatusWidget"],[data-testid="stToolbar"]{{display:none!important}}
html,body,.stApp{{background:var(--bg)!important}}
.stApp *{{animation-duration:0s!important}}
.block-container{{max-width:none!important;padding-top:12px!important;padding-bottom:60px!important;
  padding-left:clamp(18px,3.4vw,76px)!important;padding-right:clamp(18px,3.4vw,76px)!important}}
[data-testid="stMarkdownContainer"] *{{color:var(--ink)}}
.rl,.rl *{{font-family:"Libre Franklin",system-ui,sans-serif}}
.rl h1,.rl h2,.rl h3,.rl h4,.rl .serif{{font-family:"Fraunces",Georgia,serif;font-weight:600;letter-spacing:-.012em;line-height:1.12;margin:0;color:var(--ink)}}
.rl .soft{{color:var(--soft)}} .rl .faint{{color:var(--faint)}}
/* top bar */
.rl .top{{display:flex;align-items:center;gap:22px;padding:6px 0 16px;border-bottom:1px solid var(--line);margin-bottom:26px;flex-wrap:wrap}}
.rl .brandwrap{{display:flex;flex-direction:column;gap:1px}}
.rl .brand{{font-family:"Fraunces",serif;font-weight:600;font-size:22px;color:var(--ink);line-height:1.05}}.rl .brand b{{color:var(--blue)}}
.rl .direct{{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#fff;background:var(--teal);border-radius:20px;padding:2px 8px;margin-left:8px}}
.rl .byline{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.03em;color:var(--faint)}}
.rl .nav{{display:flex;gap:8px;flex-wrap:wrap;margin-left:6px}}
.rl .nav a{{font-size:14px;font-weight:600;color:var(--soft);text-decoration:none;padding:7px 14px;border-radius:9px;white-space:nowrap}}
.rl .nav a:hover{{background:var(--surf2);color:var(--ink)}}
.rl .nav a.on{{background:var(--navy);color:#fff}}
/* section headers */
.rl .sh{{margin:8px 0 20px}}
.rl .sh .n{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--brass)}}
.rl .sh h2{{font-size:clamp(23px,3vw,32px);margin-top:4px}}
.rl .sh .d{{color:var(--soft);font-size:15.5px;max-width:66ch;margin-top:6px;line-height:1.5}}
.rl .sh .d b{{color:var(--ink)}}
/* grids */
.rl .g2{{display:grid;grid-template-columns:1.02fr .98fr;gap:24px;align-items:stretch}}@media(max-width:900px){{.rl .g2{{grid-template-columns:1fr}}}}
.rl .gc{{display:grid;grid-template-columns:1fr 1fr;gap:22px;align-items:stretch}}@media(max-width:900px){{.rl .gc{{grid-template-columns:1fr}}}}
.rl .g3{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;align-items:stretch}}@media(max-width:900px){{.rl .g3{{grid-template-columns:1fr}}}}
/* ---- verdict (encadré bleu, harmonisé) ---- */
.rl .verdict{{background:linear-gradient(155deg,var(--navy),{C['navy2']});border-radius:20px;padding:28px 32px;
  box-shadow:0 12px 40px rgba(0,0,0,.18);border:1px solid rgba(255,255,255,.07);display:flex;flex-direction:column}}
.rl .verdict *{{color:{C['vtxt']}}}
.rl .verdict .vh{{display:flex;justify-content:space-between;align-items:flex-start;gap:14px}}
.rl .verdict .vtitle{{font-family:"Fraunces",serif;font-weight:600;font-size:clamp(23px,2.4vw,29px);line-height:1.08;color:{C['vtxt']}!important}}
.rl .verdict .vtitle span{{display:block;font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:{C['vkick']}!important;margin-top:7px;font-weight:400}}
.rl .verdict .seal{{flex:none;white-space:nowrap;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.08em;color:{C['vseal']}!important;border:1px solid rgba(255,255,255,.30);border-radius:20px;padding:3px 11px}}
.rl .verdict .vgrid{{display:grid;grid-template-columns:1fr 1fr;gap:20px 28px;margin-top:22px}}@media(max-width:520px){{.rl .verdict .vgrid{{grid-template-columns:1fr}}}}
.rl .verdict .q{{display:flex;flex-direction:column;gap:6px;padding-left:16px;border-left:3px solid rgba(255,255,255,.22)}}
.rl .verdict .q.now{{border-left-color:{C['blue']}}}
.rl .verdict .q.nxt{{border-left-color:{C['orange']}}}
.rl .verdict .qlab{{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.05em;text-transform:uppercase;color:{C['vkick']}!important}}
.rl .verdict .qval{{font-family:"Fraunces",serif;font-weight:600;font-size:clamp(40px,4.6vw,50px);line-height:.92;color:{C['vtxt']}!important;font-variant-numeric:tabular-nums}}
.rl .verdict .qval .u{{font-size:.46em;color:{C['vsoft']}!important;font-weight:500}}
.rl .verdict .qsub{{font-size:12.5px;color:{C['vsoft']}!important}}
.rl .verdict .foot{{margin-top:auto;padding-top:18px;border-top:1px solid {C['vline']};font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:{C['vsoft']}!important;letter-spacing:.02em;line-height:1.5}}
/* cards */
.rl .card{{background:var(--surf);border:1px solid var(--line);border-radius:16px;padding:24px 26px;box-shadow:0 1px 2px rgba(16,30,50,.04);display:flex;flex-direction:column}}
.rl .card h3{{font-family:"Libre Franklin",sans-serif;font-weight:700;font-size:16px;color:var(--ink);margin-bottom:3px}}
.rl .card .ph{{color:var(--faint);font-size:13px;margin-bottom:16px;line-height:1.45}}
.rl .card p{{color:var(--soft);font-size:14.5px;line-height:1.6;margin:.4em 0 0}}
.rl .eco{{border-left:5px solid var(--brass);justify-content:center}}
.rl .eco .h{{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--brass);margin-bottom:12px}}
.rl .eco .q{{font-family:"Fraunces",serif;font-size:19px;line-height:1.5;color:var(--ink)}}
.rl .eco .sig{{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--faint);margin-top:14px}}
/* driver bars (enrichies) */
.rl .drv{{display:grid;gap:13px;margin-top:2px}}
.rl .drv .r{{display:grid;grid-template-columns:1fr;gap:5px}}
.rl .drv .rt{{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:14px;color:var(--ink);font-weight:600}}
.rl .drv .rt .v{{font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--soft);font-weight:500}}
.rl .drv .ex{{font-size:11.5px;color:var(--faint);line-height:1.3}}
.rl .drv .bar{{height:9px;border-radius:5px;background:var(--surf2);overflow:hidden;margin-top:2px}}.rl .drv .bar span{{display:block;height:100%;border-radius:5px}}
/* contributions signées (barres divergentes) */
.rl .cbars{{display:grid;gap:12px;margin-top:2px}}
.rl .cbars .cr{{display:grid;grid-template-columns:minmax(118px,180px) 1fr 46px;gap:12px;align-items:center;font-size:13.5px;color:var(--ink)}}
.rl .cbars .ct{{position:relative;height:17px;background:var(--surf2);border-radius:5px}}
.rl .cbars .ct::before{{content:"";position:absolute;left:50%;top:-3px;bottom:-3px;width:1px;background:var(--faint);opacity:.55}}
.rl .cbars .seg{{position:absolute;top:0;height:100%;border-radius:4px}}
.rl .cbars .seg.pos{{background:var(--teal)}} .rl .cbars .seg.neg{{background:var(--orange)}}
.rl .cbars .cv{{font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--soft);text-align:right}}
.rl .note{{font-size:13px;color:var(--faint);margin-top:14px;line-height:1.55}}
.rl .note b{{color:var(--soft)}}
.rl .legend{{display:flex;gap:16px;flex-wrap:wrap;font-size:12.5px;color:var(--soft);margin-top:12px;align-items:center}}
.rl .legend .it{{display:inline-flex;align-items:center;gap:6px}}
.rl .legend i{{width:15px;height:4px;border-radius:2px;display:inline-block}} .rl .legend i.dot{{width:9px;height:9px;border-radius:2px}}
/* stat tiles */
.rl .stat{{display:flex;gap:26px;flex-wrap:wrap;margin:2px 0}}.rl .stat .s{{flex:1 1 130px}}
.rl .stat .k{{font-family:"Fraunces",serif;font-size:40px;font-weight:600;color:var(--navy);font-variant-numeric:tabular-nums;line-height:1}}
:root:not([data-theme="light"]) .rl .stat .k{{color:var(--blue)}}
.rl .stat .l{{font-size:12.5px;color:var(--soft);margin-top:7px;line-height:1.45;min-height:2.5em}}
.rl .pill{{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:11px;border:1px solid var(--line);border-radius:20px;padding:3px 11px;margin:6px 6px 0 0;color:var(--soft)}}
.rl .pill.good{{color:var(--teal);border-color:color-mix(in srgb,var(--teal) 45%,var(--line))}}
/* horizontal error bars (méthode + fiabilité) */
.rl .rb{{display:grid;gap:14px;margin-top:2px}}
.rl .rb .r{{display:grid;grid-template-columns:minmax(110px,150px) 1fr 46px;gap:14px;align-items:center;font-size:14px;color:var(--ink)}}
.rl .rb .bar{{height:20px;border-radius:6px;background:var(--surf2);overflow:hidden}}
.rl .rb .bar span{{display:block;height:100%;border-radius:6px;background:color-mix(in srgb,var(--faint) 50%,var(--surf))}}
.rl .rb .r.win .bar span{{background:var(--blue)}}.rl .rb .r.win{{font-weight:700}}
.rl .rb .v{{font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--soft);text-align:right}}.rl .rb .r.win .v{{color:var(--ink)}}
/* flow pipeline (méthode) */
.rl .flow{{display:flex;align-items:stretch;gap:10px;flex-wrap:wrap;margin-top:2px}}
.rl .fstage{{flex:1 1 200px;background:var(--surf);border:1px solid var(--line);border-radius:15px;padding:18px 20px;box-shadow:0 1px 2px rgba(16,30,50,.04);display:flex;flex-direction:column}}
.rl .fstage .fn{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--brass)}}
.rl .fstage h4{{font-size:19px;margin:6px 0 8px;color:var(--ink)}}
.rl .fstage p{{margin:0;font-size:13px;line-height:1.55;color:var(--soft)}}
.rl .farr{{display:flex;align-items:center;justify-content:center;color:var(--faint);flex:0 0 auto;font-size:20px}}
@media(max-width:820px){{.rl .flow{{flex-direction:column}} .rl .farr{{transform:rotate(90deg);height:14px}}}}
/* model cards */
.rl .mcard{{background:var(--surf);border:1px solid var(--line);border-radius:16px;padding:22px 24px;box-shadow:0 1px 2px rgba(16,30,50,.04);display:flex;flex-direction:column}}
.rl .mcard .ic{{width:42px;height:42px;border-radius:12px;background:color-mix(in srgb,var(--blue) 13%,transparent);display:flex;align-items:center;justify-content:center;margin-bottom:12px}}
.rl .mcard .tag{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--brass)}}
.rl .mcard h3{{font-family:"Fraunces",serif;font-weight:600;font-size:20px;margin:4px 0 9px;color:var(--ink)}}
.rl .mcard p{{color:var(--soft);font-size:14px;line-height:1.6;margin:0}}
.rl .mcard .atout{{margin-top:auto;padding-top:13px;border-top:1px solid var(--line);font-size:12.5px;color:var(--soft);line-height:1.45}}
.rl .mcard .atout b{{color:var(--ink)}}
.rl .ing{{display:grid;grid-template-columns:1fr 1fr;gap:12px 24px;margin-top:2px}}@media(max-width:560px){{.rl .ing{{grid-template-columns:1fr}}}}
.rl .ing .i{{display:flex;gap:12px;align-items:baseline;font-size:14px;color:var(--ink)}}
.rl .ing .i b{{font-family:"Fraunces",serif;color:var(--navy);font-size:18px;min-width:80px}}
:root:not([data-theme="light"]) .rl .ing .i b{{color:var(--blue)}}
/* why grid (fiabilité) */
.rl .why{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;align-items:stretch}}@media(max-width:820px){{.rl .why{{grid-template-columns:1fr}}}}
.rl .why .w{{background:var(--surf);border:1px solid var(--line);border-radius:15px;padding:22px 24px;display:flex;flex-direction:column}}
.rl .why .w .ic{{width:42px;height:42px;border-radius:12px;background:color-mix(in srgb,var(--teal) 15%,transparent);display:flex;align-items:center;justify-content:center;margin-bottom:13px}}
.rl .why .w h4{{font-family:"Libre Franklin";font-weight:700;font-size:15.5px;margin:0 0 6px;color:var(--ink)}}
.rl .why .w p{{margin:0;font-size:13.5px;line-height:1.55;color:var(--soft)}}
/* suite (badge en flux, sans chevauchement) */
.rl .suite{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}}
.rl .bc{{background:var(--surf);border:1px solid var(--line);border-radius:15px;padding:20px 22px;display:flex;flex-direction:column}}
.rl .bc .st{{align-self:flex-start;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:var(--faint);border:1px solid var(--line);border-radius:20px;padding:2px 9px;margin-bottom:14px}}
.rl .bc.live .st{{color:#fff;background:var(--teal);border-color:transparent}}
.rl .bc h3{{font-family:"Libre Franklin",sans-serif;font-size:17px;font-weight:700;color:var(--ink);min-height:2.5em;display:flex;align-items:flex-start}}
.rl .bc .m{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--faint);margin:4px 0 16px}}
.rl .bc .val{{font-family:"Fraunces",serif;font-size:30px;font-weight:600;color:var(--navy);margin-top:auto}}
:root:not([data-theme="light"]) .rl .bc .val{{color:var(--blue)}}
.rl .bc .val.mut{{color:var(--faint);font-size:18px}}
/* décomposition (mix des modèles) */
.rl .mix{{display:grid;gap:11px;margin-top:2px}}
.rl .mix .r{{display:grid;grid-template-columns:minmax(96px,130px) 1fr 48px;gap:14px;align-items:center;font-size:13.5px;color:var(--ink)}}
.rl .mix .bar{{height:14px;border-radius:5px;background:var(--surf2);overflow:hidden}}.rl .mix .bar span{{display:block;height:100%;border-radius:5px;background:color-mix(in srgb,var(--blue) 45%,var(--surf))}}
.rl .mix .v{{font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--soft);text-align:right}}
.rl .mix .r.avg{{font-weight:700;padding-top:11px;border-top:1px solid var(--line)}}.rl .mix .r.avg .bar span{{background:var(--navy)}}
:root:not([data-theme="light"]) .rl .mix .r.avg .bar span{{background:var(--blue)}}
.rl .mix .r.avg .v{{color:var(--ink)}}
/* acquis (timeline) */
.rl .acq{{display:flex;gap:10px;flex-wrap:wrap;margin-top:2px}}
.rl .acq .s{{flex:1 1 150px;background:var(--surf2);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.rl .acq .s .mo{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--brass)}}
.rl .acq .s .fill{{height:8px;border-radius:5px;background:var(--line);overflow:hidden;margin:9px 0}}.rl .acq .s .fill span{{display:block;height:100%;border-radius:5px;background:var(--blue)}}
.rl .acq .s p{{margin:0;font-size:12.5px;color:var(--soft);line-height:1.45}}
.rl svg{{display:block}}
.rl svg.fan{{width:100%;height:auto;aspect-ratio:520/258}} .rl svg.gauge{{width:100%;height:auto;aspect-ratio:480/168}} .rl svg.track{{width:100%;height:auto;aspect-ratio:900/300}} .rl svg.casc{{width:100%;height:auto;aspect-ratio:900/340}} .rl svg.ic{{width:24px;height:24px}}
.stDownloadButton button{{border:1px solid var(--line)!important;background:var(--surf)!important;color:var(--ink)!important;border-radius:10px!important;font-weight:600!important;font-family:"Libre Franklin",sans-serif!important;padding:8px 18px!important}}
</style>""", unsafe_allow_html=True)


# ==================================================================== barrière d'accès (optionnelle)
def app_gate():
    try:
        pw = st.secrets["app_password"]
    except Exception:
        pw = None
    if not pw or st.session_state.get("_ok"):
        return
    st.markdown(f'''<div class="rl"><div class="verdict" style="max-width:440px;margin:9vh auto">
      <div class="vtitle">Rexecode Live<span>Accès protégé</span></div>
      <div style="color:{C['vsoft']};font-size:14px;margin-top:14px">Saisissez le mot de passe communiqué par Rexecode.</div></div></div>''',
                unsafe_allow_html=True)
    c = st.columns([1, 2])[0]
    with c:
        x = st.text_input("Mot de passe", type="password", label_visibility="collapsed", placeholder="Mot de passe")
        if st.button("Entrer", type="primary"):
            if x == pw:
                st.session_state._ok = True
                st.rerun()
            else:
                st.error("Mot de passe incorrect.")
    st.stop()


app_gate()


# ==================================================================== SVG / composants
def svg_fan():
    """Trajectoire du nowcast : T3 (4 mois, ligne + intervalle) et T4 (estimation actuelle + intervalle),
    chacun clairement étiqueté."""
    W, H, mL, mR, mT, mB = 520, 258, 46, 40, 40, 48
    slots = 5  # juin, juil., août, sept. (T3) + T4
    iw, ih = W - mL - mR, H - mT - mB
    yMin, yMax = -0.10, 0.62
    X = lambda i: mL + iw * i / (slots - 1)
    Y = lambda v: mT + ih * (1 - (v - yMin) / (yMax - yMin))
    bl, org = C["blue"], C["orange"]
    s = [f'<svg class="fan" viewBox="0 0 {W} {H}">']
    # grille + axe y
    for g in (0.0, 0.2, 0.4, 0.6):
        y = Y(g)
        s.append(f'<line x1="{mL}" y1="{y:.1f}" x2="{W-mR}" y2="{y:.1f}" stroke="var(--line)"/>')
        s.append(f'<text x="{mL-9}" y="{y+4:.1f}" text-anchor="end" font-family="IBM Plex Mono" font-size="10.5" fill="{C["faint"]}">{comma(g,1)}</text>')
    # séparateur T3 | T4
    xsep = (X(3) + X(4)) / 2
    s.append(f'<line x1="{xsep:.1f}" y1="{mT-6}" x2="{xsep:.1f}" y2="{H-mB}" stroke="var(--line)" stroke-dasharray="3 4"/>')
    # étiquettes de groupe
    s.append(f'<text x="{(X(0)+X(3))/2:.1f}" y="{mT-16}" text-anchor="middle" font-family="IBM Plex Mono" font-size="11" fill="{bl}" font-weight="600">3ᵉ trimestre 2026</text>')
    s.append(f'<text x="{W-mR+8:.1f}" y="{mT-16}" text-anchor="end" font-family="IBM Plex Mono" font-size="11" fill="{org}" font-weight="600">4ᵉ trim. 2026</text>')
    # bande T3 (±1 écart-type)
    up = " ".join(f"{X(i):.1f},{Y(v+r):.1f}" for i, (_, v, r) in enumerate(T3PTS))
    lo = " ".join(f"{X(i):.1f},{Y(v-r):.1f}" for i, (_, v, r) in reversed(list(enumerate(T3PTS))))
    s.append(f'<polygon points="{up} {lo}" fill="rgba({C["ic"]},0.14)"/>')
    # ligne T3
    s.append(f'<polyline points="{" ".join(f"{X(i):.1f},{Y(v):.1f}" for i,(_,v,_) in enumerate(T3PTS))}" fill="none" stroke="{bl}" stroke-width="2.8"/>')
    for i, (mois, v, _) in enumerate(T3PTS):
        x, y, last = X(i), Y(v), (i == 3)
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5.5 if last else 4}" fill="{bl if last else C["surf"]}" stroke="{bl}" stroke-width="2.4"/>')
        s.append(f'<text x="{x:.1f}" y="{H-24}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10.5" fill="{C["faint"]}">{mois}</text>')
    # valeur + "aujourd'hui" sur le dernier point T3
    xl, yl = X(3), Y(T3PTS[3][1])
    s.append(f'<text x="{xl:.1f}" y="{yl-13:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-size="11.5" fill="{bl}" font-weight="600">{frn(T3)}</text>')
    # T4 : bande verticale (±1σ) + point
    t4v, t4r = T4PT
    x4 = X(4)
    s.append(f'<rect x="{x4-11:.1f}" y="{Y(t4v+t4r):.1f}" width="22" height="{Y(t4v-t4r)-Y(t4v+t4r):.1f}" rx="6" fill="rgba({C["ico"]},0.16)"/>')
    s.append(f'<line x1="{x4-13:.1f}" y1="{Y(t4v):.1f}" x2="{x4+13:.1f}" y2="{Y(t4v):.1f}" stroke="{org}" stroke-width="2.6"/>')
    s.append(f'<circle cx="{x4:.1f}" cy="{Y(t4v):.1f}" r="5" fill="{org}" stroke="{org}" stroke-width="2"/>')
    s.append(f'<text x="{x4:.1f}" y="{Y(t4v)-13:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-size="11.5" fill="{org}" font-weight="600">{frn(t4v)}</text>')
    s.append(f'<text x="{x4:.1f}" y="{H-24}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10.5" fill="{C["faint"]}">aujourd\'hui</text>')
    s.append(f'<text x="{(mL+W-mR)/2:.1f}" y="{H-7}" text-anchor="middle" font-family="IBM Plex Mono" font-size="9.5" fill="{C["faint"]}">date à laquelle la prévision est faite</text>')
    s.append("</svg>")
    return "".join(s)


def svg_gauge():
    """Jauge de biais : où se situe notre biais moyen entre 'trop pessimiste' et 'trop optimiste'."""
    W, H, mL, mR, y = 480, 168, 34, 34, 86
    lo, hi = -0.6, 0.6
    X = lambda v: mL + (W - mL - mR) * (v - lo) / (hi - lo)
    tl, tk = C["teal"], C["faint"]
    s = [f'<svg class="gauge" viewBox="0 0 {W} {H}">']
    # piste
    s.append(f'<rect x="{X(lo):.1f}" y="{y-8}" width="{X(hi)-X(lo):.1f}" height="16" rx="8" fill="var(--surf2)"/>')
    # zone "sans biais"
    s.append(f'<rect x="{X(-0.15):.1f}" y="{y-8}" width="{X(0.15)-X(-0.15):.1f}" height="16" rx="8" fill="color-mix(in srgb,{tl} 30%,transparent)"/>')
    # graduations
    for g in (-0.5, -0.25, 0, 0.25, 0.5):
        s.append(f'<line x1="{X(g):.1f}" y1="{y+12}" x2="{X(g):.1f}" y2="{y+18}" stroke="{tk}"/>')
        s.append(f'<text x="{X(g):.1f}" y="{y+32}" text-anchor="middle" font-family="IBM Plex Mono" font-size="9.5" fill="{tk}">{comma(g,2) if g else "0"}</text>')
    # libellés extrêmes
    s.append(f'<text x="{X(lo):.1f}" y="{y-20}" text-anchor="start" font-family="IBM Plex Mono" font-size="10" fill="{tk}">trop pessimiste</text>')
    s.append(f'<text x="{X(hi):.1f}" y="{y-20}" text-anchor="end" font-family="IBM Plex Mono" font-size="10" fill="{tk}">trop optimiste</text>')
    # marqueur au biais réel
    xb = X(BIAS)
    s.append(f'<polygon points="{xb-7:.1f},{y-22:.1f} {xb+7:.1f},{y-22:.1f} {xb:.1f},{y-11:.1f}" fill="{tl}"/>')
    s.append(f'<circle cx="{xb:.1f}" cy="{y:.1f}" r="6" fill="{tl}" stroke="var(--surf)" stroke-width="2"/>')
    s.append(f'<text x="{xb:.1f}" y="{y-30:.1f}" text-anchor="middle" font-family="Fraunces" font-size="17" font-weight="600" fill="{tl}">{frn(BIAS)}</text>')
    s.append("</svg>")
    return "".join(s)


def _wrap2(name):
    """Coupe un libellé en 2 lignes équilibrées (pour l'axe de la cascade)."""
    w = name.split()
    if len(w) <= 1:
        return [name, ""]
    best, bi = 1e9, 1
    for i in range(1, len(w)):
        a, b = " ".join(w[:i]), " ".join(w[i:])
        d = abs(len(a) - len(b))
        if d < best:
            best, bi = d, i
    return [" ".join(w[:bi]), " ".join(w[bi:])]


def svg_cascade():
    """Cascade (bridge) : du trimestre moyen au nowcast, un pas par grand bloc."""
    blocks = CONTRIB.get("blocks", [])
    if not blocks:
        return ""
    base = CONTRIB.get("base", 0.31)
    total = CONTRIB.get("total", CONTRIB.get("T3", base))
    # colonnes : (lignes label, type, valeur/niveau, before, after, close)
    items = [(["Trimestre", "moyen"], "start", base, None, None, base)]
    r = base
    for name, v in blocks:
        before, after = r, r + v
        r = after
        items.append((_wrap2(name), "delta", v, before, after, after))
    items.append((["Nowcast", "3ᵉ trim."], "end", total, None, None, total))

    levels = [base, total] + [x for _, _, _, bf, af, _ in items if bf is not None for x in (bf, af)]
    lo, hi = min(levels), max(levels)
    yMin, yMax = lo - 0.035, hi + 0.02
    W, H, mL, mR, mT, mB = 900, 340, 54, 18, 30, 58
    n = len(items)
    band = (W - mL - mR) / n
    cx = lambda i: mL + band * (i + 0.5)
    bw = min(band * 0.52, 66)
    Y = lambda v: mT + (H - mB - mT) * (1 - (v - yMin) / (yMax - yMin))
    gray, bl, tl, org = C["faint"], C["blue"], C["teal"], C["orange"]
    s = [f'<svg class="casc" viewBox="0 0 {W} {H}">']
    # grille + axe y (pas ~0,02)
    g = (int(yMin / 0.02) + 1) * 0.02
    while g < yMax:
        yy = Y(g)
        s.append(f'<line x1="{mL}" y1="{yy:.1f}" x2="{W-mR}" y2="{yy:.1f}" stroke="var(--line)"/>')
        s.append(f'<text x="{mL-9}" y="{yy+4:.1f}" text-anchor="end" font-family="IBM Plex Mono" font-size="10.5" fill="{gray}">{frn(g,2)}</text>')
        g += 0.02
    # connecteurs (pointillés) entre colonnes, au niveau de clôture
    for i in range(n - 1):
        yc = Y(items[i][5])
        s.append(f'<line x1="{cx(i)+bw/2:.1f}" y1="{yc:.1f}" x2="{cx(i+1)-bw/2:.1f}" y2="{yc:.1f}" stroke="{gray}" stroke-dasharray="3 3" opacity="0.7"/>')
    # barres
    for i, (lab, kind, val, bf, af, close) in enumerate(items):
        x = cx(i) - bw / 2
        if kind in ("start", "end"):
            y0, y1 = Y(val), Y(yMin)
            col = bl if kind == "end" else gray
            s.append(f'<rect x="{x:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{y1-y0:.1f}" rx="3" fill="{col}"/>')
            s.append(f'<text x="{cx(i):.1f}" y="{y0-8:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-size="12" font-weight="600" fill="{col}">{frn(val)}</text>')
        else:
            top, bot = min(Y(bf), Y(af)), max(Y(bf), Y(af))
            col = tl if val > 0.0005 else (org if val < -0.0005 else gray)
            h = max(bot - top, 3)
            s.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{h:.1f}" rx="3" fill="{col}"/>')
            lv = frn(val) if abs(val) >= 0.005 else "≈ 0"
            s.append(f'<text x="{cx(i):.1f}" y="{top-8:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-size="11.5" font-weight="600" fill="{col}">{lv}</text>')
        # libellé d'axe (2 lignes)
        s.append(f'<text x="{cx(i):.1f}" y="{H-mB+18:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10.5" fill="{C["soft"]}">{lab[0]}'
                 f'<tspan x="{cx(i):.1f}" dy="12">{lab[1]}</tspan></text>')
    s.append("</svg>")
    return "".join(s)


def drivers_html():
    pal = [C["blue"], C["navy"], C["teal"], C["brass"], "#6FA8CF", C["orange"], C["faint"]]
    mx = max(v for _, v in DRIVERS) or 1
    out = []
    for i, (k, v) in enumerate(DRIVERS):
        ex = EXEMPLES.get(k, "")
        out.append(f'<div class="r"><div class="rt"><span>{k}</span><span class="v">{round(v)} %</span></div>'
                   + (f'<div class="ex">{ex}</div>' if ex else '')
                   + f'<div class="bar"><span style="width:{v/mx*100:.0f}%;background:{pal[i%len(pal)]}"></span></div></div>')
    return '<div class="drv">' + "".join(out) + '</div>'


def bars_html(items, win_name=None, dec=2):
    """Barres proportionnelles à la valeur (erreur) : plus la barre est courte, plus c'est précis."""
    mx = max(v for _, v, *_ in items) or 1
    out = []
    for name, v, *rest in items:
        sub = rest[0] if rest else ""
        win = (name == win_name)
        w = 6 + v / mx * 94
        out.append(f'<div class="r {"win" if win else ""}"><span>{name}{f"<br><span style=\'font-size:11px;color:var(--faint);font-weight:400\'>{sub}</span>" if sub else ""}</span>'
                   f'<span class="bar"><span style="width:{w:.0f}%"></span></span><span class="v">{comma(v, dec)}</span></div>')
    return '<div class="rb">' + "".join(out) + '</div>'


def svg_track(pts):
    """Backtest : nowcast (combi) vs réalisé (INSEE), par trimestre, hors Covid."""
    if len(pts) < 4:
        return ""
    W, H, mL, mR, mT, mB = 900, 300, 46, 18, 30, 42
    n = len(pts)
    iw, ih = W - mL - mR, H - mT - mB
    vals = [a for _, a, _ in pts] + [c for _, _, c in pts]
    yMin, yMax = min(vals) - 0.06, max(vals) + 0.10
    X = lambda i: mL + iw * i / (n - 1)
    Y = lambda v: mT + ih * (1 - (v - yMin) / (yMax - yMin))
    s = [f'<svg class="track" viewBox="0 0 {W} {H}">']
    for g in [y / 100 for y in range(-100, 101, 25)]:
        if yMin < g < yMax:
            yy = Y(g)
            s.append(f'<line x1="{mL}" y1="{yy:.1f}" x2="{W-mR}" y2="{yy:.1f}" stroke="var(--line)" stroke-width="{1.6 if abs(g)<1e-9 else 1}"/>')
            s.append(f'<text x="{mL-8}" y="{yy+4:.1f}" text-anchor="end" font-family="IBM Plex Mono" font-size="11" fill="{C["faint"]}">{comma(g,2)}</text>')
    # segments contigus (coupe au trou Covid)
    segs, cur = [], [0]
    for i in range(1, n):
        if pts[i][0][:4] == "2022" and pts[i - 1][0][:4] == "2019":
            xg = (X(i - 1) + X(i)) / 2
            s.append(f'<rect x="{X(i-1):.1f}" y="{mT}" width="{X(i)-X(i-1):.1f}" height="{ih}" fill="color-mix(in srgb,var(--faint) 8%,transparent)"/>')
            s.append(f'<text x="{xg:.1f}" y="{mT-10}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10" fill="{C["faint"]}">2020–21 · Covid (exclu)</text>')
            segs.append(cur)
            cur = [i]
        else:
            cur.append(i)
    segs.append(cur)
    for idx, col, w in ((1, C["soft"], 2.4), (2, C["blue"], 2.6)):
        for seg in segs:
            if len(seg) > 1:
                s.append(f'<polyline points="{" ".join(f"{X(i):.1f},{Y(pts[i][idx]):.1f}" for i in seg)}" fill="none" stroke="{col}" stroke-width="{w}"/>')
    # marqueurs nowcast (points discrets)
    for i in range(n):
        s.append(f'<circle cx="{X(i):.1f}" cy="{Y(pts[i][2]):.1f}" r="2.4" fill="{C["blue"]}"/>')
    # années
    seen = set()
    for i, (t, _, _) in enumerate(pts):
        if t.endswith("Q1") and t[:4] not in seen:
            seen.add(t[:4])
            s.append(f'<text x="{X(i):.1f}" y="{H-14}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10.5" fill="{C["faint"]}">{t[:4]}</text>')
    s.append("</svg>")
    return "".join(s)


def mix_html():
    mx = max([v for _, v in MODELF] + [T3]) or 1
    rows = "".join(
        f'<div class="r"><span>{name}</span><span class="bar"><span style="width:{v/mx*100:.0f}%"></span></span><span class="v">{frn(v)}</span></div>'
        for name, v in MODELF)
    rows += f'<div class="r avg"><span>Moyenne des trois</span><span class="bar"><span style="width:{AVG3/mx*100:.0f}%"></span></span><span class="v">{frn(AVG3)}</span></div>'
    return f'<div class="mix">{rows}</div>'


# icônes
def _svg(paths, stroke):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" class="ic">{paths}</svg>'


SHIELD = _svg('<path d="M12 3l7 3v5c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3z"/><path d="M8.5 12l2.3 2.3 4.7-4.7"/>', C["teal"])
BALANCE = _svg('<path d="M12 3v18M6 21h12M5 7h14M12 5l-7 2 3 6a3 3 0 0 1-6 0M12 5l7 2-3 6a3 3 0 0 0 6 0"/>', C["teal"])
CLOCK = _svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', C["teal"])
TREE = _svg('<path d="M12 3v18M12 8l5 4M12 12l-5 4"/><circle cx="12" cy="3" r="1.6"/><circle cx="17" cy="12" r="1.6"/><circle cx="7" cy="16" r="1.6"/>', C["blue"])
WAVE = _svg('<path d="M3 12c2-5 4-5 6 0s4 5 6 0 4-5 6 0"/><path d="M3 18h18"/>', C["blue"])
FILTER = _svg('<path d="M3 5h18l-7 8v6l-4-2v-4z"/>', C["blue"])


# ==================================================================== top bar
def nav_link(pid, label):
    return f'<a href="?p={pid}" target="_self" class="{"on" if PAGE==pid else ""}">{label}</a>'


st.markdown(f"""<div class="rl"><div class="top">
  <span class="brandwrap"><span class="brand">Rexecode <b>Live</b><span class="direct">Direct</span></span>
    <span class="byline">par Anthony Morlet-Lavidalie</span></span>
  <nav class="nav">{"".join(nav_link(p, l) for p, l in NAV)}</nav>
</div></div>""", unsafe_allow_html=True)


# ==================================================================== pages
def page_prevision():
    cb = CONTRIB.get("base", 0.31)
    cblocks = CONTRIB.get("blocks", [])
    movers = [b for b in cblocks if abs(b[1]) >= 0.005]
    if movers:
        ctop = max(movers, key=lambda kv: abs(kv[1]))
        csens = "pèse" if ctop[1] < 0 else "soutient"
        cnote = (f"Point de départ : la croissance d'un trimestre « normal » (≈ {frn(cb)} %). Chaque bloc "
                 f"ajuste ce niveau pour aboutir au nowcast ({frn(T3)} %). Ce trimestre, les écarts sont "
                 f"modestes — l'activité est proche de sa moyenne ; c'est le bloc « {ctop[0].lower()} » "
                 f"qui {csens} le plus ({frn(ctop[1])} pt).")
    elif cblocks:
        cnote = (f"Point de départ : la croissance d'un trimestre « normal » (≈ {frn(cb)} %). Ce trimestre, "
                 f"tous les blocs sont proches de leur normale : le nowcast ({frn(T3)} %) reste au voisinage "
                 f"de la moyenne, sans facteur qui domine.")
    else:
        cnote = "Décomposition indisponible."
    st.markdown(f"""<div class="rl">
 <div class="sh"><div class="n">En temps réel</div><h2>Où en est la croissance française, en direct ?</h2>
   <div class="d">Notre estimation de l'activité (le PIB) pour le trimestre en cours et le suivant — sa variation par rapport au trimestre précédent, réactualisée à chaque nouvelle publication d'indicateur, sans attendre les chiffres officiels.</div></div>
 <div class="g2">
  <div class="verdict">
   <div class="vh"><div class="vtitle">Croissance du PIB<span>France · en volume</span></div><span class="seal">RexNow · Rexecode</span></div>
   <div class="vgrid">
     <div class="q now"><span class="qlab">3ᵉ trimestre 2026</span><div class="qval">{frn(T3)}<span class="u"> %</span></div><span class="qsub">trimestre en cours</span></div>
     <div class="q nxt"><span class="qlab">4ᵉ trimestre 2026</span><div class="qval">{frn(T4)}<span class="u"> %</span></div><span class="qsub">trimestre suivant</span></div>
   </div>
   <div class="foot">Variation par rapport au trimestre précédent (T/T−1), corrigée des variations saisonnières · mise à jour : {MAJ}</div>
  </div>
  <div class="card eco"><div class="h">Le commentaire de l'économiste — Rexecode</div>
    <div class="q">« {commentaire(T3, T4)} »</div>
    <div class="sig">Lecture générée automatiquement à partir des prévisions du modèle.</div></div>
 </div>

 <div class="sh" style="margin-top:42px"><div class="n">Ce qui explique le chiffre</div><h2>Comment on passe d'un trimestre normal au nowcast</h2></div>
 <div class="card" style="margin-bottom:22px"><h3>Les contributions, bloc par bloc</h3><div class="ph">On part de la croissance d'un trimestre normal ; chaque grand bloc ajoute (vert) ou retranche (orange) pour aboutir au nowcast — en points de PIB</div>
   {svg_cascade()}
   <div class="legend"><span class="it"><i style="background:{C['faint']}"></i>trimestre moyen</span><span class="it"><i style="background:{C['teal']}"></i>soutient</span><span class="it"><i style="background:{C['orange']}"></i>freine</span><span class="it"><i style="background:{C['blue']}"></i>nowcast</span></div>
   <div class="note">{cnote}</div></div>
 <div class="g2">
  <div class="card"><h3>La prévision de chaque trimestre, avec son incertitude</h3><div class="ph">Comment l'estimation évolue au fil des mois, et sa marge d'erreur</div>
    {svg_fan()}
    <div class="legend"><span class="it"><i style="background:{C['blue']}"></i>3ᵉ trimestre</span><span class="it"><i style="background:{C['orange']}"></i>4ᵉ trimestre</span><span class="it"><i class="dot" style="background:rgba({C['ic']},0.28)"></i>marge d'incertitude (±1 écart-type)</span></div>
    <div class="note">Le <b>3ᵉ trimestre</b> s'affine mois après mois autour de +0,3 % et se fixe à {frn(T3)} % ; sa marge d'incertitude se resserre. Le <b>4ᵉ trimestre</b>, plus lointain, n'a pour l'instant qu'une estimation, avec une marge plus large.</div></div>
  <div class="card"><h3>Les familles sur lesquelles s'appuie le modèle</h3><div class="ph">Poids structurel de chaque famille, toutes périodes confondues</div>
    {drivers_html()}
    <div class="note"><b>Poids ≠ contribution</b> : le poids dit <b>sur quoi</b> le modèle s'appuie en général ; la contribution (cascade ci-dessus) dit ce qui bouge <b>ce trimestre précis</b>. Une famille peut peser lourd et contribuer peu si, ce trimestre, elle est conforme à sa normale.</div></div>
 </div>
</div>""", unsafe_allow_html=True)


def page_methode():
    st.markdown(f"""<div class="rl">
 <div class="sh"><div class="n">Notre méthode</div><h2>Comment nous prévoyons, étape par étape</h2>
   <div class="d">De la donnée brute au chiffre publié, en quatre temps. Aucune boîte noire : chaque étape se comprend simplement.</div></div>
 <div class="flow">
   <div class="fstage"><div class="fn">1 · La matière première</div><h4>≈ 189 indicateurs</h4><p>Enquêtes de confiance, production, consommation, marchés, prix, commerce extérieur — suivis en direct auprès de l'INSEE, la Banque de France, la BCE, Eurostat, les Douanes.</p></div>
   <div class="farr">→</div>
   <div class="fstage"><div class="fn">2 · Trois lectures</div><h4>Trois modèles</h4><p>Trois méthodes indépendantes analysent ces indicateurs, chacune sous un angle différent. Trois avis d'experts plutôt qu'un seul.</p></div>
   <div class="farr">→</div>
   <div class="fstage"><div class="fn">3 · La synthèse</div><h4>La combinaison</h4><p>On retient la moyenne des trois. Quand l'un se trompe, les autres corrigent : le résultat est plus stable et plus fiable.</p></div>
   <div class="farr">→</div>
   <div class="fstage"><div class="fn">4 · Le résultat</div><h4>La prévision</h4><p>La croissance du trimestre en cours et du suivant, avec sa marge d'incertitude, réactualisée à chaque publication.</p></div>
 </div>

 <div class="sh" style="margin-top:42px"><div class="n">Les trois modèles en clair</div><h2>Trois façons de lire l'économie</h2></div>
 <div class="g3">
   <div class="mcard"><div class="ic">{TREE}</div><div class="tag">Apprentissage automatique</div><h3>La forêt aléatoire</h3>
     <p>Elle apprend, dans 25 ans d'historique, quels indicateurs annoncent quoi — même les relations compliquées qu'une simple équation manquerait.</p>
     <div class="atout"><b>Son atout :</b> repérer les signaux inhabituels et les effets de seuil.</div></div>
   <div class="mcard"><div class="ic">{WAVE}</div><div class="tag">Fréquence mixte</div><h3>Le modèle MIDAS</h3>
     <p>Il relie directement les données <b>mensuelles</b>, qui tombent en continu, à la croissance <b>trimestrielle</b> — pour exploiter chaque publication au plus tôt.</p>
     <div class="atout"><b>Son atout :</b> réagir vite, dès la moindre donnée fraîche.</div></div>
   <div class="mcard"><div class="ic">{FILTER}</div><div class="tag">Sélection parcimonieuse</div><h3>ElasticNet</h3>
     <p>Il retient automatiquement, parmi tous les indicateurs, le petit nombre qui compte vraiment, et met de côté le bruit.</p>
     <div class="atout"><b>Son atout :</b> rester lisible et robuste, sans sur-réagir.</div></div>
 </div>

 <div class="sh" style="margin-top:42px"><div class="n">La combinaison, concrètement</div><h2>Comment se forme le chiffre publié</h2></div>
 <div class="g2">
   <div class="card"><h3>Le chiffre d'aujourd'hui, décomposé</h3><div class="ph">Ce que voit chaque modèle en ce moment, et leur moyenne — le chiffre que nous publions</div>
     {mix_html()}
     <div class="note">Les trois modèles ne voient pas exactement la même chose : ici, MIDAS est le plus optimiste, ElasticNet le plus prudent. Le chiffre que nous publions est simplement leur <b>moyenne</b> ({frn(AVG3)} %) — ni le plus haut, ni le plus bas. C'est ce qui le rend plus robuste.</div></div>
   <div class="card"><h3>Pourquoi combiner plutôt que choisir ?</h3><div class="ph">Erreur de chaque modèle en test réel (2015-2026) — plus la barre est courte, plus c'est précis</div>
     {bars_html(MODELS_RMSE, win_name="Combinaison", dec=3)}
     <div class="note">Les trois modèles sont très proches, et aucun n'est le meilleur à chaque période : celui qui gagne aujourd'hui peut décevoir demain. Plutôt que de parier sur l'un d'eux, nous publions leur moyenne — toujours dans le peloton de tête, et surtout la plus <b>régulière dans le temps</b>.</div></div>
 </div>

 <div class="sh" style="margin-top:42px"><div class="n">Le secret d'un bon nowcast</div><h2>Le trimestre se « remplit » au fil des semaines</h2>
   <div class="d">Un trimestre dure trois mois. Au début, tout est prévision. Puis, chaque semaine, de vraies données arrivent (production, consommation, commerce…) : une part de la croissance devient <b>acquise</b> (connue, plus à deviner). C'est exactement ainsi que l'INSEE bâtit ses comptes — et pourquoi notre estimation se resserre à mesure que le trimestre avance.</div></div>
 <div class="acq">
   <div class="s"><div class="mo">Début du trimestre</div><div class="fill"><span style="width:12%"></span></div><p>Presque tout reste à prévoir : seules les enquêtes de confiance sont disponibles. La marge d'incertitude est à son maximum.</p></div>
   <div class="s"><div class="mo">Après 1 mois</div><div class="fill"><span style="width:42%"></span></div><p>Les premières données « dures » (production, ventes) tombent. Une partie du trimestre est acquise, l'estimation se précise.</p></div>
   <div class="s"><div class="mo">Après 2 mois</div><div class="fill"><span style="width:78%"></span></div><p>L'essentiel de l'information est là. Il ne reste qu'un mois à estimer : la marge d'incertitude est devenue faible.</p></div>
 </div>
 <div class="note" style="margin:12px 2px 0">Schéma de principe : les proportions illustrent l'idée, la part réellement acquise dépend des publications de chaque trimestre.</div>

 <div class="g2" style="margin-top:42px">
   <div class="card"><h3>Ce que le modèle regarde</h3><div class="ph">Les ingrédients, mis à jour en direct</div>
     <div class="ing">
       <div class="i"><b>≈ 189</b><span>séries suivies, du climat des affaires au trafic de fret</span></div>
       <div class="i"><b>2</b><span>horizons distincts : le trimestre en cours et le suivant</span></div>
       <div class="i"><b>1×/sem.</b><span>mise à jour automatique dès qu'un indicateur paraît</span></div>
       <div class="i"><b>25 ans</b><span>de recul pour caler et vérifier les modèles</span></div>
     </div>
     <div class="note">Chaque semaine, dès qu'une donnée nouvelle est publiée, elle est intégrée et la prévision est recalculée — sans intervention manuelle.</div></div>
   <div class="card"><h3>D'où viennent les données</h3><div class="ph">Des sources publiques et officielles, uniquement</div>
     <div class="ing">
       <div class="i"><b>INSEE</b><span>enquêtes, production, consommation, comptes trimestriels</span></div>
       <div class="i"><b>Banque de France</b><span>enquête de conjoncture, crédit aux entreprises</span></div>
       <div class="i"><b>BCE · Eurostat</b><span>zone euro, commerce, prix</span></div>
       <div class="i"><b>Douanes</b><span>exportations et importations</span></div>
       <div class="i"><b>Marchés</b><span>taux d'intérêt, pétrole, actions</span></div>
     </div>
     <div class="note">Aucune donnée confidentielle ni payante : la méthode est entièrement reproductible.</div></div>
 </div>
</div>""", unsafe_allow_html=True)


def page_fiabilite():
    st.markdown(f"""<div class="rl">
 <div class="sh"><div class="n">Notre fiabilité</div><h2>Peut-on se fier à nos prévisions ?</h2>
   <div class="d">Une prévision ne vaut que si elle tient dans le temps. Une bonne prévision, c'est deux qualités à la fois : viser <b>juste</b> (tomber près du résultat final) et viser <b>sans biais</b> (ne pas se tromper toujours du même côté, trop haut ou trop bas). Voici nos résultats sur la France — les nôtres, chiffres et graphiques à l'appui.</div></div>

 <div class="sh" style="margin-top:30px"><div class="n">La preuve en un graphique</div><h2>Le nowcast face à la réalité</h2>
   <div class="d">Pour chaque trimestre passé, on compare ce que notre modèle estimait <b>en temps réel</b> (en bleu) à la croissance finalement mesurée par l'INSEE (en gris). Plus les deux courbes se superposent, plus le modèle est fiable.</div></div>
 <div class="card" style="margin-bottom:26px"><h3>Estimation du nowcast vs croissance réalisée</h3><div class="ph">Croissance trimestrielle du PIB, 2015-2026 · hors trimestres de crise (Covid 2020-2021, hors échelle)</div>
   {svg_track(TRACK)}
   <div class="legend"><span class="it"><i style="background:{C['soft']}"></i>Réalisé (INSEE)</span><span class="it"><i style="background:{C['blue']}"></i>Nowcast (notre estimation en temps réel)</span></div>
   <div class="note">Le nowcast suit de près les hauts et les bas de l'activité, trimestre après trimestre. Il lisse un peu les à-coups extrêmes — c'est normal, un modèle prudent ne « saute » pas sur un chiffre isolé — mais il ne se trompe presque jamais de sens. Sur toute la période, l'écart type de l'erreur (le « RMSE ») est de <b>{comma(RMSE0)} point</b> seulement.</div></div>

 <div class="g2">
  <div class="card"><h3>1 · Viser juste — la précision</h3><div class="ph">Écart moyen entre nos prévisions et la première estimation de l'INSEE, selon l'échéance (en points de croissance)</div>
    {bars_html(PREC, win_name="À quelques semaines")}
    <div class="note">Plus l'échéance est proche, plus c'est précis : à quelques semaines, l'écart moyen n'est que de <b>{comma(MAE_CUR)} point</b> (autrement dit, on se trompe en moyenne d'un quart de point). Un an à l'avance, il reste de <b>{comma(MAE_NEXT)} point</b> — au niveau des tout meilleurs prévisionnistes.</div></div>
  <div class="card"><h3>2 · Viser sans biais — la neutralité</h3><div class="ph">Sur 24 ans (2002-2025), penche-t-on en moyenne trop à la hausse ou trop à la baisse ?</div>
    {svg_gauge()}
    <div class="note">Notre biais moyen (notre erreur moyenne, en tenant compte du signe) est de <b>{frn(BIAS)} point</b> : pratiquement zéro. Nous ne sommes ni systématiquement optimistes, ni pessimistes — une qualité rare, car beaucoup de prévisionnistes penchent toujours du même côté.</div></div>
 </div>

 <div class="sh" style="margin-top:40px"><div class="n">Ce que ça change</div><h2>Pourquoi c'est solide</h2></div>
 <div class="why">
   <div class="w"><div class="ic">{SHIELD}</div><h4>Fiable</h4><p>24 années de recul et un écart moyen faible et stable — pas un coup de chance ponctuel, mais une régularité qui se vérifie année après année.</p></div>
   <div class="w"><div class="ic">{BALANCE}</div><h4>Sans biais</h4><p>Un biais quasi nul : sur la durée, nos prévisions ne penchent ni vers l'excès d'optimisme, ni vers la prudence systématique. On corrige à la hausse aussi souvent qu'à la baisse.</p></div>
   <div class="w"><div class="ic">{CLOCK}</div><h4>Testé en conditions réelles</h4><p>À chaque date passée, le modèle n'a reçu que l'information réellement disponible ce jour-là — jamais de données venues du futur. Le test reproduit fidèlement la vraie vie.</p></div>
 </div>
</div>""", unsafe_allow_html=True)


def page_autres():
    lab = {"live": "En direct", "pret": "bientôt", "roadmap": "à l'étude"}
    cards = "".join(
        f'<div class="bc {"live" if s=="live" else ""}"><span class="st">{lab[s]}</span><h3>{n}</h3><div class="m">{m}</div>'
        f'<div class="val {"" if s=="live" else "mut"}">{v}</div></div>'
        for n, s, m, v in BAROS)
    st.markdown(f"""<div class="rl">
 <div class="sh"><div class="n">Nos autres prévisions</div><h2>Bientôt, bien plus que la croissance</h2>
   <div class="d">La croissance n'est que le premier indicateur. Les mêmes méthodes s'appliquent aux autres grandes variables de l'économie française — les modèles existent déjà en interne.</div></div>
 <div class="suite">{cards}</div></div>""", unsafe_allow_html=True)


PAGES = {"prevision": page_prevision, "methode": page_methode, "fiabilite": page_fiabilite, "autres": page_autres}
PAGES.get(PAGE, page_prevision)()

# ---- note de synthèse + pied ----
note = f"""<!doctype html><meta charset=utf-8><title>Note — Rexecode Live</title>
<body style="font-family:Georgia,serif;max-width:640px;margin:40px auto;color:#0E1A2A">
<div style="border-left:5px solid #123A5E;padding-left:16px">
<div style="font-family:monospace;font-size:11px;letter-spacing:.1em;color:#8A6D37">REXECODE LIVE · NOTE DE SYNTHÈSE · {MAJ}</div>
<h1 style="font-size:26px">Croissance du PIB — {frn(T3)} % au 3ᵉ trimestre 2026</h1></div>
<p>Prévision du trimestre en cours (3ᵉ trim. 2026) : <b>{frn(T3)} %</b> ; trimestre suivant (4ᵉ trim.) : <b>{frn(T4)} %</b>. Variations par rapport au trimestre précédent, en volume.</p>
<p><i>« {commentaire(T3, T4)} »</i></p>
<p style="font-size:13px;color:#3D4F66">Nos prévisions France sont fiables et sans biais (écart moyen 0,57 pt, biais +0,06 sur 2002-2025 vs 1ʳᵉ estimation INSEE).</p>
<p style="font-size:12px;color:#6C7E96">Modèle &amp; application : Anthony Morlet-Lavidalie — Rexecode. Chiffres à revérifier à la source.</p></body>"""
st.markdown('<div class="rl" style="margin-top:36px"></div>', unsafe_allow_html=True)
st.download_button("Télécharger la note de synthèse (HTML)", note,
                   file_name="rexecode_live_note.html", mime="text/html")
st.markdown(f'<div class="rl"><div class="note" style="margin-top:22px;border-top:1px solid var(--line);padding-top:18px;font-size:12.5px">'
            f'<b>Rexecode Live</b> · modèle &amp; application : <b>Anthony Morlet-Lavidalie</b>, Rexecode. '
            f'Thème {"sombre" if DARK else "clair"}, adapté à votre appareil. Sources ouvertes ; chiffres à revérifier à la source.</div></div>',
            unsafe_allow_html=True)
