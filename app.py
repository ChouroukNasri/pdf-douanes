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

# ── Charger logo ──────────────────────────────────────────────────────────────
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
.stApp {
    background: radial-gradient(ellipse at 30% 20%, #0d2060 0%, #020b28 55%, #010818 100%);
    min-height: 100vh;
}
header[data-testid="stHeader"] {
    background: rgba(2,11,40,0.95) !important;
    border-bottom: 1px solid rgba(0,180,255,0.15) !important;
}
section[data-testid="stSidebar"] {
    background: rgba(2,11,40,0.97) !important;
    border-right: 1px solid rgba(0,180,255,0.2) !important;
}
section[data-testid="stSidebar"] * { color: rgba(180,215,255,0.85) !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(0,180,255,0.2) !important; }
p, li { color: rgba(200,225,255,0.88) !important; }
h1,h2,h3 { color: #ffffff !important; }
label { color: rgba(180,210,255,0.85) !important; }
input[type="text"],input[type="password"],textarea {
    background: rgba(0,30,80,0.55) !important;
    border: 1px solid rgba(0,180,255,0.3) !important;
    color: #ffffff !important; border-radius: 8px !important;
}
input:focus,textarea:focus {
    border-color: #00c8ff !important;
    box-shadow: 0 0 0 2px rgba(0,200,255,0.2) !important;
}
.stButton button[kind="primary"],.stFormSubmitButton button {
    background: linear-gradient(90deg,#0050d8,#00a8ff) !important;
    color:white !important; border:none !important;
    border-radius:8px !important; font-weight:600 !important;
}
.stButton button[kind="primary"]:hover,.stFormSubmitButton button:hover {
    background: linear-gradient(90deg,#0060f0,#00c0ff) !important;
    box-shadow: 0 0 20px rgba(0,180,255,0.4) !important;
}
.stButton button {
    background: rgba(0,60,160,0.35) !important;
    border: 1px solid rgba(0,180,255,0.3) !important;
    color: rgba(180,220,255,0.9) !important; border-radius:8px !important;
}
.stTabs [data-baseweb="tab-list"] { background:rgba(0,20,70,0.6) !important; border-radius:10px; padding:4px; }
.stTabs [data-baseweb="tab"] { color:rgba(160,200,255,0.7) !important; }
.stTabs [aria-selected="true"] { color:#00c8ff !important; background:rgba(0,80,200,0.3) !important; border-radius:8px !important; }
.streamlit-expanderHeader { background:rgba(0,40,120,0.4) !important; border:1px solid rgba(0,180,255,0.2) !important; border-radius:8px !important; }
.streamlit-expanderContent { background:rgba(0,15,55,0.6) !important; }
[data-testid="stMetricLabel"] { color:rgba(150,190,255,0.7) !important; }
[data-testid="stMetricValue"] { color:#00c8ff !important; font-weight:700 !important; }
.stSuccess { background:rgba(0,80,50,0.35) !important; border-left-color:#00e090 !important; }
.stError   { background:rgba(120,0,0,0.35) !important;  border-left-color:#ff5050 !important; }
.stWarning { background:rgba(100,60,0,0.35) !important; border-left-color:#ffb800 !important; }
.stInfo    { background:rgba(0,50,140,0.35) !important; border-left-color:#00c8ff !important; }
.stProgress > div > div { background:linear-gradient(90deg,#0050d8,#00c8ff) !important; }
hr { border-color:rgba(0,180,255,0.15) !important; }

/* Cards dashboard */
.module-card {
    background: rgba(4,20,80,0.6);
    border: 1px solid rgba(0,150,255,0.3);
    border-radius: 16px; padding: 28px;
    text-align: center; cursor: pointer;
    transition: all 0.2s;
}
.module-card:hover {
    border-color: rgba(0,200,255,0.6);
    box-shadow: 0 0 30px rgba(0,150,255,0.2);
    transform: translateY(-2px);
}
.module-icon { font-size: 3rem; margin-bottom: 12px; }
.module-title { font-size: 1.1rem; font-weight: 700; color: #ffffff !important; margin-bottom: 6px; }
.module-desc  { font-size: 0.78rem; color: rgba(150,190,255,0.7) !important; margin-bottom: 16px; }
.module-count { font-size: 2rem; font-weight: 800; color: #00c8ff !important; }
.module-label { font-size: 0.72rem; color: rgba(130,170,220,0.6) !important; }
.acceder-btn  { display:inline-block; margin-top:14px; padding:8px 24px;
    background:linear-gradient(90deg,#0050d8,#00a8ff); color:white !important;
    border-radius:8px; font-weight:600; font-size:0.85rem; }

/* Result cards */
.result-card { background:rgba(255,255,255,0.04) !important; border:1px solid rgba(0,180,255,0.2) !important; border-radius:10px; padding:14px; margin-bottom:8px; }
.badge       { background:linear-gradient(90deg,#0050d8,#00a8ff); color:white !important; border-radius:4px; padding:2px 8px; font-size:0.82rem; font-weight:600; }
.badge-green { background:rgba(0,180,100,0.2); border:1px solid rgba(0,200,100,0.4); color:#00e090 !important; border-radius:4px; padding:2px 8px; font-size:0.82rem; font-weight:600; }
.badge-purple{ background:rgba(120,80,220,0.2); border:1px solid rgba(150,100,255,0.4); color:#b090ff !important; border-radius:4px; padding:2px 8px; font-size:0.82rem; font-weight:600; }
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

    st.markdown("""
    <style>
    header[data-testid="stHeader"]   { display:none !important; }
    section[data-testid="stSidebar"] { display:none !important; }
    #MainMenu, footer { display:none !important; }
    .block-container { padding-top:0 !important; max-width:100% !important; }
    .stTextInput label { display:none !important; }
    .stCheckbox label span { color:rgba(150,190,255,0.75) !important; font-size:0.8rem !important; }
    .login-submit button {
        background:linear-gradient(90deg,#0050d8,#0099ff) !important;
        color:white !important; border:none !important; border-radius:10px !important;
        font-weight:700 !important; font-size:1rem !important; padding:13px !important;
    }
    .login-submit button:hover {
        background:linear-gradient(90deg,#0066ff,#00bbff) !important;
        box-shadow:0 4px 28px rgba(0,140,255,0.5) !important;
    }
    </style>""", unsafe_allow_html=True)

    _img_tag = f'<img src="data:image/png;base64,{_logo}" style="width:160px;filter:drop-shadow(0 0 18px rgba(0,150,255,0.4));">' if _logo else ""

    st.markdown("<br>", unsafe_allow_html=True)
    _, _col, _ = st.columns([1, 2, 1])
    with _col:
        # Card complète — haut (illustration + titre + features)
        st.markdown(f"""
        <div style="background:rgba(4,16,60,0.82);border:1px solid rgba(0,140,255,0.35);
            border-radius:24px;overflow:hidden;backdrop-filter:blur(20px);
            box-shadow:0 8px 60px rgba(0,80,255,0.22);max-width:460px;margin:0 auto;">

          <!-- TOP : logo + titre + features -->
          <div style="background:radial-gradient(ellipse at 50% 30%,#0d2878,#020f40);
              border-bottom:1px solid rgba(0,140,255,0.2);padding:28px 28px 20px;text-align:center;">
            {_img_tag}
            <div style="font-size:2.2rem;font-weight:900;letter-spacing:1px;margin-top:10px;margin-bottom:4px;">
              <span style="color:#fff;">Douane</span><span style="color:#00aaff;">Xtract</span>
            </div>
            <div style="color:rgba(150,190,255,0.65);font-size:0.76rem;letter-spacing:0.7px;margin-bottom:18px;">
              Base de données — Avis de Classement Tarifaire
            </div>
            <!-- 4 features -->
            <div style="display:flex;justify-content:center;align-items:center;">
              <div style="display:flex;flex-direction:column;align-items:center;gap:4px;padding:0 12px;">
                <div style="width:36px;height:36px;background:rgba(0,80,200,0.3);border:1px solid rgba(0,150,255,0.3);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">📄</div>
                <span style="color:rgba(160,200,255,0.8);font-size:0.6rem;font-weight:700;letter-spacing:1px;">EXTRAIRE</span>
              </div>
              <div style="width:1px;height:40px;background:rgba(0,150,255,0.18);"></div>
              <div style="display:flex;flex-direction:column;align-items:center;gap:4px;padding:0 12px;">
                <div style="width:36px;height:36px;background:rgba(0,80,200,0.3);border:1px solid rgba(0,150,255,0.3);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">🗄️</div>
                <span style="color:rgba(160,200,255,0.8);font-size:0.6rem;font-weight:700;letter-spacing:1px;">COMPRENDRE</span>
              </div>
              <div style="width:1px;height:40px;background:rgba(0,150,255,0.18);"></div>
              <div style="display:flex;flex-direction:column;align-items:center;gap:4px;padding:0 12px;">
                <div style="width:36px;height:36px;background:rgba(0,80,200,0.3);border:1px solid rgba(0,150,255,0.3);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">📈</div>
                <span style="color:rgba(160,200,255,0.8);font-size:0.6rem;font-weight:700;letter-spacing:1px;">VALORISER</span>
              </div>
              <div style="width:1px;height:40px;background:rgba(0,150,255,0.18);"></div>
              <div style="display:flex;flex-direction:column;align-items:center;gap:4px;padding:0 12px;">
                <div style="width:36px;height:36px;background:rgba(0,80,200,0.3);border:1px solid rgba(0,150,255,0.3);border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;">🛡️</div>
                <span style="color:rgba(160,200,255,0.8);font-size:0.6rem;font-weight:700;letter-spacing:1px;">SÉCURISÉ</span>
              </div>
            </div>
          </div>

          <!-- BOTTOM : auth header -->
          <div style="padding:20px 28px 4px 28px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;">
              <div style="width:42px;height:42px;background:rgba(0,80,200,0.3);border:1px solid rgba(0,150,255,0.4);border-radius:11px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;">🔐</div>
              <div>
                <div style="font-size:1.05rem;font-weight:800;color:#fff;">Authentification</div>
                <div style="font-size:0.72rem;color:rgba(130,175,230,0.65);">Accédez à votre base de données en toute sécurité</div>
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Formulaire — rendu sous la card visuellement aligné
        st.markdown("""
        <div style="background:rgba(4,16,60,0.82);border:1px solid rgba(0,140,255,0.35);
            border-top:none;border-radius:0 0 24px 24px;padding:0 28px 24px 28px;
            max-width:460px;margin:-6px auto 0 auto;backdrop-filter:blur(20px);">
        </div>""", unsafe_allow_html=True)

        with st.form("login_form"):
            _email = st.text_input("em", placeholder="✉   User@email.com",  label_visibility="collapsed")
            _pwd   = st.text_input("pw", placeholder="🔒   Mot de passe",    type="password", label_visibility="collapsed")
            _c1, _c2 = st.columns([1.2, 1])
            with _c1: st.checkbox("Se souvenir de moi")
            with _c2: st.markdown('<div style="text-align:right;padding-top:6px;color:#0099ff;font-size:0.77rem;cursor:pointer;">Mot de passe oublié ?</div>', unsafe_allow_html=True)
            _submit = st.form_submit_button("Se connecter  →", use_container_width=True)

        st.markdown('<div style="text-align:center;color:rgba(80,120,180,0.35);font-size:0.67rem;margin-top:12px;max-width:460px;margin-left:auto;margin-right:auto;">DouaneXtract v1.0 &nbsp;·&nbsp; Direction Générale des Douanes Tunisiennes</div>', unsafe_allow_html=True)

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

# Module actif (dashboard ou sous-module)
if "module" not in st.session_state:
    st.session_state["module"] = "dashboard"

module = st.session_state["module"]


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    logo_html = f'<img src="data:image/png;base64,{LOGO_B64}" style="width:80px;display:block;margin:0 auto 8px auto;">' if LOGO_B64 else ""
    st.markdown(f"""
    {logo_html}
    <div style="text-align:center;font-size:1.1rem;font-weight:800;margin-bottom:2px;">
        <span style="color:#fff;">Douane</span><span style="color:#00aaff;">Xtract</span>
    </div>
    <div style="text-align:center;font-size:0.65rem;color:rgba(130,170,220,0.6);margin-bottom:12px;letter-spacing:0.5px;">
        Base de données Douanes
    </div>
    """, unsafe_allow_html=True)


    # Navigation principale
    if st.button("🏠  Tableau de bord",  use_container_width=True):
        st.session_state["module"] = "dashboard"; st.rerun()
    if st.button("📋  Avis Tarifaires",  use_container_width=True):
        st.session_state["module"] = "tarifaires"; st.rerun()
    if st.button("📁  Secrétariat",      use_container_width=True):
        st.session_state["module"] = "secretariat"; st.rerun()
    if st.button("🌐  Décisions OMD",    use_container_width=True):
        st.session_state["module"] = "omd"; st.rerun()
    if is_admin:
        if st.button("👥  Utilisateurs",  use_container_width=True):
            st.session_state["module"] = "users"; st.rerun()

    st.markdown("---")
    st.markdown(f"**{stats['total']}** documents total")
    st.markdown("---")
    if st.button("🚪  Se déconnecter", use_container_width=True):
        del st.session_state["user"]
        st.session_state["module"] = "dashboard"
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  HELPER : upload PDF générique
# ══════════════════════════════════════════════════════════════════════════════
def upload_pdfs(insert_fn, extra_fields=None):
    tab_up, tab_dir = st.tabs(["📎 Upload fichiers","📂 Import dossier"])
    with tab_up:
        files = st.file_uploader("PDFs", type=["pdf"], accept_multiple_files=True)
        if files and st.button("🚀 Lancer OCR", type="primary"):
            progress = st.progress(0); status = st.empty(); doc_id = None
            for i,f in enumerate(files):
                status.info(f"⏳ {f.name} ({i+1}/{len(files)})")
                dest = os.path.join(PDF_DIR, f.name)
                with open(dest,"wb") as fp: fp.write(f.getbuffer())
                data = ocr.process_pdf(dest, f.name)
                if extra_fields: data.update(extra_fields)
                doc_id = insert_fn(data)
                progress.progress((i+1)/len(files))
            status.success(f"✅ {len(files)} document(s) ajouté(s) !")
            if doc_id: st.rerun()
    with tab_dir:
        folder = st.text_input("Chemin du dossier", placeholder=r"Ex: C:\PDFs")
        if st.button("📂 Importer", type="primary", disabled=not folder):
            if not os.path.exists(folder): st.error("Dossier introuvable.")
            else:
                pdfs = list(set(glob.glob(os.path.join(folder,"**","*.pdf"),recursive=True)+
                                glob.glob(os.path.join(folder,"**","*.PDF"),recursive=True)))
                if not pdfs: st.warning("Aucun PDF trouvé.")
                else:
                    p = st.progress(0); l = st.empty(); ok=0
                    for i,pdf in enumerate(pdfs):
                        fname = os.path.basename(pdf)
                        l.info(f"⏳ {fname}")
                        try:
                            dest = os.path.join(PDF_DIR,fname)
                            shutil.copy2(pdf,dest)
                            data = ocr.process_pdf(dest,fname)
                            if extra_fields: data.update(extra_fields)
                            insert_fn(data); ok+=1
                        except Exception as e: st.error(f"✗ {fname}: {e}")
                        p.progress((i+1)/len(pdfs))
                    l.empty(); st.success(f"✅ {ok} importés"); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if module == "dashboard":
    st.markdown(f"<h1 style='margin-bottom:4px;'>Bonjour, {user['nom']} 👋</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:rgba(150,190,255,0.6);margin-bottom:32px;'>Que souhaitez-vous consulter aujourd'hui ?</p>", unsafe_allow_html=True)

    # 3 cards modules
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="module-card">
            <div class="module-icon">📋</div>
            <div class="module-title">Avis Tarifaires</div>
            <div class="module-desc">Documents PDF scannés — Classement tarifaire</div>
            <div class="module-count">{stats['tarifaires']}</div>
            <div class="module-label">documents indexés</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Accéder →", key="btn_tar", use_container_width=True):
            st.session_state["module"] = "tarifaires"; st.rerun()

    with c2:
        st.markdown(f"""
        <div class="module-card">
            <div class="module-icon">📁</div>
            <div class="module-title">Avis Secrétariat</div>
            <div class="module-desc">Correspondances et avis du secrétariat</div>
            <div class="module-count">{stats['secretariat']}</div>
            <div class="module-label">documents indexés</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Accéder →", key="btn_sec", use_container_width=True):
            st.session_state["module"] = "secretariat"; st.rerun()

    with c3:
        st.markdown(f"""
        <div class="module-card">
            <div class="module-icon">🌐</div>
            <div class="module-title">Décisions OMD</div>
            <div class="module-desc">Organisation Mondiale des Douanes</div>
            <div class="module-count">{stats['omd']}</div>
            <div class="module-label">documents indexés</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Accéder →", key="btn_omd", use_container_width=True):
            st.session_state["module"] = "omd"; st.rerun()

    # Statistiques
    st.markdown("---")
    st.markdown("### Statistiques")
    s1,s2,s3,s4 = st.columns(4)
    s1.metric("📋 Avis Tarifaires",  stats['tarifaires'])
    s2.metric("📁 Secrétariat",      stats['secretariat'])
    s3.metric("🌐 Décisions OMD",    stats['omd'])
    s4.metric("📊 Total documents",  stats['total'])

    # Derniers ajouts
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

    page = st.radio("", ["📤 Ajouter","🔍 Recherche","📋 Documents","✏️ Modifier"],
                    horizontal=True, label_visibility="collapsed")

    if page == "📤 Ajouter":
        upload_pdfs(db.insert_document)

    elif page == "🔍 Recherche":
        cq, cb = st.columns([4,1])
        with cq: query = st.text_input("q", placeholder="N° avis, désignation, tarifaire, NDP…", label_visibility="collapsed")
        with cb: st.button("Rechercher", type="primary", use_container_width=True)
        with st.expander("🔧 Filtres"):
            f1,f2,f3 = st.columns(3)
            fa = f1.text_input("N° Avis")
            ft = f2.text_input("N° Tarifaire")
            fn = f3.text_input("NDP")
        if query or fa or ft or fn:
            results = db.search_documents(query) if query else db.get_all_documents()
            if fa: results = [r for r in results if fa in (r.get("numero_avis") or "")]
            if ft: results = [r for r in results if ft in (r.get("tarif_number") or "")]
            if fn: results = [r for r in results if fn in (r.get("ndp") or "")]
            st.markdown(f"**{len(results)} résultat(s)**")
            for doc in results:
                st.markdown(f"""<div class='result-card'>
                    <b>📄 {doc['filename']}</b> &nbsp;
                    <span class='badge'>{doc.get('tarif_number') or '?'}</span> &nbsp;
                    <span style='color:#00c8ff;font-size:0.82rem'>NDP {doc.get('ndp') or '?'}</span>
                    <span style='float:right;color:#aaa;font-size:0.78rem'>{doc.get('upload_date','')[:10]}</span>
                </div>""", unsafe_allow_html=True)
                a,b,c = st.columns(3)
                a.metric("N° Avis", doc.get("numero_avis") or "—")
                b.metric("N° Tarifaire", doc.get("tarif_number") or "—")
                c.metric("NDP", doc.get("ndp") or "—")
                st.write(f"**Usage :** {doc.get('usage_text') or '—'}")
                with st.expander("📄 Texte OCR"): st.text(doc.get("full_text","")[:3000])
                st.markdown("---")

    elif page == "📋 Documents":
        docs = db.get_all_documents()
        if not docs: st.info("Aucun document.")
        else:
            df = pd.DataFrame(docs)[["id","numero_avis","tarif_number","ndp","usage_text","upload_date"]]
            df.columns = ["ID","N° Avis","N° Tarifaire","NDP","Usage","Date"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("⬇️ CSV", data=csv, file_name="avis_tarifaires.csv", mime="text/csv")

    elif page == "✏️ Modifier":
        docs = db.get_all_documents()
        if not docs: st.info("Aucun document.")
        else:
            opts = {f"[{d['id']}] {d['filename']}": d['id'] for d in docs}
            sel  = st.selectbox("Document", list(opts.keys()))
            doc  = db.get_document_by_id(opts[sel])
            tab_e, tab_o, tab_d = st.tabs(["✏️ Modifier","📄 OCR","🗑️ Supprimer"])
            with tab_e:
                with st.form("edit_tar"):
                    c1,c2,c3 = st.columns(3)
                    na = c1.text_input("N° Avis",      value=doc.get("numero_avis") or "")
                    tn = c2.text_input("N° Tarifaire", value=doc.get("tarif_number") or "")
                    nd = c3.text_input("NDP",          value=doc.get("ndp") or "")
                    de = st.text_area("Désignation",   value=doc.get("designation") or "", height=60)
                    us = st.text_area("Usage",         value=doc.get("usage_text") or "", height=80)
                    if st.form_submit_button("💾 Enregistrer", type="primary"):
                        db.update_document(opts[sel],{"numero_avis":na,"designation":de,"usage_text":us,"tarif_number":tn,"ndp":nd})
                        st.success("✅ Mis à jour !"); st.rerun()
            with tab_o: st.text_area("OCR", value=doc.get("full_text") or "", height=400)
            with tab_d:
                st.warning(f"Supprimer {doc['filename']} ?")
                if st.checkbox("Confirmer"):
                    if st.button("🗑️ Supprimer", type="primary"):
                        db.delete_document(opts[sel]); st.success("Supprimé."); st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — SECRETARIAT
# ══════════════════════════════════════════════════════════════════════════════
elif module == "secretariat":
    st.markdown("## 📁 Avis Secrétariat")
    st.caption("Correspondances et avis du secrétariat général")
    st.markdown("---")

    page = st.radio("", ["📤 Ajouter","🔍 Recherche","📋 Documents","✏️ Modifier"],
                    horizontal=True, label_visibility="collapsed")

    if page == "📤 Ajouter":
        upload_pdfs(db.insert_secretariat)

    elif page == "🔍 Recherche":
        cq, cb = st.columns([4,1])
        with cq: query = st.text_input("q", placeholder="N° avis, objet, destinataire, référence…", label_visibility="collapsed")
        with cb: st.button("Rechercher", type="primary", use_container_width=True)
        with st.expander("🔧 Filtres"):
            f1,f2 = st.columns(2)
            fa = f1.text_input("N° Avis")
            fo = f2.text_input("Objet contient")
        if query or fa or fo:
            results = db.search_secretariat(query) if query else db.get_all_secretariat()
            if fa: results = [r for r in results if fa in (r.get("numero_avis") or "")]
            if fo: results = [r for r in results if fo.lower() in (r.get("objet") or "").lower()]
            st.markdown(f"**{len(results)} résultat(s)**")
            for doc in results:
                st.markdown(f"""<div class='result-card'>
                    <b>📄 {doc['filename']}</b> &nbsp;
                    <span class='badge-green'>N° {doc.get('numero_avis') or '?'}</span>
                    <span style='float:right;color:#aaa;font-size:0.78rem'>{doc.get('upload_date','')[:10]}</span>
                </div>""", unsafe_allow_html=True)
                a,b,c = st.columns(3)
                a.metric("N° Avis",      doc.get("numero_avis") or "—")
                b.metric("Date",         doc.get("date_avis") or "—")
                c.metric("Référence",    doc.get("reference") or "—")
                st.write(f"**Objet :** {doc.get('objet') or '—'}")
                st.write(f"**Destinataire :** {doc.get('destinataire') or '—'}")
                with st.expander("📄 Texte OCR"): st.text(doc.get("full_text","")[:3000])
                st.markdown("---")

    elif page == "📋 Documents":
        docs = db.get_all_secretariat()
        if not docs: st.info("Aucun document.")
        else:
            df = pd.DataFrame(docs)[["id","numero_avis","objet","date_avis","destinataire","reference","upload_date"]]
            df.columns = ["ID","N° Avis","Objet","Date Avis","Destinataire","Référence","Ajouté le"]
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("⬇️ CSV", data=csv, file_name="secretariat.csv", mime="text/csv")

    elif page == "✏️ Modifier":
        docs = db.get_all_secretariat()
        if not docs: st.info("Aucun document.")
        else:
            opts = {f"[{d['id']}] {d['filename']}": d['id'] for d in docs}
            sel  = st.selectbox("Document", list(opts.keys()))
            doc  = db.get_secretariat_by_id(opts[sel])
            tab_e, tab_o, tab_d = st.tabs(["✏️ Modifier","📄 OCR","🗑️ Supprimer"])
            with tab_e:
                with st.form("edit_sec"):
                    c1,c2,c3 = st.columns(3)
                    na = c1.text_input("N° Avis",      value=doc.get("numero_avis") or "")
                    da = c2.text_input("Date Avis",    value=doc.get("date_avis") or "")
                    re = c3.text_input("Référence",    value=doc.get("reference") or "")
                    ob = st.text_area("Objet",         value=doc.get("objet") or "", height=80)
                    de = st.text_input("Destinataire", value=doc.get("destinataire") or "")
                    if st.form_submit_button("💾 Enregistrer", type="primary"):
                        db.update_secretariat(opts[sel],{"numero_avis":na,"objet":ob,"date_avis":da,"destinataire":de,"reference":re})
                        st.success("✅ Mis à jour !"); st.rerun()
            with tab_o: st.text_area("OCR", value=doc.get("full_text") or "", height=400)
            with tab_d:
                st.warning(f"Supprimer {doc['filename']} ?")
                if st.checkbox("Confirmer"):
                    if st.button("🗑️ Supprimer", type="primary"):
                        db.delete_secretariat(opts[sel]); st.success("Supprimé."); st.rerun()


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
        upload_pdfs(db.insert_omd)

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
                b.metric("Date",        doc.get("date_dec") or "—")
                c.metric("Code SH",     doc.get("code_sh") or "—")
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
                    dd = c2.text_input("Date",        value=doc.get("date_dec") or "")
                    cs = c3.text_input("Code SH",     value=doc.get("code_sh") or "")
                    ti = st.text_area("Titre",        value=doc.get("titre") or "", height=70)
                    ch = st.text_input("Chapitre",    value=doc.get("chapitre") or "")
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