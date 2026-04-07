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
    _lp = _os.path.join(_os.path.dirname(__file__), "logo.png")
    if _os.path.exists(_lp):
        with open(_lp,"rb") as _f:
            _logo = _b64.b64encode(_f.read()).decode()

    # CSS complet isolé pour la page login — écrase tout
    st.markdown("""
    <style>
    /* Reset complet pour la page login */
    .stApp {
        background: radial-gradient(ellipse at 30% 20%, #0d2060 0%, #020b28 55%, #010818 100%) !important;
        min-height: 100vh;
    }
    header[data-testid="stHeader"]   { display:none !important; }
    section[data-testid="stSidebar"] { display:none !important; }
    #MainMenu, footer                 { display:none !important; }
    .block-container {
        padding-top: 0 !important;
        max-width: 100% !important;
        background: transparent !important;
        box-shadow: none !important;
    }
    /* Textes login */
    p, span, div, label { color: rgba(200,225,255,0.88) !important; }
    h1,h2,h3 { color: #ffffff !important; }
    /* Inputs login */
    .stTextInput input {
        background: rgba(0,18,60,0.75) !important;
        border: 1px solid rgba(0,130,255,0.3) !important;
        color: #ffffff !important;
        border-radius: 10px !important;
        padding: 12px 16px !important;
    }
    .stTextInput input:focus {
        border-color: #0088ff !important;
        box-shadow: 0 0 0 3px rgba(0,136,255,0.18) !important;
    }
    .stTextInput input::placeholder { color: rgba(120,160,220,0.5) !important; }
    .stTextInput label { display:none !important; }
    /* Checkbox */
    .stCheckbox label span { color: rgba(150,190,255,0.75) !important; font-size:0.8rem !important; }
    /* Bouton login */
    .stFormSubmitButton button {
        background: linear-gradient(90deg, #0050d8 0%, #0099ff 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 13px !important;
    }
    .stFormSubmitButton button:hover {
        background: linear-gradient(90deg, #0066ff 0%, #00bbff 100%) !important;
        box-shadow: 0 4px 28px rgba(0,140,255,0.5) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    _img_tag = f'<img src="data:image/png;base64,{_logo}" style="width:160px;filter:drop-shadow(0 0 18px rgba(0,150,255,0.4));">' if _logo else ""

    st.markdown("<br>", unsafe_allow_html=True)
    _, _col, _ = st.columns([1, 2, 1])
    with _col:
        st.markdown(f"""
        <div style="background:rgba(4,16,60,0.82);border:1px solid rgba(0,140,255,0.35);
            border-radius:24px;overflow:hidden;backdrop-filter:blur(20px);
            box-shadow:0 8px 60px rgba(0,80,255,0.22);max-width:460px;margin:0 auto;">

          <div style="background:radial-gradient(ellipse at 50% 30%,#0d2878,#020f40);
              border-bottom:1px solid rgba(0,140,255,0.2);padding:28px 28px 20px;text-align:center;">
            {_img_tag}
            <div style="font-size:2.2rem;font-weight:900;letter-spacing:1px;margin-top:10px;margin-bottom:4px;">
              <span style="color:#ffffff !important;">Douane</span><span style="color:#00aaff !important;">Xtract</span>
            </div>
            <div style="color:rgba(150,190,255,0.65) !important;font-size:0.76rem;letter-spacing:0.7px;margin-bottom:18px;">
              Base de données — Avis de Classement Tarifaire
            </div>
            <div style="display:flex;justify-content:center;align-items:center;">
              <div style="display:flex;flex-direction:column;align-items:center;gap:4px;padding:0 12px;">
                <div style="width:36px;height:36px;background:rgba(0,80,200,0.3);border:1px solid rgba(0,150,255,0.3);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">📄</div>
                <span style="color:rgba(160,200,255,0.8) !important;font-size:0.6rem;font-weight:700;letter-spacing:1px;">EXTRAIRE</span>
              </div>
              <div style="width:1px;height:40px;background:rgba(0,150,255,0.18);"></div>
              <div style="display:flex;flex-direction:column;align-items:center;gap:4px;padding:0 12px;">
                <div style="width:36px;height:36px;background:rgba(0,80,200,0.3);border:1px solid rgba(0,150,255,0.3);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">🗄️</div>
                <span style="color:rgba(160,200,255,0.8) !important;font-size:0.6rem;font-weight:700;letter-spacing:1px;">COMPRENDRE</span>
              </div>
              <div style="width:1px;height:40px;background:rgba(0,150,255,0.18);"></div>
              <div style="display:flex;flex-direction:column;align-items:center;gap:4px;padding:0 12px;">
                <div style="width:36px;height:36px;background:rgba(0,80,200,0.3);border:1px solid rgba(0,150,255,0.3);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">📈</div>
                <span style="color:rgba(160,200,255,0.8) !important;font-size:0.6rem;font-weight:700;letter-spacing:1px;">VALORISER</span>
              </div>
              <div style="width:1px;height:40px;background:rgba(0,150,255,0.18);"></div>
              <div style="display:flex;flex-direction:column;align-items:center;gap:4px;padding:0 12px;">
                <div style="width:36px;height:36px;background:rgba(0,80,200,0.3);border:1px solid rgba(0,150,255,0.3);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">🛡️</div>
                <span style="color:rgba(160,200,255,0.8) !important;font-size:0.6rem;font-weight:700;letter-spacing:1px;">SÉCURISÉ</span>
              </div>
            </div>
          </div>

          <div style="padding:20px 28px 4px 28px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
              <div style="width:42px;height:42px;background:rgba(0,80,200,0.3);border:1px solid rgba(0,150,255,0.4);border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;">🔐</div>
              <div>
                <div style="font-size:1.05rem;font-weight:800;color:#ffffff !important;">Authentification</div>
                <div style="font-size:0.72rem;color:rgba(130,175,230,0.65) !important;">Accédez à votre base de données en toute sécurité</div>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            _email = st.text_input("em", placeholder="✉   User@email.com",  label_visibility="collapsed")
            _pwd   = st.text_input("pw", placeholder="🔒   Mot de passe",    type="password", label_visibility="collapsed")
            _c1, _c2 = st.columns([1.2, 1])
            with _c1: st.checkbox("Se souvenir de moi")
            with _c2: st.markdown('<div style="text-align:right;padding-top:6px;color:#0099ff !important;font-size:0.77rem;cursor:pointer;">Mot de passe oublié ?</div>', unsafe_allow_html=True)
            _submit = st.form_submit_button("Se connecter  →", use_container_width=True)

        st.markdown('<div style="text-align:center;color:rgba(80,120,180,0.45) !important;font-size:0.67rem;margin-top:12px;">DouaneXtract v1.0 &nbsp;·&nbsp; Direction Générale des Douanes Tunisiennes</div>', unsafe_allow_html=True)

        if _submit:
            if not _email or not _pwd:
                st.error("⚠️ Veuillez remplir tous les champs.")
            else:
                _user = auth.login(_email, _pwd)
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
    logo_html = f'<img src="data:image/png;base64,{LOGO_B64}" style="width:90px;display:block;margin:0 auto 12px auto;filter:drop-shadow(0 0 10px rgba(100,160,255,0.3));">' if LOGO_B64 else ""
    st.markdown(f"""
    <div style="padding:24px 16px 8px 16px;text-align:center;">
        {logo_html}
        <div style="font-size:1.6rem;font-weight:900;letter-spacing:0.5px;margin-bottom:2px;">
            <span style="color:#ffffff;">Douane</span><span style="color:#60a5fa;">Xtract</span>
        </div>
        <div style="font-size:0.68rem;color:rgba(148,163,184,0.8);letter-spacing:0.5px;">
            Base de données Douanes
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:12px 0;'>", unsafe_allow_html=True)

    # Bouton actif en surbrillance
    mod = st.session_state.get("module","dashboard")
    def nav_btn(label, key, icon=""):
        active = "background:rgba(37,99,235,0.6) !important;border-color:rgba(96,165,250,0.5) !important;color:white !important;" if mod==key else ""
        if st.button(label, use_container_width=True, key=f"nav_{key}"):
            st.session_state["module"] = key; st.rerun()

    nav_btn("🏠  Tableau de bord",  "dashboard")
    nav_btn("📋  Avis Tarifaires",  "tarifaires")
    nav_btn("📁  Secrétariat",      "secretariat")
    nav_btn("🌐  Décisions OMD",    "omd")
    if is_admin:
        nav_btn("👥  Utilisateurs", "users")

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:16px 0 12px 0;'>", unsafe_allow_html=True)
    if st.button("🚪  Se déconnecter", use_container_width=True, key="nav_logout"):
        del st.session_state["user"]
        st.session_state["module"] = "dashboard"
        st.rerun()


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

    page = st.radio("", ["🔍 Recherche", "📤 Ajouter", "✏️ Modifier"],
                    horizontal=True, label_visibility="collapsed")

    total_omd = len(db.get_all_omd())

    # ── RECHERCHE ─────────────────────────────────────────────────────────────
    if page == "🔍 Recherche":
        st.markdown("""
        <h2 style='color:#0a1628;font-size:1.65rem;font-weight:800;margin-bottom:4px;'>
            Recherche — Décisions OMD
        </h2>
        <p style='color:#6b7280;font-size:0.9rem;margin-bottom:20px;'>
            Recherchez par code de classement, description ou motif.
        </p>
        """, unsafe_allow_html=True)

        if total_omd > 0:
            st.markdown(f"""
            <div style='display:inline-flex;align-items:center;gap:8px;
                background:#eff6ff;border:1px solid #bfdbfe;
                border-radius:8px;padding:6px 14px;margin-bottom:16px;'>
                <span style='color:#1d4ed8;font-size:0.82rem;'>
                    ℹ️ Base de données : <b>{total_omd:,}</b> décisions disponibles
                </span>
            </div>
            """, unsafe_allow_html=True)

        # Barre de recherche
        st.markdown("""
        <div style='background:#f8fafc;border:1.5px solid #e2e8f0;
            border-radius:12px;padding:20px 24px;margin-bottom:24px;'>
            <div style='color:#374151;font-size:0.82rem;font-weight:600;margin-bottom:8px;'>
                Recherche libre
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_q, col_btn = st.columns([4, 1])
        with col_q:
            query = st.text_input("q", placeholder="Ex: 17.04, sucreries, bacon, 22ème session...",
                                  label_visibility="collapsed", key="omd_q")
        with col_btn:
            rechercher = st.button("🔍  Rechercher", type="primary", use_container_width=True)

        # Filtres
        with st.expander("🔧 Filtres par champ", expanded=False):
            fc1, fc2, fc3 = st.columns(3)
            f_classement = fc1.text_input("Classement (ex: 17, 19.05)", key="omd_fc")
            f_session    = fc2.text_input("Session (ex: 22ème)", key="omd_fs")
            f_desc       = fc3.text_input("Description contient", key="omd_fd")

        if (rechercher or query or f_classement or f_session or f_desc) and total_omd > 0:
            # Recherche
            if query:
                results = db.search_omd(query)
            else:
                results = db.get_all_omd()

            # Filtres additionnels
            if f_classement.strip():
                results = [r for r in results if f_classement.strip() in (r.get("classement") or "")]
            if f_session.strip():
                results = [r for r in results if f_session.strip().lower() in (r.get("session") or "").lower()]
            if f_desc.strip():
                results = [r for r in results if f_desc.strip().lower() in (r.get("description") or "").lower()]

            nb = len(results)

            if nb == 0:
                st.markdown("""
                <div style='background:#fef2f2;border:1px solid #fecaca;border-radius:10px;
                    padding:14px 20px;display:flex;align-items:center;gap:10px;'>
                    <span>❌</span>
                    <span style='color:#dc2626;font-size:0.9rem;'>Aucune décision trouvée.</span>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;
                    padding:12px 20px;display:flex;align-items:center;gap:10px;margin-bottom:20px;'>
                    <span>✅</span>
                    <span style='color:#15803d;font-size:0.9rem;'>
                        <b>{nb}</b> décision(s) trouvée(s)
                    </span>
                </div>""", unsafe_allow_html=True)

                for doc in results:
                    clas  = doc.get("classement")  or "—"
                    desc  = doc.get("description") or "—"
                    sess  = doc.get("session")     or "—"
                    motif = doc.get("motif")       or ""
                    num   = doc.get("numero")      or ""

                    # Description courte pour l'en-tête (première ligne)
                    desc_lines = desc.strip().split("\n")
                    desc_short = desc_lines[0][:80] + ("…" if len(desc_lines[0]) > 80 else "")
                    desc_bold  = desc_short.split(" ")[0] if desc_short else ""
                    desc_rest  = desc_short[len(desc_bold):]

                    motif_html = (
                        '<div style="margin-top:10px;padding-top:10px;'
                        'border-top:1px solid #e5e7eb;">'
                        '<span style="color:#374151;font-size:0.82rem;">'
                        '<b>Motif</b> : ' + motif + '</span></div>'
                    ) if motif else ""

                    card = (
                        '<div style="background:#ffffff;border:1px solid #e2e8f0;'
                        'border-radius:12px;padding:18px 20px;margin-bottom:12px;'
                        'box-shadow:0 1px 6px rgba(0,0,0,0.05);">'

                        # Icône + Classement
                        '<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;">'
                        '<div style="width:36px;height:36px;background:#fef3c7;border:1px solid #fcd34d;'
                        'border-radius:8px;display:flex;align-items:center;justify-content:center;'
                        'font-size:18px;flex-shrink:0;">📁</div>'
                        '<div style="font-size:1rem;font-weight:700;color:#1a1a1a;">'
                        'Classement : <span style="color:#d97706;">' + clas + '</span>'
                        '</div>'
                        '</div>'

                        # Description
                        '<div style="color:#374151;font-size:0.875rem;line-height:1.6;margin-bottom:6px;">'
                        '<b>' + desc_bold + '</b>' + desc_rest
                        + '</div>'

                        # Session
                        '<div style="color:#6b7280;font-size:0.8rem;">'
                        '<b>Session</b> : <em>' + sess + '</em>'
                        '</div>'

                        + motif_html +
                        '</div>'
                    )
                    st.markdown(card, unsafe_allow_html=True)

                    # Description complète si longue
                    if len(desc) > 80 or len(desc_lines) > 1:
                        with st.expander("📄 Description complète"):
                            st.write(desc)

        elif total_omd == 0:
            st.warning("⚠️ Aucune décision en base. Ajoutez un fichier via 'Ajouter'.")

    # ── AJOUTER ──────────────────────────────────────────────────────────────
    elif page == "📤 Ajouter":
        st.markdown("""
        <h2 style='color:#0a1628;font-size:1.5rem;font-weight:800;margin-bottom:8px;'>
            📤 Ajouter des décisions OMD
        </h2>
        """, unsafe_allow_html=True)
        st.markdown("---")

        st.info("""
        **Format du fichier Excel attendu :**
        - Colonne **N°** ou **NUMERO** — numéro de la décision
        - Colonne **DESCRIPTION** — description du produit
        - Colonne **CLASSEMENT** — code HS (ex: 17.04, 19.05)
        - Colonne **MOTIF** — motif du classement (optionnel)
        - Colonne **SESSION** — session du comité (ex: 22ème Session (1998))

        **Ou uploadez directement le PDF** — les données seront extraites automatiquement.
        """)

        tab_xl, tab_pdf, tab_manuel = st.tabs(["📊 Fichier Excel", "📄 PDF", "✏️ Saisie manuelle"])

        # ── Excel
        with tab_xl:
            uploaded_xl = st.file_uploader("Glisser le fichier Excel", type=["xlsx","xls"], key="omd_xl")
            if uploaded_xl:
                import pandas as _pd
                try:
                    df = _pd.read_excel(uploaded_xl)
                    st.success(f"✅ {len(df)} lignes détectées")
                    st.dataframe(df.head(5), use_container_width=True, hide_index=True)

                    # Mapper les colonnes
                    cols = [c.upper() for c in df.columns]
                    col_map = {}
                    for field, aliases in {
                        "numero":      ["N°","NUMERO","NUM","NO"],
                        "description": ["DESCRIPTION","DESC","PRODUIT"],
                        "classement":  ["CLASSEMENT","HS CODE","CODE","HS"],
                        "motif":       ["MOTIF","MOTIF DU CLASSEMENT","RAISON"],
                        "session":     ["SESSION","COMITE"],
                    }.items():
                        for a in aliases:
                            if a in cols:
                                col_map[field] = df.columns[cols.index(a)]
                                break

                    st.write("**Correspondance colonnes :**", col_map)

                    if st.button("🚀 Importer", type="primary"):
                        ok_count = 0
                        for _, row in df.iterrows():
                            data = {
                                "filename":    uploaded_xl.name,
                                "numero":      str(row.get(col_map.get("numero",""),"")) if col_map.get("numero") else "",
                                "description": str(row.get(col_map.get("description",""),"")) if col_map.get("description") else "",
                                "classement":  str(row.get(col_map.get("classement",""),"")) if col_map.get("classement") else "",
                                "motif":       str(row.get(col_map.get("motif",""),"")) if col_map.get("motif") else "",
                                "session":     str(row.get(col_map.get("session",""),"")) if col_map.get("session") else "",
                            }
                            if data["description"] and data["description"] != "nan":
                                db.insert_omd(data)
                                ok_count += 1
                        st.success(f"✅ {ok_count} décisions importées !")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")

        # ── PDF (Extraction automatique)
        with tab_pdf:
            st.markdown(
                '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;'
                'padding:14px 18px;margin-bottom:16px;">"'
                '<b style="color:#1d4ed8;">📄 Extraction automatique</b><br>'
                '<span style="color:#374151;font-size:0.85rem;">Le PDF est analysé automatiquement.'
                ' Décisions extraites et enregistrées directement.</span></div>',
                unsafe_allow_html=True)
            uploaded_pdf = st.file_uploader("Glisser le PDF OMD", type=["pdf"], key="omd_pdf")
            if uploaded_pdf:
                dest = os.path.join(PDF_DIR, uploaded_pdf.name)
                with open(dest,"wb") as fp: fp.write(uploaded_pdf.getbuffer())
                if st.button("🚀 Extraire et enregistrer automatiquement", type="primary", key="omd_extract"):
                    with st.spinner("Extraction en cours..."):
                        decisions = ocr.parse_omd_pdf(dest, uploaded_pdf.name)
                    if not decisions:
                        st.error("❌ Aucune décision trouvée. Vérifiez le format du PDF.")
                    else:
                        st.success(f"✅ **{len(decisions)}** décision(s) détectée(s) !")
                        st.markdown("**Aperçu des premières décisions extraites :**")
                        for d in decisions[:5]:
                            card = (
                                '<div style="background:#f8fafc;border:1px solid #e2e8f0;'
                                'border-radius:8px;padding:10px 14px;margin-bottom:8px;">'
                                '<span style="color:#d97706;font-weight:700;">N°' + d["numero"] + ' — ' + d["classement"] + '</span><br>'
                                '<span style="color:#374151;font-size:0.82rem;">' + d["description"][:100] + '...</span></div>'
                            )
                            st.markdown(card, unsafe_allow_html=True)
                        if len(decisions) > 5:
                            st.caption(f"... et {len(decisions)-5} autres décisions")
                        st.markdown("---")
                        col_ok, col_ann = st.columns(2)
                        with col_ok:
                            if st.button("💾 Confirmer et enregistrer en base", type="primary", key="omd_save"):
                                for d in decisions:
                                    db.insert_omd(d)
                                st.success(f"✅ {len(decisions)} décisions enregistrées !")
                                st.rerun()
                        with col_ann:
                            if st.button("❌ Annuler", key="omd_cancel"):
                                st.rerun()

        # ── Saisie manuelle
        with tab_manuel:
            with st.form("add_omd_form"):
                st.markdown("**Ajouter une décision manuellement**")
                c1, c2 = st.columns(2)
                num  = c1.text_input("N° de décision")
                clas = c2.text_input("Classement (ex: 17.04)")
                sess = st.text_input("Session (ex: 22ème Session (1998))")
                desc = st.text_area("Description du produit", height=120)
                motif_txt = st.text_area("Motif du classement (optionnel)", height=80)
                if st.form_submit_button("➕ Ajouter", type="primary"):
                    if not desc or not clas:
                        st.error("Description et Classement sont obligatoires.")
                    else:
                        db.insert_omd({
                            "filename": "saisie_manuelle",
                            "numero": num, "description": desc,
                            "classement": clas, "motif": motif_txt, "session": sess
                        })
                        st.success("✅ Décision ajoutée !")
                        st.rerun()

    # ── MODIFIER ──────────────────────────────────────────────────────────────
    elif page == "✏️ Modifier":
        st.markdown("""
        <h2 style='color:#0a1628;font-size:1.5rem;font-weight:800;margin-bottom:8px;'>
            ✏️ Modifier / Supprimer
        </h2>
        """, unsafe_allow_html=True)
        st.markdown("---")

        docs = db.get_all_omd()
        if not docs:
            st.info("Aucune décision disponible.")
        else:
            q_mod = st.text_input("Rechercher par classement ou description",
                                   placeholder="ex: 17.04, sucreries")
            if q_mod:
                docs = [d for d in docs if
                        q_mod.lower() in (d.get("classement") or "").lower() or
                        q_mod.lower() in (d.get("description") or "").lower()]

            if not docs:
                st.warning("Aucun résultat.")
            else:
                opts = {f"[{d['id']}] {d.get('classement','')} — {(d.get('description') or '')[:40]}": d['id'] for d in docs}
                sel  = st.selectbox("Choisir une décision", list(opts.keys()))
                doc  = db.get_omd_by_id(opts[sel])

                tab_e, tab_d = st.tabs(["✏️ Modifier","🗑️ Supprimer"])
                with tab_e:
                    with st.form("edit_omd"):
                        c1, c2 = st.columns(2)
                        num  = c1.text_input("N°",           value=doc.get("numero")     or "")
                        clas = c2.text_input("Classement",   value=doc.get("classement") or "")
                        sess = st.text_input("Session",      value=doc.get("session")    or "")
                        desc = st.text_area("Description",   value=doc.get("description") or "", height=120)
                        motif_txt = st.text_area("Motif",    value=doc.get("motif")      or "", height=80)
                        if st.form_submit_button("💾 Enregistrer", type="primary"):
                            db.update_omd(opts[sel],{
                                "numero":num,"description":desc,
                                "classement":clas,"motif":motif_txt,"session":sess})
                            st.success("✅ Mis à jour !"); st.rerun()
                with tab_d:
                    st.warning(f"⚠️ Supprimer la décision **{doc.get('classement')}** ?")
                    if st.checkbox("Je confirme"):
                        if st.button("🗑️ Supprimer", type="primary"):
                            db.delete_omd(opts[sel])
                            st.success("Supprimé."); st.rerun()


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