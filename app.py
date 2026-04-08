"""
DouaneXtract — Base de données Douanes Tunisiennes
"""
import os, shutil, glob, base64
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
section[data-testid="stSidebar"] .stButton button:hover {
    background:rgba(26,86,219,0.5) !important;
}
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
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE LOGIN — Design Streamlit natif (fiable, pas de HTML brut)
# ══════════════════════════════════════════════════════════════════════════════
def show_login():
    # CSS global login
    st.markdown("""
    <style>
    .stApp {
        background: #2d4a7a !important;
        min-height: 100vh;
    }
    header[data-testid="stHeader"]   { display:none !important; }
    section[data-testid="stSidebar"] { display:none !important; }
    #MainMenu, footer                 { display:none !important; }
    .block-container {
        padding-top: 48px !important;
        max-width: 520px !important;
        margin: 0 auto !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    /* Labels champs */
    section[data-testid="stMain"] label {
        color: #1e3a5f !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }
    /* Inputs — style photo : fond blanc, bordure grise */
    section[data-testid="stMain"] input[type="text"],
    section[data-testid="stMain"] input[type="password"] {
        background: #f7f8fa !important;
        border: 1px solid #d0d7e3 !important;
        color: #1e3a5f !important;
        border-radius: 8px !important;
        padding: 14px 16px !important;
        font-size: 1rem !important;
    }
    section[data-testid="stMain"] input::placeholder {
        color: #a0aec0 !important;
    }
    section[data-testid="stMain"] input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59,130,246,0.15) !important;
    }
    /* Bouton Connexion */
    section[data-testid="stMain"] .stFormSubmitButton button {
        background: linear-gradient(180deg, #4a90d9 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 14px !important;
        letter-spacing: 0.3px !important;
        box-shadow: 0 4px 14px rgba(37,99,235,0.4) !important;
    }
    section[data-testid="stMain"] .stFormSubmitButton button:hover {
        background: linear-gradient(180deg, #5ba3f0 0%, #1d4ed8 100%) !important;
    }
    /* Lien mdp oublie */
    section[data-testid="stMain"] a,
    section[data-testid="stMain"] .mdp-link { color: #3b82f6 !important; }
    /* Textes généraux dans la carte */
    section[data-testid="stMain"] p { color: #374151 !important; }
    section[data-testid="stMain"] .stCheckbox label span { color: #374151 !important; font-size:0.88rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # ── Logo + titre (au-dessus de la carte) ──────────────────────────────────
    logo_b64 = LOGO_B64
    logo_html = (
        '<img src="data:image/png;base64,' + logo_b64 + '" '
        'style="width:72px;vertical-align:middle;margin-right:14px;'
        'filter:drop-shadow(0 2px 8px rgba(0,0,0,0.3));">'
    ) if logo_b64 else ""

    st.markdown(
        '<div style="text-align:center;margin-bottom:28px;padding-top:8px;">'
        + logo_html +
        '<span style="font-size:2.2rem;font-weight:900;color:#ffffff;vertical-align:middle;">'
        'Douane<span style="color:#60a5fa;">Xtract</span></span>'
        '<div style="color:#1e3a8a;font-size:0.85rem;margin-top:10px;letter-spacing:0.3px;">'
        'Base de données — Avis de Classement Tarifaire'
        '</div></div>',
        unsafe_allow_html=True)

    # ── Carte blanche ──────────────────────────────────────────────────────────

    with st.form("login_form"):
        email    = st.text_input("Adresse email", placeholder="user@email.com")
        password = st.text_input("Mot de passe",  placeholder="••••••••", type="password")

        # Lien mot de passe oublié
        st.markdown(
            '<div style="text-align:left;margin:-6px 0 16px 0;">'
            '<span style="color:#3b82f6;font-size:0.85rem;cursor:pointer;">'
            'Mot de passe oublié ?</span></div>',
            unsafe_allow_html=True)

        # Séparateur
        st.markdown('<hr style="border-color:#e5e7eb;margin:0 0 16px 0;">', unsafe_allow_html=True)

        submit = st.form_submit_button("Connexion", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown(
        '<div style="text-align:center;margin-top:24px;color:rgba(200,220,255,0.55);font-size:0.75rem;">'
        '<b style="color:rgba(200,220,255,0.75);">DouaneXtract</b> v1.0 &nbsp;·&nbsp; '
        'Direction Générale des Douanes Tunisiennes</div>',
        unsafe_allow_html=True)

    # ── Logique ────────────────────────────────────────────────────────────────
    if submit:
        if not email or not password:
            st.error("⚠️ Veuillez remplir tous les champs.")
        else:
            user = auth.login(email, password)
            if user:
                st.session_state["user"] = user
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
    logo_html = ('<img src="data:image/png;base64,' + LOGO_B64 + '" style="width:90px;display:block;margin:0 auto 12px auto;">') if LOGO_B64 else ""
    st.markdown(
        '<div style="padding:24px 16px 8px;text-align:center;">'
        + logo_html +
        '<div style="font-size:1.6rem;font-weight:900;margin-bottom:2px;">'
        '<span style="color:#fff;">Douane</span><span style="color:#60a5fa;">Xtract</span></div>'
        '<div style="font-size:0.68rem;color:rgba(148,163,184,0.8);">Base de données Douanes</div>'
        '</div>', unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:12px 0;'>", unsafe_allow_html=True)

    mod = st.session_state.get("module","dashboard")
    def nav_btn(label, key):
        if st.button(label, use_container_width=True, key="nav_"+key):
            st.session_state["module"] = key; st.rerun()

    nav_btn("🏠  Tableau de bord",  "dashboard")
    nav_btn("📋  Avis Tarifaires",  "tarifaires")
    nav_btn("📁  Secrétariat",      "secretariat")
    nav_btn("🌐  Décisions OMD",    "omd")
    if is_admin:
        nav_btn("👥  Utilisateurs", "users")

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:16px 0 12px;'>", unsafe_allow_html=True)
    if st.button("🚪  Se déconnecter", use_container_width=True, key="nav_logout"):
        del st.session_state["user"]
        st.session_state["module"] = "dashboard"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if module == "dashboard":
    st.markdown(f"<h1 style='margin-bottom:4px;'>Bonjour, {user['nom']} 👋</h1>", unsafe_allow_html=True)
    st.caption("Que souhaitez-vous consulter aujourd'hui ?")

    c1, c2, c3 = st.columns(3)
    for col, icon, title, desc, key, cnt in [
        (c1,"📋","Avis Tarifaires","Documents PDF scannés","tarifaires",stats['tarifaires']),
        (c2,"📁","Avis Secrétariat","Correspondances et avis","secretariat",stats['secretariat']),
        (c3,"🌐","Décisions OMD","Organisation Mondiale des Douanes","omd",stats['omd']),
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
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("📋 Avis Tarifaires", stats['tarifaires'])
    s2.metric("📁 Secrétariat",     stats['secretariat'])
    s3.metric("🌐 Décisions OMD",   stats['omd'])
    s4.metric("📊 Total",           stats['total'])

    st.markdown("---")
    st.markdown("### 🕐 Derniers documents ajoutés")
    t1, t2, t3 = st.tabs(["📋 Tarifaires","📁 Secrétariat","🌐 OMD"])
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


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — AVIS TARIFAIRES
# ══════════════════════════════════════════════════════════════════════════════
elif module == "tarifaires":
    st.markdown("## 📋 Avis Tarifaires")
    st.caption("Documents PDF scannés — Classement tarifaire douanier")
    st.markdown("---")

    page = st.radio("", ["📤 Ajouter","🔍 Recherche","✏️ Modifier"],
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

                    # Surligner NDP
                    ndp_display = ndp_val
                    if filter_ndp.strip() and filter_ndp.strip() in ndp_val:
                        ndp_display = ndp_val.replace(filter_ndp.strip(),
                            '<span style="background:#bbf7d0;border-radius:3px;padding:0 2px;">' + filter_ndp.strip() + '</span>')

                    card = (
                        '<div style="background:#ffffff;border:1.5px solid #e2e8f0;border-radius:12px;'
                        'padding:16px 20px;margin-bottom:12px;box-shadow:0 1px 6px rgba(0,0,0,0.05);">'

                        # En-tête fichier
                        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">'
                        '<span style="font-size:0.85rem;font-weight:700;color:#0a1628;">📄 ' + doc['filename'] + '</span>'
                        '<span style="color:#9ca3af;font-size:0.75rem;">' + date_val + '</span>'
                        '</div>'



                        # 3 cartes blanches : N° AVIS / NDP / N° TARIFAIRE
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

                        # Pour le classement tarifaire
                        '<div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;'
                        'padding:8px 12px;margin-bottom:10px;">'
                        '<span style="color:#0369a1;font-size:0.68rem;font-weight:700;letter-spacing:0.5px;">POUR LE CLASSEMENT TARIFAIRE :</span>'
                        '<span style="color:#1e3a5f;font-size:0.85rem;">' + usage_short + '</span>'
                        '</div>'
                        
                        # Désignation au-dessus
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
                    c1,c2,c3 = st.columns(3)
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

                    # Surligner recherche
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
                        c1,c2,c3 = st.columns(3)
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

                    words   = desc.strip().split(" ")
                    first_w = words[0] if words else ""
                    rest_d  = desc[len(first_w):]
                    short   = (first_w + rest_d)[:120] + ("…" if len(desc)>120 else "")

                    motif_line = ""
                    if motif and motif not in ("—","nan","None",""):
                        motif_line = (
                            '<div style="margin-top:10px;padding-top:10px;border-top:1px solid #e5e7eb;">'
                            '<span style="color:#374151;font-size:0.83rem;"><b>Motif</b> : ' + motif[:150] + ('…' if len(motif)>150 else '') + '</span></div>'
                        )


                    card = (
                        '<div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:14px;'
                        'padding:18px 22px;margin-bottom:14px;box-shadow:0 1px 6px rgba(0,0,0,0.05);">'

                        # Icône + Classement
                        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">'
                        '<div style="width:34px;height:34px;background:#fef3c7;border:1px solid #fcd34d;'
                        'border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:17px;">📁</div>'
                        '<div style="font-size:1rem;font-weight:600;color:#1a1a1a;">'
                        'Classement : <span style="color:#d97706;font-weight:700;">' + clas + '</span>'
                        '</div>'
                        '</div>'

                        # Session uniquement
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
        st.info("📄 **Extraction automatique** — les décisions sont extraites et enregistrées directement.")
        files = st.file_uploader("Glissez vos PDFs OMD", type=["pdf"], accept_multiple_files=True)
        if files:
            st.markdown(f"**{len(files)} fichier(s) sélectionné(s)**")
            if st.button("🚀 Lancer l'extraction OCR", type="primary"):
                total_added = 0; progress = st.progress(0); status = st.empty()
                for i, f in enumerate(files):
                    status.info(f"⏳ {f.name} ({i+1}/{len(files)})")
                    dest = os.path.join(PDF_DIR, f.name)
                    with open(dest,"wb") as fp: fp.write(f.getbuffer())
                    decisions = ocr.parse_omd_pdf(dest, f.name)
                    if not decisions:
                        st.warning(f"⚠️ Aucune décision trouvée dans {f.name}")
                    else:
                        for d in decisions: db.insert_omd(d)
                        total_added += len(decisions)
                        st.success(f"✅ {f.name} — **{len(decisions)}** décisions extraites")
                    progress.progress((i+1)/len(files))
                status.success(f"✅ Import terminé — **{total_added}** décisions enregistrées !")
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
#  GESTION UTILISATEURS
# ══════════════════════════════════════════════════════════════════════════════
elif module == "users" and is_admin:
    st.header("👥 Gestion des utilisateurs")
    tab_list, tab_add = st.tabs(["📋 Liste","➕ Ajouter"])
    with tab_list:
        users = auth.get_all_users()
        for u in users:
            c1,c2,c3,c4,c5 = st.columns([3,2,1,1,1])
            c1.write(f"**{u['nom']}** — {u['email']}")
            c2.write(f"🔑 {u['role']}")
            c3.write("✅" if u["actif"] else "❌")
            if u["role"] != "admin":
                if c4.button("Activer" if not u["actif"] else "Désactiver", key=f"t{u['id']}"):
                    auth.toggle_user(u["id"], 0 if u["actif"] else 1); st.rerun()
                if c5.button("🗑️", key=f"d{u['id']}"):
                    auth.delete_user(u["id"]); st.rerun()
            st.markdown("---")
    with tab_add:
        with st.form("add_u"):
            c1,c2 = st.columns(2)
            nm = c1.text_input("Nom"); em = c2.text_input("Email")
            pw = c1.text_input("Mot de passe", type="password")
            ro = c2.selectbox("Rôle",["user","admin"])
            if st.form_submit_button("➕ Créer", type="primary"):
                if not nm or not em or not pw: st.error("Tous les champs requis.")
                else:
                    ok,msg = auth.add_user(em,pw,nm,ro)
                    if ok: st.success(f"✅ {msg}"); st.rerun()
                    else:  st.error(f"❌ {msg}")