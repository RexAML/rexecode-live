"""Rexecode Live — version ULTRA PREMIUM sur Streamlit.

Produit haut de gamme : verdict, voix de l'économiste, moteurs, preuve (track record
fiable & sans biais), suite de baromètres, premium, alertes, note de comité.
Thème clair/sombre qui suit l'appareil du visiteur. Graphiques en SVG généré (pas de
widgets génériques) pour un rendu sur mesure. API & widget viendront en dernier.

Lancer :  .venv\\Scripts\\python.exe -m streamlit run rexlive\\app.py
Modèle & application : Anthony Morlet-Lavidalie — Rexecode.
"""
from __future__ import annotations
import json, datetime as dt
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "pib"

st.set_page_config(page_title="Rexecode Live — Nowcast PIB", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")


def loadjson(name, default=None):
    for base in (OUT, Path(__file__).resolve().parent / "data"):
        p = base / name
        try:
            raw = p.read_bytes()
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


# ---------------- thème (suit l'appareil) ----------------
try:
    DARK = (st.context.theme.type == "dark")
except Exception:
    DARK = False

if DARK:
    C = dict(bg="#0A0F16", surf="#111A25", surf2="#16212E", ink="#E9EEF5", soft="#A7B5C7", faint="#6A7C90",
             navy="#173A5C", navy2="#0F2942", blue="#57ADE0", orange="#EC8A54", brass="#C6A366", teal="#3BB394",
             line="#213142", lineS="#192535", combi="#22344A", axis="#9FB0C0", grid="rgba(150,160,175,0.16)",
             band="#274a6b", ic="87,173,224", good="#3BB394")
    COL = dict(combi="#57ADE0", rf="#F79A5E", midas="#43C9AA", en="#9CC4E6", obs="#E9EEF5")
else:
    C = dict(bg="#EFF3F8", surf="#FFFFFF", surf2="#F1F7FC", ink="#0E1A2A", soft="#42546B", faint="#7F90A5",
             navy="#123A5E", navy2="#0E2E4B", blue="#0A6FB0", orange="#DE6B2A", brass="#9C7B3F", teal="#1E8F73",
             line="#DBE2EC", lineS="#E9EEF4", combi="#EAF4FB", axis="#5B6B7A", grid="rgba(130,140,155,0.22)",
             band="#CFE0EE", ic="10,111,176", good="#1E7F5C")
    COL = dict(combi="#0A6FB0", rf="#DE6B2A", midas="#1E8F73", en="#123A5E", obs="#0E1A2A")

# ---------------- données ----------------
hs = loadjson("horizon_summary.json")
f3, f4 = hs.get("forecast_T3_h0", {}), hs.get("forecast_T4_h1", {})
r0, r1 = hs.get("rmse_h0", {}), hs.get("rmse_h1", {})
def _mtime():
    for base in (OUT, Path(__file__).resolve().parent / "data"):
        p = base / "horizon_summary.json"
        if p.exists():
            try:
                return dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%d/%m/%Y")
            except Exception:
                pass
    return "septembre 2026"
MAJ = _mtime()
T3, T4 = f3.get("COMBI", 0.20), f4.get("COMBI", 0.26)
cats = loadjson("cats_importance.json", {})
DRIVERS = sorted(cats.items(), key=lambda kv: -kv[1])[:7]
NOMS = {"rf": "Random Forest", "midas": "MIDAS", "en": "ElasticNet", "combi": "Combinaison"}
MK = {"rf": "RandomForest", "midas": "MIDAS", "en": "ElasticNet", "combi": "COMBI"}
# trajectoire (récit de révision) : [stage, valeur, IC±, connu]
FAN = [("avant T", 0.305, 0.231, True), ("fin juillet", 0.30, 0.228, True),
       ("fin août", 0.28, 0.238, True), ("IPI juillet", round(T3, 3), 0.215, True),
       ("fin sept.", round(T3, 3), 0.214, False)]
PEERS = [("OCDE", 0.29, False), ("Rexecode", 0.32, True), ("Banque de France", 0.34, False),
         ("FMI", 0.34, False), ("Commission eur.", 0.34, False), ("OFCE", 0.47, False), ("Gouvernement", 0.54, False)]
BAROS = [("Croissance / PIB", "live", "nowcast RexNow", frn(T3) + " %"),
         ("Inflation", "pret", "prix France (IPC)", "à brancher"),
         ("Emploi & SMIC", "pret", "marché du travail", "à brancher"),
         ("Production manuf.", "pret", "industrie C1–C5", "à brancher"),
         ("Taux & OAT", "pret", "marché souverain", "à brancher"),
         ("Finances publiques", "roadmap", "déficit & dette", "à venir")]

# ---------------- routage ----------------
qp = st.query_params
PAGE = qp.get("p", "produit")
MODE = qp.get("m", "decideur")

# ==================================================================== CSS
st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Libre+Franklin:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
:root{{--bg:{C['bg']};--surf:{C['surf']};--surf2:{C['surf2']};--ink:{C['ink']};--soft:{C['soft']};--faint:{C['faint']};
 --navy:{C['navy']};--blue:{C['blue']};--orange:{C['orange']};--brass:{C['brass']};--teal:{C['teal']};--line:{C['line']};--combi:{C['combi']};}}
#MainMenu,footer,header[data-testid="stHeader"],[data-testid="stStatusWidget"],[data-testid="stToolbar"]{{display:none!important}}
html,body,.stApp{{background:var(--bg)!important}}
.stApp *{{animation-duration:0s!important}}
.block-container{{max-width:1120px!important;padding-top:14px!important;padding-bottom:60px!important}}
[data-testid="stMarkdownContainer"] *{{color:var(--ink)}}
.rl,.rl *{{font-family:"Libre Franklin",system-ui,sans-serif}}
.rl h1,.rl h2,.rl h3,.rl .serif{{font-family:"Fraunces",Georgia,serif;font-weight:600;letter-spacing:-.012em;line-height:1.12;margin:0}}
.rl .mono{{font-family:"IBM Plex Mono",ui-monospace,monospace}}
.rl .kick{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--brass)}}
.rl .soft{{color:var(--soft)}} .rl .faint{{color:var(--faint)}}
.rl .tnum{{font-variant-numeric:tabular-nums;font-family:"IBM Plex Mono",monospace}}
/* top bar */
.rl .top{{display:flex;align-items:center;gap:18px;padding:6px 0 16px;border-bottom:1px solid var(--line);margin-bottom:22px;flex-wrap:wrap}}
.rl .brandwrap{{display:flex;flex-direction:column;gap:1px}}
.rl .brand{{font-family:"Fraunces",serif;font-weight:600;font-size:21px;color:var(--ink);line-height:1.05}}.rl .brand b{{color:var(--blue)}}
.rl .byline{{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.03em;color:var(--faint)}}
.rl .direct{{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#fff;background:var(--teal);border-radius:20px;padding:2px 8px;margin-left:8px}}
.rl .nav{{display:flex;gap:16px;font-size:13.5px;font-weight:600;margin-left:8px;flex-wrap:wrap}}
.rl .nav a{{color:var(--soft);text-decoration:none}} .rl .nav a.on{{color:var(--blue)}}
.rl .grow{{flex:1}}
.rl .toggle{{display:inline-flex;background:var(--surf2);border:1px solid var(--line);border-radius:22px;padding:3px}}
.rl .toggle a{{font-size:12.5px;font-weight:600;color:var(--soft);text-decoration:none;padding:6px 13px;border-radius:20px}}
.rl .toggle a.on{{background:var(--navy);color:#fff}}
/* sections */
.rl .sh{{display:flex;align-items:baseline;gap:14px;margin:6px 0 18px;flex-wrap:wrap}}
.rl .sh .n{{font-family:"IBM Plex Mono",monospace;font-size:12px;color:var(--brass)}}
.rl .sh h2{{font-size:clamp(21px,3vw,29px);color:var(--ink)}}
.rl .sh .d{{flex-basis:100%;color:var(--soft);font-size:14.5px;max-width:52em;margin-top:-2px}}
/* grids */
.rl .g2{{display:grid;grid-template-columns:1.05fr .95fr;gap:26px}}@media(max-width:820px){{.rl .g2{{grid-template-columns:1fr}}}}
.rl .gc{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}@media(max-width:820px){{.rl .gc{{grid-template-columns:1fr}}}}
/* verdict */
.rl .verdict{{background:linear-gradient(160deg,var(--navy),{C['navy2']});color:#fff;border-radius:18px;padding:26px 30px;
 box-shadow:0 10px 34px rgba(0,0,0,.16);border:1px solid rgba(255,255,255,.06)}}
.rl .verdict .vh{{display:flex;justify-content:space-between;align-items:flex-start;gap:12px}}
.rl .verdict .vk{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;letter-spacing:.13em;text-transform:uppercase;color:#9FC2DE}}
.rl .verdict .seal{{flex:none;white-space:nowrap;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.1em;color:#B9D5EA;border:1px solid rgba(255,255,255,.22);border-radius:20px;padding:3px 10px}}
.rl .verdict .clu{{display:flex;gap:16px 34px;flex-wrap:wrap;align-items:flex-end;margin-top:10px}}
.rl .verdict .big{{font-family:"Fraunces",serif;font-weight:600;font-size:64px;line-height:.92;color:#fff;font-variant-numeric:tabular-nums}}
.rl .verdict .big .u{{font-size:25px;color:#B9D5EA}}
.rl .verdict .nx .l{{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#9FC2DE;display:block}}
.rl .verdict .nx .v{{font-family:"Fraunces",serif;font-size:29px;font-weight:600;color:#fff;font-variant-numeric:tabular-nums}}
.rl .verdict .rev{{display:inline-block;margin-top:14px;font-size:13px;line-height:1.5;color:#DCEAF6;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);border-radius:13px;padding:5px 13px}}
.rl .verdict .rev b{{color:#F3B183}}
.rl .verdict .foot{{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-top:18px;padding-top:14px;border-top:1px solid rgba(255,255,255,.16);font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:#9FC2DE}}
/* cards */
.rl .card{{background:var(--surf);border:1px solid var(--line);border-radius:14px;padding:20px 22px;box-shadow:0 1px 2px rgba(0,0,0,.04)}}
.rl .card h3{{font-family:"Libre Franklin",sans-serif;font-weight:700;font-size:15px;color:var(--ink);margin-bottom:2px}}
.rl .card .ph{{color:var(--faint);font-size:12.5px;margin-bottom:14px}}
.rl .eco{{border-left:4px solid var(--brass)}}
.rl .eco .h{{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--brass);margin-bottom:8px}}
.rl .eco .q{{font-family:"Fraunces",serif;font-size:18.5px;line-height:1.45;color:var(--ink)}}
.rl .trust{{display:flex;gap:15px;align-items:center}}
.rl .trust .bd{{flex:none;width:44px;height:44px;border-radius:11px;background:color-mix(in srgb,var(--teal) 15%,transparent);display:flex;align-items:center;justify-content:center}}
.rl .trust .tx{{font-size:13.5px;color:var(--soft);line-height:1.5}} .rl .trust .tx b{{color:var(--ink)}}
/* driver bars */
.rl .drv{{display:grid;gap:9px}}
.rl .drv .r{{display:grid;grid-template-columns:130px 1fr 36px;gap:12px;align-items:center;font-size:13.5px;color:var(--ink)}}
.rl .drv .bar{{height:15px;border-radius:4px;background:var(--surf2);overflow:hidden}}.rl .drv .bar span{{display:block;height:100%;border-radius:4px}}
.rl .drv .v{{font-family:"IBM Plex Mono",monospace;font-size:12.5px;color:var(--soft);text-align:right}}
.rl .note{{font-size:12.5px;color:var(--faint);margin-top:12px;line-height:1.5}}
.rl .legend{{display:flex;gap:16px;flex-wrap:wrap;font-size:12.5px;color:var(--soft);margin-top:8px}}
.rl .legend i{{width:13px;height:3px;border-radius:2px;display:inline-block;vertical-align:middle;margin-right:5px}}
/* stats */
.rl .stat{{display:flex;gap:18px;flex-wrap:wrap;margin:2px 0}}.rl .stat .s{{flex:1 1 120px}}
.rl .stat .k{{font-family:"Fraunces",serif;font-size:31px;font-weight:600;color:var(--navy);font-variant-numeric:tabular-nums;line-height:1}}
.rl .stat .l{{font-size:12px;color:var(--soft);margin-top:5px}}
.rl .pill{{display:inline-block;font-family:"IBM Plex Mono",monospace;font-size:10.5px;border:1px solid var(--line);border-radius:20px;padding:2px 9px;margin:5px 5px 0 0;color:var(--soft)}}
.rl .pill.good{{color:var(--teal);border-color:color-mix(in srgb,var(--teal) 40%,var(--line))}}
.rl .peer{{display:grid;grid-template-columns:132px 1fr 42px;gap:12px;align-items:center;font-size:13.5px;margin:7px 0;color:var(--ink)}}
.rl .peer.us{{font-weight:700}} .rl .peer .bar{{height:16px;background:var(--surf2);border-radius:4px;overflow:hidden}}
.rl .peer .bar span{{display:block;height:100%;border-radius:4px;background:color-mix(in srgb,var(--blue) 55%,var(--surf))}}
.rl .peer.us .bar span{{background:var(--blue)}} .rl .peer .v{{font-family:"IBM Plex Mono",monospace;text-align:right;color:var(--soft)}}.rl .peer.us .v{{color:var(--ink)}}
/* model table */
.rl table.mt{{width:100%;border-collapse:collapse;font-size:13.5px}}
.rl table.mt th,.rl table.mt td{{padding:9px 10px;text-align:right;border-bottom:1px solid var(--line);color:var(--ink)}}
.rl table.mt th:first-child,.rl table.mt td:first-child{{text-align:left}}
.rl table.mt thead th{{font-family:"IBM Plex Mono",monospace;font-size:11px;text-transform:uppercase;letter-spacing:.04em;color:var(--faint);font-weight:500}}
.rl table.mt td:not(:first-child){{font-family:"IBM Plex Mono",monospace;font-variant-numeric:tabular-nums}}
.rl table.mt tr.hi td{{background:var(--combi);font-weight:700;color:var(--navy)}}
/* suite */
.rl .suite{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:14px}}
.rl .bc{{background:var(--surf);border:1px solid var(--line);border-radius:13px;padding:18px;position:relative}}
.rl .bc .st{{position:absolute;top:14px;right:15px;font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.05em;text-transform:uppercase;color:var(--faint);border:1px solid var(--line);border-radius:20px;padding:2px 8px}}
.rl .bc.live .st{{color:#fff;background:var(--teal);border-color:transparent}}
.rl .bc h3{{font-family:"Libre Franklin",sans-serif;font-size:16px;font-weight:700;color:var(--ink);margin-bottom:2px}}
.rl .bc .m{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--faint);margin-bottom:12px}}
.rl .bc .val{{font-family:"Fraunces",serif;font-size:26px;font-weight:600;color:var(--navy)}}.rl .bc .val.mut{{color:var(--faint);font-size:17px}}
.rl .bc .d{{font-size:12.5px;color:var(--soft);margin-top:8px;line-height:1.5}}
/* alertes */
.rl .al{{display:grid;grid-template-columns:44px 1fr;gap:15px;align-items:start;margin-bottom:12px}}
.rl .al .ic{{width:44px;height:44px;border-radius:11px;background:color-mix(in srgb,var(--blue) 14%,transparent);display:flex;align-items:center;justify-content:center}}
.rl .al .m{{font-size:14.5px;color:var(--ink)}}.rl .al .dd{{font-family:"IBM Plex Mono",monospace;font-size:11.5px;color:var(--faint);margin-top:3px}}
.rl svg{{display:block}}
.rl svg.fan{{width:100%;height:auto;aspect-ratio:460/214}}
.rl svg.i24{{width:24px;height:24px}} .rl svg.i22{{width:22px;height:22px}}
/* download button (note de comité) */
.stDownloadButton button{{border:1px solid var(--line)!important;background:var(--surf)!important;color:var(--ink)!important;border-radius:9px!important;font-weight:600!important;font-family:"Libre Franklin",sans-serif!important}}
</style>""", unsafe_allow_html=True)


# ==================================================================== barriere d'acces (optionnelle)
def app_gate():
    try:
        pw = st.secrets["app_password"]
    except Exception:
        pw = None
    if not pw or st.session_state.get("_ok"):
        return
    st.markdown(f'''<div class="rl"><div class="verdict" style="max-width:420px;margin:8vh auto">
      <div class="vk">Rexecode Live</div>
      <h1 style="color:#fff;font-size:26px;margin:.2em 0">Accès protégé</h1>
      <div style="color:#DCEAF6;font-size:14px">Saisissez le mot de passe communiqué par Rexecode.</div></div></div>''', unsafe_allow_html=True)
    c = st.columns([1, 2])[0]
    with c:
        x = st.text_input("Mot de passe", type="password", label_visibility="collapsed", placeholder="Mot de passe")
        if st.button("Entrer", type="primary"):
            if x == pw:
                st.session_state._ok = True; st.rerun()
            else:
                st.error("Mot de passe incorrect.")
    st.stop()


app_gate()


# ==================================================================== SVG helpers
def svg_fan():
    W, H, mL, mR, mT, mB = 460, 214, 34, 14, 14, 30
    iw, ih, n = W - mL - mR, H - mT - mB, len(FAN)
    yMin, yMax = -0.15, 0.85
    X = lambda i: mL + iw * i / (n - 1)
    Y = lambda v: mT + ih * (1 - (v - yMin) / (yMax - yMin))
    s = [f'<svg class="fan" viewBox="0 0 {W} {H}">']
    for g in (0, .25, .5, .75):
        y = Y(g); s.append(f'<line x1="{mL}" y1="{y:.1f}" x2="{W-mR}" y2="{y:.1f}" stroke="{C["lineS"]}"/>')
        s.append(f'<text x="{mL-5}" y="{y+3:.1f}" text-anchor="end" font-family="IBM Plex Mono" font-size="9" fill="{C["faint"]}">{g:.2f}</text>')
    up = lambda m: " ".join(f"{X(i):.1f},{Y(v+m*r):.1f}" for i,(_,v,r,_) in enumerate(FAN))
    lo = lambda m: " ".join(f"{X(i):.1f},{Y(v-m*r):.1f}" for i,(_,v,r,_) in reversed(list(enumerate(FAN))))
    s.append(f'<polygon points="{up(1.96)} {lo(1.96)}" fill="rgba({C["ic"]},0.10)"/>')
    s.append(f'<polygon points="{up(1)} {lo(1)}" fill="rgba({C["ic"]},0.22)"/>')
    s.append(f'<polyline points="{" ".join(f"{X(i):.1f},{Y(v):.1f}" for i,(_,v,_,_) in enumerate(FAN))}" fill="none" stroke="{C["blue"]}" stroke-width="2.4"/>')
    for i, (st_, v, r, k) in enumerate(FAN):
        x, y = X(i), Y(v)
        s.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{C["blue"] if k else C["surf"]}" stroke="{C["blue"]}" stroke-width="2"/>')
        s.append(f'<text x="{x:.1f}" y="{H-9}" text-anchor="middle" font-family="IBM Plex Mono" font-size="8.5" fill="{C["faint"]}">{st_}</text>')
    s.append(f'<text x="{X(3):.1f}" y="{Y(FAN[3][1])-11:.1f}" text-anchor="middle" font-family="IBM Plex Mono" font-size="10.5" fill="{C["orange"]}" font-weight="600">{frn(FAN[3][1])}</text>')
    s.append(f'<text x="{X(0)+4:.1f}" y="{Y(0.305)-11:.1f}" font-family="IBM Plex Mono" font-size="10" fill="{C["soft"]}">+0,30</text>')
    s.append("</svg>")
    return "".join(s)


def drivers_html():
    pal = [C["blue"], C["navy"], C["teal"], C["brass"], "#5A9BC8", C["orange"], C["faint"]]
    mx = max(v for _, v in DRIVERS) or 1
    rows = "".join(
        f'<div class="r"><span>{k}</span><span class="bar"><span style="width:{v/mx*100:.0f}%;background:{pal[i%len(pal)]}"></span></span><span class="v">{round(v)}%</span></div>'
        for i, (k, v) in enumerate(DRIVERS))
    return f'<div class="drv">{rows}</div>'


def peers_html():
    mx = max(v for _, v, _ in PEERS)
    out = []
    for n, v, us in PEERS:
        vv = f"{v:.2f}".replace(".", ",")
        out.append(f'<div class="peer {"us" if us else ""}"><span>{n}</span>'
                   f'<span class="bar"><span style="width:{v/mx*100:.0f}%"></span></span>'
                   f'<span class="v">{vv}</span></div>')
    return "".join(out)


SHIELD = f'<svg viewBox="0 0 24 24" fill="none" stroke="{C["teal"]}" stroke-width="1.7" class="i24"><path d="M12 3l7 3v5c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3z"/><path d="M8.5 12l2.3 2.3 4.7-4.7"/></svg>'
BELL = f'<svg viewBox="0 0 24 24" fill="none" stroke="{C["blue"]}" stroke-width="1.7" class="i22"><path d="M12 3l7 3v5c0 4.4-3 7.6-7 9-4-1.4-7-4.6-7-9V6l7-3z"/><path d="M12 8v4M12 15.5v.5"/></svg>'


# ==================================================================== top bar
def nav_link(pid, label):
    return f'<a href="?p={pid}&m={MODE}" target="_self" class="{"on" if PAGE==pid else ""}">{label}</a>'

st.markdown(f"""<div class="rl"><div class="top">
  <span class="brandwrap"><span class="brand">Rexecode <b>Live</b><span class="direct">Direct</span></span><span class="byline">par Anthony Morlet-Lavidalie</span></span>
  <nav class="nav">{nav_link("produit","Produit")}{nav_link("suite","Suite")}{nav_link("preuve","Preuve")}{nav_link("alertes","Alertes")}{nav_link("premium","Premium")}</nav>
  <span class="grow"></span>
  <span class="toggle"><a href="?p={PAGE}&m=decideur" target="_self" class="{"on" if MODE!="analyste" else ""}">Décideur</a><a href="?p={PAGE}&m=analyste" target="_self" class="{"on" if MODE=="analyste" else ""}">Analyste</a></span>
</div></div>""", unsafe_allow_html=True)


# ==================================================================== pages
def page_produit():
    st.markdown(f"""<div class="rl">
 <div class="sh"><span class="n">01 · Le verdict</span><h2>Ce qu'il faut retenir aujourd'hui</h2></div>
 <div class="g2">
  <div class="verdict">
   <div class="vh"><div class="vk">Croissance du PIB · trimestre en cours</div><span class="seal">RexNow · Rexecode</span></div>
   <div class="clu"><div class="big">{frn(T3)}<span class="u"> %</span></div>
     <div class="nx"><span class="l">Trimestre suivant</span><span class="v">{frn(T4)} %</span></div></div>
   <div class="rev">Révisé de +0,28 à <b>{frn(T3)} %</b> après l'IPI de juillet</div>
   <div class="foot"><span>T3 2026 · nowcast</span><span>Millésime : septembre 2026</span></div>
  </div>
  <div style="display:flex;flex-direction:column;gap:16px">
   <div class="card eco"><div class="h">La lecture de l'économiste — Rexecode</div>
     <div class="q">« L'activité reste sur un rythme modéré : les enquêtes tiennent, mais la baisse de la production industrielle en juillet a pesé sur le trimestre. Ni accélération, ni rupture. »</div></div>
   <div class="card trust"><div class="bd">{SHIELD}</div><div class="tx"><b>Une prévision fiable et sans biais.</b>
     Sur 24 ans, les prévisions France de Rexecode collent à la première estimation de l'INSEE (erreur moyenne 0,57 pt) avec un biais quasi nul (+0,06). <a href="?p=preuve&m={MODE}" target="_self" style="color:var(--blue);font-weight:600">Voir la preuve →</a></div></div>
  </div>
 </div>

 <div class="sh" style="margin-top:34px"><span class="n">02 · Les moteurs</span><h2>Pourquoi ce chiffre</h2>
   <span class="d">Ce qui porte l'activité, ce qui pèse, et comment la prévision s'est construite au fil des publications.</span></div>
 <div class="gc">
  <div class="card"><h3>Ce qui fait bouger le nowcast</h3><div class="ph">Contribution des grandes familles d'indicateurs</div>
    {drivers_html()}
    <div class="note">Les <b>enquêtes de conjoncture</b> et la <b>production réelle</b> portent l'essentiel du signal ; le reste joue un rôle d'appoint.</div></div>
  <div class="card"><h3>La trajectoire de la prévision · T3 2026</h3><div class="ph">Comment l'estimation s'est affinée, avec son intervalle de confiance</div>
    {svg_fan()}
    <div class="legend"><span><i style="background:{C['blue']}"></i>Prévision</span><span><i style="background:rgba({C['ic']},0.4);height:9px;border-radius:2px"></i>Intervalle de confiance</span></div>
    <div class="note">Restée proche de <b>+0,30 %</b> tant que seules les enquêtes étaient connues, la prévision a été <b>révisée à {frn(T3)} %</b> avec l'IPI de juillet (−0,8 %). L'intervalle se resserre à mesure que les données dures tombent.</div></div>
 </div>
</div>""", unsafe_allow_html=True)

    if MODE == "analyste":
        def _rrow(k):
            rm = f"{r0.get(MK[k],0):.3f}".replace(".", ",")
            hi = "hi" if k == "combi" else ""
            return (f'<tr class="{hi}"><td>{NOMS[k]}</td><td>{frn(f3.get(MK[k],0))}</td>'
                    f'<td>{frn(f4.get(MK[k],0))}</td><td>{rm}</td></tr>')
        rows = "".join(_rrow(k) for k in ["rf", "midas", "en", "combi"])
        st.markdown(f"""<div class="rl"><div class="gc" style="margin-top:18px">
   <div class="card"><h3>Le modèle en détail · RexNow</h3><div class="ph">Trois familles + combinaison · RMSE hors-échantillon</div>
     <table class="mt"><thead><tr><th>Modèle</th><th>T3</th><th>T4</th><th>RMSE test</th></tr></thead><tbody>{rows}</tbody></table>
     <div class="note">Deux modèles distincts par horizon (nowcast T, prévision T+1). Backtest temps réel 2015–2026 hors crises.</div></div>
   <div class="card"><h3>Indépendance &amp; méthode</h3><div class="ph">Construction propre à Rexecode, sources ouvertes</div>
     <p class="soft" style="font-size:14px">≈ 189 séries branchées en direct (INSEE, Banque de France, BCE, Eurostat, Douanes…), l'acquis des données dures reproduit comme l'INSEE, et une combinaison plutôt qu'un pari sur un seul modèle.</p>
     <div><span class="pill">189 séries</span><span class="pill">mise à jour auto</span><span class="pill">2 horizons</span><span class="pill">intervalle de confiance</span></div></div>
 </div></div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="rl"><div class="note" style="font-style:italic">Passez en mode <b>Analyste</b> (en haut à droite) pour le détail des modèles, les backtests et la méthodologie.</div></div>', unsafe_allow_html=True)


def page_preuve():
    rn0 = f"{r0.get('COMBI',0):.2f}".replace(".", ",")
    rn1 = f"{r1.get('COMBI',0):.2f}".replace(".", ",")
    st.markdown(f"""<div class="rl">
 <div class="sh"><span class="n">03 · La preuve</span><h2>Pourquoi y croire</h2>
   <span class="d">La crédibilité d'un institut se mesure à son historique. Celui de Rexecode est public, mesuré et vérifié.</span></div>
 <div class="gc">
  <div class="card"><h3>Un track record fiable et neutre</h3><div class="ph">Prévision d'automne pour l'année suivante · 2002–2025 · vs 1ʳᵉ estimation INSEE</div>
   <div class="stat"><div class="s"><div class="k">0,57</div><div class="l">Erreur absolue moyenne (pts)</div></div>
     <div class="s"><div class="k">+0,06</div><div class="l">Biais moyen — quasi nul</div></div>
     <div class="s"><div class="k">0,24</div><div class="l">Erreur sur l'année en cours</div></div></div>
   <div><span class="pill good">sans biais</span><span class="pill">24 années</span><span class="pill">hors Covid 2020</span></div>
   <div class="note">L'apparent « pessimisme » face au chiffre définitif est un artefact des révisions haussières de l'INSEE (non prévisibles) : face à la première estimation, Rexecode est <b>quasi sans biais</b>.</div></div>
  <div class="card"><h3>La fiabilité du nowcast en temps réel</h3><div class="ph">Erreur hors-échantillon du modèle RexNow (RMSE, points de croissance)</div>
   <div class="stat"><div class="s"><div class="k">{rn0}</div><div class="l">Nowcast du trimestre en cours</div></div>
     <div class="s"><div class="k">{rn1}</div><div class="l">Prévision du trimestre suivant</div></div></div>
   <div><span class="pill">backtest 2015–2026</span><span class="pill">hors crises</span><span class="pill">2 horizons</span></div>
   <div class="note">Deux modèles distincts par horizon, estimation harmonisée depuis 2000, testés en conditions réelles à chaque publication.</div></div>
 </div></div>""", unsafe_allow_html=True)


def page_suite():
    lab = {"live": "Direct", "pret": "Modèle prêt", "roadmap": "Roadmap"}
    cards = "".join(
        f'<div class="bc {"live" if s=="live" else ""}"><span class="st">{lab[s]}</span><h3>{n}</h3><div class="m">{m}</div>'
        f'<div class="val {"" if s=="live" else "mut"}">{v}</div></div>'
        for n, s, m, v in BAROS)
    st.markdown(f"""<div class="rl">
 <div class="sh"><span class="n">04 · La plateforme</span><h2>Rexecode Live — la suite de baromètres</h2>
   <span class="d">Le PIB n'est que le premier. Les modèles des autres baromètres existent déjà en interne, prêts à être branchés.</span></div>
 <div class="suite">{cards}</div></div>""", unsafe_allow_html=True)


def page_alertes():
    feed = [(MAJ, f"Nowcast T3 révisé à la baisse : +0,28 → {frn(T3)} % (après l'IPI de juillet)."),
            ("—", "Le flux se remplit automatiquement à chaque révision du nowcast. En production, ces alertes partent par e-mail ou Teams.")]
    items = "".join(f'<div class="card al"><div class="ic">{BELL}</div><div><div class="m">{m}</div><div class="dd">{d}</div></div></div>' for d, m in feed)
    st.markdown(f"""<div class="rl">
 <div class="sh"><span class="n">05 · Le flux d'alertes</span><h2>Quand le nowcast bouge, on le sait</h2>
   <span class="d">Ici, les alertes sont visibles en local pour valider le mécanisme.</span></div>
 <div style="max-width:640px">{items}</div></div>""", unsafe_allow_html=True)


def page_premium():
    st.markdown(f"""<div class="rl">
 <div class="sh"><span class="n">05 · Premium</span><h2>La profondeur, pour les clients &amp; adhérents</h2>
   <span class="d">Espace réservé (au-delà du verdict public) : historique complet, détail du modèle, données.
   Ici, la vue premium est ouverte pour la démonstration.</span></div></div>""", unsafe_allow_html=True)
    page_preuve()


PAGES = {"produit": page_produit, "suite": page_suite, "preuve": page_preuve, "alertes": page_alertes, "premium": page_premium}
PAGES.get(PAGE, page_produit)()

# ---- note de comité (téléchargement) ----
note = f"""<!doctype html><meta charset=utf-8><title>Note de comité — Rexecode Live</title>
<body style="font-family:Georgia,serif;max-width:640px;margin:40px auto;color:#0E1A2A">
<div style="border-left:5px solid #123A5E;padding-left:16px">
<div style="font-family:monospace;font-size:11px;letter-spacing:.1em;color:#9C7B3F">REXECODE LIVE · NOTE DE COMITÉ · {MAJ}</div>
<h1 style="font-size:26px">Croissance du PIB — {frn(T3)} % au T3 2026</h1></div>
<p>Prévision du trimestre en cours : <b>{frn(T3)} %</b> ; trimestre suivant : <b>{frn(T4)} %</b>.
Le nowcast a été révisé à la baisse (+0,28 → {frn(T3)} %) après la publication de l'IPI de juillet (−0,8 %).</p>
<p><i>« L'activité reste sur un rythme modéré : les enquêtes tiennent, mais la baisse de la production industrielle en juillet a pesé sur le trimestre. Ni accélération, ni rupture. »</i></p>
<p style="font-size:13px;color:#42546B">Prévisions Rexecode : fiables et sans biais (erreur moyenne 0,57 pt, biais +0,06 vs 1ʳᵉ estimation INSEE, 2002–2025).</p>
<p style="font-size:12px;color:#7F90A5">Modèle &amp; application : Anthony Morlet-Lavidalie — Rexecode. Chiffres à revérifier à la source.</p></body>"""
st.markdown('<div class="rl" style="margin-top:30px"></div>', unsafe_allow_html=True)
st.download_button("⎙  Télécharger la note de comité", note, file_name=f"rexecode_live_note_{MAJ.replace('/','-')}.html", mime="text/html")
st.markdown(f'<div class="rl"><div class="note" style="margin-top:20px;border-top:1px solid var(--line);padding-top:16px">'
            f'<b>Rexecode Live</b> · modèle &amp; application : <b>Anthony Morlet-Lavidalie</b>. '
            f'Thème {"sombre" if DARK else "clair"} — suit votre appareil. Sources ouvertes ; chiffres à revérifier à la source.</div></div>',
            unsafe_allow_html=True)
