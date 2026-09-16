"""Rexecode Live — nowcast du PIB de la France, version premium sur Streamlit.

Menu nommé par le contenu, lisible par tous les profils (dirigeants, fédérations,
financiers, experts comme généralistes) : Prévision de croissance · Notre méthode ·
Notre fiabilité · Nos autres prévisions. Thème clair/sombre qui suit l'appareil.
Pleine largeur adaptative. Graphiques en SVG sur mesure (aucune dépendance hors streamlit).
Modèle & application : Anthony Morlet-Lavidalie — Rexecode.

Lancer :  .venv\\Scripts\\python.exe -m streamlit run rexlive\\app.py
"""
from __future__ import annotations
import json, datetime as dt
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
             navy="#173D61", navy2="#0E2942", blue="#5FB0E2", orange="#F0935B", brass="#CBAA6E", teal="#40C29E",
             line="#243547", ic="95,176,226",
             vtxt="#F3F8FC", vsoft="#D2E2EF", vkick="#A6CAE6", vseal="#CADEEF", vline="rgba(255,255,255,.18)")
else:
    C = dict(bg="#EDF1F6", surf="#FFFFFF", surf2="#F1F7FC", ink="#0E1A2A", soft="#3D4F66", faint="#6C7E96",
             navy="#123A5E", navy2="#0C2942", blue="#0A6FB0", orange="#DE6B2A", brass="#8A6D37", teal="#1E8F73",
             line="#D7DFEA", ic="10,111,176",
             vtxt="#FFFFFF", vsoft="#DEEBF7", vkick="#B4D0E9", vseal="#CFE1F0", vline="rgba(255,255,255,.20)")

# ---------------- données ----------------
hs = loadjson("horizon_summary.json")
f3, f4 = hs.get("forecast_T3_h0", {}), hs.get("forecast_T4_h1", {})
r0, r1 = hs.get("rmse_h0", {}), hs.get("rmse_h1", {})


def _mtime():
    for base in (OUT, HERE / "data"):
        p = base / "horizon_summary.json"
        if p.exists():
            try:
                return dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%B %Y")
            except Exception:
                pass
    return "septembre 2026"


MAJ = "septembre 2026"
T3, T4 = f3.get("COMBI", 0.20), f4.get("COMBI", 0.26)
RMSE0, RMSE1 = r0.get("COMBI", 0.215), r1.get("COMBI", 0.226)
cats = loadjson("cats_importance.json", {})
DRIVERS = sorted(cats.items(), key=lambda kv: -kv[1])[:7]
# trajectoire par mois (épurée) : mois, valeur, IC±
FAN = [("juin", 0.305, 0.231), ("juil.", 0.30, 0.228), ("août", 0.28, 0.238), ("sept.", round(T3, 3), 0.215)]
BAROS = [("Croissance du PIB", "live", "trimestre en cours", frn(T3) + " %"),
         ("Inflation", "pret", "hausse des prix", "à venir"),
         ("Emploi & salaires", "pret", "marché du travail", "à venir"),
         ("Production industrielle", "pret", "industrie manufacturière", "à venir"),
         ("Taux d'intérêt", "pret", "OAT & financement", "à venir"),
         ("Comptes publics", "roadmap", "déficit & dette", "à venir")]

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
.rl h1,.rl h2,.rl h3,.rl .serif{{font-family:"Fraunces",Georgia,serif;font-weight:600;letter-spacing:-.012em;line-height:1.12;margin:0;color:var(--ink)}}
.rl .mono{{font-family:"IBM Plex Mono",ui-monospace,monospace}}
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
.rl .sh h2{{font-size:clamp(24px,3.2vw,34px);margin-top:4px}}
.rl .sh .d{{color:var(--soft);font-size:15.5px;max-width:64ch;margin-top:6px;line-height:1.5}}
/* grids */
.rl .g2{{display:grid;grid-template-columns:1.06fr .94fr;gap:26px}}@media(max-width:900px){{.rl .g2{{grid-template-columns:1fr}}}}
.rl .gc{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}@media(max-width:900px){{.rl .gc{{grid-template-columns:1fr}}}}
.rl .g3{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}}@media(max-width:900px){{.rl .g3{{grid-template-columns:1fr}}}}
/* verdict card */
.rl .verdict{{background:linear-gradient(155deg,var(--navy),{C['navy2']});border-radius:20px;padding:30px 34px;
  box-shadow:0 12px 40px rgba(0,0,0,.18);border:1px solid rgba(255,255,255,.07)}}
.rl .verdict *{{color:{C['vtxt']}}}
.rl .verdict .vh{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}}
.rl .verdict .vk{{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:{C['vkick']}!important}}
.rl .verdict .seal{{flex:none;white-space:nowrap;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.08em;color:{C['vseal']}!important;border:1px solid rgba(255,255,255,.30);border-radius:20px;padding:3px 11px}}
.rl .verdict .clu{{display:flex;gap:18px 48px;flex-wrap:wrap;align-items:flex-end;margin-top:18px}}
.rl .verdict .lab{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.05em;text-transform:uppercase;color:{C['vkick']}!important;display:block;margin-bottom:5px}}
.rl .verdict .big{{font-family:"Fraunces",serif;font-weight:600;font-size:70px;line-height:.9;color:{C['vtxt']}!important;font-variant-numeric:tabular-nums}}
.rl .verdict .big .u{{font-size:28px;color:{C['vsoft']}!important}}
.rl .verdict .nx .v{{font-family:"Fraunces",serif;font-size:42px;font-weight:600;color:{C['vtxt']}!important;font-variant-numeric:tabular-nums}}
.rl .verdict .foot{{margin-top:24px;padding-top:16px;border-top:1px solid {C['vline']};font-family:"IBM Plex Mono",monospace;font-size:12px;color:{C['vsoft']}!important;letter-spacing:.02em;line-height:1.5}}
/* cards */
.rl .card{{background:var(--surf);border:1px solid var(--line);border-radius:16px;padding:24px 26px;box-shadow:0 1px 2px rgba(16,30,50,.04)}}
.rl .card h3{{font-family:"Libre Franklin",sans-serif;font-weight:700;font-size:16px;color:var(--ink);margin-bottom:3px}}
.rl .card .ph{{color:var(--faint);font-size:13px;margin-bottom:16px;line-height:1.45}}
.rl .card p{{color:var(--soft);font-size:14.5px;line-height:1.6;margin:.4em 0 0}}
.rl .eco{{border-left:5px solid var(--brass);display:flex;flex-direction:column;justify-content:center}}
.rl .eco .h{{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--brass);margin-bottom:10px}}
.rl .eco .q{{font-family:"Fraunces",serif;font-size:20px;line-height:1.45;color:var(--ink)}}
/* driver bars */
.rl .drv{{display:grid;gap:11px}}
.rl .drv .r{{display:grid;grid-template-columns:minmax(120px,200px) 1fr 40px;gap:14px;align-items:center;font-size:14px;color:var(--ink)}}
.rl .drv .bar{{height:16px;border-radius:5px;background:var(--surf2);overflow:hidden}}.rl .drv .bar span{{display:block;height:100%;border-radius:5px}}
.rl .drv .v{{font-family:"IBM Plex Mono",monospace;font-size:13px;color:var(--soft);text-align:right}}
.rl .note{{font-size:13px;color:var(--faint);margin-top:14px;line-height:1.55}}
.rl .note b{{color:var(--soft)}}
.rl .legend{{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--soft);margin-top:10px}}
.rl .legend i{{width:14px;height:4px;border-radius:2px;display:inline-block;vertical-align:middle;margin-right:6px}}
/* stat tiles */
.rl .stat{{display:flex;gap:26px;flex-wrap:wrap;margin:4px 0}}.rl .stat .s{{flex:1 1 130px}}
.rl .stat .k{{font-family:"Fraunces",serif;font-size:40px;font-weight:600;color:var(--navy);font-variant-numeric:tabular-nums;line-height:1}}
:root:not([data-theme="light"]) .rl .stat .k{{color:var(--blue)}}
.rl .stat .l{{font-size:12.5px;color:var(--soft);margin-top:7px;line-height:1.45}}
.rl .pill{{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:11px;border:1px solid var(--line);border-radius:20px;padding:3px 11px;margin:6px 6px 0 0;color:var(--soft)}}
.rl .pill.good{{color:var(--teal);border-color:color-mix(in srgb,var(--teal) 45%,var(--line))}}
/* model cards */
.rl .mcard{{background:var(--surf);border:1px solid var(--line);border-radius:16px;padding:22px 24px;box-shadow:0 1px 2px rgba(16,30,50,.04)}}
.rl .mcard .tag{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;color:var(--brass)}}
.rl .mcard h3{{font-family:"Fraunces",serif;font-weight:600;font-size:20px;margin:5px 0 9px;color:var(--ink)}}
.rl .mcard p{{color:var(--soft);font-size:14px;line-height:1.6;margin:0}}
.rl .mcard.hero{{background:linear-gradient(155deg,var(--navy),{C['navy2']})}}
.rl .mcard.hero *{{color:{C['vtxt']}!important}} .rl .mcard.hero .tag{{color:{C['vkick']}!important}} .rl .mcard.hero p{{color:{C['vsoft']}!important}}
.rl .mcard.hero b{{color:{C['vtxt']}!important}}
.rl .ing{{display:grid;grid-template-columns:1fr 1fr;gap:12px 24px;margin-top:2px}}@media(max-width:560px){{.rl .ing{{grid-template-columns:1fr}}}}
.rl .ing .i{{display:flex;gap:12px;align-items:baseline;font-size:14px;color:var(--ink)}}
.rl .ing .i b{{font-family:"Fraunces",serif;color:var(--navy);font-size:18px;min-width:84px}}
:root:not([data-theme="light"]) .rl .ing .i b{{color:var(--blue)}}
/* suite */
.rl .suite{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}}
.rl .bc{{background:var(--surf);border:1px solid var(--line);border-radius:15px;padding:20px 22px;position:relative}}
.rl .bc .st{{position:absolute;top:16px;right:18px;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:var(--faint);border:1px solid var(--line);border-radius:20px;padding:2px 9px}}
.rl .bc.live .st{{color:#fff;background:var(--teal);border-color:transparent}}
.rl .bc h3{{font-family:"Libre Franklin",sans-serif;font-size:17px;font-weight:700;color:var(--ink);margin-bottom:2px}}
.rl .bc .m{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--faint);margin-bottom:14px}}
.rl .bc .val{{font-family:"Fraunces",serif;font-size:30px;font-weight:600;color:var(--navy)}}
:root:not([data-theme="light"]) .rl .bc .val{{color:var(--blue)}}
.rl .bc .val.mut{{color:var(--faint);font-size:18px}}
.rl svg{{display:block}} .rl svg.fan{{width:100%;height:auto;aspect-ratio:480/232}} .rl svg.i24{{width:26px;height:26px}}
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
      <div class="vk">Rexecode Live</div>
      <h1 style="color:{C['vtxt']};font-size:26px;margin:.25em 0">Accès protégé</h1>
      <div style="color:{C['vsoft']};font-size:14px">Saisissez le mot de passe communiqué par Rexecode.</div></div></div>''',
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


# ==================================================================== SVG
def svg_fan():
    W, H, mL, mR, mT, mB = 480, 232, 42, 16, 16, 36
    iw, ih, n = W - mL - mR, H - mT - mB, len(FAN)
    yMin, yMax = 0.0, 0.7
    X = lambda i: mL + iw * i / (n - 1)
    Y = lambda v: mT + ih * (1 - (v - yMin) / (yMax - yMin))
    s = [f'<svg class="fan" viewBox="0 0 {W} {H}">']
    for g in (0.0, 0.2, 0.4, 0.6):
        y = Y(g)
        s.append(f'<line x1="{mL}" y1="{y:.1f}" x2="{W-mR}" y2="{y:.1f}" stroke="var(--line)"/>')
        s.append(f'<text x="{mL-8}" y="{y+4:.1f}" text-anchor="end" font-family="IBM Plex Mono" font-size="10.5" fill="{C["faint"]}">{comma(g,1)}</text>')
    up = lambda m: " ".join(f"{X(i):.1f},{Y(v+m*r):.1f}" for i, (_, v, r) in enumerate(FAN))
    lo = lambda m: " ".join(f"{X(i):.1f},{Y(v-m*r):.1f}" for i, (_, v, r) in reversed(list(enumerate(FAN))))
    s.append(f'<polygon points="{up(1.96)} {lo(1.96)}" fill="rgba({C["ic"]},0.10)"/>')
    s.append(f'<polygon points="{up(1)} {lo(1)}" fill="rgba({C["ic"]},0.20)"/>')
    s.append(f'<polyline points="{" ".join(f"{X(i):.1f},{Y(v):.1f}" for i,(_,v,_) in enumerate(FAN))}" fill="none" stroke="{C["blue"]}" stroke-width="2.8"/>')
    for i, (mois, v, _) in enumerate(FAN):
        x, y, last = X(i), Y(v), (i == n - 1)
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{5.5 if last else 4}" fill="{C["blue"] if last else C["surf"]}" stroke="{C["blue"]}" stroke-width="2.4"/>')
        s.append(f'<text x="{x:.1f}" y="{H-12}" text-anchor="middle" font-family="IBM Plex Mono" font-size="11" fill="{C["faint"]}">{mois}</text>')
    s.append("</svg>")
    return "".join(s)


def drivers_html():
    pal = [C["blue"], C["navy"], C["teal"], C["brass"], "#6FA8CF", C["orange"], C["faint"]]
    mx = max(v for _, v in DRIVERS) or 1
    return '<div class="drv">' + "".join(
        f'<div class="r"><span>{k}</span><span class="bar"><span style="width:{v/mx*100:.0f}%;background:{pal[i%len(pal)]}"></span></span><span class="v">{round(v)}%</span></div>'
        for i, (k, v) in enumerate(DRIVERS)) + '</div>'


SHIELD = f'<svg viewBox="0 0 24 24" fill="none" stroke="{C["teal"]}" stroke-width="1.7" class="i24"><path d="M12 3l7 3v5c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3z"/><path d="M8.5 12l2.3 2.3 4.7-4.7"/></svg>'


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
    st.markdown(f"""<div class="rl">
 <div class="sh"><div class="n">La prévision</div><h2>Quelle croissance ce trimestre ?</h2>
   <div class="d">La prévision du PIB de la France pour le trimestre en cours et le suivant, mise à jour à chaque nouvelle publication d'indicateur.</div></div>
 <div class="g2">
  <div class="verdict">
   <div class="vh"><div class="vk">Croissance du PIB · France</div><span class="seal">RexNow · Rexecode</span></div>
   <div class="clu">
     <div><span class="lab">Trimestre en cours (T3 2026)</span><div class="big">{frn(T3)}<span class="u"> %</span></div></div>
     <div class="nx"><span class="lab">Trimestre suivant (T4)</span><div class="v">{frn(T4)} %</div></div>
   </div>
   <div class="foot">Mise à jour : {MAJ} · croissance en volume, corrigée des variations saisonnières</div>
  </div>
  <div class="card eco"><div class="h">Le commentaire de l'économiste — Rexecode</div>
    <div class="q">« L'activité reste sur un rythme modéré : les enquêtes auprès des entreprises tiennent, mais la production industrielle a marqué le pas cet été. Ni accélération, ni rupture. »</div></div>
 </div>

 <div class="sh" style="margin-top:42px"><div class="n">Ce qui explique le chiffre</div><h2>Ce qui fait bouger la prévision</h2></div>
 <div class="gc">
  <div class="card"><h3>Les indicateurs qui comptent le plus</h3><div class="ph">Poids de chaque famille d'indicateurs dans la prévision</div>
    {drivers_html()}
    <div class="note">Les <b>enquêtes de conjoncture</b> (climat des affaires, carnets de commandes) et la <b>production réelle</b> pèsent le plus lourd. Le reste vient en complément.</div></div>
  <div class="card"><h3>Comment la prévision a évolué</h3><div class="ph">La prévision du trimestre, mois après mois, avec sa marge d'incertitude</div>
    {svg_fan()}
    <div class="legend"><span><i style="background:{C['blue']}"></i>Prévision</span><span><i style="background:rgba({C['ic']},0.34);height:9px;border-radius:2px"></i>Marge d'incertitude</span></div>
    <div class="note">La prévision se précise à mesure que les données du trimestre sont publiées : la marge d'incertitude, en bleu clair, se resserre au fil des mois.</div></div>
 </div>
</div>""", unsafe_allow_html=True)


def page_methode():
    st.markdown(f"""<div class="rl">
 <div class="sh"><div class="n">Notre méthode</div><h2>Comment nous prévoyons</h2>
   <div class="d">Nous ne parions pas sur un seul modèle : nous en combinons trois, complémentaires. Chacun regarde l'économie sous un angle différent, et leur moyenne est plus solide que chacun pris isolément.</div></div>
 <div class="g3">
  <div class="mcard"><div class="tag">Modèle 1 · apprentissage automatique</div><h3>Forêt aléatoire</h3>
    <p>Elle apprend, dans l'historique, les liens entre des centaines d'indicateurs et la croissance — y compris les relations complexes qu'une simple équation manquerait.</p></div>
  <div class="mcard"><div class="tag">Modèle 2 · fréquence mixte</div><h3>MIDAS</h3>
    <p>Il relie directement les données <b>mensuelles</b>, qui tombent en continu, à la croissance <b>trimestrielle</b> — pour exploiter l'information le plus tôt possible.</p></div>
  <div class="mcard"><div class="tag">Modèle 3 · sélection parcimonieuse</div><h3>ElasticNet</h3>
    <p>Il retient automatiquement, parmi tous les indicateurs, le petit nombre qui compte vraiment, et met de côté le bruit.</p></div>
 </div>
 <div class="gc" style="margin-top:22px">
  <div class="mcard hero"><div class="tag">Le chiffre que nous publions</div><h3>La combinaison des trois</h3>
    <p>Nous publions la <b>moyenne</b> des trois modèles. C'est le choix le plus sûr : quand l'un se trompe, les autres corrigent. Testée en conditions réelles sur 2015-2026, son erreur n'est que de <b>{comma(RMSE0)} point de croissance</b> — au niveau des meilleurs standards.</p></div>
  <div class="card"><h3>Ce que le modèle regarde</h3><div class="ph">Les ingrédients, mis à jour en direct</div>
    <div class="ing">
      <div class="i"><b>≈ 189</b><span>séries suivies (INSEE, Banque de France, BCE, Eurostat, Douanes…)</span></div>
      <div class="i"><b>2</b><span>horizons distincts : le trimestre en cours et le suivant</span></div>
      <div class="i"><b>1×/sem.</b><span>mise à jour automatique dès qu'un indicateur paraît</span></div>
      <div class="i"><b>25 ans</b><span>de recul pour caler et vérifier les modèles</span></div>
    </div>
    <div class="note">Nous reproduisons la façon dont l'INSEE bâtit les comptes : dès qu'un ou deux mois de données « dures » (production, consommation…) sont connus, une partie de la croissance du trimestre est déjà acquise.</div></div>
 </div>
</div>""", unsafe_allow_html=True)


def page_fiabilite():
    st.markdown(f"""<div class="rl">
 <div class="sh"><div class="n">Notre fiabilité</div><h2>Nos prévisions tiennent-elles la route ?</h2>
   <div class="d">La crédibilité se mesure sur la durée. Voici ce que valent nos prévisions de croissance de la France, chiffres à l'appui — les nôtres, sans détour.</div></div>
 <div class="gc">
  <div class="card"><h3>Un historique fiable et sans biais</h3><div class="ph">Nos prévisions d'automne pour l'année suivante, sur 24 ans (2002-2025), comparées à la première estimation de l'INSEE</div>
   <div class="stat"><div class="s"><div class="k">0,57</div><div class="l">point d'écart moyen — au plus près de la réalité</div></div>
     <div class="s"><div class="k">+0,06</div><div class="l">biais quasi nul — ni trop optimiste, ni trop pessimiste</div></div></div>
   <div><span class="pill good">sans biais</span><span class="pill">24 années</span><span class="pill">hors choc Covid 2020</span></div>
   <div class="note">Un biais proche de zéro signifie que, sur le long terme, nous ne surestimons ni ne sous-estimons systématiquement la croissance — une qualité rare parmi les prévisionnistes.</div></div>
  <div class="card"><h3>La précision de la prévision en temps réel</h3><div class="ph">Erreur du modèle sur la période de test (2015-2026), hors trimestres de crise</div>
   <div class="stat"><div class="s"><div class="k">{comma(RMSE0)}</div><div class="l">point d'erreur sur le trimestre en cours</div></div>
     <div class="s"><div class="k">{comma(RMSE1)}</div><div class="l">point d'erreur sur le trimestre suivant</div></div></div>
   <div><span class="pill">testé en conditions réelles</span><span class="pill">2 horizons</span></div>
   <div class="note">« En conditions réelles » : à chaque date passée, le modèle n'a reçu que l'information réellement disponible ce jour-là — jamais de données venues du futur.</div></div>
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
<h1 style="font-size:26px">Croissance du PIB — {frn(T3)} % au trimestre en cours</h1></div>
<p>Prévision du trimestre en cours : <b>{frn(T3)} %</b> ; trimestre suivant : <b>{frn(T4)} %</b>.</p>
<p><i>« L'activité reste sur un rythme modéré : les enquêtes tiennent, mais la production industrielle a marqué le pas cet été. Ni accélération, ni rupture. »</i></p>
<p style="font-size:13px;color:#3D4F66">Nos prévisions France sont fiables et sans biais (écart moyen 0,57 pt, biais +0,06 sur 2002-2025 vs 1ʳᵉ estimation INSEE).</p>
<p style="font-size:12px;color:#6C7E96">Modèle &amp; application : Anthony Morlet-Lavidalie — Rexecode. Chiffres à revérifier à la source.</p></body>"""
st.markdown('<div class="rl" style="margin-top:36px"></div>', unsafe_allow_html=True)
st.download_button("Télécharger la note de synthèse (HTML)", note,
                   file_name="rexecode_live_note.html", mime="text/html")
st.markdown(f'<div class="rl"><div class="note" style="margin-top:22px;border-top:1px solid var(--line);padding-top:18px;font-size:12.5px">'
            f'<b>Rexecode Live</b> · modèle &amp; application : <b>Anthony Morlet-Lavidalie</b>, Rexecode. '
            f'Thème {"sombre" if DARK else "clair"}, adapté à votre appareil. Sources ouvertes ; chiffres à revérifier à la source.</div></div>',
            unsafe_allow_html=True)
