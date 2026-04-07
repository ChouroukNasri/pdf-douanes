"""
DouaneXtract — Base de données Douanes Tunisiennes
3 modules : Avis Tarifaires / Secrétariat / Décisions OMD
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
/* ════ FOND BLANC GLOBAL ════ */
.stApp {
    background: #f0f2f6 !important;
}
/* Zone contenu principale blanche */
section[data-testid="stMain"] .block-container {
    background: #ffffff !important;
    border-radius: 12px;
    padding: 32px 40px !important;
    margin-top: 12px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06);
}
/* Header blanc */
header[data-testid="stHeader"] {
    background: #ffffff !important;
    border-bottom: 1px solid #e5e7eb !important;
}
/* ════ SIDEBAR BLEU MARINE ════ */
section[data-testid="stSidebar"] {
    background: #0d1b3e !important;
    border-right: none !important;
}
section[data-testid="stSidebar"] * { color: rgba(200,220,255,0.9) !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }
/* Boutons sidebar */
section[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    color: rgba(200,220,255,0.9) !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    margin-bottom: 2px !important;
    text-align: left !important;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(26,86,219,0.5) !important;
    border-color: rgba(100,160,255,0.4) !important;
}
/* ════ TEXTES CONTENU ════ */
section[data-testid="stMain"] p,
section[data-testid="stMain"] li { color: #374151 !important; }
section[data-testid="stMain"] h1,
section[data-testid="stMain"] h2,
section[data-testid="stMain"] h3 { color: #0a1628 !important; }
section[data-testid="stMain"] label { color: #374151 !important; }
section[data-testid="stMain"] span  { color: #374151 !important; }
/* ════ INPUTS ════ */
section[data-testid="stMain"] input[type="text"],
section[data-testid="stMain"] textarea {
    background: #f9fafb !important;
    border: 1.5px solid #d1d5db !important;
    color: #111827 !important;
    border-radius: 8px !important;
}
section[data-testid="stMain"] input[type="text"]:focus,
section[data-testid="stMain"] textarea:focus {
    border-color: #1a56db !important;
    box-shadow: 0 0 0 3px rgba(26,86,219,0.1) !important;
}
/* ════ BOUTONS ════ */
section[data-testid="stMain"] .stButton button[kind="primary"],
section[data-testid="stMain"] .stFormSubmitButton button {
    background: #1a56db !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
section[data-testid="stMain"] .stButton button[kind="primary"]:hover,
section[data-testid="stMain"] .stFormSubmitButton button:hover {
    background: #1e40af !important;
}
section[data-testid="stMain"] .stButton button {
    background: #f3f4f6 !important;
    border: 1px solid #d1d5db !important;
    color: #374151 !important;
    border-radius: 8px !important;
}
/* ════ TABS ════ */
section[data-testid="stMain"] .stTabs [data-baseweb="tab-list"] {
    background: #f3f4f6 !important;
    border-radius: 8px; padding: 3px;
}
section[data-testid="stMain"] .stTabs [data-baseweb="tab"] { color: #6b7280 !important; }
section[data-testid="stMain"] .stTabs [aria-selected="true"] {
    color: #1a56db !important;
    background: #ffffff !important;
    border-radius: 6px !important;
}
/* ════ RADIO ════ */
section[data-testid="stMain"] .stRadio label span { color: #374151 !important; }
/* ════ EXPANDER ════ */
section[data-testid="stMain"] .streamlit-expanderHeader {
    background: #f9fafb !important;
    border: 1px solid #e5e7eb !important;
    color: #374151 !important;
    border-radius: 8px !important;
}
section[data-testid="stMain"] .streamlit-expanderContent {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
}
/* ════ METRICS ════ */
section[data-testid="stMain"] [data-testid="stMetricLabel"] { color: #6b7280 !important; }
section[data-testid="stMain"] [data-testid="stMetricValue"] { color: #1a56db !important; font-weight:700 !important; }
/* ════ ALERTES ════ */
section[data-testid="stMain"] .stSuccess { background:#f0fdf4 !important; border-left-color:#16a34a !important; }
section[data-testid="stMain"] .stError   { background:#fef2f2 !important; border-left-color:#dc2626 !important; }
section[data-testid="stMain"] .stInfo    { background:#eff6ff !important; border-left-color:#2563eb !important; }
section[data-testid="stMain"] .stWarning { background:#fffbeb !important; border-left-color:#d97706 !important; }
/* ════ PROGRESS ════ */
section[data-testid="stMain"] .stProgress > div > div { background:#1a56db !important; }
/* ════ DATAFRAME ════ */
section[data-testid="stMain"] .stDataFrame { border:1px solid #e5e7eb !important; border-radius:8px !important; }
/* ════ HR ════ */
section[data-testid="stMain"] hr { border-color:#e5e7eb !important; }
/* ════ DASHBOARD CARDS ════ */
.module-card {
    background: #ffffff !important;
    border: 1.5px solid #e2e8f0 !important;
    border-radius: 14px; padding: 28px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: all 0.2s;
}
.module-card:hover {
    border-color: #1a56db !important;
    box-shadow: 0 4px 20px rgba(26,86,219,0.12);
    transform: translateY(-2px);
}
.module-icon  { font-size:2.8rem; margin-bottom:10px; }
.module-title { font-size:1.05rem; font-weight:700; color:#0a1628 !important; margin-bottom:6px; }
.module-desc  { font-size:0.78rem; color:#6b7280 !important; margin-bottom:14px; }
.module-count { font-size:2rem; font-weight:800; color:#1a56db !important; }
.module-label { font-size:0.72rem; color:#9ca3af !important; }
/* ════ RESULT CARDS ════ */
.result-card  { background:#f9fafb !important; border:1px solid #e5e7eb !important; border-radius:10px; padding:14px; margin-bottom:8px; }
.badge        { background:#1a56db; color:white !important; border-radius:4px; padding:2px 8px; font-size:0.82rem; font-weight:600; }
.badge-green  { background:#dcfce7; border:1px solid #86efac; color:#15803d !important; border-radius:4px; padding:2px 8px; font-size:0.82rem; }
.badge-purple { background:#ede9fe; border:1px solid #c4b5fd; color:#6d28d9 !important; border-radius:4px; padding:2px 8px; font-size:0.82rem; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def show_login():
    import base64 as _b64, os as _os

    _logo = ""
    try:
        _lp = _os.path.join(_os.path.dirname(__file__), "logo.png")
    except NameError:
        _lp = "logo.png"  # fallback si __file__ non dispo (Streamlit Cloud)

    if _os.path.exists(_lp):
        with open(_lp, "rb") as _f:
            _logo = _b64.b64encode(_f.read()).decode()

    # CSS
    st.markdown("""<style> ... </style>""", unsafe_allow_html=True)

    _img_tag = f'<img src="data:image/png;base64,{_logo}" style="width:160px;filter:drop-shadow(0 0 18px rgba(0,150,255,0.4));">' if _logo else ""

    st.markdown("<br>", unsafe_allow_html=True)
    _, _col, _ = st.columns([1, 2, 1])

    with _col:
        st.markdown(f""" ... {_img_tag} ... """, unsafe_allow_html=True)

        with st.form("login_form"):
            _email = st.text_input("em", placeholder="✉   User@email.com", label_visibility="collapsed")
            _pwd   = st.text_input("pw", placeholder="🔒   Mot de passe", type="password", label_visibility="collapsed")

            _c1, _c2 = st.columns([1.2, 1])
            with _c1:
                st.checkbox("Se souvenir de moi")
            with _c2:
                st.markdown(
                    '<div style="text-align:right;padding-top:6px;color:#0099ff !important;font-size:0.77rem;">Mot de passe oublié ?</div>',
                    unsafe_allow_html=True
                )

            _submit = st.form_submit_button("Se connecter  →", use_container_width=True)

        st.markdown(
            '<div style="text-align:center;color:rgba(80,120,180,0.45);font-size:0.67rem;margin-top:12px;">DouaneXtract v1.0 · Direction Générale des Douanes Tunisiennes</div>',
            unsafe_allow_html=True
        )

        if _submit:
            if not _email or not _pwd:
                st.error("⚠️ Veuillez remplir tous les champs.")
            else:
                # 🔴 PROTECTION si auth non défini
                try:
                    _user = auth.login(_email, _pwd)
                except Exception as e:
                    st.error(f"Erreur auth: {e}")
                    return

                if _user:
                    st.session_state["user"] = _user
                    st.rerun()
                else:
                    st.error("❌ Email ou mot de passe incorrect.")


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION
# ══════════════════════════════════════════════════════════════════════════════
if "user" not in st.session_state:
    show_login()
    st.stop()

user = st.session_state["user"]

# 🔴 éviter crash si role absent
is_admin = user.get("role") == "admin"

# 🔴 protéger db
try:
    stats = db.get_stats()
except:
    stats = {}

if "module" not in st.session_state:
    st.session_state["module"] = "dashboard"

module = st.session_state["module"]

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if module == "dashboard":
    st.markdown(f"<h1 style='margin-bottom:4px;'>Bonjour, {user['nom']} 👋</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(150,190,255,0.6);margin-bottom:32px;'>Que souhaitez-vous consulter aujourd'hui ?</p>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="module-card">
            <div class="module-icon">📋</div>
            <div class="module-title">Avis Tarifaires</div>
            <div class="module-desc">Documents PDF scannés — Classement tarifaire</div>
            <div class="module-count">{stats['tarifaires']}</div>
            <div class="module-label">documents indexés</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Accéder →", key="btn_tar", use_container_width=True):
            st.session_state["module"] = "tarifaires"; st.rerun()
    with c2:
        st.markdown(f"""<div class="module-card">
            <div class="module-icon">📁</div>
            <div class="module-title">Avis Secrétariat</div>
            <div class="module-desc">Correspondances et avis du secrétariat</div>
            <div class="module-count">{stats['secretariat']}</div>
            <div class="module-label">documents indexés</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Accéder →", key="btn_sec", use_container_width=True):
            st.session_state["module"] = "secretariat"; st.rerun()
    with c3:
        st.markdown(f"""<div class="module-card">
            <div class="module-icon">🌐</div>
            <div class="module-title">Décisions OMD</div>
            <div class="module-desc">Organisation Mondiale des Douanes</div>
            <div class="module-count">{stats['omd']}</div>
            <div class="module-label">documents indexés</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Accéder →", key="btn_omd", use_container_width=True):
            st.session_state["module"] = "omd"; st.rerun()

    st.markdown("---")
    st.markdown("### Statistiques")
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("📋 Avis Tarifaires",  stats['tarifaires'])
    s2.metric("📁 Secrétariat",      stats['secretariat'])
    s3.metric("🌐 Décisions OMD",    stats['omd'])
    s4.metric("📊 Total documents",  stats['total'])

    st.markdown("---")
    st.markdown("### 🕐 Derniers documents ajoutés")
    t1, t2, t3 = st.tabs(["📋 Tarifaires","📁 Secrétariat","🌐 OMD"])
    with t1:
        docs = db.get_all_documents()[:5]
        if not docs: st.info("Aucun document.")
        else:
            for d in docs:
                st.markdown(f"""<div class='result-card'>
                    <b>📄 {d['filename']}</b> &nbsp;
                    <span class='badge'>{d.get('tarif_number') or '?'}</span>
                    <span style='float:right;color:#aaa;font-size:0.78rem'>{d.get('upload_date','')[:10]}</span><br>
                    <small style='color:rgba(150,190,255,0.6)'>N° {d.get('numero_avis') or '—'} · NDP {d.get('ndp') or '—'}</small>
                </div>""", unsafe_allow_html=True)
    with t2:
        docs = db.get_all_secretariat()[:5]
        if not docs: st.info("Aucun document.")
        else:
            for d in docs:
                st.markdown(f"""<div class='result-card'>
                    <b>📄 {d['filename']}</b>
                    <span style='float:right;color:#aaa;font-size:0.78rem'>{d.get('upload_date','')[:10]}</span><br>
                    <small style='color:rgba(150,190,255,0.6)'>N° {d.get('numero_avis') or '—'} · {d.get('objet') or '—'}</small>
                </div>""", unsafe_allow_html=True)
    with t3:
        docs = db.get_all_omd()[:5]
        if not docs: st.info("Aucun document.")
        else:
            for d in docs:
                st.markdown(f"""<div class='result-card'>
                    <b>📄 {d['filename']}</b> &nbsp;
                    <span class='badge-purple'>{d.get('code_sh') or '?'}</span>
                    <span style='float:right;color:#aaa;font-size:0.78rem'>{d.get('upload_date','')[:10]}</span><br>
                    <small style='color:rgba(150,190,255,0.6)'>N° {d.get('numero_dec') or '—'} · {d.get('titre') or '—'}</small>
                </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — AVIS TARIFAIRES
# ══════════════════════════════════════════════════════════════════════════════
elif module == "tarifaires":
    st.markdown("## 📋 Avis Tarifaires")
    st.caption("Documents PDF scannés — Classement tarifaire douanier")
    st.markdown("---")

    page = st.radio("", ["📤 Ajouter","🔍 Recherche","✏️ Modifier"],
                    horizontal=True, label_visibility="collapsed")

    # ── AJOUTER ──────────────────────────────────────────────────────────────
    if page == "📤 Ajouter":
        st.subheader("📤 Ajouter des PDFs")
        files = st.file_uploader("Glissez vos PDFs ici", type=["pdf"], accept_multiple_files=True)
        if files:
            st.markdown(f"**{len(files)} fichier(s) sélectionné(s)**")
            if st.button("🚀 Lancer l'extraction OCR", type="primary"):
                existing   = {d["filename"] for d in db.get_all_documents()}
                to_process = [f for f in files if f.name not in existing]
                skipped    = [f.name for f in files if f.name in existing]
                if skipped:
                    st.warning(f"⟳ Déjà en base : {', '.join(skipped)}")
                progress = st.progress(0); status = st.empty(); doc_id = None
                for i, f in enumerate(to_process):
                    status.info(f"⏳ {f.name} ({i+1}/{len(to_process)})")
                    dest = os.path.join(PDF_DIR, f.name)
                    with open(dest,"wb") as fp: fp.write(f.getbuffer())
                    data   = ocr.process_pdf(dest, f.name)
                    doc_id = db.insert_document(data)
                    progress.progress((i+1)/len(to_process))
                if to_process:
                    status.success(f"✅ {len(to_process)} document(s) ajouté(s) !")
                    if doc_id:
                        doc = db.get_document_by_id(doc_id)
                        st.markdown("---")
                        a, b, c = st.columns(3)
                        a.metric("N° Avis",      doc.get("numero_avis")  or "Non détecté")
                        b.metric("N° Tarifaire", doc.get("tarif_number") or "Non détecté")
                        c.metric("NDP",          doc.get("ndp")          or "Non détecté")
                        st.write(f"**Désignation :** {doc.get('designation') or 'Non détectée'}")
                        with st.expander("📄 Texte OCR complet"):
                            st.text(doc.get("full_text","")[:4000])

    # ── RECHERCHE ─────────────────────────────────────────────────────────────
    elif page == "🔍 Recherche":
        st.subheader("🔍 Recherche")

        cq, cb = st.columns([4,1])
        with cq:
            query = st.text_input("q",
                placeholder="Mot-clé, désignation, N° avis…",
                label_visibility="collapsed")
        with cb:
            rechercher = st.button("Rechercher", type="primary", use_container_width=True)

        with st.expander("🔧 Filtres par champ", expanded=True):
            f1, f2, f3 = st.columns(3)
            filter_avis  = f1.text_input("🔵 N° Avis",        placeholder="ex: 2206755")
            filter_ndp   = f2.text_input("🟢 NDP (partiel)",   placeholder="ex: 94, 9405, 94054010099")
            filter_tarif = f3.text_input("🟡 N° Tarifaire",    placeholder="ex: 940540")

        if query or filter_avis or filter_ndp or filter_tarif or rechercher:
            results = db.search_documents(query) if query else db.get_all_documents()

            if filter_avis.strip():
                results = [r for r in results if filter_avis.strip() in (r.get("numero_avis") or "")]
            if filter_ndp.strip():
                results = [r for r in results if filter_ndp.strip() in (r.get("ndp") or "")]
            if filter_tarif.strip():
                results = [r for r in results if filter_tarif.strip() in (r.get("tarif_number") or "")]

            nb = len(results)
            if nb == 0:
                st.warning("🔍 Aucun document trouvé.")
            else:
                extra = f" pour <b>{query}</b>" if query else ""
                st.markdown(f"""
                <div style="background:rgba(0,80,200,0.2);border:1px solid rgba(0,180,255,0.35);
                    border-radius:10px;padding:12px 20px;margin-bottom:16px;
                    display:flex;align-items:center;gap:12px;">
                    <span style="font-size:1.6rem;font-weight:800;color:#00c8ff;">{nb}</span>
                    <span style="color:rgba(180,215,255,0.8);font-size:0.9rem;">document(s) trouvé(s){extra}</span>
                </div>""", unsafe_allow_html=True)

                for doc in results:
                    ndp_val   = doc.get("ndp")          or "—"
                    avis_val  = doc.get("numero_avis")  or "—"
                    tarif_val = doc.get("tarif_number") or "—"
                    desig_val = doc.get("designation")  or "—"
                    usage_val = doc.get("usage_text")   or "—"
                    date_val  = doc.get("upload_date","")[:10]
                    desig_short = desig_val[:60] + ("…" if len(desig_val)>60 else "")
                    usage_short = usage_val[:120] + ("…" if len(usage_val)>120 else "")

                    # Surligner NDP
                    ndp_display = ndp_val
                    if filter_ndp.strip() and filter_ndp.strip() in ndp_val:
                        ndp_display = ndp_val.replace(
                            filter_ndp.strip(),
                            f'<span style="background:rgba(0,200,100,0.3);border-radius:3px;padding:0 2px;">{filter_ndp.strip()}</span>'
                        )

                    st.markdown(f"""
                    <div style="background:rgba(4,20,70,0.6);border:1px solid rgba(0,150,255,0.25);
                        border-radius:12px;padding:16px;margin-bottom:12px;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:12px;">
                            <span style="font-size:0.88rem;font-weight:700;color:#fff;">📄 {doc['filename']}</span>
                            <span style="color:rgba(150,180,220,0.5);font-size:0.75rem;">{date_val}</span>
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;margin-bottom:10px;">
                            <div style="background:rgba(0,50,140,0.4);border:1px solid rgba(0,140,255,0.2);border-radius:8px;padding:10px;">
                                <div style="color:rgba(140,180,230,0.55);font-size:0.65rem;letter-spacing:0.5px;margin-bottom:3px;">N° AVIS</div>
                                <div style="color:#00c8ff;font-weight:700;font-size:0.9rem;">{avis_val}</div>
                            </div>
                            <div style="background:rgba(0,50,140,0.4);border:1px solid rgba(0,140,255,0.2);border-radius:8px;padding:10px;">
                                <div style="color:rgba(140,180,230,0.55);font-size:0.65rem;letter-spacing:0.5px;margin-bottom:3px;">NDP</div>
                                <div style="color:#00e090;font-weight:700;font-size:0.9rem;">{ndp_display}</div>
                            </div>
                            <div style="background:rgba(0,50,140,0.4);border:1px solid rgba(0,140,255,0.2);border-radius:8px;padding:10px;">
                                <div style="color:rgba(140,180,230,0.55);font-size:0.65rem;letter-spacing:0.5px;margin-bottom:3px;">N° TARIFAIRE</div>
                                <div style="color:#ffb800;font-weight:700;font-size:0.9rem;">{tarif_val}</div>
                            </div>
                            <div style="background:rgba(0,50,140,0.4);border:1px solid rgba(0,140,255,0.2);border-radius:8px;padding:10px;">
                                <div style="color:rgba(140,180,230,0.55);font-size:0.65rem;letter-spacing:0.5px;margin-bottom:3px;">DÉSIGNATION</div>
                                <div style="color:rgba(200,225,255,0.9);font-size:0.8rem;line-height:1.3;">{desig_short}</div>
                            </div>
                        </div>
                        <div style="background:rgba(0,30,100,0.3);border-radius:6px;padding:8px 12px;">
                            <span style="color:rgba(140,180,230,0.5);font-size:0.67rem;">POUR LE CLASSEMENT TARIFAIRE · </span>
                            <span style="color:rgba(170,205,255,0.75);font-size:0.8rem;">{usage_short}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    with st.expander("📄 Voir texte OCR complet"):
                        st.text(doc.get("full_text","")[:3000])

    # ── MODIFIER ──────────────────────────────────────────────────────────────
    elif page == "✏️ Modifier":
        st.subheader("✏️ Modifier / Supprimer")
        docs = db.get_all_documents()
        if not docs:
            st.info("Aucun document disponible.")
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
                        db.update_document(opts[sel],{
                            "numero_avis":na,"designation":de,
                            "usage_text":us,"tarif_number":tn,"ndp":nd})
                        st.success("✅ Mis à jour !"); st.rerun()
            with tab_o:
                st.text_area("Texte OCR complet", value=doc.get("full_text") or "", height=400)
            with tab_d:
                st.warning(f"⚠️ Supprimer **{doc['filename']}** ?")
                if st.checkbox("Je confirme la suppression"):
                    if st.button("🗑️ Supprimer définitivement", type="primary"):
                        db.delete_document(opts[sel])
                        st.success("Document supprimé."); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — SECRETARIAT
# ══════════════════════════════════════════════════════════════════════════════
elif module == "secretariat":


    page = st.radio("", ["🔍 Recherche", "📤 Ajouter fichier xlsx", "✏️ Modifier"],
                    horizontal=True, label_visibility="collapsed")

    # ── RECHERCHE ─────────────────────────────────────────────────────────────
    if page == "🔍 Recherche":
        st.markdown("""
        <h2 style='color:#0a1628;font-size:1.65rem;font-weight:800;margin-bottom:4px;'>
            Recherche par Numéro de Lettre
        </h2>
        <p style='color:#6b7280;font-size:0.9rem;margin-bottom:20px;'>
            Entrez le numéro de lettre pour afficher les informations correspondantes.
        </p>
        """, unsafe_allow_html=True)

        # Compteur total
        total = len(db.get_all_secretariat())
        if total > 0:
            st.markdown(f"""
            <div style='display:inline-flex;align-items:center;gap:8px;
                background:#eff6ff;border:1px solid #bfdbfe;
                border-radius:8px;padding:6px 14px;margin-bottom:16px;'>
                <span style='color:#1d4ed8;font-size:0.82rem;'>
                    ℹ️ Base de données : <b>{total:,}</b> entrées disponibles
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Zone de recherche
        st.markdown("""
        <div style='background:#f8fafc;border:1.5px solid #e2e8f0;
            border-radius:12px;padding:20px 24px;margin-bottom:24px;'>
            <div style='color:#374151;font-size:0.82rem;font-weight:600;margin-bottom:8px;'>
                Numéro de lettre
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_inp, col_btn = st.columns([4, 1])
        with col_inp:
            num_lettre = st.text_input("nl", placeholder="ex: L10642A, L106, L10...",
                                       label_visibility="collapsed", key="sec_search")
        with col_btn:
            rechercher = st.button("🔍  Rechercher", type="primary", use_container_width=True)

        # Lancer recherche
        if (rechercher or num_lettre) and len(num_lettre.strip()) >= 2:
            q       = num_lettre.strip().upper()
            results = db.search_secretariat_by_lettre(q)
            nb      = len(results)

            st.markdown("### Résultat")

            if nb == 0:
                st.markdown(f"""
                <div style='background:#fef2f2;border:1px solid #fecaca;border-radius:10px;
                    padding:14px 20px;display:flex;align-items:center;gap:10px;'>
                    <span>❌</span>
                    <span style='color:#dc2626;font-size:0.9rem;'>
                        Aucun résultat pour le numéro de lettre : <b>{q}</b>
                    </span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                    padding:14px 20px;display:flex;align-items:center;gap:10px;margin-bottom:20px;'>
                    <span>✅</span>
                    <span style='color:#15803d;font-size:0.9rem;'>
                        <b>{nb}</b> résultat(s) trouvé(s) pour le numéro de lettre : <b>{q}</b>
                    </span>
                </div>""", unsafe_allow_html=True)

                for doc in results:
                    num_val  = doc.get("numero_lettre") or "—"
                    date_val = doc.get("date_avis")     or "—"
                    hs_val   = doc.get("hs_code")       or "—"
                    desc_fr  = doc.get("desc_fr")       or "—"

                    # Surligner la partie recherchée
                    num_display = num_val
                    idx = num_val.upper().find(q)
                    if idx >= 0:
                        num_display = (
                            num_val[:idx] +
                            '<span style="background:#dbeafe;border-radius:3px;padding:0 2px;'
                            'font-weight:800;color:#1d4ed8;">' +
                            num_val[idx:idx+len(q)] + '</span>' +
                            num_val[idx+len(q):]
                        )

                    card_html = (
                        '<div style="background:#ffffff;border:1.5px solid #e2e8f0;'
                        'border-radius:14px;overflow:hidden;margin-bottom:20px;'
                        'box-shadow:0 2px 10px rgba(0,0,0,0.06);">'

                        '<div style="display:grid;grid-template-columns:1fr 1px 1fr 1px 1fr;'
                        'background:#f8fafc;border-bottom:1.5px solid #e2e8f0;">'

                        '<div style="padding:16px 22px;">'
                        '<div style="color:#9ca3af;font-size:0.62rem;letter-spacing:1px;'
                        'text-transform:uppercase;margin-bottom:6px;">NUMÉRO DE LETTRE</div>'
                        '<div style="color:#1a56db;font-weight:800;font-size:1.2rem;">' + num_display + '</div>'
                        '</div>'

                        '<div style="background:#e2e8f0;"></div>'

                        '<div style="padding:16px 22px;">'
                        '<div style="color:#9ca3af;font-size:0.62rem;letter-spacing:1px;'
                        'text-transform:uppercase;margin-bottom:6px;">📅 DATE</div>'
                        '<div style="color:#111827;font-weight:700;font-size:1.05rem;">📅 ' + date_val + '</div>'
                        '</div>'

                        '<div style="background:#e2e8f0;"></div>'

                        '<div style="padding:16px 22px;">'
                        '<div style="color:#9ca3af;font-size:0.62rem;letter-spacing:1px;'
                        'text-transform:uppercase;margin-bottom:6px;">🏷 HS CODE</div>'
                        '<div style="color:#111827;font-weight:700;font-size:1.05rem;">🏷 ' + hs_val + '</div>'
                        '</div>'

                        '</div>'

                        '<div style="padding:18px 22px;">'
                        '<div style="color:#9ca3af;font-size:0.62rem;letter-spacing:1px;'
                        'text-transform:uppercase;margin-bottom:8px;">DESCRIPTION EN FRANÇAIS</div>'
                        '<div style="background:#fefce8;border:1px solid #fde68a;'
                        'border-radius:8px;padding:14px 18px;'
                        'color:#374151;font-size:0.875rem;line-height:1.7;">'
                        + desc_fr +
                        '</div>'
                        '</div>'

                        '</div>'
                    )
                    st.markdown(card_html, unsafe_allow_html=True)


                # Boutons bas
                _, bc2, bc3 = st.columns([2, 1, 1])
                with bc2:
                    import pandas as _pd
                    df_exp = _pd.DataFrame(results)[['numero_lettre','date_avis','hs_code','desc_fr','desc_en']]
                    df_exp.columns = ['N° Lettre','Date','HS Code','Description FR','Description EN']
                    csv_data = df_exp.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                    st.download_button("⬇️  Exporter le résultat", data=csv_data,
                        file_name=f"secretariat_{q}.csv", mime="text/csv", use_container_width=True)
                with bc3:
                    if st.button("↺  Nouvelle recherche", use_container_width=True, key="sec_new"):
                        st.rerun()

        elif num_lettre and len(num_lettre.strip()) < 2:
            st.info("✏️ Entrez au moins 2 caractères pour lancer la recherche.")

        elif total == 0:
            st.warning("⚠️ Aucune donnée en base. Ajoutez un fichier .xlsx via 'Ajouter fichier xlsx'.")

    # ── AJOUTER XLSX ──────────────────────────────────────────────────────────
    elif page == "📤 Ajouter fichier xlsx":
        st.markdown("""
        <h2 style='color:#0a1628;font-size:1.5rem;font-weight:800;margin-bottom:8px;'>
            📤 Ajouter un fichier Excel
        </h2>
        """, unsafe_allow_html=True)
        st.markdown("---")

        st.info("""
        **Format attendu du fichier Excel :**
        - Colonne **LETTER NUMBER** — numéro de lettre (ex: L10642A)
        - Colonne **DATE** — date de l'avis (ex: 2023.06.23)
        - Colonne **HS CODE** — code SH (ex: 3924.90)
        - Colonne **DESCRIPTION EN FRANCAIS** — description en français
        - Colonne **DESCRIPTION IN ENGLISH** — description en anglais (optionnel)
        """)

        uploaded = st.file_uploader("Glisser votre fichier Excel (.xlsx)", type=["xlsx","xls"])

        if uploaded:
            import pandas as _pd
            try:
                df = _pd.read_excel(uploaded)
                # Nettoyer ligne d'avertissement si présente
                df = df[
                    df['LETTER NUMBER'].notna() &
                    ~df['LETTER NUMBER'].astype(str).str.contains('This information', na=False)
                ].reset_index(drop=True)

                # Vérifier colonnes requises
                required = ['LETTER NUMBER','DATE','HS CODE','DESCRIPTION EN FRANCAIS']
                missing  = [c for c in required if c not in df.columns]
                if missing:
                    st.error(f"❌ Colonnes manquantes : {missing}")
                else:
                    st.success(f"✅ Fichier valide — **{len(df):,}** lignes détectées")
                    st.markdown(f"**Aperçu (5 premières lignes) :**")
                    st.dataframe(df.head(5)[['LETTER NUMBER','DATE','HS CODE','DESCRIPTION EN FRANCAIS']], 
                                 use_container_width=True, hide_index=True)

                    # Options import
                    col_opt1, col_opt2 = st.columns(2)
                    skip_existing = col_opt1.checkbox("Ignorer les numéros déjà en base", value=True)

                    if st.button("🚀 Importer dans la base", type="primary"):
                        existing_nums = {r["numero_lettre"] for r in db.get_all_secretariat()}
                        progress = st.progress(0); status = st.empty()
                        ok_count = skipped = 0

                        for i, row in df.iterrows():
                            num = str(row.get('LETTER NUMBER','')).strip()
                            if skip_existing and num in existing_nums:
                                skipped += 1
                            else:
                                data = {
                                    "filename":      uploaded.name,
                                    "numero_lettre": num,
                                    "date_avis":     str(row.get('DATE','')) if _pd.notna(row.get('DATE')) else "",
                                    "hs_code":       str(row.get('HS CODE','')) if _pd.notna(row.get('HS CODE')) else "",
                                    "desc_fr":       str(row.get('DESCRIPTION EN FRANCAIS','')) if _pd.notna(row.get('DESCRIPTION EN FRANCAIS')) else "",
                                    "desc_en":       str(row.get('DESCRIPTION IN ENGLISH','')) if _pd.notna(row.get('DESCRIPTION IN ENGLISH')) else "",
                                }
                                db.insert_secretariat(data)
                                existing_nums.add(num)
                                ok_count += 1
                            progress.progress(min((i+1)/len(df), 1.0))
                            if (i+1) % 100 == 0:
                                status.info(f"⏳ {i+1}/{len(df)} lignes traitées...")

                        progress.progress(1.0)
                        status.success(f"✅ Import terminé — **{ok_count}** ajoutés · **{skipped}** ignorés")
                        st.rerun()

            except Exception as e:
                st.error(f"❌ Erreur lors de la lecture : {e}")

    # ── MODIFIER ──────────────────────────────────────────────────────────────
    elif page == "✏️ Modifier":
        st.markdown("""
        <h2 style='color:#0a1628;font-size:1.5rem;font-weight:800;margin-bottom:8px;'>
            ✏️ Modifier / Supprimer
        </h2>
        """, unsafe_allow_html=True)
        st.markdown("---")

        docs = db.get_all_secretariat()
        if not docs:
            st.info("Aucun document disponible.")
        else:
            # Recherche rapide pour trouver le doc à modifier
            q_mod = st.text_input("Rechercher un numéro de lettre à modifier",
                                   placeholder="ex: L10642A")
            if q_mod:
                docs = [d for d in docs if q_mod.upper() in (d.get("numero_lettre") or "").upper()]

            if not docs:
                st.warning("Aucun résultat.")
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
                        df_en = st.text_area("Description EN", value=doc.get("desc_en") or "", height=80)
                        if st.form_submit_button("💾 Enregistrer", type="primary"):
                            db.update_secretariat(opts[sel],{
                                "numero_lettre":nl,"date_avis":da,"hs_code":hs,
                                "desc_fr":df_fr,"desc_en":df_en})
                            st.success("✅ Mis à jour !"); st.rerun()
                with tab_d:
                    st.warning(f"⚠️ Supprimer l'entrée **{doc.get('numero_lettre')}** ?")
                    if st.checkbox("Je confirme la suppression"):
                        if st.button("🗑️ Supprimer", type="primary"):
                            db.delete_secretariat(opts[sel])
                            st.success("Supprimé."); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 3 — DECISIONS OMD
# ══════════════════════════════════════════════════════════════════════════════
elif module == "omd":
    st.markdown("## 🌐 Décisions OMD")
    st.caption("Organisation Mondiale des Douanes — Décisions et recommandations")
    st.markdown("---")

    page = st.radio("", ["📤 Ajouter","🔍 Recherche","📋 Documents","✏️ Modifier"],
                    horizontal=True, label_visibility="collapsed")

    if page == "📤 Ajouter":
        files = st.file_uploader("Glissez vos PDFs", type=["pdf"], accept_multiple_files=True)
        if files and st.button("🚀 Lancer OCR", type="primary"):
            progress = st.progress(0); status = st.empty()
            for i,f in enumerate(files):
                status.info(f"⏳ {f.name} ({i+1}/{len(files)})")
                dest = os.path.join(PDF_DIR, f.name)
                with open(dest,"wb") as fp: fp.write(f.getbuffer())
                data = ocr.process_pdf(dest, f.name)
                db.insert_omd(data)
                progress.progress((i+1)/len(files))
            status.success(f"✅ {len(files)} document(s) ajouté(s) !")
            st.rerun()

    elif page == "🔍 Recherche":
        cq, cb = st.columns([4,1])
        with cq: query = st.text_input("q", placeholder="N° décision, titre, chapitre, code SH…", label_visibility="collapsed")
        with cb: st.button("Rechercher", type="primary", use_container_width=True)
        with st.expander("🔧 Filtres"):
            f1,f2 = st.columns(2)
            fn = f1.text_input("N° Décision")
            fc = f2.text_input("Code SH")
        if query or fn or fc:
            results = db.search_omd(query) if query else db.get_all_omd()
            if fn: results = [r for r in results if fn in (r.get("numero_dec") or "")]
            if fc: results = [r for r in results if fc in (r.get("code_sh") or "")]
            st.markdown(f"**{len(results)} résultat(s)**")
            for doc in results:
                st.markdown(f"""<div class='result-card'>
                    <b>📄 {doc['filename']}</b> &nbsp;
                    <span class='badge-purple'>{doc.get('code_sh') or '?'}</span>
                    <span style='float:right;color:#aaa;font-size:0.78rem'>{doc.get('upload_date','')[:10]}</span>
                </div>""", unsafe_allow_html=True)
                a,b,c = st.columns(3)
                a.metric("N° Décision", doc.get("numero_dec") or "—")
                b.metric("Date",        doc.get("date_dec")   or "—")
                c.metric("Code SH",     doc.get("code_sh")    or "—")
                st.write(f"**Titre :** {doc.get('titre') or '—'}")
                st.write(f"**Chapitre :** {doc.get('chapitre') or '—'}")
                with st.expander("📄 Texte OCR"): st.text(doc.get("full_text","")[:3000])
                st.markdown("---")

    elif page == "📋 Documents":
        docs = db.get_all_omd()
        if not docs: st.info("Aucun document.")
        else:
            df = pd.DataFrame(docs)[["id","numero_dec","titre","date_dec","chapitre","code_sh","upload_date"]]
            df.columns = ["ID","N° Décision","Titre","Date","Chapitre","Code SH","Ajouté le"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("⬇️ CSV", data=csv, file_name="decisions_omd.csv", mime="text/csv")

    elif page == "✏️ Modifier":
        docs = db.get_all_omd()
        if not docs: st.info("Aucun document.")
        else:
            opts = {f"[{d['id']}] {d['filename']}": d['id'] for d in docs}
            sel  = st.selectbox("Document", list(opts.keys()))
            doc  = db.get_omd_by_id(opts[sel])
            tab_e, tab_o, tab_d = st.tabs(["✏️ Modifier","📄 OCR","🗑️ Supprimer"])
            with tab_e:
                with st.form("edit_omd"):
                    c1,c2,c3 = st.columns(3)
                    nd = c1.text_input("N° Décision", value=doc.get("numero_dec") or "")
                    dd = c2.text_input("Date",        value=doc.get("date_dec")   or "")
                    cs = c3.text_input("Code SH",     value=doc.get("code_sh")    or "")
                    ti = st.text_area("Titre",        value=doc.get("titre")      or "", height=70)
                    ch = st.text_input("Chapitre",    value=doc.get("chapitre")   or "")
                    if st.form_submit_button("💾 Enregistrer", type="primary"):
                        db.update_omd(opts[sel],{"numero_dec":nd,"titre":ti,"date_dec":dd,"chapitre":ch,"code_sh":cs})
                        st.success("✅ Mis à jour !"); st.rerun()
            with tab_o: st.text_area("OCR", value=doc.get("full_text") or "", height=400)
            with tab_d:
                st.warning(f"Supprimer {doc['filename']} ?")
                if st.checkbox("Confirmer"):
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
                    else: st.error(f"❌ {msg}")