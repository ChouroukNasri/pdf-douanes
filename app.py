"""
PDF Database Manager - Avis de Classement Tarifaire
Avec authentification email / mot de passe
Lancer : streamlit run app.py
"""

import os
import shutil
import glob

import streamlit as st
import pandas as pd

import database as db
import ocr_processor as ocr
import auth

st.set_page_config(page_title="Douanes — Base PDF", page_icon="📑", layout="wide")

PDF_DIR = os.path.join(os.path.dirname(__file__), "data", "pdfs")
os.makedirs(PDF_DIR, exist_ok=True)
db.init_db()
auth.init_auth()

st.markdown("""
<style>
    .main-title  { font-size:2rem; font-weight:700; color:#1a3a5c; }
    .stat-box    { background:#f0f4ff; border-radius:10px; padding:16px; text-align:center; }
    .stat-num    { font-size:2rem; font-weight:800; color:#1a3a5c; }
    .stat-label  { font-size:0.85rem; color:#666; }
    .result-card { background:#fff; border:1px solid #e0e0e0; border-radius:8px;
                   padding:14px; margin-bottom:8px; }
    .badge       { background:#1a3a5c; color:white; border-radius:4px;
                   padding:2px 8px; font-size:0.82rem; font-weight:600; }
    .badge-ndp   { background:#2d6a4f; color:white; border-radius:4px;
                   padding:2px 8px; font-size:0.82rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ECRAN DE CONNEXION
# ══════════════════════════════════════════════════════════════════════════════
def show_login():
    col = st.columns([1, 2, 1])[1]
    with col:
        st.markdown("## 📑 Base PDF Douanes")
        st.caption("Connectez-vous pour accéder à l'application")
        with st.form("login_form"):
            email    = st.text_input("📧 Email",        placeholder="votre@email.com")
            password = st.text_input("🔒 Mot de passe", type="password")
            submit   = st.form_submit_button("Se connecter", type="primary", use_container_width=True)
        if submit:
            if not email or not password:
                st.error("Veuillez remplir tous les champs.")
            else:
                user = auth.login(email, password)
                if user:
                    st.session_state["user"] = user
                    st.rerun()
                else:
                    st.error("Email ou mot de passe incorrect.")
        st.caption("Problème de connexion ? Contactez l'administrateur.")


# ══════════════════════════════════════════════════════════════════════════════
#  VERIFIER SESSION
# ══════════════════════════════════════════════════════════════════════════════
if "user" not in st.session_state:
    show_login()
    st.stop()

user     = st.session_state["user"]
is_admin = user["role"] == "admin"
stats    = db.get_stats()


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 📑 PDF Douanes DB")
    st.markdown(f"👤 **{user['nom']}**")
    st.caption(user["email"])
    if is_admin:
        st.caption("🔑 Administrateur")
    st.markdown("---")

    pages = [
        "🏠 Accueil",
        "📤 Ajouter PDF",
        "🔍 Recherche",
        "📋 Tous les documents",
        "✏️  Modifier / Supprimer",
    ]
    if is_admin:
        pages.append("👥 Gestion utilisateurs")

    page = st.radio("Navigation", pages)
    st.markdown("---")

    st.markdown(f"**{stats['total']}** documents indexés")
    st.markdown("---")

    if st.button("🚪 Se déconnecter", use_container_width=True):
        del st.session_state["user"]
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  ACCUEIL
# ══════════════════════════════════════════════════════════════════════════════
if page == "🏠 Accueil":
    st.markdown(f"<div class='main-title'>📑 Bonjour, {user['nom']} 👋</div>", unsafe_allow_html=True)
    st.caption("Base de données — Avis de Classement Tarifaire")
    st.markdown("---")

    st.markdown(f"""
    <div class='stat-box'>
        <div class='stat-num'>{stats['total']}</div>
        <div class='stat-label'>PDFs indexés</div>
    </div>
    """, unsafe_allow_html=True)

    if stats["total"] > 0:
        st.markdown("### 🕐 Derniers documents ajoutés")
        for doc in db.get_all_documents()[:5]:
            with st.expander(f"📄 {doc['filename']}  —  {doc['upload_date'][:10]}"):
                a, b, c = st.columns(3)
                a.metric("N° Avis",      doc.get("numero_avis")  or "—")
                b.metric("N° Tarifaire", doc.get("tarif_number") or "—")
                c.metric("NDP",          doc.get("ndp")          or "—")
                st.write(f"**Désignation :** {doc.get('designation') or '—'}")


# ══════════════════════════════════════════════════════════════════════════════
#  AJOUTER PDF
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📤 Ajouter PDF":
    st.header("📤 Ajouter des PDFs")
    tab_upload, tab_folder = st.tabs(["📎 Upload fichiers", "📂 Import depuis un dossier"])

    with tab_upload:
        uploaded_files = st.file_uploader("Glissez vos PDFs", type=["pdf"], accept_multiple_files=True)
        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} fichier(s)**")
            if st.button("🚀 Lancer l'extraction OCR", type="primary"):
                existing   = {d["filename"] for d in db.get_all_documents()}
                to_process = [f for f in uploaded_files if f.name not in existing]
                skipped    = [f.name for f in uploaded_files if f.name in existing]
                if skipped:
                    st.warning(f"⟳ Déjà en base : {', '.join(skipped)}")
                progress = st.progress(0)
                status   = st.empty()
                doc_id   = None
                for i, uploaded in enumerate(to_process):
                    status.info(f"⏳ {uploaded.name} ({i+1}/{len(to_process)})")
                    dest = os.path.join(PDF_DIR, uploaded.name)
                    with open(dest, "wb") as f:
                        f.write(uploaded.getbuffer())
                    data   = ocr.process_pdf(dest, uploaded.name)
                    doc_id = db.insert_document(data)
                    progress.progress((i + 1) / len(to_process))
                if to_process:
                    status.success(f"✅ {len(to_process)} document(s) ajouté(s) !")
                    if doc_id:
                        doc = db.get_document_by_id(doc_id)
                        a, b, c = st.columns(3)
                        a.metric("N° Avis",      doc.get("numero_avis")  or "Non détecté")
                        b.metric("N° Tarifaire", doc.get("tarif_number") or "Non détecté")
                        c.metric("NDP",          doc.get("ndp")          or "Non détecté")
                        st.write(f"**Désignation :** {doc.get('designation') or 'Non détectée'}")
                        with st.expander("📄 Texte OCR"):
                            st.text(doc.get("full_text", "")[:4000])

    with tab_folder:
        st.info("💡 Importez en masse tous les PDFs d'un dossier local.")
        folder_path   = st.text_input("Chemin du dossier", placeholder=r"Ex: C:\Users\Vous\PDFs_Douanes")
        skip_existing = st.checkbox("Ignorer les fichiers déjà en base", value=True)
        if st.button("📂 Lancer l'import", type="primary", disabled=not folder_path):
            if not os.path.exists(folder_path):
                st.error("❌ Dossier introuvable.")
            else:
                pdf_files = list(set(
                    glob.glob(os.path.join(folder_path, "**", "*.pdf"), recursive=True) +
                    glob.glob(os.path.join(folder_path, "**", "*.PDF"), recursive=True)
                ))
                if not pdf_files:
                    st.warning("Aucun PDF trouvé.")
                else:
                    existing = {d["filename"] for d in db.get_all_documents()}
                    progress = st.progress(0)
                    log      = st.empty()
                    results  = {"ok": 0, "skipped": 0, "error": 0}
                    for i, pdf_path in enumerate(pdf_files):
                        fname = os.path.basename(pdf_path)
                        if skip_existing and fname in existing:
                            results["skipped"] += 1
                        else:
                            log.info(f"⏳ ({i+1}/{len(pdf_files)}) {fname}")
                            try:
                                dest = os.path.join(PDF_DIR, fname)
                                shutil.copy2(pdf_path, dest)
                                data = ocr.process_pdf(dest, fname)
                                db.insert_document(data)
                                existing.add(fname)
                                results["ok"] += 1
                            except Exception as e:
                                results["error"] += 1
                                st.error(f"✗ {fname} : {e}")
                        progress.progress((i + 1) / len(pdf_files))
                    log.empty()
                    st.success(f"✅ {results['ok']} importés · {results['skipped']} ignorés · {results['error']} erreurs")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  RECHERCHE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔍 Recherche":
    st.header("🔍 Recherche")
    col_q, col_btn = st.columns([4, 1])
    with col_q:
        query = st.text_input("Rechercher", label_visibility="collapsed",
            placeholder="Ex: LED, 940540, RGBW…")
    with col_btn:
        st.button("Rechercher", type="primary", use_container_width=True)

    with st.expander("🔧 Filtres par champ"):
        f1, f2, f3 = st.columns(3)
        filter_avis  = f1.text_input("N° Avis")
        filter_tarif = f2.text_input("N° Tarifaire")
        filter_ndp   = f3.text_input("NDP")

    if query or filter_avis or filter_tarif or filter_ndp:
        results = db.search_documents(query) if query else db.get_all_documents()
        if filter_avis:  results = [r for r in results if filter_avis  in (r.get("numero_avis")  or "")]
        if filter_tarif: results = [r for r in results if filter_tarif in (r.get("tarif_number") or "")]
        if filter_ndp:   results = [r for r in results if filter_ndp   in (r.get("ndp")          or "")]

        st.markdown(f"**{len(results)} résultat(s)**")
        if not results:
            st.warning("Aucun document trouvé.")
        else:
            for doc in results:
                st.markdown(f"""
                <div class='result-card'>
                    <b>📄 {doc['filename']}</b> &nbsp;
                    <span class='badge'>{doc.get('tarif_number') or '?'}</span> &nbsp;
                    <span class='badge-ndp'>NDP {doc.get('ndp') or '?'}</span>
                    <span style='color:#aaa;font-size:0.8rem;float:right'>{doc.get('upload_date','')[:10]}</span>
                </div>
                """, unsafe_allow_html=True)
                a, b, c = st.columns(3)
                a.metric("N° Avis",      doc.get("numero_avis")  or "—")
                b.metric("N° Tarifaire", doc.get("tarif_number") or "—")
                c.metric("NDP",          doc.get("ndp")          or "—")
                st.write(f"**Désignation :** {doc.get('designation') or '—'}")
                with st.expander("📄 Texte OCR"):
                    st.text(doc.get("full_text", "")[:3000])
                st.markdown("---")


# ══════════════════════════════════════════════════════════════════════════════
#  TOUS LES DOCUMENTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Tous les documents":
    st.header("📋 Tous les documents")
    docs = db.get_all_documents()
    if not docs:
        st.info("Aucun document.")
    else:
        df = pd.DataFrame(docs)[["id","filename","numero_avis","designation","tarif_number","ndp","upload_date"]]
        df.columns = ["ID","Fichier","N° Avis","Désignation","N° Tarifaire","NDP","Date"]
        st.dataframe(df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MODIFIER / SUPPRIMER
# ══════════════════════════════════════════════════════════════════════════════
elif page == "✏️  Modifier / Supprimer":
    st.header("✏️ Modifier / Supprimer")
    docs = db.get_all_documents()
    if not docs:
        st.info("Aucun document disponible.")
    else:
        options  = {f"[{d['id']}] {d['filename']}": d['id'] for d in docs}
        selected = st.selectbox("Choisir un document", list(options.keys()))
        doc_id   = options[selected]
        doc      = db.get_document_by_id(doc_id)

        tab_edit, tab_ocr, tab_del = st.tabs(["✏️ Modifier", "📄 Texte OCR", "🗑️ Supprimer"])

        with tab_edit:
            with st.form("edit_form"):
                c1, c2, c3 = st.columns(3)
                numero_avis  = c1.text_input("N° Avis",      value=doc.get("numero_avis")  or "")
                tarif_number = c2.text_input("N° Tarifaire", value=doc.get("tarif_number") or "")
                ndp          = c3.text_input("NDP",          value=doc.get("ndp")          or "")
                designation  = st.text_area("Désignation",   value=doc.get("designation")  or "", height=80)
                if st.form_submit_button("💾 Enregistrer", type="primary"):
                    db.update_document(doc_id, {
                        "numero_avis":  numero_avis,
                        "designation":  designation,
                        "tarif_number": tarif_number,
                        "ndp":          ndp,
                    })
                    st.success("✅ Mis à jour !")
                    st.rerun()

        with tab_ocr:
            st.text_area("Texte OCR complet", value=doc.get("full_text") or "", height=450)

        with tab_del:
            st.warning(f"⚠️ Supprimer **{doc['filename']}** ?")
            if st.checkbox("Je confirme"):
                if st.button("🗑️ Supprimer", type="primary"):
                    db.delete_document(doc_id)
                    st.success("Supprimé.")
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  GESTION UTILISATEURS (admin seulement)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Gestion utilisateurs" and is_admin:
    st.header("👥 Gestion des utilisateurs")

    tab_list, tab_add = st.tabs(["📋 Liste des utilisateurs", "➕ Ajouter un utilisateur"])

    with tab_list:
        users = auth.get_all_users()
        for u in users:
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            col1.write(f"**{u['nom']}** — {u['email']}")
            col2.write(f"🔑 {u['role']}")
            col3.write("✅ Actif" if u["actif"] else "❌ Inactif")
            if u["role"] != "admin":
                if col4.button("Désactiver" if u["actif"] else "Activer", key=f"tog_{u['id']}"):
                    auth.toggle_user(u["id"], 0 if u["actif"] else 1)
                    st.rerun()
                if col5.button("🗑️", key=f"del_{u['id']}", help="Supprimer"):
                    auth.delete_user(u["id"])
                    st.rerun()
            st.markdown("---")

    with tab_add:
        with st.form("add_user_form"):
            st.markdown("#### Nouveau compte utilisateur")
            c1, c2 = st.columns(2)
            new_nom   = c1.text_input("Nom complet")
            new_email = c2.text_input("Email")
            new_pass  = c1.text_input("Mot de passe", type="password")
            new_role  = c2.selectbox("Rôle", ["user", "admin"])
            if st.form_submit_button("➕ Créer le compte", type="primary"):
                if not new_nom or not new_email or not new_pass:
                    st.error("Tous les champs sont obligatoires.")
                else:
                    ok, msg = auth.add_user(new_email, new_pass, new_nom, new_role)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")