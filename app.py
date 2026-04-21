"""
DouaneXtract — Base de données Douanes Tunisiennes
"""
import os, shutil, glob, base64, re
import streamlit as st
import pandas as pd
import database as db
import ocr_processor as ocr
import auth

st.set_page_config(page_title="DouaneXtract", page_icon="🛃", layout="wide")

PDF_DIR = os.path.join(os.path.dirname(__file__), "data", "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)
db.init_db()
auth.init_auth()

def load_logo():
    path = os.path.join(os.path.dirname(__file__), "logo.png")
    if os.path.exists(path):
        with open(path,"rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = load_logo()

# ══════════════════════════════════════════════════════════════════════════════
#  CSS GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.stApp { background:#f0f2f6 !important; }
section[data-testid="stMain"] .block-container {
    background:#ffffff !important; border-radius:12px;
    padding:32px 40px !important; margin-top:12px;
    box-shadow:0 1px 6px rgba(0,0,0,0.06);
}
header[data-testid="stHeader"] { background:#ffffff !important; border-bottom:1px solid #e5e7eb !important; }
section[data-testid="stSidebar"] { background:#0d1b3e !important; border-right:none !important; }
section[data-testid="stSidebar"] * { color:rgba(200,220,255,0.9) !important; }
section[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,0.1) !important; }
section[data-testid="stSidebar"] .stButton button {
    background:rgba(255,255,255,0.08) !important; border:1px solid rgba(255,255,255,0.12) !important;
    color:rgba(200,220,255,0.9) !important; border-radius:10px !important;
    font-weight:500 !important; margin-bottom:2px !important;
}
section[data-testid="stSidebar"] .stButton button:hover { background:rgba(26,86,219,0.5) !important; }
section[data-testid="stMain"] p, section[data-testid="stMain"] li { color:#374151 !important; }
section[data-testid="stMain"] h1, section[data-testid="stMain"] h2, section[data-testid="stMain"] h3 { color:#0a1628 !important; }
section[data-testid="stMain"] label { color:#374151 !important; }
section[data-testid="stMain"] span  { color:#374151 !important; }
section[data-testid="stMain"] input[type="text"], section[data-testid="stMain"] textarea {
    background:#f9fafb !important; border:1.5px solid #d1d5db !important;
    color:#111827 !important; border-radius:8px !important;
}
section[data-testid="stMain"] input[type="text"]:focus, section[data-testid="stMain"] textarea:focus {
    border-color:#1a56db !important; box-shadow:0 0 0 3px rgba(26,86,219,0.1) !important;
}
section[data-testid="stMain"] .stButton button[kind="primary"],
section[data-testid="stMain"] .stFormSubmitButton button {
    background:#1a56db !important; color:white !important; border:none !important;
    border-radius:8px !important; font-weight:600 !important;
}
section[data-testid="stMain"] .stButton button[kind="primary"]:hover,
section[data-testid="stMain"] .stFormSubmitButton button:hover { background:#1e40af !important; }
section[data-testid="stMain"] .stButton button {
    background:#f3f4f6 !important; border:1px solid #d1d5db !important;
    color:#374151 !important; border-radius:8px !important;
}
section[data-testid="stMain"] .stTabs [data-baseweb="tab-list"] { background:#f3f4f6 !important; border-radius:8px; padding:3px; }
section[data-testid="stMain"] .stTabs [data-baseweb="tab"] { color:#6b7280 !important; }
section[data-testid="stMain"] .stTabs [aria-selected="true"] { color:#1a56db !important; background:#ffffff !important; border-radius:6px !important; }
section[data-testid="stMain"] .stRadio label span { color:#374151 !important; }
section[data-testid="stMain"] .streamlit-expanderHeader { background:#f9fafb !important; border:1px solid #e5e7eb !important; color:#374151 !important; border-radius:8px !important; }
section[data-testid="stMain"] .streamlit-expanderContent { background:#ffffff !important; border:1px solid #e5e7eb !important; }
section[data-testid="stMain"] [data-testid="stMetricLabel"] { color:#6b7280 !important; }
section[data-testid="stMain"] [data-testid="stMetricValue"] { color:#1a56db !important; font-weight:700 !important; }
section[data-testid="stMain"] .stSuccess { background:#f0fdf4 !important; border-left-color:#16a34a !important; }
section[data-testid="stMain"] .stError   { background:#fef2f2 !important; border-left-color:#dc2626 !important; }
section[data-testid="stMain"] .stInfo    { background:#eff6ff !important; border-left-color:#2563eb !important; }
section[data-testid="stMain"] .stWarning { background:#fffbeb !important; border-left-color:#d97706 !important; }
section[data-testid="stMain"] .stProgress > div > div { background:#1a56db !important; }
section[data-testid="stMain"] .stDataFrame { border:1px solid #e5e7eb !important; border-radius:8px !important; }
section[data-testid="stMain"] hr { border-color:#e5e7eb !important; }
.module-card { background:#ffffff !important; border:1.5px solid #e2e8f0 !important; border-radius:14px; padding:28px; text-align:center; box-shadow:0 2px 8px rgba(0,0,0,0.05); }
.module-icon  { font-size:2.8rem; margin-bottom:10px; }
.module-title { font-size:1.05rem; font-weight:700; color:#0a1628 !important; margin-bottom:6px; }
.module-desc  { font-size:0.78rem; color:#6b7280 !important; margin-bottom:14px; }
.module-count { font-size:2rem; font-weight:800; color:#1a56db !important; }
.module-label { font-size:0.72rem; color:#9ca3af !important; }
.result-card  { background:#f9fafb !important; border:1px solid #e5e7eb !important; border-radius:10px; padding:14px; margin-bottom:8px; }
.badge        { background:#1a56db; color:white !important; border-radius:4px; padding:2px 8px; font-size:0.82rem; font-weight:600; }
.badge-green  { background:#dcfce7; border:1px solid #86efac; color:#15803d !important; border-radius:4px; padding:2px 8px; font-size:0.82rem; }
.badge-purple { background:#ede9fe; border:1px solid #c4b5fd; color:#6d28d9 !important; border-radius:4px; padding:2px 8px; font-size:0.82rem; }
.badge-blue   { background:#dbeafe; border:1px solid #93c5fd; color:#1d4ed8 !important; border-radius:4px; padding:2px 8px; font-size:0.75rem; font-weight:600; margin:2px 2px 2px 0; display:inline-block; }
.badge-hs     { background:#ede9fe; border:2px solid #7c3aed; color:#5b21b6 !important; border-radius:6px; padding:4px 12px; font-size:0.88rem; font-weight:800; letter-spacing:0.5px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def show_login():
    import base64 as _b64, os as _os

    _logo_path = _os.path.join(_os.path.dirname(__file__), "logo.png")
    _logo_b64 = ""
    if _os.path.exists(_logo_path):
        with open(_logo_path, "rb") as _f:
            _logo_b64 = _b64.b64encode(_f.read()).decode()

    _logo_css = (
        f"background-image: url('data:image/png;base64,{_logo_b64}') !important;"
        if _logo_b64 else
        "background: linear-gradient(135deg,#0a1628,#1a3a6e) !important;"
    )

    st.markdown(f"""
    <style>
    .stApp {{
        {_logo_css}
        background-size: cover !important;
        background-position: center top !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
        min-height: 100vh !important;
    }}
    section[data-testid="stMain"] .block-container {{
        background: transparent !important;
        box-shadow: none !important;
        border-radius: 0 !important;
        padding: 0 !important;
        max-width: 100% !important;
        margin: 0 !important;
    }}
    header[data-testid="stHeader"]   {{ display:none !important; }}
    section[data-testid="stSidebar"] {{ display:none !important; }}
    #MainMenu, footer                 {{ display:none !important; }}
    section[data-testid="stMain"] [data-testid="stForm"] {{
        background: rgba(255, 255, 255, 0.25) !important;
        border-radius: 20px !important;
        padding: 28px 28px 20px 28px !important;
        border: 1px solid rgba(255,255,255,0.7) !important;
        box-shadow: 0 8px 40px rgba(0,0,0,0.22) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
    }}
    section[data-testid="stMain"] label {{
        color: #ffffff !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
    }}
    section[data-testid="stMain"] input[type="text"],
    section[data-testid="stMain"] input[type="password"] {{
        background: rgba(255,255,255,0.98) !important;
        border: 1.5px solid rgba(180,200,230,0.8) !important;
        color: #1a2f50 !important;
        border-radius: 10px !important;
        padding: 14px 16px !important;
        font-size: 1rem !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
    }}
    section[data-testid="stMain"] input::placeholder {{ color: #a0aec0 !important; }}
    section[data-testid="stMain"] input:focus {{
        border-color: #2563eb !important;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.15) !important;
    }}
    section[data-testid="stMain"] .stFormSubmitButton button {{
        background: linear-gradient(180deg,#3b7dd8 0%,#1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 13px !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 16px rgba(29,78,216,0.45) !important;
    }}
    section[data-testid="stMain"] .stFormSubmitButton button:hover {{
        background: linear-gradient(180deg,#4a8fe8 0%,#2563eb 100%) !important;
    }}
    section[data-testid="stMain"] .stError {{
        background: rgba(254,242,242,0.95) !important;
        border-radius: 8px !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:80px'></div>", unsafe_allow_html=True)
    _, _col, _ = st.columns([1, 1.3, 1])

    with _col:
        with st.form("login_form"):
            st.markdown(
                '<div style="padding:8px 0 18px;text-align:center;">'
                '<div style="font-size:2rem;font-weight:900;margin-bottom:4px;">'
                '<span style="color:#ffffff;">Douane</span>'
                '<span style="color:#93c5fd;">Xtract</span>'
                '</div>'
                '<div style="font-size:0.85rem;color:rgba(255,255,255,0.85);margin-bottom:4px;">'
                'Base de données Douanes Tunisiennes'
                '</div>'
                '<hr style="border:none;border-top:1px solid rgba(255,255,255,0.3);margin:12px 0 4px;">'
                '</div>',
                unsafe_allow_html=True)

            _email    = st.text_input("Adresse e-mail", placeholder="✉  user@email.com")
            _password = st.text_input("Mot de passe",   placeholder="🔒  ••••••••", type="password")

            st.markdown(
                '<div style="text-align:right;margin:-4px 0 16px;">'
                '<span style="color:rgba(255,255,255,0.9);font-size:0.82rem;cursor:pointer;">'
                'Mot de passe oublié ?</span></div>',
                unsafe_allow_html=True)

            _submit = st.form_submit_button("Se connecter", use_container_width=True)

        st.markdown(
            '<div style="text-align:center;margin-top:20px;">'
            '<span style="color:rgba(255,255,255,0.85);font-size:0.72rem;'
            'text-shadow:0 1px 6px rgba(0,0,0,0.5);">'
            '<b style="color:white;">DouaneXtract</b> v1.0 &nbsp;·&nbsp; '
            'Direction Générale des Douanes Tunisiennes'
            '</span></div>',
            unsafe_allow_html=True)

    if _submit:
        if not _email or not _password:
            st.error("⚠️ Veuillez remplir tous les champs.")
        else:
            _user = auth.login(_email, _password)
            if _user:
                st.session_state["user"] = _user
                st.rerun()
            else:
                st.error("❌ Email ou mot de passe incorrect.")


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION
# ══════════════════════════════════════════════════════════════════════════════
if "user" not in st.session_state:
    show_login(); st.stop()

user     = st.session_state["user"]
is_admin = user["role"] == "admin"
stats    = db.get_stats()

if "module" not in st.session_state:
    st.session_state["module"] = "dashboard"
module = st.session_state["module"]


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(
        '<div style="padding:24px 16px 8px;text-align:center;">'
        '<div style="font-size:1.6rem;font-weight:900;margin-bottom:2px;">'
        '<span style="color:#fff;">Douane</span><span style="color:#60a5fa;">Xtract</span></div>'
        '<div style="font-size:0.68rem;color:rgba(148,163,184,0.8);">Base de données Douanes</div>'
        '</div>', unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:12px 0;'>", unsafe_allow_html=True)

    def nav_btn(label, key):
        if st.button(label, use_container_width=True, key="nav_"+key):
            st.session_state["module"] = key; st.rerun()

    nav_btn("🏠  Tableau de bord",  "dashboard")
    nav_btn("📋  Avis Tarifaires",  "tarifaires")
    nav_btn("📁  Secrétariat",      "secretariat")
    nav_btn("🌐  Décisions OMD",    "omd")
    nav_btn("📑  Avis Tarés",       "avis_tares")
    if is_admin:
        nav_btn("👥  Utilisateurs", "users")

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:16px 0 12px;'>", unsafe_allow_html=True)
    if st.button("🚪  Se déconnecter", use_container_width=True, key="nav_logout"):
        del st.session_state["user"]
        st.session_state["module"] = "dashboard"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD — 4 cartes
# ══════════════════════════════════════════════════════════════════════════════
if module == "dashboard":
    st.markdown(f"<h1 style='margin-bottom:4px;'>Bonjour, {user['nom']} 👋</h1>", unsafe_allow_html=True)
    st.caption("Que souhaitez-vous consulter aujourd'hui ?")

    c1, c2, c3, c4 = st.columns(4)
    for col, icon, title, desc, key, cnt in [
        (c1, "📋", "Avis Tarifaires",  "Documents PDF scannés",                   "tarifaires",  stats['tarifaires']),
        (c2, "📁", "Secrétariat",      "Correspondances et avis",                  "secretariat", stats['secretariat']),
        (c3, "🌐", "Décisions OMD",    "Organisation Mondiale des Douanes",         "omd",         stats['omd']),
        (c4, "📑", "Avis Tarés",       "Recueils tarifaires par chapitre SH",       "avis_tares",  stats['avis_tares']),
    ]:
        with col:
            st.markdown(
                '<div class="module-card">'
                '<div class="module-icon">' + icon + '</div>'
                '<div class="module-title">' + title + '</div>'
                '<div class="module-desc">' + desc + '</div>'
                '<div class="module-count">' + str(cnt) + '</div>'
                '<div class="module-label">documents indexés</div>'
                '</div>', unsafe_allow_html=True)
            if st.button("Accéder →", key="btn_"+key, use_container_width=True):
                st.session_state["module"] = key; st.rerun()

    st.markdown("---")
    st.markdown("### Statistiques")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("📋 Avis Tarifaires", stats['tarifaires'])
    s2.metric("📁 Secrétariat",     stats['secretariat'])
    s3.metric("🌐 Décisions OMD",   stats['omd'])
    s4.metric("📑 Avis Tarés",      stats['avis_tares'])
    s5.metric("📊 Total",           stats['total'])

    st.markdown("---")
    st.markdown("### 🕐 Derniers documents ajoutés")
    t1, t2, t3, t4 = st.tabs(["📋 Tarifaires", "📁 Secrétariat", "🌐 OMD", "📑 Avis Tarés"])

    with t1:
        docs = db.get_all_documents()[:5]
        if not docs: st.info("Aucun document.")
        else:
            for d in docs:
                st.markdown(
                    '<div class="result-card"><b>📄 ' + d['filename'] + '</b> &nbsp;'
                    '<span class="badge">' + (d.get('tarif_number') or '?') + '</span>'
                    '<span style="float:right;color:#6b7280;font-size:0.78rem">' + d.get('upload_date','')[:10] + '</span><br>'
                    '<small style="color:#6b7280">N° ' + (d.get('numero_avis') or '—') + ' · NDP ' + (d.get('ndp') or '—') + '</small></div>',
                    unsafe_allow_html=True)
    with t2:
        docs = db.get_all_secretariat()[:5]
        if not docs: st.info("Aucun document.")
        else:
            for d in docs:
                st.markdown(
                    '<div class="result-card"><b>' + (d.get('numero_lettre') or d.get('filename','')) + '</b>'
                    '<span style="float:right;color:#6b7280;font-size:0.78rem">' + d.get('upload_date','')[:10] + '</span><br>'
                    '<small style="color:#6b7280">' + (d.get('desc_fr') or '')[:80] + '</small></div>',
                    unsafe_allow_html=True)
    with t3:
        docs = db.get_all_omd()[:5]
        if not docs: st.info("Aucun document.")
        else:
            for d in docs:
                st.markdown(
                    '<div class="result-card"><span class="badge-purple">' + (d.get('classement') or '?') + '</span>'
                    '<span style="float:right;color:#6b7280;font-size:0.78rem">' + d.get('upload_date','')[:10] + '</span><br>'
                    '<small style="color:#6b7280">' + (d.get('description') or '')[:80] + '</small></div>',
                    unsafe_allow_html=True)
    with t4:
        docs = db.get_all_avis_tares()[:5]
        if not docs: st.info("Aucun document.")
        else:
            for d in docs:
                st.markdown(
                    '<div class="result-card"><span class="badge-hs">' + (d.get('hs_code') or '?') + '</span>'
                    '<span style="float:right;color:#6b7280;font-size:0.78rem">' + d.get('upload_date','')[:10] + '</span><br>'
                    '<b style="color:#0a1628;font-size:0.9rem;">' + (d.get('nom') or '—') + '</b><br>'
                    '<small style="color:#6b7280">' + (d.get('description') or '')[:80] + '</small></div>',
                    unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — AVIS TARIFAIRES
# ══════════════════════════════════════════════════════════════════════════════
elif module == "tarifaires":
    st.markdown("## 📋 Avis Tarifaires")
    st.caption("Documents PDF scannés — Classement tarifaire douanier")
    st.markdown("---")

    page = st.radio("", ["🔍 Recherche","📤 Ajouter","✏️ Modifier"],
                    horizontal=True, label_visibility="collapsed")

    if page == "📤 Ajouter":
        st.subheader("📤 Ajouter des PDFs")
        files = st.file_uploader("Glissez vos PDFs ici", type=["pdf"], accept_multiple_files=True)
        if files:
            st.markdown(f"**{len(files)} fichier(s) sélectionné(s)**")
            if st.button("🚀 Lancer l'extraction OCR", type="primary"):
                existing   = {d["filename"] for d in db.get_all_documents()}
                to_process = [f for f in files if f.name not in existing]
                skipped    = [f.name for f in files if f.name in existing]
                if skipped: st.warning(f"⟳ Déjà en base : {', '.join(skipped)}")
                progress = st.progress(0); status = st.empty(); doc_id = None
                for i, f in enumerate(to_process):
                    status.info(f"⏳ {f.name} ({i+1}/{len(to_process)})")
                    dest = os.path.join(PDF_DIR, f.name)
                    with open(dest,"wb") as fp: fp.write(f.getbuffer())
                    data = ocr.process_pdf(dest, f.name)
                    doc_id = db.insert_document(data)
                    progress.progress((i+1)/len(to_process))
                if to_process:
                    status.success(f"✅ {len(to_process)} document(s) ajouté(s) !")
                    if doc_id:
                        doc = db.get_document_by_id(doc_id)
                        a, b, c = st.columns(3)
                        a.metric("N° Avis",      doc.get("numero_avis")  or "Non détecté")
                        b.metric("N° Tarifaire", doc.get("tarif_number") or "Non détecté")
                        c.metric("NDP",          doc.get("ndp")          or "Non détecté")
                        with st.expander("📄 Texte OCR complet"):
                            st.text(doc.get("full_text","")[:4000])

    elif page == "🔍 Recherche":
        st.subheader("🔍 Recherche")
        cq, cb = st.columns([4,1])
        with cq:
            query = st.text_input("q", placeholder="Mot-clé, désignation, N° avis…", label_visibility="collapsed")
        with cb:
            rechercher = st.button("Rechercher", type="primary", use_container_width=True)

        with st.expander("🔧 Filtres par champ", expanded=True):
            f1, f2, f3 = st.columns(3)
            filter_avis  = f1.text_input("🔵 N° Avis",       placeholder="ex: 2206755")
            filter_ndp   = f2.text_input("🟢 NDP (partiel)", placeholder="ex: 94, 9405, 94054010099")
            filter_tarif = f3.text_input("🟡 N° Tarifaire",  placeholder="ex: 940540")

        if query or filter_avis or filter_ndp or filter_tarif or rechercher:
            results = db.search_documents(query) if query else db.get_all_documents()
            if filter_avis.strip():  results = [r for r in results if filter_avis.strip()  in (r.get("numero_avis")  or "")]
            if filter_ndp.strip():   results = [r for r in results if filter_ndp.strip()   in (r.get("ndp")          or "")]
            if filter_tarif.strip(): results = [r for r in results if filter_tarif.strip() in (r.get("tarif_number") or "")]

            nb = len(results)
            if nb == 0:
                st.warning("🔍 Aucun document trouvé.")
            else:
                st.markdown(
                    '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;'
                    'padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">'
                    '<span style="font-size:1.4rem;font-weight:800;color:#1a56db;">' + str(nb) + '</span>'
                    '<span style="color:#374151;font-size:0.9rem;">document(s) trouvé(s)</span>'
                    '</div>', unsafe_allow_html=True)

                for doc in results:
                    ndp_val   = doc.get("ndp")          or "—"
                    avis_val  = doc.get("numero_avis")  or "—"
                    tarif_val = doc.get("tarif_number") or "—"
                    desig_val = doc.get("designation")  or "—"
                    usage_val = doc.get("usage_text")   or "—"
                    date_val  = doc.get("upload_date","")[:10]
                    usage_short = usage_val[:120] + ("…" if len(usage_val)>120 else "")

                    ndp_display = ndp_val
                    if filter_ndp.strip() and filter_ndp.strip() in ndp_val:
                        ndp_display = ndp_val.replace(filter_ndp.strip(),
                            '<span style="background:#bbf7d0;border-radius:3px;padding:0 2px;">' + filter_ndp.strip() + '</span>')

                    card = (
                        '<div style="background:#ffffff;border:1.5px solid #e2e8f0;border-radius:12px;'
                        'padding:16px 20px;margin-bottom:12px;box-shadow:0 1px 6px rgba(0,0,0,0.05);">'
                        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
                        '<span style="font-size:0.85rem;font-weight:700;color:#0a1628;">📄 ' + doc['filename'] + '</span>'
                        '<span style="color:#9ca3af;font-size:0.75rem;">' + date_val + '</span>'
                        '</div>'
                        '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:10px;">'
                        '<div style="background:#ffffff;border:1.5px solid #e2e8f0;border-radius:8px;padding:10px;">'
                        '<div style="color:#9ca3af;font-size:0.62rem;letter-spacing:0.5px;margin-bottom:3px;">N° AVIS</div>'
                        '<div style="color:#1a56db;font-weight:700;font-size:0.95rem;">' + avis_val + '</div>'
                        '</div>'
                        '<div style="background:#ffffff;border:1.5px solid #e2e8f0;border-radius:8px;padding:10px;">'
                        '<div style="color:#9ca3af;font-size:0.62rem;letter-spacing:0.5px;margin-bottom:3px;">NDP</div>'
                        '<div style="color:#059669;font-weight:700;font-size:0.95rem;">' + ndp_display + '</div>'
                        '</div>'
                        '<div style="background:#ffffff;border:1.5px solid #e2e8f0;border-radius:8px;padding:10px;">'
                        '<div style="color:#9ca3af;font-size:0.62rem;letter-spacing:0.5px;margin-bottom:3px;">N° TARIFAIRE</div>'
                        '<div style="color:#d97706;font-weight:700;font-size:0.95rem;">' + tarif_val + '</div>'
                        '</div>'
                        '</div>'
                        '<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;'
                        'padding:8px 12px;margin-bottom:10px;">'
                        '<span style="color:#0369a1;font-size:0.68rem;font-weight:700;letter-spacing:0.5px;">POUR LE CLASSEMENT TARIFAIRE :</span>'
                        '<span style="color:#1e3a5f;font-size:0.85rem;">' + usage_short + '</span>'
                        '</div>'
                        '<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;'
                        'padding:8px 12px;margin-bottom:10px;">'
                        '<span style="color:#0369a1;font-size:0.68rem;font-weight:700;letter-spacing:0.5px;">DÉSIGNATION :</span>'
                        '<span style="color:#1e3a5f;font-size:0.85rem;">' + desig_val[:100] + ('…' if len(desig_val)>100 else '') + '</span>'
                        '</div>'
                        '</div>'
                    )
                    st.markdown(card, unsafe_allow_html=True)
                    with st.expander("📄 Voir texte OCR complet"):
                        st.text(doc.get("full_text","")[:3000])

    elif page == "✏️ Modifier":
        st.subheader("✏️ Modifier / Supprimer")
        docs = db.get_all_documents()
        if not docs: st.info("Aucun document disponible.")
        else:
            opts = {f"[{d['id']}] {d['filename']}": d['id'] for d in docs}
            sel  = st.selectbox("Choisir un document", list(opts.keys()))
            doc  = db.get_document_by_id(opts[sel])
            tab_e, tab_o, tab_d = st.tabs(["✏️ Modifier","📄 OCR","🗑️ Supprimer"])
            with tab_e:
                with st.form("edit_tar"):
                    c1, c2, c3 = st.columns(3)
                    na = c1.text_input("N° Avis",      value=doc.get("numero_avis")  or "")
                    tn = c2.text_input("N° Tarifaire", value=doc.get("tarif_number") or "")
                    nd = c3.text_input("NDP",          value=doc.get("ndp")          or "")
                    de = st.text_area("Désignation",   value=doc.get("designation")  or "", height=60)
                    us = st.text_area("Pour le classement tarifaire", value=doc.get("usage_text") or "", height=80)
                    if st.form_submit_button("💾 Enregistrer", type="primary"):
                        db.update_document(opts[sel],{"numero_avis":na,"designation":de,"usage_text":us,"tarif_number":tn,"ndp":nd})
                        st.success("✅ Mis à jour !"); st.rerun()
            with tab_o: st.text_area("Texte OCR", value=doc.get("full_text") or "", height=400)
            with tab_d:
                st.warning(f"⚠️ Supprimer **{doc['filename']}** ?")
                if st.checkbox("Je confirme"):
                    if st.button("🗑️ Supprimer", type="primary"):
                        db.delete_document(opts[sel]); st.success("Supprimé."); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — SECRETARIAT
# ══════════════════════════════════════════════════════════════════════════════
elif module == "secretariat":
    st.markdown("## 📁 Secrétariat")
    st.caption("Documents et fichiers relatifs au Secrétariat")
    st.markdown("---")

    page = st.radio("", ["🔍 Recherche", "📤 Ajouter fichier xlsx", "✏️ Modifier"],
                    horizontal=True, label_visibility="collapsed")

    if page == "🔍 Recherche":
        st.markdown("<h2 style='color:#0a1628;font-size:1.65rem;font-weight:800;margin-bottom:4px;'>Recherche par Numéro de Lettre</h2>", unsafe_allow_html=True)
        st.caption("Entrez le numéro de lettre pour afficher les informations correspondantes.")

        total = len(db.get_all_secretariat())
        if total > 0:
            st.info(f"ℹ️ Base de données : **{total:,}** entrées disponibles")

        col_inp, col_btn = st.columns([4, 1])
        with col_inp:
            num_lettre = st.text_input("nl", placeholder="ex: L10642A, L106, L10...",
                                       label_visibility="collapsed", key="sec_search")
        with col_btn:
            rechercher = st.button("🔍  Rechercher", type="primary", use_container_width=True)

        if (rechercher or num_lettre) and len(num_lettre.strip()) >= 2:
            q = num_lettre.strip().upper()
            results = db.search_secretariat_by_lettre(q)
            nb = len(results)
            st.markdown("### Résultat")

            if nb == 0:
                st.error(f"❌ Aucun résultat pour : **{q}**")
            else:
                st.success(f"✅ **{nb}** résultat(s) pour : **{q}**")
                for doc in results:
                    num_val  = doc.get("numero_lettre") or "—"
                    date_val = doc.get("date_avis")     or "—"
                    hs_val   = doc.get("hs_code")       or "—"
                    desc_fr  = doc.get("desc_fr")       or "—"

                    idx = num_val.upper().find(q)
                    if idx >= 0:
                        num_display = (num_val[:idx] +
                            '<span style="background:#dbeafe;border-radius:3px;padding:0 2px;font-weight:800;color:#1d4ed8;">' +
                            num_val[idx:idx+len(q)] + '</span>' + num_val[idx+len(q):])
                    else:
                        num_display = num_val

                    card = (
                        '<div style="background:#ffffff;border:1.5px solid #e2e8f0;border-radius:14px;'
                        'overflow:hidden;margin-bottom:20px;box-shadow:0 2px 10px rgba(0,0,0,0.06);">'
                        '<div style="display:grid;grid-template-columns:1fr 1px 1fr 1px 1fr;background:#f8fafc;border-bottom:1.5px solid #e2e8f0;">'
                        '<div style="padding:16px 22px;"><div style="color:#9ca3af;font-size:0.62rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">NUMÉRO DE LETTRE</div>'
                        '<div style="color:#1a56db;font-weight:800;font-size:1.2rem;">' + num_display + '</div></div>'
                        '<div style="background:#e2e8f0;"></div>'
                        '<div style="padding:16px 22px;"><div style="color:#9ca3af;font-size:0.62rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">📅 DATE</div>'
                        '<div style="color:#111827;font-weight:700;font-size:1.05rem;">📅 ' + date_val + '</div></div>'
                        '<div style="background:#e2e8f0;"></div>'
                        '<div style="padding:16px 22px;"><div style="color:#9ca3af;font-size:0.62rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:6px;">🏷 HS CODE</div>'
                        '<div style="color:#111827;font-weight:700;font-size:1.05rem;">🏷 ' + hs_val + '</div></div>'
                        '</div>'
                        '<div style="padding:18px 22px;">'
                        '<div style="color:#9ca3af;font-size:0.62rem;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px;">DESCRIPTION EN FRANÇAIS</div>'
                        '<div style="background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:14px 18px;color:#374151;font-size:0.875rem;line-height:1.7;">' + desc_fr + '</div>'
                        '</div></div>'
                    )
                    st.markdown(card, unsafe_allow_html=True)

                _, bc2, bc3 = st.columns([2, 1, 1])
                with bc2:
                    import pandas as _pd
                    df_exp = _pd.DataFrame(results)[['numero_lettre','date_avis','hs_code','desc_fr']]
                    df_exp.columns = ['N° Lettre','Date','HS Code','Description FR']
                    csv_data = df_exp.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                    st.download_button("⬇️ Exporter", data=csv_data, file_name=f"secretariat_{q}.csv", mime="text/csv", use_container_width=True)
                with bc3:
                    if st.button("↺ Nouvelle recherche", use_container_width=True, key="sec_new"): st.rerun()

        elif num_lettre and len(num_lettre.strip()) < 2:
            st.info("✏️ Entrez au moins 2 caractères.")
        elif total == 0:
            st.warning("⚠️ Aucune donnée. Ajoutez un fichier via 'Ajouter fichier xlsx'.")

    elif page == "📤 Ajouter fichier xlsx":
        st.markdown("<h2 style='color:#0a1628;'>📤 Ajouter un fichier Excel</h2>", unsafe_allow_html=True)
        st.markdown("---")
        st.info("**Colonnes requises :** LETTER NUMBER · DATE · HS CODE · DESCRIPTION EN FRANCAIS")
        uploaded = st.file_uploader("Glisser votre fichier Excel (.xlsx)", type=["xlsx","xls"])
        if uploaded:
            import pandas as _pd
            try:
                df = _pd.read_excel(uploaded)
                df = df[df['LETTER NUMBER'].notna() & ~df['LETTER NUMBER'].astype(str).str.contains('This information', na=False)].reset_index(drop=True)
                required = ['LETTER NUMBER','DATE','HS CODE','DESCRIPTION EN FRANCAIS']
                missing  = [c for c in required if c not in df.columns]
                if missing:
                    st.error(f"❌ Colonnes manquantes : {missing}")
                else:
                    st.success(f"✅ Fichier valide — **{len(df):,}** lignes")
                    st.dataframe(df.head(5)[['LETTER NUMBER','DATE','HS CODE','DESCRIPTION EN FRANCAIS']], use_container_width=True, hide_index=True)
                    skip_existing = st.checkbox("Ignorer les numéros déjà en base", value=True)
                    if st.button("🚀 Importer dans la base", type="primary"):
                        existing_nums = {r["numero_lettre"] for r in db.get_all_secretariat()}
                        progress = st.progress(0); status = st.empty(); ok_count = skipped = 0
                        for i, row in df.iterrows():
                            num = str(row.get('LETTER NUMBER','')).strip()
                            if skip_existing and num in existing_nums:
                                skipped += 1
                            else:
                                db.insert_secretariat({
                                    "filename": uploaded.name, "numero_lettre": num,
                                    "date_avis": str(row.get('DATE','')) if _pd.notna(row.get('DATE')) else "",
                                    "hs_code":   str(row.get('HS CODE','')) if _pd.notna(row.get('HS CODE')) else "",
                                    "desc_fr":   str(row.get('DESCRIPTION EN FRANCAIS','')) if _pd.notna(row.get('DESCRIPTION EN FRANCAIS')) else "",
                                    "desc_en":   str(row.get('DESCRIPTION IN ENGLISH','')) if _pd.notna(row.get('DESCRIPTION IN ENGLISH')) else "",
                                })
                                existing_nums.add(num); ok_count += 1
                            progress.progress(min((i+1)/len(df), 1.0))
                        status.success(f"✅ {ok_count} ajoutés · {skipped} ignorés")
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur : {e}")

    elif page == "✏️ Modifier":
        st.markdown("<h2 style='color:#0a1628;'>✏️ Modifier / Supprimer</h2>", unsafe_allow_html=True)
        st.markdown("---")
        docs = db.get_all_secretariat()
        if not docs: st.info("Aucun document disponible.")
        else:
            q_mod = st.text_input("Rechercher un numéro de lettre", placeholder="ex: L10642A")
            if q_mod: docs = [d for d in docs if q_mod.upper() in (d.get("numero_lettre") or "").upper()]
            if not docs: st.warning("Aucun résultat.")
            else:
                opts = {f"[{d['id']}] {d.get('numero_lettre','')} — {d.get('date_avis','')}": d['id'] for d in docs}
                sel  = st.selectbox("Choisir une entrée", list(opts.keys()))
                doc  = db.get_secretariat_by_id(opts[sel])
                tab_e, tab_d = st.tabs(["✏️ Modifier","🗑️ Supprimer"])
                with tab_e:
                    with st.form("edit_sec"):
                        c1, c2, c3 = st.columns(3)
                        nl = c1.text_input("N° Lettre", value=doc.get("numero_lettre") or "")
                        da = c2.text_input("Date",      value=doc.get("date_avis")     or "")
                        hs = c3.text_input("HS Code",   value=doc.get("hs_code")       or "")
                        df_fr = st.text_area("Description FR", value=doc.get("desc_fr") or "", height=100)
                        if st.form_submit_button("💾 Enregistrer", type="primary"):
                            db.update_secretariat(opts[sel],{"numero_lettre":nl,"date_avis":da,"hs_code":hs,"desc_fr":df_fr,"desc_en":doc.get("desc_en","")})
                            st.success("✅ Mis à jour !"); st.rerun()
                with tab_d:
                    st.warning(f"⚠️ Supprimer **{doc.get('numero_lettre')}** ?")
                    if st.checkbox("Je confirme"):
                        if st.button("🗑️ Supprimer", type="primary"):
                            db.delete_secretariat(opts[sel]); st.success("Supprimé."); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 3 — DECISIONS OMD
# ══════════════════════════════════════════════════════════════════════════════
elif module == "omd":
    st.markdown("## 🌐 Décisions OMD")
    st.caption("Textes officiels et décisions de l'OMD")
    st.markdown("---")

    page = st.radio("", ["🔍 Recherche", "📤 Ajouter", "✏️ Modifier"],
                    horizontal=True, label_visibility="collapsed")

    total_omd = len(db.get_all_omd())

    if page == "🔍 Recherche":
        st.markdown("<h2 style='color:#0a1628;font-size:1.65rem;font-weight:800;margin-bottom:4px;'>Recherche — Décisions OMD</h2>", unsafe_allow_html=True)
        st.caption("Recherchez par code de classement (partiel ou complet) ou description.")

        if total_omd > 0:
            st.info(f"ℹ️ Base de données : **{total_omd:,}** décisions disponibles")

        col_inp, col_btn = st.columns([4, 1])
        with col_inp:
            q_class = st.text_input("cl", placeholder="ex: 17  ou  17.04  ou  19.05  ou  8471...",
                                    label_visibility="collapsed", key="omd_search")
        with col_btn:
            rechercher = st.button("🔍  Rechercher", type="primary", use_container_width=True)

        with st.expander("🔧 Recherche dans la description"):
            q_desc = st.text_input("Description contient", placeholder="ex: sucreries, bacon, véhicule...", key="omd_desc")

        if (rechercher or q_class or q_desc) and total_omd > 0:
            results = db.get_all_omd()
            if q_class.strip(): results = [r for r in results if q_class.strip() in (r.get("classement") or "")]
            if q_desc.strip():  results = [r for r in results if q_desc.strip().lower() in (r.get("description") or "").lower()]
            nb = len(results)

            if nb == 0:
                st.error("❌ Aucune décision trouvée.")
            else:
                st.success(f"✅ **{nb}** décision(s) trouvée(s)")
                for doc in results:
                    clas  = doc.get("classement")  or "—"
                    desc  = doc.get("description") or "—"
                    sess  = doc.get("session")     or "—"
                    motif = doc.get("motif")       or ""

                    if not desc or desc in ('—','nan','None',''):
                        desc = '(description non disponible — veuillez réimporter ce PDF)'
                    words   = desc.strip().split(" ")
                    first_w = words[0] if words else ""
                    rest_d  = desc[len(first_w):]
                    short   = (first_w + rest_d)[:120] + ("…" if len(desc)>120 else "")

                    card = (
                        '<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;'
                        'padding:18px 22px;margin-bottom:14px;box-shadow:0 1px 6px rgba(0,0,0,0.05);">'
                        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">'
                        '<div style="width:34px;height:34px;background:#fef3c7;border:1px solid #fcd34d;'
                        'border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:17px;">📁</div>'
                        '<div style="font-size:1rem;font-weight:600;color:#1a1a1a;">'
                        'Classement : <span style="color:#d97706;font-weight:700;">' + clas + '</span>'
                        '</div>'
                        '</div>'
                        '<div style="color:#374151;font-size:0.85rem;">'
                        '<b>Session</b> : <em>' + sess + '</em>'
                        '</div>'
                        '</div>'
                    )
                    st.markdown(card, unsafe_allow_html=True)
                    if len(desc) > 120:
                        with st.expander("📄 Description complète"):
                            st.write(desc)
                            if motif: st.markdown("**Motif :** " + motif)

        elif total_omd == 0:
            st.warning("⚠️ Aucune décision en base. Ajoutez des PDFs via 'Ajouter'.")

    elif page == "📤 Ajouter":
        st.markdown("<h2 style='color:#0a1628;'>📤 Ajouter des PDFs OMD</h2>", unsafe_allow_html=True)
        st.markdown("---")

        tab_import, tab_fix, tab_clean = st.tabs(["📄 Importer un PDF", "🔄 Corriger les sessions", "🧹 Nettoyer doublons"])

        with tab_import:
            st.info("📄 **Extraction automatique** — session + décisions extraites et enregistrées directement.")
            files = st.file_uploader("Glissez vos PDFs OMD", type=["pdf"], accept_multiple_files=True, key="omd_upload")
            if files:
                st.markdown(f"**{len(files)} fichier(s) sélectionné(s)**")
                reimport = st.checkbox("Réimporter (remplace les décisions existantes du même fichier)", value=False)
                if st.button("🚀 Lancer l'extraction", type="primary", key="omd_launch"):
                    total_added = 0; progress = st.progress(0); status = st.empty()
                    for i, f in enumerate(files):
                        status.info(f"⏳ {f.name} ({i+1}/{len(files)})")
                        dest = os.path.join(PDF_DIR, f.name)
                        with open(dest,"wb") as fp: fp.write(f.getbuffer())
                        decisions = ocr.parse_omd_pdf(dest, f.name)
                        if not decisions:
                            st.warning(f"⚠️ Aucune décision trouvée dans **{f.name}**")
                        else:
                            session_det = decisions[0].get("session","") if decisions else ""
                            if reimport:
                                deleted = db.delete_omd_by_filename(f.name)
                                st.info(f"🔄 {deleted} anciennes décisions supprimées")
                            existing_keys = {
                                (r["filename"], r["classement"], r["description"])
                                for r in db.get_all_omd()
                            }
                            new_dec = [d for d in decisions
                                       if (d["filename"], d["classement"], d["description"]) not in existing_keys]
                            skip_dup = len(decisions) - len(new_dec)
                            for d in new_dec: db.insert_omd(d)
                            total_added += len(new_dec)
                            info_msg = f"✅ **{f.name}** — {len(new_dec)} décisions · Session : **{session_det}**"
                            if skip_dup > 0: info_msg += f" · ⚠️ {skip_dup} doublon(s) ignoré(s)"
                            st.success(info_msg)
                        progress.progress((i+1)/len(files))
                    status.success(f"✅ Import terminé — **{total_added}** décisions enregistrées !")
                    st.rerun()

        with tab_fix:
            st.markdown("**Corriger la session des décisions déjà importées**")
            filenames = db.get_omd_filenames()
            if not filenames:
                st.info("Aucune décision en base.")
            else:
                all_docs = db.get_all_omd()
                file_sessions = {}
                for doc in all_docs:
                    fn = doc.get("filename","")
                    sess = doc.get("session","") or ""
                    if fn not in file_sessions:
                        file_sessions[fn] = sess

                for fn, sess in file_sessions.items():
                    if not sess or sess == "—":
                        icon = "❌"; label = "Session manquante"
                    else:
                        icon = "✅"; label = sess
                    st.markdown(
                        '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
                        'padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;">'
                        '<span style="color:#374151;font-size:0.85rem;">📄 ' + fn + '</span>'
                        '<span style="color:' + ('#15803d' if icon=='✅' else '#dc2626') + ';font-size:0.82rem;">'
                        + icon + ' ' + label + '</span>'
                        '</div>',
                        unsafe_allow_html=True)

                st.markdown("---")
                fix_file = st.file_uploader("Glisser le PDF à corriger", type=["pdf"], key="omd_fix")
                if fix_file:
                    dest = os.path.join(PDF_DIR, fix_file.name)
                    with open(dest,"wb") as fp: fp.write(fix_file.getbuffer())
                    if st.button("🔄 Détecter et corriger la session", type="primary", key="omd_fix_btn"):
                        with st.spinner("Extraction en cours..."):
                            decisions = ocr.parse_omd_pdf(dest, fix_file.name)
                        if not decisions:
                            st.error("❌ Impossible d'extraire la session depuis ce PDF.")
                        else:
                            session_det = decisions[0].get("session","")
                            if not session_det:
                                st.error("❌ Session non détectée dans ce PDF.")
                            else:
                                updated = db.update_omd_session_by_filename(fix_file.name, session_det)
                                if updated > 0:
                                    st.success(f"✅ Session **{session_det}** appliquée à **{updated}** décisions")
                                else:
                                    for d in decisions: db.insert_omd(d)
                                    st.success(f"✅ {len(decisions)} décisions importées avec session **{session_det}**")
                                st.rerun()

                st.markdown("---")
                col_fn, col_sess, col_btn2 = st.columns([2,2,1])
                with col_fn:
                    fn_sel = col_fn.selectbox("Fichier", filenames, key="fn_sel")
                with col_sess:
                    sess_input = st.text_input("Session", placeholder="ex: 22ème Session (Novembre 1998)", key="sess_input")
                with col_btn2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("💾 Appliquer", type="primary", key="apply_sess"):
                        if sess_input.strip():
                            updated = db.update_omd_session_by_filename(fn_sel, sess_input.strip())
                            st.success(f"✅ Session appliquée à **{updated}** décisions")
                            st.rerun()
                        else:
                            st.error("Saisissez une session.")

        with tab_clean:
            nb_dup = db.get_omd_duplicate_count()
            total  = len(db.get_all_omd())
            col_a, col_b = st.columns(2)
            col_a.metric("Total décisions", total)
            col_b.metric("Doublons détectés", nb_dup)
            if nb_dup == 0:
                st.success("✅ Aucun doublon — base propre !")
            else:
                st.warning(f"⚠️ **{nb_dup}** doublon(s) détecté(s).")
                if st.button("🧹 Supprimer les doublons", type="primary", key="clean_dup"):
                    deleted = db.deduplicate_omd()
                    st.success(f"✅ **{deleted}** doublon(s) supprimé(s) !")
                    st.rerun()

    elif page == "✏️ Modifier":
        st.markdown("<h2 style='color:#0a1628;'>✏️ Modifier / Supprimer</h2>", unsafe_allow_html=True)
        st.markdown("---")
        docs = db.get_all_omd()
        if not docs: st.info("Aucune décision disponible.")
        else:
            q_mod = st.text_input("Rechercher par classement ou description", placeholder="ex: 17.04, sucreries")
            if q_mod: docs = [d for d in docs if q_mod.lower() in (d.get("classement") or "").lower() or q_mod.lower() in (d.get("description") or "").lower()]
            if not docs: st.warning("Aucun résultat.")
            else:
                opts = {f"[{d['id']}] {d.get('classement','')} — {(d.get('description') or '')[:40]}": d['id'] for d in docs}
                sel  = st.selectbox("Choisir une décision", list(opts.keys()))
                doc  = db.get_omd_by_id(opts[sel])
                tab_e, tab_d = st.tabs(["✏️ Modifier","🗑️ Supprimer"])
                with tab_e:
                    with st.form("edit_omd"):
                        c1, c2 = st.columns(2)
                        num  = c1.text_input("N°",         value=doc.get("numero")      or "")
                        clas = c2.text_input("Classement", value=doc.get("classement")  or "")
                        sess = st.text_input("Session",    value=doc.get("session")     or "")
                        desc = st.text_area("Description", value=doc.get("description") or "", height=120)
                        moti = st.text_area("Motif",       value=doc.get("motif")       or "", height=80)
                        if st.form_submit_button("💾 Enregistrer", type="primary"):
                            db.update_omd(opts[sel],{"numero":num,"description":desc,"classement":clas,"motif":moti,"session":sess})
                            st.success("✅ Mis à jour !"); st.rerun()
                with tab_d:
                    st.warning(f"⚠️ Supprimer **{doc.get('classement')}** ?")
                    if st.checkbox("Je confirme"):
                        if st.button("🗑️ Supprimer", type="primary"):
                            db.delete_omd(opts[sel]); st.success("Supprimé."); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 4 — AVIS TARÉS (kap_XX_f.pdf)
# ══════════════════════════════════════════════════════════════════════════════
elif module == "avis_tares":
    st.markdown("## 📑 Avis Tarés")
    st.caption("Recueils tarifaires par chapitre — format kap_XX_f.pdf")
    st.markdown("---")

    page = st.radio("", ["🔍 Recherche", "📤 Ajouter", "✏️ Modifier"],
                    horizontal=True, label_visibility="collapsed")

    total_at = len(db.get_all_avis_tares())

    # ── Recherche ──────────────────────────────────────────────────────────────
    if page == "🔍 Recherche":
        st.markdown(
            "<h2 style='color:#0a1628;font-size:1.65rem;font-weight:800;margin-bottom:4px;'>"
            "Recherche — Avis Tarés</h2>", unsafe_allow_html=True)
        st.caption("Tapez un code SH (partiel), un nom de produit ou un mot-clé.")

        if total_at > 0:
            st.info(f"ℹ️ Base de données : **{total_at:,}** produits disponibles")

        col_inp, col_btn = st.columns([4, 1])
        with col_inp:
            q_at = st.text_input("at", placeholder="ex: 0402  ou  lait  ou  fromage  ou  sucre…",
                                 label_visibility="collapsed", key="at_search")
        with col_btn:
            rechercher = st.button("🔍  Rechercher", type="primary", use_container_width=True)

        # Aide contextuelle
        st.markdown(
            '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
            'padding:10px 16px;margin:8px 0 16px;font-size:0.8rem;color:#6b7280;">'
            '💡 <b>Exemples :</b>&nbsp;&nbsp;'
            '<code>0402</code> → tous les produits du chapitre 04 contenant 0402 &nbsp;|&nbsp;'
            '<code>0402.9910</code> → lait concentré (exact) &nbsp;|&nbsp;'
            '<code>lait</code> → tous les produits avec "lait" &nbsp;|&nbsp;'
            '<code>fromage</code> → Fromage frais, Mozzarella, Skyr…'
            '</div>', unsafe_allow_html=True)

        if (rechercher or q_at) and q_at.strip():
            results = db.search_avis_tares(q_at.strip())
            nb = len(results)

            if nb == 0:
                st.error(f"❌ Aucun produit trouvé pour : **{q_at}**")
            else:
                st.markdown(
                    '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;'
                    'padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;">'
                    '<span style="font-size:1.4rem;font-weight:800;color:#1a56db;">' + str(nb) + '</span>'
                    '<span style="color:#374151;font-size:0.9rem;">produit(s) trouvé(s)</span>'
                    '</div>', unsafe_allow_html=True)

                for doc in results:
                    hs_val   = doc.get("hs_code")     or "—"
                    nom_val  = doc.get("nom")         or "—"
                    desc_val = doc.get("description") or ""
                    mots_val = doc.get("mots_cles")   or ""
                    ref_val  = doc.get("ref_numero")  or ""

                    # Badges HS — un badge par code (ex: "0405.2011, 0405.2091" → 2 badges)
                    q_stripped = q_at.strip()
                    hs_codes_list = [c.strip() for c in hs_val.split(",") if c.strip()] if hs_val != "—" else [hs_val]
                    hs_badges_html = ""
                    for code in hs_codes_list:
                        if q_stripped and q_stripped in code:
                            code_disp = code.replace(q_stripped,
                                f'<span style="background:#fef08a;border-radius:2px;padding:0 2px;">{q_stripped}</span>')
                        else:
                            code_disp = code
                        hs_badges_html += f'<span class="badge-hs" style="margin-right:6px;margin-bottom:4px;display:inline-block;">{code_disp}</span>'

                    # Badges mots-clés
                    mots_list = [m.strip() for m in re.split(r'[/]', mots_val) if m.strip()] if mots_val else []
                    badges_html = "".join(
                        f'<span class="badge-blue">{m}</span>' for m in mots_list[:10]
                    )

                    ref_html  = f'<div style="font-size:0.72rem;color:#9ca3af;margin-bottom:6px;">Réf. {ref_val}</div>' if ref_val else ''
                    desc_html = (
                        '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
                        f'padding:12px 16px;margin-bottom:10px;color:#374151;font-size:0.85rem;line-height:1.7;">{desc_val}</div>'
                    ) if desc_val else ''
                    mots_html = (
                        '<div style="margin-top:6px;">'
                        '<span style="color:#9ca3af;font-size:0.68rem;font-weight:700;letter-spacing:0.5px;margin-right:6px;">MOTS-CLÉS :</span>'
                        f'{badges_html}</div>'
                    ) if badges_html else ''

                    card = (
                        '<div style="background:#ffffff;border:1.5px solid #e2e8f0;border-radius:14px;'
                        'padding:18px 22px;margin-bottom:16px;box-shadow:0 2px 8px rgba(0,0,0,0.05);">'
                        # Codes HS en haut
                        f'<div style="margin-bottom:10px;">{hs_badges_html}</div>'
                        # Nom
                        f'<div style="font-size:1rem;font-weight:800;color:#0a1628;margin-bottom:4px;">{nom_val}</div>'
                        f'{ref_html}'
                        # Description complète
                        f'{desc_html}'
                        f'{mots_html}'
                        '</div>'
                    )
                    st.markdown(card, unsafe_allow_html=True)

        elif total_at == 0:
            st.warning("⚠️ Aucun produit en base. Ajoutez des PDFs via 'Ajouter'.")

    # ── Ajouter ───────────────────────────────────────────────────────────────
    elif page == "📤 Ajouter":
        st.markdown("<h2 style='color:#0a1628;'>📤 Ajouter des PDFs — Avis Tarés</h2>", unsafe_allow_html=True)
        st.markdown("---")
        st.info(
            "📄 **Format attendu :** fichiers `kap_XX_f.pdf` (recueils tarifaires par chapitre SH).\n\n"
            "L'extraction détecte automatiquement : code SH · nom du produit · description · mots-clés."
        )

        files = st.file_uploader(
            "Glissez vos PDFs kap_XX_f.pdf",
            type=["pdf"], accept_multiple_files=True, key="at_upload"
        )

        if files:
            st.markdown(f"**{len(files)} fichier(s) sélectionné(s)**")
            reimport_at = st.checkbox("Réimporter (remplace les produits du même fichier)", value=False)

            if st.button("🚀 Lancer l'extraction", type="primary", key="at_launch"):
                total_added = 0
                progress = st.progress(0)
                status = st.empty()

                for i, f in enumerate(files):
                    status.info(f"⏳ {f.name} ({i+1}/{len(files)})")
                    dest = os.path.join(PDF_DIR, f.name)
                    with open(dest, "wb") as fp:
                        fp.write(f.getbuffer())

                    products = ocr.parse_kap_pdf(dest, f.name)

                    if not products:
                        st.warning(f"⚠️ Aucun produit trouvé dans **{f.name}**")
                    else:
                        if reimport_at:
                            deleted = db.delete_avis_tares_by_filename(f.name)
                            st.info(f"🔄 {deleted} anciens produits supprimés pour {f.name}")

                        # Dédoublonnage par (filename, hs_code, nom)
                        existing_keys = {
                            (r["filename"], r["hs_code"], r["nom"])
                            for r in db.get_all_avis_tares()
                        }
                        new_prods = [
                            p for p in products
                            if (p["filename"], p["hs_code"], p["nom"]) not in existing_keys
                        ]
                        skip_dup = len(products) - len(new_prods)

                        for p in new_prods:
                            db.insert_avis_tare(p)
                        total_added += len(new_prods)

                        info_msg = f"✅ **{f.name}** — {len(new_prods)} produit(s) ajouté(s)"
                        if skip_dup > 0:
                            info_msg += f" · ⚠️ {skip_dup} doublon(s) ignoré(s)"
                        st.success(info_msg)

                        # Aperçu des premiers produits extraits
                        with st.expander(f"👁️ Aperçu — {f.name} ({len(products)} produits)"):
                            for p in products[:5]:
                                st.markdown(
                                    f'<div class="result-card">'
                                    f'<span class="badge-hs">{p["hs_code"] or "?"}</span>&nbsp;&nbsp;'
                                    f'<b>{p["nom"][:80]}</b><br>'
                                    f'<small style="color:#6b7280">{p["description"][:120]}…</small><br>'
                                    f'<small style="color:#9ca3af">Mots-clés : {p["mots_cles"][:80]}</small>'
                                    f'</div>',
                                    unsafe_allow_html=True
                                )

                    progress.progress((i+1)/len(files))

                status.success(f"✅ Import terminé — **{total_added}** produit(s) enregistré(s) !")
                st.rerun()

        # Fichiers déjà importés
        filenames_at = db.get_avis_tares_filenames()
        if filenames_at:
            st.markdown("---")
            st.markdown("**📂 Fichiers déjà en base :**")
            for fn in filenames_at:
                count = len([d for d in db.get_all_avis_tares() if d.get("filename") == fn])
                st.markdown(
                    f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
                    f'padding:8px 14px;margin-bottom:4px;display:flex;justify-content:space-between;">'
                    f'<span style="color:#374151;font-size:0.85rem;">📄 {fn}</span>'
                    f'<span style="color:#1a56db;font-size:0.82rem;font-weight:700;">{count} produits</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    # ── Modifier ──────────────────────────────────────────────────────────────
    elif page == "✏️ Modifier":
        st.markdown("<h2 style='color:#0a1628;'>✏️ Modifier / Supprimer</h2>", unsafe_allow_html=True)
        st.markdown("---")

        docs = db.get_all_avis_tares()
        if not docs:
            st.info("Aucun produit disponible.")
        else:
            q_mod = st.text_input("Rechercher par code HS ou nom", placeholder="ex: 0402, lait, fromage")
            if q_mod:
                docs = [d for d in docs if
                        q_mod.lower() in (d.get("hs_code") or "").lower() or
                        q_mod.lower() in (d.get("nom") or "").lower()]
            if not docs:
                st.warning("Aucun résultat.")
            else:
                opts = {
                    f"[{d['id']}] {d.get('hs_code','')} — {(d.get('nom') or '')[:50]}": d['id']
                    for d in docs
                }
                sel = st.selectbox("Choisir un produit", list(opts.keys()))
                doc = db.get_avis_tare_by_id(opts[sel])

                tab_e, tab_d = st.tabs(["✏️ Modifier", "🗑️ Supprimer"])

                with tab_e:
                    with st.form("edit_at"):
                        c1, c2 = st.columns(2)
                        hs_e  = c1.text_input("Code HS",    value=doc.get("hs_code")   or "")
                        ref_e = c2.text_input("Réf. N°",    value=doc.get("ref_numero") or "")
                        nom_e = st.text_input("Nom",         value=doc.get("nom")       or "")
                        desc_e = st.text_area("Description", value=doc.get("description") or "", height=120)
                        mots_e = st.text_area("Mots-clés (séparés par /)",
                                              value=doc.get("mots_cles") or "", height=60)
                        if st.form_submit_button("💾 Enregistrer", type="primary"):
                            db.update_avis_tare(opts[sel], {
                                "hs_code":     hs_e,
                                "nom":         nom_e,
                                "description": desc_e,
                                "mots_cles":   mots_e,
                                "ref_numero":  ref_e,
                            })
                            st.success("✅ Mis à jour !"); st.rerun()

                with tab_d:
                    st.warning(f"⚠️ Supprimer **{doc.get('hs_code')} — {doc.get('nom','')}** ?")
                    if st.checkbox("Je confirme la suppression"):
                        if st.button("🗑️ Supprimer", type="primary"):
                            db.delete_avis_tare(opts[sel])
                            st.success("Supprimé."); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  GESTION UTILISATEURS
# ══════════════════════════════════════════════════════════════════════════════
elif module == "users" and is_admin:
    st.markdown("<h2 style='color:#0a1628;font-weight:800;'>👥 Gestion des utilisateurs</h2>", unsafe_allow_html=True)
    st.markdown("---")

    tab_list, tab_add, tab_pwd = st.tabs(["📋 Liste des utilisateurs", "➕ Ajouter", "🔑 Changer mot de passe"])

    with tab_list:
        users_list = auth.get_all_users()
        if not users_list:
            st.info("Aucun utilisateur.")
        else:
            for u in users_list:
                is_self    = u["email"] == user["email"]
                is_admin_u = u["role"] == "admin"
                actif_icon = "🟢" if u["actif"] else "🔴"
                role_badge = (
                    '<span style="background:#dbeafe;color:#1d4ed8;border-radius:4px;'
                    'padding:2px 8px;font-size:0.75rem;font-weight:700;">ADMIN</span>'
                    if is_admin_u else
                    '<span style="background:#f3f4f6;color:#6b7280;border-radius:4px;'
                    'padding:2px 8px;font-size:0.75rem;font-weight:600;">USER</span>'
                )
                st.markdown(
                    '<div style="background:#ffffff;border:1.5px solid #e2e8f0;border-radius:10px;'
                    'padding:14px 18px;margin-bottom:8px;display:flex;align-items:center;'
                    'justify-content:space-between;">'
                    '<div>'
                    '<span style="font-size:0.95rem;font-weight:700;color:#0a1628;">'
                    + actif_icon + ' ' + (u["nom"] or "—") + '</span>'
                    '<span style="color:#6b7280;font-size:0.82rem;margin-left:10px;">' + u["email"] + '</span>'
                    '<span style="margin-left:10px;">' + role_badge + '</span>'
                    '</div>'
                    '<div style="color:#9ca3af;font-size:0.75rem;">'
                    + ('(vous)' if is_self else (u.get("created_at") or "")) +
                    '</div>'
                    '</div>',
                    unsafe_allow_html=True)

                if not is_admin_u and not is_self:
                    ca, cb, _ = st.columns([1, 1, 4])
                    with ca:
                        lbl = "🔴 Désactiver" if u["actif"] else "🟢 Activer"
                        if st.button(lbl, key=f"tog_{u['id']}", use_container_width=True):
                            auth.toggle_user(u["id"], 0 if u["actif"] else 1)
                            st.rerun()
                    with cb:
                        if st.button("🗑️ Supprimer", key=f"del_{u['id']}", use_container_width=True):
                            auth.delete_user(u["id"])
                            st.success("Utilisateur supprimé.")
                            st.rerun()

    with tab_add:
        st.markdown("**Créer un nouveau compte**")
        with st.form("add_user_form"):
            c1, c2 = st.columns(2)
            nm  = c1.text_input("Nom complet",   placeholder="ex: Jean Dupont")
            em  = c2.text_input("Adresse email", placeholder="ex: jean.dupont@douanes.tn")
            pw  = c1.text_input("Mot de passe",  placeholder="min. 8 caractères", type="password")
            pw2 = c2.text_input("Confirmer",     placeholder="répétez le mot de passe", type="password")
            ro  = st.selectbox("Rôle", ["user", "admin"],
                               format_func=lambda x: "👤 Utilisateur" if x=="user" else "🔑 Administrateur")
            submitted = st.form_submit_button("➕ Créer le compte", type="primary", use_container_width=True)

        if submitted:
            if not nm or not em or not pw:
                st.error("⚠️ Tous les champs sont obligatoires.")
            elif pw != pw2:
                st.error("⚠️ Les mots de passe ne correspondent pas.")
            elif len(pw) < 8:
                st.error("⚠️ Le mot de passe doit contenir au moins 8 caractères.")
            else:
                ok, msg = auth.add_user(em, pw, nm, ro)
                if ok:
                    st.success(f"✅ Compte créé pour **{nm}** ({em})")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

    with tab_pwd:
        st.markdown("**Modifier le mot de passe d'un utilisateur**")
        users_list2 = auth.get_all_users()
        opts_pwd = {f"{u['nom']} ({u['email']})": u['id'] for u in users_list2}

        with st.form("change_pwd_form"):
            sel_user = st.selectbox("Choisir l'utilisateur", list(opts_pwd.keys()))
            new_pw   = st.text_input("Nouveau mot de passe", type="password", placeholder="min. 8 caractères")
            new_pw2  = st.text_input("Confirmer",            type="password", placeholder="répétez")
            submitted_pwd = st.form_submit_button("🔑 Changer le mot de passe", type="primary", use_container_width=True)

        if submitted_pwd:
            if not new_pw:
                st.error("⚠️ Saisissez un nouveau mot de passe.")
            elif new_pw != new_pw2:
                st.error("⚠️ Les mots de passe ne correspondent pas.")
            elif len(new_pw) < 8:
                st.error("⚠️ Minimum 8 caractères.")
            else:
                auth.change_password(opts_pwd[sel_user], new_pw)
                st.success(f"✅ Mot de passe mis à jour pour **{sel_user}**")