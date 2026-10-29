"""Rexecode Live — nowcast du PIB de la France, version premium sur Streamlit.

Menu nommé par le contenu, lisible par tous les profils : Prévision de croissance ·
Notre méthode · Notre fiabilité · Nos autres prévisions. Thème clair/sombre qui suit
l'appareil. Pleine largeur adaptative. Graphiques en SVG sur mesure, construits sur les
vraies données du modèle. Commentaire économique automatisé à partir des chiffres.
Modèle & application : Anthony Morlet-Lavidalie — Rexecode.

Lancer :  .venv\\Scripts\\python.exe -m streamlit run rexlive\\app.py
"""
from __future__ import annotations
import json, math
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
ET = loadjson("etat.json", {})       # calendrier (pib_nowcast/calendrier.py) : trimestres et libellés du jour
MAJ = ET.get("maj", "octobre 2026")
LT, LTN = ET.get("lib_T", "3ᵉ trimestre 2026"), ET.get("lib_TN", "4ᵉ trimestre 2026")
LT_C, LTN_C = ET.get("court_T", "3ᵉ trim."), ET.get("court_TN", "4ᵉ trim. 2026")
LT_MIN = LT.split(" ")[0] + " trimestre"; LTN_MIN = LTN.split(" ")[0] + " trimestre"
T3, T4 = f3.get("COMBI", 0.204), f4.get("COMBI", 0.261)
RMSE0, RMSE1 = r0.get("COMBI", 0.215), r1.get("COMBI", 0.226)
# croissance potentielle (Commission, AMECO) : ancre du niveau de la prévision T+1
POT = hs.get("potentiel", {})
ANCRE4 = bool(POT.get("ancre_T4")) and isinstance(POT.get("T4"), (int, float))
POT4 = POT.get("T4", 0.27)
POT4_AN = ((1 + POT4 / 100) ** 4 - 1) * 100
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
MODELS_RMSE = [("Forêt aléatoire", _rm("RandomForest", 0.211)), ("ElasticNet", _rm("ElasticNet", 0.209)),
               ("MIDAS", _rm("MIDAS", 0.193)), ("Acquis durs", _rm("MIH", 0.174)),
               ("Combinaison", _rm("COMBI", RMSE0))]
PERIODE = hs.get("rmse_periode", "2010-2026")
MOM = hs.get("metriques_moments", {})
COEFS = hs.get("mih_coefs", [])
TRAJ = loadjson("trajectoire.json", {})
# track record vs 1ère estimation INSEE (2002-2025)
BIAS, MAE_CUR, MAE_NEXT = 0.06, 0.24, 0.57
PREC = [("À quelques semaines", MAE_CUR, "trimestre en cours"), ("Un an à l'avance", MAE_NEXT, "année suivante")]

# contributions signées par famille (contributions.json)
CONTRIB = loadjson("contributions.json", {})
ACQ = CONTRIB.get("acquis", {})
ACQV, ACQN = ACQ.get("valeurs", {}), ACQ.get("mois", {})
MOIS_T3 = ET.get("mois_T", ["juillet", "août", "septembre"])
MOIS_T3_AB = ET.get("mois_T_ab", ["juil.", "août", "sept."])
MOIS_AV, MOIS_AV_AB = ET.get("mois_avant", "juin"), ET.get("mois_avant_ab", "juin")


def _mois_txt(n):
    return "effet de report seul" if n <= 0 else (MOIS_T3[0] if n == 1 else f"{MOIS_T3[0]}-{MOIS_T3[n-1]}")

# trajectoire réelle du nowcast (nowcast_evolution.json)
evo = loadjson("nowcast_evolution.json", {})
rstage = evo.get("rmse_stage", {})
q3 = evo.get("paths", {}).get(ET.get("T", "2026Q3"), {})


def _q3(k, d):
    v = q3.get(k)
    return v if isinstance(v, (int, float)) else d


# T3 : quatre points mensuels (valeur, ±1 écart-type) ; le point final = le chiffre publié
# incertitude : écarts-types par étape d'information, backtest temps réel 2008-2026
INC = loadjson("incertitude.json", {})
SIG = {**rstage, **INC.get("sigma_etapes", {})}
SIG3 = INC.get("sigma_now", {}).get("T3", SIG.get("fin M3", 0.215))
SIG4 = INC.get("sigma_now", {}).get("T4", RMSE1)
# 4 positions : fin du mois précédent, fin M1, M2, M3 ; seules les étapes déjà passées sont tracées,
# le chiffre du jour se place au mois en cours (au 3e mois une fois le trimestre terminé).
_STG = [("avant T", MOIS_AV_AB), ("fin M1", MOIS_T3_AB[0]), ("fin M2", MOIS_T3_AB[1]), ("fin M3", MOIS_T3_AB[2])]
try:
    _d, _t = ET.get("date"), ET.get("T")
    _off = (int(_d[:4]) * 12 + int(_d[5:7])) - (int(_t[:4]) * 12 + (int(_t[-1]) - 1) * 3 + 1)
    SLOT = min(max(_off, 0), 2) + 1
except Exception:
    SLOT = 3
T3PTS = [(lab, (q3.get(k) if isinstance(q3.get(k), (int, float)) and i < SLOT else None), SIG.get(k, SIG3)) for i, (k, lab) in enumerate(_STG)]
T3PTS[SLOT] = (_STG[SLOT][1], T3, SIG3)
T4PT = (T4, SIG4)  # T4 : estimation actuelle, ±1 écart-type
pneg = lambda v, s: 0.5 * (1 + math.erf(-v / (s * math.sqrt(2))))   # P(croissance < 0), loi normale
PNEG3, PNEG4 = pneg(T3, SIG3), pneg(T4, SIG4)
BIAIS = INC.get("biais_glissant", {})

# décomposition du chiffre publié (RexNow v2) : ½ trio d'apprentissage + ½ modèle d'acquis durs
MODELF = [("Forêt aléatoire", f3.get("RandomForest", 0.278)),
          ("ElasticNet", f3.get("ElasticNet", 0.266)),
          ("MIDAS", f3.get("MIDAS", 0.254))]
AVG3 = round(f3.get("TRIO", sum(v for _, v in MODELF) / len(MODELF)), 3)
MIHV = f3.get("MIH", AVG3)

# backtest : nowcast (combi) vs réalisé (INSEE), hors trimestres Covid 2020-2021
tv2 = loadjson("chart_v2.json", [])
TRACK = [(x["t"], x["a"], x["combi"], x.get("mih")) for x in tv2
         if isinstance(x.get("a"), (int, float)) and isinstance(x.get("combi"), (int, float))
         and x["t"][:4] not in ("2020", "2021")]

BAROS = [("Croissance du PIB", "live", "trimestre en cours", frn(T3) + " %"),
         ("Inflation", "pret", "hausse des prix (IPC)", "à venir"),
         ("Production industrielle", "pret", "industrie manufacturière", "à venir"),
         ("Émissions de CO₂", "roadmap", "empreinte carbone", "à venir")]


# ---------------- commentaire économique automatisé ----------------
def commentaire(t3, t4):
    ot, otn, od = ET.get("ord_T", "troisième"), ET.get("ord_TN", "quatrième"), ET.get("ord_dernier", "deuxième")
    pp = ET.get("pib_dernier", 0.16)
    prec = ("en recul" if pp < -0.05 else "quasi stable" if pp < 0.1 else "en hausse modérée" if pp < 0.35 else "en nette hausse") + f" ({frn(pp)} %)"
    if t3 <= 0:
        verbe = "reculerait"
    elif pp < 0.1:
        verbe = "renouerait avec la croissance"
    else:
        verbe = "continuerait de progresser"
    amp = "un rythme faible" if abs(t3) < 0.15 else ("un rythme modéré" if abs(t3) < 0.30 else "un rythme soutenu")
    d = t4 - t3
    if d > 0.05:
        suite = f"Au {otn} trimestre ({frn(t4)} %), la croissance se prolongerait, à peine plus soutenue"
    elif d < -0.05:
        suite = f"Au {otn} trimestre ({frn(t4)} %), le rythme fléchirait légèrement"
    else:
        suite = f"Au {otn} trimestre ({frn(t4)} %), le rythme resterait globalement inchangé"
    dur = ""
    pr, co = ACQV.get("sv_PROD"), ACQV.get("sv_CONSO")
    if isinstance(pr, (int, float)) and isinstance(co, (int, float)):
        np_, nc = ACQN.get("IND", 0), ACQN.get("CONSO", 0)
        if (pr >= 0) == (co >= 0):
            dur = (f" Les données dures déjà publiées vont dans le même sens : acquis de {frn(pr, 1)} % pour la production "
                   f"({_mois_txt(np_)}) et de {frn(co, 1)} % pour la consommation de biens ({_mois_txt(nc)}).")
        else:
            dur = (f" Les données dures déjà publiées sont contrastées : la consommation de biens affiche un acquis de "
                   f"{frn(co, 1)} % ({_mois_txt(nc)}), mais la production {'recule' if pr < 0 else 'progresse'} "
                   f"({frn(pr, 1)} % d'acquis, {_mois_txt(np_)}).")
    return (f"Après un {od} trimestre {prec}, l'activité {verbe} au {ot} trimestre ({frn(t3)} %), "
            f"soit {amp}.{dur} {suite}.")


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
.rl .verdict .qrisk{{font-size:12.5px;color:{C['vkick']}!important;margin-top:2px}}
.rl .verdict .qrisk b{{color:{C['vtxt']}!important;font-weight:600}}
.rl svg.bias{{width:100%;height:auto;aspect-ratio:460/190}}
.rl .stat-pill{{display:inline-block;align-self:flex-start;width:fit-content;font-size:12px;font-weight:600;padding:3px 10px;border-radius:20px;margin-bottom:10px}}
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
.rl .g4{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}}@media(max-width:1100px){{.rl .g4{{grid-template-columns:1fr 1fr}}}}@media(max-width:640px){{.rl .g4{{grid-template-columns:1fr}}}}
.rl .mix .r.sub{{font-weight:600}}.rl .mix .r.sub .bar span{{background:color-mix(in srgb,var(--teal) 60%,var(--surf))}}
.rl .mix .r.sep{{padding-top:11px;border-top:1px dashed var(--line)}}
.rl .mix .r{{display:grid;grid-template-columns:minmax(120px,178px) 1fr 48px;gap:14px;align-items:center;font-size:13.5px;color:var(--ink)}}
.rl .mix .bar{{height:14px;border-radius:5px;background:var(--surf2);overflow:hidden}}.rl .mix .bar span{{display:block;height:100%;border-radius:5px;background:color-mix(in srgb,var(--blue) 45%,var(--surf))}}
.rl .mix .v{{font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--soft);text-align:right}}
.rl .mix .r.avg{{font-weight:700;padding-top:11px;border-top:1px solid var(--line)}}.rl .mix .r.avg .bar span{{background:var(--navy)}}
:root:not([data-theme="light"]) .rl .mix .r.avg .bar span{{background:var(--blue)}}
.rl .mix .r.avg .v{{color:var(--ink)}}
/* deux regards */
.rl .rg{{display:grid;grid-template-columns:1fr 54px 1fr 40px 1fr;gap:12px;align-items:stretch}}@media(max-width:900px){{.rl .rg{{grid-template-columns:1fr}}}}
.rl .rb{{border-radius:14px;padding:16px 18px;border:1px solid var(--line);background:var(--surf2);display:flex;flex-direction:column;gap:5px}}
.rl .rb .rt{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--soft)}}
.rl .rb.sig .rt{{color:var(--navy)}} :root:not([data-theme="light"]) .rl .rb.sig .rt{{color:var(--blue)}} .rl .rb.fai .rt{{color:var(--brass)}}
.rl .rb.pub{{background:var(--surf);border:2px solid var(--blue)}} .rl .rb.pub .rt{{color:var(--blue)}}
.rl .rb .rv{{font-family:"Fraunces",serif;font-size:34px;font-weight:600;color:var(--ink);line-height:1.1;font-variant-numeric:tabular-nums}} .rl .rb .rv span{{font-size:17px}}
.rl .rb p{{margin:0;font-size:13px;color:var(--soft);line-height:1.5}}
.rl .rop{{align-self:center;font-family:"IBM Plex Mono",monospace;font-size:15px;color:var(--faint);text-align:center;white-space:nowrap}}
/* fil du trimestre */
.rl .moves{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:16px}}
.rl .mv{{background:var(--surf2);border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:7px}}
.rl .mv-h{{display:flex;justify-content:space-between;align-items:baseline;gap:8px}} .rl .mv-l{{font-weight:600;font-size:14px;color:var(--ink)}}
.rl .mv-s{{font-family:"IBM Plex Mono",monospace;font-size:10px;color:var(--faint);text-transform:uppercase;letter-spacing:.05em}}
.rl .mv-v{{font-family:"IBM Plex Mono",monospace;font-size:22px;font-weight:600;color:var(--ink);display:flex;align-items:baseline;gap:10px;font-variant-numeric:tabular-nums}} .rl .mv-v > span:first-child{{font-size:13px}}
.rl .mv-d{{font-size:12px;padding:2px 8px;border-radius:10px;background:var(--surf);border:1px solid var(--line);color:var(--soft)}}
.rl .mv .up{{color:var(--teal)}} .rl .mv .dn{{color:var(--orange)}} .rl .mv-why{{font-size:12.5px;color:var(--soft);line-height:1.45}} .rl .mv-why span{{font-weight:600}}
.rl .mv-new{{margin-top:auto;padding-top:8px;border-top:1px dashed var(--line)}} .rl .mv-new > span{{font-family:"IBM Plex Mono",monospace;font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--faint)}}
.rl .mv-new ul{{margin:4px 0 0;padding-left:16px;font-size:12px;color:var(--soft);line-height:1.45}}
/* deux regards — page méthode */
.rl .tagr{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;margin-bottom:4px}}
.rl .ml{{display:grid;gap:12px;margin-top:6px}} .rl .ml .r{{display:grid;grid-template-columns:30px 1fr;gap:12px;align-items:start}}
.rl .ml .r b{{display:block;font-size:14px;color:var(--ink)}} .rl .ml .r span{{font-size:13px;color:var(--soft);line-height:1.5}}
.rl .steps{{margin:6px 0 0;padding:0;list-style:none;display:grid;gap:12px;counter-reset:st}}
.rl .steps li{{display:grid;grid-template-columns:30px 1fr;gap:12px;font-size:13px;color:var(--soft);line-height:1.5;counter-increment:st}}
.rl .steps li::before{{content:counter(st);width:26px;height:26px;border-radius:50%;background:color-mix(in srgb,var(--brass) 18%,transparent);color:var(--brass);font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:600;display:flex;align-items:center;justify-content:center}}
.rl .steps li b{{color:var(--ink)}}
/* acquis des données dures */
.rl .hard{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:4px}}@media(max-width:1100px){{.rl .hard{{grid-template-columns:1fr 1fr 1fr}}}}@media(max-width:640px){{.rl .hard{{grid-template-columns:1fr 1fr}}}}
.rl .hard .hd{{background:var(--surf2);border:1px solid var(--line);border-radius:12px;padding:14px 16px;display:flex;flex-direction:column}}
.rl .hard .hl{{font-weight:600;font-size:14px;color:var(--ink)}} .rl .hard .hs{{font-size:11.5px;color:var(--faint);line-height:1.35;margin-top:2px;min-height:46px}}
.rl .hard .hv{{font-family:"IBM Plex Mono",monospace;font-weight:600;font-size:26px;margin:8px 0 6px;font-variant-numeric:tabular-nums}} .rl .hard .hv span{{font-size:14px}}
.rl .hard .hx{{font-size:11.5px;color:var(--soft);line-height:1.35;margin:-2px 0 8px}}
.rl .hard .hm{{margin-top:auto;white-space:nowrap;font-family:"IBM Plex Mono",monospace;font-size:10.5px;color:var(--soft);display:flex;align-items:center;gap:8px}}
.rl .hard .seg{{display:inline-flex;gap:3px}} .rl .hard .seg i{{width:14px;height:7px;border-radius:2px;background:var(--line)}} .rl .hard .seg i.on{{background:var(--blue)}}
/* acquis (timeline) */
.rl .acq{{display:flex;gap:10px;flex-wrap:wrap;margin-top:2px}}
.rl .acq .s{{flex:1 1 150px;background:var(--surf2);border:1px solid var(--line);border-radius:12px;padding:14px 16px}}
.rl .acq .s .mo{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--brass)}}
.rl .acq .s .fill{{height:8px;border-radius:5px;background:var(--line);overflow:hidden;margin:9px 0}}.rl .acq .s .fill span{{display:block;height:100%;border-radius:5px;background:var(--blue)}}
.rl .acq .s p{{margin:0;font-size:12.5px;color:var(--soft);line-height:1.45}}
.rl svg{{display:block}}
.rl svg.fan{{width:100%;height:auto;aspect-ratio:520/258}} .rl svg.gauge{{width:100%;height:auto;aspect-ratio:480/168}} .rl svg.track{{width:100%;height:auto;aspect-ratio:900/300}} .rl svg.casc{{width:100%;height:auto;aspect-ratio:900/340}} .rl svg.mom{{width:100%;height:auto;aspect-ratio:520/250}} .rl svg.coef{{width:100%;height:auto;aspect-ratio:520/276}} .rl svg.ic{{width:24px;height:24px}}
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
    s.append(f'<text x="{(X(0)+X(3))/2:.1f}" y="{mT-16}" text-anchor="middle" font-family="IBM Plex Mono" font-size="11" fill="{bl}" font-weight="600">{LT}</text>')
    s.append(f'<text x="{W-mR+8:.1f}" y="{mT-16}" text-anchor="end" font-family="IBM Plex Mono" font-size="11" fill="{org}" font-weight="600">{LTN_C}</text>')
    pts = [(i, v, r) for i, (_, v, r) in enumerate(T3PTS) if isinstance(v, (int, float))]
    # bande (±1 écart-type) et ligne, sur les étapes déjà passées
    if len(pts) > 1:
        up = " ".join(f"{X(i):.1f},{Y(v+r):.1f}" for i, v, r in pts)
        lo = " ".join(f"{X(i):.1f},{Y(v-r):.1f}" for i, v, r in reversed(pts))
        s.append(f'<polygon points="{up} {lo}" fill="rgba({C["ic"]},0.14)"/>')
        s.append(f'<polyline points="{" ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v, _ in pts)}" fill="none" stroke="{bl}" stroke-width="2.8"/>')
    else:
        i, v, r = pts[0]
        s.append(f'<rect x="{X(i)-11:.1f}" y="{Y(v+r):.1f}" width="22" height="{Y(v-r)-Y(v+r):.1f}" rx="6" fill="rgba({C["ic"]},0.14)"/>')
    for i, (mois, v, _) in enumerate(T3PTS):
        s.append(f'<text x="{X(i):.1f}" y="{H-24}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10.5" fill="{C["faint"]}">{mois}</text>')
        if isinstance(v, (int, float)):
            last = (i == SLOT)
            s.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="{5.5 if last else 4}" fill="{bl if last else C["surf"]}" stroke="{bl}" stroke-width="2.4"/>')
    # valeur sur le point du jour
    xl, yl = X(SLOT), Y(T3PTS[SLOT][1])
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


def svg_bridge(start_lab, start, steps, end_lab, end, cls="casc"):
    """Pont (cascade) générique : niveau de départ, une marche par bloc, niveau d'arrivée."""
    items = [(start_lab, "start", start, None, None, start)]
    r = start
    for name, v in steps:
        items.append((_wrap2(name), "delta", v, r, r + v, r + v))
        r += v
    items.append((end_lab, "end", end, None, None, end))
    levels = [start, end] + [x for _, _, _, bf, af, _ in items if bf is not None for x in (bf, af)]
    lo, hi = min(levels), max(levels)
    span = max(hi - lo, 0.06)
    yMin, yMax = lo - 0.35 * span, hi + 0.2 * span
    W, H, mL, mR, mT, mB = 900, 340, 54, 18, 30, 58
    n = len(items)
    band = (W - mL - mR) / n
    cx = lambda i: mL + band * (i + 0.5)
    bw = min(band * 0.52, 66)
    Y = lambda v: mT + (H - mB - mT) * (1 - (v - yMin) / (yMax - yMin))
    gray, bl, tl, org = C["faint"], C["blue"], C["teal"], C["orange"]
    s = [f'<svg class="{cls}" viewBox="0 0 {W} {H}">']
    step = 0.02 if span < 0.16 else 0.05
    g = (int(yMin / step) + 1) * step
    while g < yMax:
        yy = Y(g)
        s.append(f'<line x1="{mL}" y1="{yy:.1f}" x2="{W-mR}" y2="{yy:.1f}" stroke="var(--line)"/>')
        s.append(f'<text x="{mL-9}" y="{yy+4:.1f}" text-anchor="end" font-family="IBM Plex Mono" font-size="10.5" fill="{gray}">{frn(g,2)}</text>')
        g += step
    for i in range(n - 1):
        yc = Y(items[i][5])
        s.append(f'<line x1="{cx(i)+bw/2:.1f}" y1="{yc:.1f}" x2="{cx(i+1)-bw/2:.1f}" y2="{yc:.1f}" stroke="{gray}" stroke-dasharray="3 3" opacity="0.7"/>')
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
            s.append(f'<rect x="{x:.1f}" y="{top:.1f}" width="{bw:.1f}" height="{max(bot - top, 3):.1f}" rx="3" fill="{col}"/>')
            lv = frn(val) if abs(val) >= 0.005 else "≈ 0"
            s.append(f'<text x="{cx(i):.1f}" y="{top-8:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-size="11.5" font-weight="600" fill="{col}">{lv}</text>')
        s.append(f'<text x="{cx(i):.1f}" y="{H-mB+18:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10.5" fill="{C["soft"]}">{lab[0]}'
                 f'<tspan x="{cx(i):.1f}" dy="12">{lab[1]}</tspan></text>')
    s.append("</svg>")
    return "".join(s)


def svg_cascade():
    """Cascade du chiffre publié : du trimestre moyen au nowcast, un pas par grand bloc."""
    blocks = CONTRIB.get("blocks", [])
    if not blocks:
        return ""
    base = CONTRIB.get("base", 0.31)
    return svg_bridge(["Trimestre", "moyen"], base, blocks, ["Nowcast", LT_C], CONTRIB.get("total", base))


def svg_moves():
    """Ce qui a fait bouger la prévision depuis la fin du trimestre précédent."""
    tot, et = TRAJ.get("total"), TRAJ.get("etapes", [])
    if not tot or len(et) < 2:
        return ""
    steps = [[k, v] for k, v in tot["blocs"].items()]
    if abs(tot.get("modele", 0)) >= 0.005:
        steps.append(["Ajustement du modèle", tot["modele"]])
    return svg_bridge(["Prévision", et[0]["label"]], tot["depart"], steps, ["Prévision", "aujourd'hui"], tot["arrivee"])


def moves_html():
    """Fil du trimestre : à chaque étape, le chiffre, sa variation, ce qui l'explique, ce qui est paru."""
    et = TRAJ.get("etapes", [])
    if len(et) < 2:
        return ""
    out = []
    for i, e in enumerate(et):
        if i == 0:
            body = f'<div class="mv-why">point de départ : le trimestre n\'a pas commencé, seules les données de {MOIS_AV} et d\'avant sont connues</div>'
            dl = ""
        else:
            d = e.get("delta", 0)
            movers = sorted(e.get("delta_blocks", {}).items(), key=lambda kv: -abs(kv[1]))
            movers = [(k, v) for k, v in movers if abs(v) >= 0.005][:2]
            why = " · ".join(f'<span class="{"up" if v > 0 else "dn"}">{k[0].lower() + k[1:]} {frn(v)}</span>' for k, v in movers) or "aucun facteur marquant"
            nw = "".join(f"<li>{x}</li>" for x in e.get("news", []))
            body = f'<div class="mv-why">{why}</div>' + (f'<div class="mv-new"><span>Données parues</span><ul>{nw}</ul></div>' if nw else "")
            dl = f'<span class="mv-d {"up" if d >= 0.005 else ("dn" if d <= -0.005 else "")}">{frn(d) if abs(d) >= 0.005 else "≈ 0"} pt</span>'
        out.append(f'<div class="mv"><div class="mv-h"><span class="mv-l">{e["label"]}</span><span class="mv-s">{e["sub"]}</span></div>'
                   f'<div class="mv-v">{frn(e["pred"])}<span> %</span>{dl}</div>{body}</div>')
    return '<div class="moves">' + "".join(out) + "</div>"


def regards_html():
    """Deux regards, un seul chiffre : signaux (3 modèles statistiques) + faits (acquis durs)."""
    sig, fai = AVG3, MIHV
    gap = sig - fai
    if abs(gap) < 0.05:
        lec = "Les deux regards <b>concordent</b> : les données déjà mesurées confirment ce qu'annoncent les enquêtes."
    elif gap > 0:
        lec = (f"Les faits mesurés sont <b>moins bons</b> que ce qu'annoncent les signaux (écart de {comma(gap)} pt) : "
               "les enquêtes sont plus optimistes que la production et le commerce déjà publiés. Le chiffre publié se place entre les deux.")
    else:
        lec = (f"Les faits mesurés sont <b>meilleurs</b> que ce qu'annoncent les signaux (écart de {comma(-gap)} pt) : "
               "l'activité réelle résiste mieux que le moral des acteurs. Le chiffre publié se place entre les deux.")
    return (f'<div class="rg">'
            f'<div class="rb sig"><div class="rt">Regard 1 · les signaux</div><div class="rv">{frn(sig)}<span> %</span></div>'
            f'<p>Ce que disent les <b>enquêtes, les marchés et 189 indicateurs</b>, lus par trois modèles statistiques.</p></div>'
            f'<div class="rop">½ + ½</div>'
            f'<div class="rb fai"><div class="rt">Regard 2 · les faits</div><div class="rv">{frn(fai)}<span> %</span></div>'
            f'<p>Ce qui est <b>déjà mesuré</b> dans le trimestre : production, consommation, commerce extérieur — comme l\'INSEE.</p></div>'
            f'<div class="rop">=</div>'
            f'<div class="rb pub"><div class="rt">Chiffre publié</div><div class="rv">{frn(T3)}<span> %</span></div>'
            f'<p>La moitié de chaque regard : quand l\'un se trompe, l\'autre corrige.</p></div>'
            f'</div><div class="note">{lec}</div>')


def svg_moments():
    """Erreur (RMSE) selon le moment du trimestre : signaux / faits / publié."""
    cuts = [("C1", "fin du 1er mois"), ("C2", "fin du 2e mois"), ("C3", "fin du 3e mois"), ("C4", "1re estim. INSEE")]
    keys = [("trio", C["faint"]), ("mih", C["brass"]), ("combi", C["blue"])]
    if not all(c in MOM for c, _ in cuts):
        return ""
    W, H, mL, mR, mT, mB = 520, 250, 44, 10, 18, 40
    vmax = max(MOM[c][k]["rmse"] for c, _ in cuts for k, _ in keys if k in MOM[c]) * 1.12
    Y = lambda v: mT + (H - mT - mB) * (1 - v / vmax)
    band = (W - mL - mR) / len(cuts); bw = min(band / 4.2, 22)
    s = [f'<svg class="mom" viewBox="0 0 {W} {H}">']
    for g in (0.05, 0.10, 0.15, 0.20, 0.25):
        if g < vmax:
            s.append(f'<line x1="{mL}" y1="{Y(g):.1f}" x2="{W-mR}" y2="{Y(g):.1f}" stroke="var(--line)"/>'
                     f'<text x="{mL-7}" y="{Y(g)+4:.1f}" text-anchor="end" font-family="IBM Plex Mono" font-size="10.5" fill="{C["faint"]}">{comma(g)}</text>')
    for i, (c, lab) in enumerate(cuts):
        x0 = mL + band * i + (band - 3 * bw - 8) / 2
        for j, (k, col) in enumerate(keys):
            v = MOM[c].get(k, {}).get("rmse")
            if v is None:
                continue
            x = x0 + j * (bw + 4)
            s.append(f'<rect x="{x:.1f}" y="{Y(v):.1f}" width="{bw:.1f}" height="{Y(0)-Y(v):.1f}" rx="3" fill="{col}"/>')
            if k == "combi":
                s.append(f'<text x="{x+bw/2:.1f}" y="{Y(v)-5:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10.5" font-weight="600" fill="{C["blue"]}">{comma(v)}</text>')
        s.append(f'<text x="{mL + band*(i+0.5):.1f}" y="{H-mB+18:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10.5" fill="{C["soft"]}">{lab}</text>')
    s.append("</svg>")
    return "".join(s)


def svg_coefs():
    """Ce qui pèse dans le regard « faits » : coefficients standardisés ± 1 écart-type."""
    if not COEFS:
        return ""
    W, rowh, mL, mR, mT = 520, 30, 250, 18, 10
    H = mT + rowh * len(COEFS) + 26
    lim = max(abs(c["coef"]) + c["sd"] for c in COEFS) * 1.1
    X = lambda v: mL + (W - mL - mR) * (v + lim) / (2 * lim)
    s = [f'<svg class="coef" viewBox="0 0 {W} {H}" data-h="{H}">']
    s.append(f'<line x1="{X(0):.1f}" y1="{mT}" x2="{X(0):.1f}" y2="{H-24}" stroke="{C["soft"]}" stroke-width="1"/>')
    for i, c in enumerate(COEFS):
        yc = mT + rowh * i + rowh / 2
        col = C["brass"] if c["dur"] else (C["faint"] if c["coef"] < 0 else C["navy"])
        x0, x1 = sorted((X(0), X(c["coef"])))
        nom = c["var"].replace("Enquête : ", "")
        nom = nom[0].upper() + nom[1:]
        s.append(f'<text x="{mL-10}" y="{yc+4:.1f}" text-anchor="end" font-size="11.5" fill="{C["ink"]}">{nom}</text>')
        s.append(f'<rect x="{x0:.1f}" y="{yc-8:.1f}" width="{max(x1-x0,2):.1f}" height="16" rx="3" fill="{col}"/>')
        s.append(f'<line x1="{X(c["coef"]-c["sd"]):.1f}" y1="{yc:.1f}" x2="{X(c["coef"]+c["sd"]):.1f}" y2="{yc:.1f}" stroke="{C["ink"]}" stroke-width="1.2" opacity="0.55"/>')
    s.append("</svg>")
    return "".join(s)


def hard_html():
    """Acquis des données dures du 3e trimestre : valeur complétée par les enquêtes (utilisée
    par le modèle) + acquis INSEE « par report » + mois déjà connus (sur 3)."""
    def det():
        parts = [(n, ACQV.get(k)) for n, k in (("industrie", "sv_IND"), ("services", "sv_SERV"), ("construction", "sv_IPI_F"))]
        return "dont " + " · ".join(f"{n} {frn(v, 1)} %" for n, v in parts if isinstance(v, (int, float)))
    rows = [("Production", "industrie par branche, construction, services (IPS) — pondérés en valeur ajoutée", "sv_PROD", "acq_PROD", "IND", det()),
            ("Consommation de biens", "dépenses des ménages en biens, en volume (INSEE)", "sv_CONSO", "acq_CONSO", "CONSO", ""),
            ("Exportations", "biens, en volume (Douanes déflatées par les prix INSEE)", "sv_X_MIX", "acq_X_MIX", "X", ""),
            ("Importations", "biens, en volume (Douanes déflatées par les prix INSEE)", "sv_M_MIX", "acq_M_MIX", "M", ""),
            ("Travaux publics", "travaux réalisés (FNTP) — investissement en génie civil", "TP", None, "TP", "")]
    out = []
    for lab, sub, k, kr, km, extra in rows:
        v, n = ACQV.get(k), ACQN.get(km, 0)
        if not isinstance(v, (int, float)):
            continue
        vr = ACQV.get(kr) if kr else None
        rep = f'<div class="hx">report INSEE (mois manquants = dernier connu) : {frn(vr, 1)} %</div>' if isinstance(vr, (int, float)) else ''
        col = "var(--teal)" if v > 0.05 else ("var(--orange)" if v < -0.05 else "var(--soft)")
        seg = "".join(f'<i class="{"on" if j < n else ""}" title="{MOIS_T3[j]}"></i>' for j in range(3))
        out.append(f'<div class="hd"><div class="hl">{lab}</div><div class="hs">{sub}</div>'
                   f'<div class="hv" style="color:{col}">{frn(v, 1)}<span> %</span></div>'
                   + (f'<div class="hx">{extra}</div>' if extra else '') + rep
                   + f'<div class="hm"><span class="seg">{seg}</span>{n}/3 mois · {["report seul", MOIS_T3_AB[0], f"{MOIS_T3_AB[0]}-{MOIS_T3_AB[1]}", f"{MOIS_T3_AB[0]}-{MOIS_T3_AB[2]}"][max(0, min(n, 3))]}</div></div>')
    return '<div class="hard">' + "".join(out) + '</div>' if out else ""


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


def _trim(q):
    return f"{'1er' if q[-1] == '1' else q[-1] + 'ᵉ'} trim. {q[:4]}"


def svg_bias(b):
    """Biais glissant (moyenne des erreurs prévu − observé sur N trimestres) et zone normale."""
    ser = b.get("serie", [])
    if len(ser) < 3:
        return ""
    W, H, mL, mR, mT, mB = 460, 190, 44, 12, 14, 26
    n, thr = len(ser), b["seuil"]
    vals = [p["b"] for p in ser]
    lim = max(thr * 1.6, max(abs(v) for v in vals) * 1.15)
    X = lambda i: mL + (W - mL - mR) * i / (n - 1)
    Y = lambda v: mT + (H - mT - mB) * (1 - (v + lim) / (2 * lim))
    s = [f'<svg class="bias" viewBox="0 0 {W} {H}">']
    s.append(f'<rect x="{mL}" y="{Y(thr):.1f}" width="{W-mL-mR}" height="{Y(-thr)-Y(thr):.1f}" '
             f'fill="color-mix(in srgb,{C["teal"]} 13%,transparent)"/>')
    for v, lab, dash in ((thr, frn(thr), "4 3"), (0.0, "0", "0"), (-thr, frn(-thr), "4 3")):
        s.append(f'<line x1="{mL}" y1="{Y(v):.1f}" x2="{W-mR}" y2="{Y(v):.1f}" stroke="{C["faint"]}" '
                 f'stroke-width="1" stroke-dasharray="{dash}" opacity="0.8"/>')
        s.append(f'<text x="{mL-6}" y="{Y(v)+4:.1f}" text-anchor="end" font-family="IBM Plex Mono" '
                 f'font-size="10" fill="{C["faint"]}">{lab}</text>')
    s.append(f'<polyline points="{" ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))}" '
             f'fill="none" stroke="{C["blue"]}" stroke-width="2"/>')
    for i, v in enumerate(vals):
        if abs(v) > thr:
            s.append(f'<circle cx="{X(i):.1f}" cy="{Y(v):.1f}" r="3" fill="{C["orange"]}"/>')
    lc = C["orange"] if abs(vals[-1]) > thr else C["blue"]
    s.append(f'<circle cx="{X(n-1):.1f}" cy="{Y(vals[-1]):.1f}" r="4.5" fill="{lc}" stroke="{C["surf"]}" stroke-width="2"/>')
    for i, p in enumerate(ser):
        if p["t"].endswith("Q1") and int(p["t"][:4]) % 2 == 0:
            s.append(f'<text x="{X(i):.1f}" y="{H-8}" text-anchor="middle" font-family="IBM Plex Mono" '
                     f'font-size="10" fill="{C["faint"]}">{p["t"][:4]}</text>')
    s.append("</svg>")
    return "".join(s)


def bias_card(h):
    b = BIAIS.get(h)
    if not b:
        return ""
    alerte = b["alerte"]
    sens = "surestime" if b["actuel"] > 0 else "sous-estime"
    pill = (f'<span class="stat-pill" style="background:{C["orange"]};color:#fff">Alerte : le modèle {sens} durablement</span>'
            if alerte else f'<span class="stat-pill" style="background:{C["teal"]};color:#fff">Pas de dérive</span>')
    titre = "Trimestre en cours" if h == "h0" else "Trimestre suivant"
    return (f'<div class="card"><h3>{titre}</h3>'
            f'<div class="ph">Erreur moyenne sur les {b["fenetre"]} derniers trimestres connus (prévu − observé), en points</div>'
            f'{pill}{svg_bias(b)}'
            f'<div class="note">Jusqu\'au {_trim(b["dernier_trim"])} : <b>{frn(b["actuel"])} point</b>, pour une zone normale de '
            f'±{comma(b["seuil"])}. Au-delà, l\'écart n\'est plus dû au hasard.</div></div>')


def svg_track(pts):
    """Backtest : nowcast (combi) vs réalisé (INSEE), par trimestre, hors Covid."""
    if len(pts) < 4:
        return ""
    W, H, mL, mR, mT, mB = 900, 300, 46, 18, 30, 42
    n = len(pts)
    iw, ih = W - mL - mR, H - mT - mB
    vals = [p[1] for p in pts] + [p[2] for p in pts] + [p[3] for p in pts if isinstance(p[3], (int, float))]
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
    for idx, col, w, dash in ((1, C["soft"], 2.4, ""), (3, C["brass"], 1.8, "5 4"), (2, C["blue"], 2.6, "")):
        for seg in segs:
            sg = [i for i in seg if isinstance(pts[i][idx], (int, float))]
            if len(sg) > 1:
                s.append(f'<polyline points="{" ".join(f"{X(i):.1f},{Y(pts[i][idx]):.1f}" for i in sg)}" fill="none" stroke="{col}" stroke-width="{w}"'
                         + (f' stroke-dasharray="{dash}"' if dash else '') + '/>')
    # marqueurs nowcast (points discrets)
    for i in range(n):
        s.append(f'<circle cx="{X(i):.1f}" cy="{Y(pts[i][2]):.1f}" r="2.4" fill="{C["blue"]}"/>')
    # années
    seen = set()
    for i, (t, *_r) in enumerate(pts):
        if t.endswith("Q1") and t[:4] not in seen:
            seen.add(t[:4])
            s.append(f'<text x="{X(i):.1f}" y="{H-14}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10.5" fill="{C["faint"]}">{t[:4]}</text>')
    s.append("</svg>")
    return "".join(s)


def mix_html():
    mx = max([v for _, v in MODELF] + [T3, AVG3, MIHV]) or 1
    bar = lambda name, v, cls="": (f'<div class="r {cls}"><span>{name}</span><span class="bar"><span style="width:{max(v, 0)/mx*100:.0f}%"></span>'
                                   f'</span><span class="v">{frn(v)}</span></div>')
    rows = "".join(bar(name, v) for name, v in MODELF)
    rows += bar("Regard « signaux »", AVG3, "sub sep")
    rows += bar("Regard « faits »", MIHV, "sub")
    rows += bar("Chiffre publié (½ + ½)", T3, "avg")
    return f'<div class="mix">{rows}</div>'


# icônes
def _svg(paths, stroke):
    return f'<svg viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" class="ic">{paths}</svg>'


BARS = _svg('<path d="M4 20V11M10 20V5M16 20v-8M21 20H3"/>', C["blue"])
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
    hh = hard_html()
    hard_card = (f"""<div class="card" style="margin-bottom:22px"><h3>Ce que disent déjà les données dures</h3><div class="ph">Acquis de croissance du {LT_MIN} à partir des seuls mois déjà publiés — la méthode de l'INSEE pour bâtir les comptes trimestriels</div>
   {hh}
   <div class="note"><b>Acquis</b> = croissance du trimestre si l'indicateur restait, jusqu'à la fin du trimestre, au niveau du dernier mois connu. Ce sont les indicateurs sur lesquels l'INSEE étalonne ses comptes trimestriels (IPI, production des services, consommation de biens, Douanes en volume, travaux publics). Ils forment le cœur du modèle d'acquis durs (la moitié du chiffre publié) : les mois non encore publiés y sont <b>prévus par les enquêtes</b> du mois plutôt que simplement reconduits. Ils ne remplacent pas les enquêtes : un mois isolé d'industrie est très volatil. Ce trimestre, leur apport net au chiffre est de {frn(sum(ACQ.get('contrib', {}).values()), 2)} pt (déjà inclus dans la cascade ci-dessus).</div></div>""" if hh else "")
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
    tot = TRAJ.get("total")
    moves_sec = ""
    if tot and svg_moves():
        big = max(tot["blocs"].items(), key=lambda kv: abs(kv[1]))
        mnote = (f"Depuis {TRAJ['etapes'][0]['label']}, la prévision du {LT_MIN} est passée de {frn(tot['depart'])} % à {frn(tot['arrivee'])} %. "
                 f"Le bloc qui l'a le plus fait bouger : « {big[0][0].lower() + big[0][1:]} » ({frn(big[1])} pt). Chaque carte ci-dessous montre, mois par mois, "
                 f"la variation, ses deux principaux moteurs et les publications parues entre-temps.")
        moves_sec = f"""<div class="sh" style="margin-top:42px"><div class="n">Au fil du trimestre</div><h2>Ce qui a fait bouger la prévision</h2>
   <div class="d">Chaque mois apporte son lot de données nouvelles. Voici comment notre estimation a évolué depuis {TRAJ['etapes'][0]['label']}, et pourquoi.</div></div>
 <div class="card" style="margin-bottom:22px"><h3>De {frn(tot['depart'])} % à {frn(tot['arrivee'])} % : la variation, bloc par bloc</h3><div class="ph">Variation de la prévision du {LT_MIN} entre {TRAJ['etapes'][0]['label']} et aujourd'hui, en points de PIB</div>
   {svg_moves()}
   <div class="legend"><span class="it"><i style="background:{C['faint']}"></i>prévision {TRAJ['etapes'][0]['label']}</span><span class="it"><i style="background:{C['teal']}"></i>a fait monter</span><span class="it"><i style="background:{C['orange']}"></i>a fait baisser</span><span class="it"><i style="background:{C['blue']}"></i>prévision aujourd'hui</span></div>
   {moves_html()}
   <div class="note">{mnote}</div></div>"""
    st.markdown(f"""<div class="rl">
 <div class="sh"><div class="n">En temps réel</div><h2>Où en est la croissance française, en direct ?</h2>
   <div class="d">Notre estimation de l'activité (le PIB) pour le trimestre en cours et le suivant — sa variation par rapport au trimestre précédent, réactualisée à chaque nouvelle publication d'indicateur, sans attendre les chiffres officiels.</div></div>
 <div class="g2">
  <div class="verdict">
   <div class="vh"><div class="vtitle">Croissance du PIB<span>France · en volume</span></div><span class="seal">RexNow · Rexecode</span></div>
   <div class="vgrid">
     <div class="q now"><span class="qlab">{LT}</span><div class="qval">{frn(T3)}<span class="u"> %</span></div><span class="qsub">trimestre en cours</span><span class="qrisk">risque de trimestre négatif : <b>≈ {round(100*PNEG3)} %</b></span></div>
     <div class="q nxt"><span class="qlab">{LTN}</span><div class="qval">{frn(T4)}<span class="u"> %</span></div><span class="qsub">trimestre suivant</span><span class="qrisk">risque de trimestre négatif : <b>≈ {round(100*PNEG4)} %</b></span></div>
   </div>
   <div class="foot">Variation par rapport au trimestre précédent (T/T−1), corrigée des variations saisonnières · mise à jour : {MAJ}</div>
  </div>
  <div class="card eco"><div class="h">Le commentaire de l'économiste — Rexecode</div>
    <div class="q">« {commentaire(T3, T4)} »</div>
    <div class="sig">Lecture générée automatiquement à partir des prévisions du modèle.</div></div>
 </div>

 <div class="sh" style="margin-top:42px"><div class="n">Comment se forme le chiffre</div><h2>Deux regards, un seul chiffre</h2>
   <div class="d">Pour estimer la croissance, nous croisons deux regards complémentaires : ce que <b>signalent</b> les enquêtes et les marchés, et ce que <b>mesurent</b> déjà les statistiques du trimestre. Le chiffre publié prend la moitié de chacun.</div></div>
 <div class="card" style="margin-bottom:22px">{regards_html()}</div>

 <div class="sh" style="margin-top:42px"><div class="n">Ce qui explique le chiffre</div><h2>Pourquoi {frn(T3)} % ?</h2></div>
 <div class="card" style="margin-bottom:22px"><h3>Les contributions, bloc par bloc</h3><div class="ph">Les deux regards réunis : on part de la croissance d'un trimestre normal ; chaque grand bloc ajoute (vert) ou retranche (orange) pour aboutir au chiffre publié — en points de PIB</div>
   {svg_cascade()}
   <div class="legend"><span class="it"><i style="background:{C['faint']}"></i>trimestre moyen</span><span class="it"><i style="background:{C['teal']}"></i>soutient</span><span class="it"><i style="background:{C['orange']}"></i>freine</span><span class="it"><i style="background:{C['blue']}"></i>nowcast</span></div>
   <div class="note">{cnote}</div></div>
 {moves_sec}
 {hard_card}
 <div class="g2">
  <div class="card"><h3>La prévision de chaque trimestre, avec son incertitude</h3><div class="ph">Comment l'estimation évolue au fil des mois, et sa marge d'erreur</div>
    {svg_fan()}
    <div class="legend"><span class="it"><i style="background:{C['blue']}"></i>{LT_MIN}</span><span class="it"><i style="background:{C['orange']}"></i>{LTN_MIN}</span><span class="it"><i class="dot" style="background:rgba({C['ic']},0.28)"></i>marge d'incertitude (±1 écart-type, erreurs passées {PERIODE})</span></div>
    <div class="note">Le <b>{LT_MIN}</b> s'affine mois après mois et se fixe à {frn(T3)} % ; sa marge d'incertitude se resserre à mesure que les données paraissent. Le <b>{LTN_MIN}</b>, plus lointain, n'a pour l'instant qu'une estimation, avec une marge plus large{f' ; son niveau de référence est la croissance potentielle estimée par la Commission européenne (≈ {frn(POT4)} %/trim., soit ≈ {comma(POT4_AN, 1)} %/an)' if ANCRE4 else ''}.</div></div>
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
   <div class="fstage"><div class="fn">2 · Deux regards</div><h4>Signaux et faits</h4><p>Trois modèles statistiques lisent les <b>signaux</b> (enquêtes, marchés) ; un modèle d'acquis lit les <b>faits</b> déjà mesurés (production, consommation, commerce).</p></div>
   <div class="farr">→</div>
   <div class="fstage"><div class="fn">3 · Moitié-moitié</div><h4>La combinaison</h4><p>Le chiffre publié prend la moitié de chaque regard. Quand l'un se trompe, l'autre corrige : le résultat est plus stable et plus fiable.</p></div>
   <div class="farr">→</div>
   <div class="fstage"><div class="fn">4 · Le résultat</div><h4>La prévision</h4><p>La croissance du trimestre en cours et du suivant, avec sa marge d'incertitude, réactualisée à chaque publication.</p></div>
 </div>

 <div class="sh" style="margin-top:42px"><div class="n">Les deux regards en clair</div><h2>Les signaux et les faits</h2>
   <div class="d">Inutile d'entrer dans les équations : retenez qu'un regard <b>écoute</b> ce que disent les acteurs et les marchés, et que l'autre <b>compte</b> ce qui est déjà produit, consommé et vendu.</div></div>
 <div class="g2">
   <div class="card"><div class="tagr" style="color:var(--navy)">Regard 1 · les signaux</div><h3>Trois modèles statistiques</h3>
     <div class="ph">Ils lisent les 189 indicateurs — surtout les enquêtes et les marchés — et ont appris, sur 25 ans d'historique, ce qui annonce la croissance.</div>
     <div class="ml">
       <div class="r"><div>{TREE}</div><div><b>La forêt aléatoire</b><span>repère les signaux inhabituels et les effets de seuil.</span></div></div>
       <div class="r"><div>{WAVE}</div><div><b>MIDAS</b><span>exploite chaque donnée mensuelle dès qu'elle paraît.</span></div></div>
       <div class="r"><div>{FILTER}</div><div><b>ElasticNet</b><span>retient le petit nombre d'indicateurs qui compte vraiment.</span></div></div>
     </div>
     <div class="note">Leur force : réagir tôt, dès le premier mois, quand aucune donnée « dure » n'est encore parue.</div></div>
   <div class="card"><div class="tagr" style="color:var(--brass)">Regard 2 · les faits</div><h3>Le modèle des acquis</h3>
     <div class="ph">Il raisonne comme l'INSEE pour bâtir les comptes trimestriels : à partir de ce qui est déjà mesuré.</div>
     <ol class="steps">
       <li><div><b>On part du mesuré.</b> Production (industrie, construction, services), consommation de biens, exportations et importations des mois déjà publiés.</div></li>
       <li><div><b>On complète les mois manquants</b> grâce aux enquêtes du mois, publiées bien plus tôt.</div></li>
       <li><div><b>On traduit en croissance du PIB</b> avec une équation simple, calée sur 25 ans et protégée contre les valeurs extrêmes.</div></li>
     </ol>
     <div class="note">Sa force : ancrer le chiffre dans le réel, d'autant plus que le trimestre avance.</div></div>
 </div>

 <div class="sh" style="margin-top:42px"><div class="n">La combinaison, concrètement</div><h2>Comment se forme le chiffre publié</h2></div>
 <div class="g2">
   <div class="card"><h3>Le chiffre d'aujourd'hui, décomposé</h3><div class="ph">Ce que voit chaque modèle en ce moment, et comment on passe au chiffre publié</div>
     {mix_html()}
     <div class="note">Le regard « signaux » (moyenne des trois modèles, {frn(AVG3)} %) lit surtout les enquêtes et les marchés ; le regard « faits » ({frn(MIHV)} %) part de ce qui est déjà mesuré. Le chiffre publié est la <b>moitié de chacun</b> ({frn(T3)} %). Quand les deux divergent, c'est un signal : les données dures ne confirment pas (encore) ce que disent les enquêtes.</div></div>
   <div class="card"><h3>Pourquoi combiner plutôt que choisir ?</h3><div class="ph">Erreur de chaque modèle en test réel ({PERIODE}, fin du 3ᵉ mois) — plus la barre est courte, plus c'est précis</div>
     {bars_html(MODELS_RMSE, win_name="Combinaison", dec=3)}
     <div class="note">Aucun modèle n'est le meilleur à chaque période : celui qui gagne aujourd'hui peut décevoir demain. Nous avons testé une cinquantaine de méthodes (ponts à la manière de l'INSEE, régressions pénalisées, facteurs dynamiques, forêts, boosting…) aux quatre moments du trimestre ; la combinaison retenue est la plus <b>régulière</b> sur 2010-2017 comme sur 2018-2026, et nettement meilleure que l'ancien trio en fin de trimestre.</div></div>
 </div>

 <div class="sh" style="margin-top:42px"><div class="n">Le secret d'un bon nowcast</div><h2>Le trimestre se « remplit » au fil des semaines</h2>
   <div class="d">Un trimestre dure trois mois. Au début, tout est prévision. Puis, chaque semaine, de vraies données arrivent (production, consommation, commerce…) : une part de la croissance devient <b>acquise</b> (connue, plus à deviner). C'est exactement ainsi que l'INSEE bâtit ses comptes — et pourquoi notre estimation se resserre à mesure que le trimestre avance.</div></div>
 <div class="acq">
   <div class="s"><div class="mo">Début du trimestre</div><div class="fill"><span style="width:12%"></span></div><p>Presque tout reste à prévoir : seules les enquêtes de confiance sont disponibles. La marge d'incertitude est à son maximum.</p></div>
   <div class="s"><div class="mo">Après 1 mois</div><div class="fill"><span style="width:42%"></span></div><p>Les enquêtes du 1er mois sont connues et les premières données « dures » arrivent (consommation de biens). L'estimation se précise.</p></div>
   <div class="s"><div class="mo">Fin du trimestre</div><div class="fill"><span style="width:78%"></span></div><p>Production, consommation et commerce extérieur des premiers mois sont publiés. Leurs <b>acquis</b> entrent alors directement dans les modèles, et la marge d'incertitude est à son plus bas.</p></div>
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
     <div class="note">Chaque semaine, dès qu'une donnée nouvelle est publiée, elle est intégrée et la prévision est recalculée — sans intervention manuelle.</div>
     {f'<div class="note"><b>Trimestre suivant : ancré sur la croissance potentielle.</b> À un trimestre d&#39;avance, aucune donnée du trimestre visé n&#39;existe encore : la prévision repose surtout sur le rythme « normal » de l&#39;économie. Nous le fixons sur la croissance potentielle estimée par la Commission européenne (≈ {comma(POT4_AN, 1)} %/an), plutôt que sur la moyenne des 25 dernières années, plus élevée. Les modèles prévoient l&#39;écart à ce potentiel. Pour le trimestre en cours, en revanche, les données du trimestre suffisent à fixer le niveau.</div>' if ANCRE4 else ''}</div>
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
 <div class="card" style="margin-bottom:26px"><h3>Estimation du nowcast vs croissance réalisée</h3><div class="ph">Croissance trimestrielle du PIB, {PERIODE} · estimation en fin de trimestre · hors trimestres de crise (Covid 2020-2021, hors échelle)</div>
   {svg_track(TRACK)}
   <div class="legend"><span class="it"><i style="background:{C['soft']}"></i>Réalisé (INSEE)</span><span class="it"><i style="background:{C['blue']}"></i>Chiffre publié (notre estimation en temps réel)</span><span class="it"><i style="background:{C['brass']}"></i>Regard « faits » seul (pointillés)</span></div>
   <div class="note">Le nowcast suit de près les hauts et les bas de l'activité, trimestre après trimestre. Il lisse un peu les à-coups extrêmes — c'est normal, un modèle prudent ne « saute » pas sur un chiffre isolé — mais il ne se trompe presque jamais de sens. Sur toute la période, l'écart type de l'erreur (le « RMSE ») est de <b>{comma(RMSE0)} point</b> seulement.</div></div>

 <div class="sh" style="margin-top:30px"><div class="n">Les deux regards à l'épreuve</div><h2>Plus le trimestre avance, plus les faits comptent</h2>
   <div class="d">Le même test en conditions réelles, à quatre moments du trimestre. En tout début de trimestre, les deux regards se valent ; à mesure que les données dures paraissent, le regard « faits » devient le plus précis — et le chiffre publié, qui combine les deux, en profite.</div></div>
 <div class="g2" style="margin-bottom:26px">
  <div class="card"><h3>L'erreur selon le moment du trimestre</h3><div class="ph">Écart type de l'erreur (RMSE), en points de croissance, {PERIODE} — plus c'est bas, mieux c'est</div>
    {svg_moments()}
    <div class="legend"><span class="it"><i style="background:{C['faint']}"></i>regard « signaux » (3 modèles)</span><span class="it"><i style="background:{C['brass']}"></i>regard « faits » (acquis)</span><span class="it"><i style="background:{C['blue']}"></i>chiffre publié</span></div>
    <div class="note">En fin de trimestre, le chiffre publié se trompe en moyenne de <b>{comma(MOM.get("C3", {}).get("combi", {}).get("mae", 0.14))} point</b> ; sa corrélation avec la croissance mesurée atteint <b>{comma(MOM.get("C3", {}).get("combi", {}).get("corr", 0.74))}</b> et <b>{MOM.get("C3", {}).get("combi", {}).get("pct02", 74)} %</b> des trimestres tombent à moins de 0,2 point du chiffre de l'INSEE.</div></div>
  <div class="card"><h3>Ce qui pèse dans le regard « faits »</h3><div class="ph">Les variables les plus influentes : effet sur la croissance pour un écart type, et son incertitude (trait fin)</div>
    {svg_coefs()}
    <div class="legend"><span class="it"><i style="background:{C['brass']}"></i>acquis des données dures</span><span class="it"><i style="background:{C['navy']}"></i>enquêtes</span><span class="it"><i style="background:{C['faint']}"></i>effet négatif</span></div>
    <div class="note">Les acquis d'exportations, de consommation et de production figurent parmi les variables les plus solides. Le PIB du trimestre précédent joue <b>en sens inverse</b> : un trimestre très fort est souvent suivi d'un trimestre plus calme, et inversement.</div></div>
 </div>

 <div class="g2">
  <div class="card"><h3>1 · Viser juste — la précision</h3><div class="ph">Écart moyen entre nos prévisions et la première estimation de l'INSEE, selon l'échéance (en points de croissance)</div>
    {bars_html(PREC, win_name="À quelques semaines")}
    <div class="note">Plus l'échéance est proche, plus c'est précis : à quelques semaines, l'écart moyen n'est que de <b>{comma(MAE_CUR)} point</b> (autrement dit, on se trompe en moyenne d'un quart de point). Un an à l'avance, il reste de <b>{comma(MAE_NEXT)} point</b> — au niveau des tout meilleurs prévisionnistes.</div></div>
  <div class="card"><h3>2 · Viser sans biais — la neutralité</h3><div class="ph">Sur 24 ans (2002-2025), penche-t-on en moyenne trop à la hausse ou trop à la baisse ?</div>
    {svg_gauge()}
    <div class="note">Notre biais moyen (notre erreur moyenne, en tenant compte du signe) est de <b>{frn(BIAS)} point</b> : pratiquement zéro. Nous ne sommes ni systématiquement optimistes, ni pessimistes — une qualité rare, car beaucoup de prévisionnistes penchent toujours du même côté.</div></div>
 </div>
 <div class="sh" style="margin-top:40px"><div class="n">Veille</div><h2>Le modèle dérive-t-il ?</h2>
   <div class="d">Un modèle peut se mettre à surestimer ou à sous-estimer durablement, notamment quand la croissance change de rythme. Nous surveillons donc la moyenne de ses erreurs sur les 8 derniers trimestres connus. Tant qu'elle reste dans la zone verte, les écarts relèvent du hasard ; si elle en sort, il faut recaler le modèle. C'est arrivé en <b>2012-2014</b> : après la crise, le modèle continuait de prévoir l'ancien rythme de croissance.</div></div>
 <div class="g2">
  {bias_card("h0")}
  {bias_card("h1")}
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
<h1 style="font-size:26px">Croissance du PIB — {frn(T3)} % au {LT}</h1></div>
<p>Prévision du trimestre en cours ({LT}) : <b>{frn(T3)} %</b> ; trimestre suivant ({LTN}) : <b>{frn(T4)} %</b>. Variations par rapport au trimestre précédent, en volume.</p>
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
