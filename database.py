import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "database.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── MODULE 1 : Avis Tarifaires ────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            filename     TEXT NOT NULL,
            filepath     TEXT,
            full_text    TEXT,
            upload_date  TEXT,
            numero_avis  TEXT,
            designation  TEXT,
            usage_text   TEXT,
            tarif_number TEXT,
            ndp          TEXT
        )
    """)
    try: c.execute("ALTER TABLE documents ADD COLUMN usage_text TEXT DEFAULT ''")
    except: pass

    # ── MODULE 2 : Avis Secretariat ───────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS secretariat (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            filename     TEXT NOT NULL,
            upload_date  TEXT,
            numero_lettre TEXT,
            date_avis    TEXT,
            hs_code      TEXT,
            desc_fr      TEXT,
            desc_en      TEXT
        )
    """)

    # ── MODULE 3 : Decisions OMD ──────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS omd (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT NOT NULL,
            upload_date TEXT,
            numero      TEXT,
            description TEXT,
            classement  TEXT,
            motif       TEXT,
            session     TEXT
        )
    """)

    # ── MODULE 4 : Avis Tarés (kap_XX_f.pdf) ─────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS avis_tares (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT NOT NULL,
            upload_date TEXT,
            hs_code     TEXT,
            nom         TEXT,
            description TEXT,
            mots_cles   TEXT,
            ref_numero  TEXT
        )
    """)

    # FTS pour avis tarifaires
    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
            full_text, filename, numero_avis, designation, usage_text, tarif_number, ndp,
            content=documents, content_rowid=id
        )
    """)
    # FTS pour secretariat
    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS secretariat_fts USING fts5(
            numero_lettre, date_avis, hs_code, desc_fr, desc_en, filename,
            content=secretariat, content_rowid=id
        )
    """)
    # FTS pour OMD
    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS omd_fts USING fts5(
            numero, description, classement, motif, session, filename,
            content=omd, content_rowid=id
        )
    """)
    # FTS pour Avis Tarés
    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS avis_tares_fts USING fts5(
            hs_code, nom, description, mots_cles, filename,
            content=avis_tares, content_rowid=id
        )
    """)

    # Triggers documents
    c.execute("""CREATE TRIGGER IF NOT EXISTS docs_ai AFTER INSERT ON documents BEGIN
        INSERT INTO documents_fts(rowid,full_text,filename,numero_avis,designation,usage_text,tarif_number,ndp)
        VALUES(new.id,new.full_text,new.filename,new.numero_avis,new.designation,new.usage_text,new.tarif_number,new.ndp);
    END""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS docs_ad AFTER DELETE ON documents BEGIN
        INSERT INTO documents_fts(documents_fts,rowid,full_text,filename,numero_avis,designation,usage_text,tarif_number,ndp)
        VALUES('delete',old.id,old.full_text,old.filename,old.numero_avis,old.designation,old.usage_text,old.tarif_number,old.ndp);
    END""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS docs_au AFTER UPDATE ON documents BEGIN
        INSERT INTO documents_fts(documents_fts,rowid,full_text,filename,numero_avis,designation,usage_text,tarif_number,ndp)
        VALUES('delete',old.id,old.full_text,old.filename,old.numero_avis,old.designation,old.usage_text,old.tarif_number,old.ndp);
        INSERT INTO documents_fts(rowid,full_text,filename,numero_avis,designation,usage_text,tarif_number,ndp)
        VALUES(new.id,new.full_text,new.filename,new.numero_avis,new.designation,new.usage_text,new.tarif_number,new.ndp);
    END""")

    # Triggers secretariat
    c.execute("""CREATE TRIGGER IF NOT EXISTS sec_ai AFTER INSERT ON secretariat BEGIN
        INSERT INTO secretariat_fts(rowid,numero_lettre,date_avis,hs_code,desc_fr,desc_en,filename)
        VALUES(new.id,new.numero_lettre,new.date_avis,new.hs_code,new.desc_fr,new.desc_en,new.filename);
    END""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS sec_ad AFTER DELETE ON secretariat BEGIN
        INSERT INTO secretariat_fts(secretariat_fts,rowid,numero_lettre,date_avis,hs_code,desc_fr,desc_en,filename)
        VALUES('delete',old.id,old.numero_lettre,old.date_avis,old.hs_code,old.desc_fr,old.desc_en,old.filename);
    END""")

    # Triggers OMD
    c.execute("""CREATE TRIGGER IF NOT EXISTS omd_ai AFTER INSERT ON omd BEGIN
        INSERT INTO omd_fts(rowid,numero,description,classement,motif,session,filename)
        VALUES(new.id,new.numero,new.description,new.classement,new.motif,new.session,new.filename);
    END""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS omd_ad AFTER DELETE ON omd BEGIN
        INSERT INTO omd_fts(omd_fts,rowid,numero,description,classement,motif,session,filename)
        VALUES('delete',old.id,old.numero,old.description,old.classement,old.motif,old.session,old.filename);
    END""")

    # Triggers avis_tares
    c.execute("""CREATE TRIGGER IF NOT EXISTS at_ai AFTER INSERT ON avis_tares BEGIN
        INSERT INTO avis_tares_fts(rowid,hs_code,nom,description,mots_cles,filename)
        VALUES(new.id,new.hs_code,new.nom,new.description,new.mots_cles,new.filename);
    END""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS at_ad AFTER DELETE ON avis_tares BEGIN
        INSERT INTO avis_tares_fts(avis_tares_fts,rowid,hs_code,nom,description,mots_cles,filename)
        VALUES('delete',old.id,old.hs_code,old.nom,old.description,old.mots_cles,old.filename);
    END""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS at_au AFTER UPDATE ON avis_tares BEGIN
        INSERT INTO avis_tares_fts(avis_tares_fts,rowid,hs_code,nom,description,mots_cles,filename)
        VALUES('delete',old.id,old.hs_code,old.nom,old.description,old.mots_cles,old.filename);
        INSERT INTO avis_tares_fts(rowid,hs_code,nom,description,mots_cles,filename)
        VALUES(new.id,new.hs_code,new.nom,new.description,new.mots_cles,new.filename);
    END""")

    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — AVIS TARIFAIRES
# ══════════════════════════════════════════════════════════════════════════════
def insert_document(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO documents(filename,filepath,full_text,upload_date,
        numero_avis,designation,usage_text,tarif_number,ndp)
        VALUES(:filename,:filepath,:full_text,:upload_date,
        :numero_avis,:designation,:usage_text,:tarif_number,:ndp)""", {
        "filename":data.get("filename",""), "filepath":data.get("filepath",""),
        "full_text":data.get("full_text",""), "upload_date":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "numero_avis":data.get("numero_avis",""), "designation":data.get("designation",""),
        "usage_text":data.get("usage_text",""), "tarif_number":data.get("tarif_number",""),
        "ndp":data.get("ndp",""),
    })
    doc_id = c.lastrowid
    conn.commit(); conn.close()
    return doc_id

def search_documents(query):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("SELECT d.* FROM documents d JOIN documents_fts f ON d.id=f.rowid WHERE documents_fts MATCH ? ORDER BY rank",(query,))
    except:
        like = "%"+query+"%"
        c.execute("SELECT * FROM documents WHERE full_text LIKE ? OR numero_avis LIKE ? OR designation LIKE ? OR usage_text LIKE ? OR tarif_number LIKE ? OR ndp LIKE ?",(like,like,like,like,like,like))
    results = [dict(r) for r in c.fetchall()]; conn.close(); return results

def get_all_documents():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM documents ORDER BY upload_date DESC")
    results = [dict(r) for r in c.fetchall()]; conn.close(); return results

def get_document_by_id(doc_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM documents WHERE id=?",(doc_id,))
    row = c.fetchone(); conn.close()
    return dict(row) if row else {}

def update_document(doc_id, data):
    conn = get_connection(); c = conn.cursor()
    c.execute("""UPDATE documents SET numero_avis=:numero_avis,designation=:designation,
        usage_text=:usage_text,tarif_number=:tarif_number,ndp=:ndp WHERE id=:id""",
        {**data,"id":doc_id})
    conn.commit(); conn.close()

def delete_document(doc_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM documents WHERE id=?",(doc_id,))
    conn.commit(); conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — SECRETARIAT
# ══════════════════════════════════════════════════════════════════════════════
def insert_secretariat(data):
    conn = get_connection(); c = conn.cursor()
    c.execute("""INSERT INTO secretariat(filename,upload_date,
        numero_lettre,date_avis,hs_code,desc_fr,desc_en)
        VALUES(:filename,:upload_date,
        :numero_lettre,:date_avis,:hs_code,:desc_fr,:desc_en)""", {
        "filename":      data.get("filename",""),
        "upload_date":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "numero_lettre": data.get("numero_lettre",""),
        "date_avis":     data.get("date_avis",""),
        "hs_code":       data.get("hs_code",""),
        "desc_fr":       data.get("desc_fr",""),
        "desc_en":       data.get("desc_en",""),
    })
    doc_id = c.lastrowid; conn.commit(); conn.close(); return doc_id

def search_secretariat(query):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("SELECT d.* FROM secretariat d JOIN secretariat_fts f ON d.id=f.rowid WHERE secretariat_fts MATCH ? ORDER BY rank",(query,))
    except:
        like = "%"+query+"%"
        c.execute("SELECT * FROM secretariat WHERE numero_lettre LIKE ? OR hs_code LIKE ? OR desc_fr LIKE ? OR desc_en LIKE ?",(like,like,like,like))
    results = [dict(r) for r in c.fetchall()]; conn.close(); return results

def search_secretariat_by_lettre(query):
    conn = get_connection(); c = conn.cursor()
    like = "%"+query.upper()+"%"
    c.execute("SELECT * FROM secretariat WHERE UPPER(numero_lettre) LIKE ? ORDER BY date_avis DESC",(like,))
    results = [dict(r) for r in c.fetchall()]; conn.close(); return results

def get_all_secretariat():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM secretariat ORDER BY upload_date DESC")
    results = [dict(r) for r in c.fetchall()]; conn.close(); return results

def get_secretariat_by_id(doc_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM secretariat WHERE id=?",(doc_id,))
    row = c.fetchone(); conn.close(); return dict(row) if row else {}

def update_secretariat(doc_id, data):
    conn = get_connection(); c = conn.cursor()
    c.execute("""UPDATE secretariat SET numero_lettre=:numero_lettre,
        date_avis=:date_avis,hs_code=:hs_code,desc_fr=:desc_fr,desc_en=:desc_en
        WHERE id=:id""", {**data,"id":doc_id})
    conn.commit(); conn.close()

def delete_secretariat(doc_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM secretariat WHERE id=?",(doc_id,))
    conn.commit(); conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 3 — DECISIONS OMD
# ══════════════════════════════════════════════════════════════════════════════
def insert_omd(data):
    conn = get_connection(); c = conn.cursor()
    c.execute("""INSERT INTO omd(filename,upload_date,numero,description,classement,motif,session)
        VALUES(:filename,:upload_date,:numero,:description,:classement,:motif,:session)""", {
        "filename":    data.get("filename",""),
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "numero":      data.get("numero",""),
        "description": data.get("description",""),
        "classement":  data.get("classement",""),
        "motif":       data.get("motif",""),
        "session":     data.get("session",""),
    })
    doc_id = c.lastrowid; conn.commit(); conn.close(); return doc_id

def search_omd(query):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("SELECT d.* FROM omd d JOIN omd_fts f ON d.id=f.rowid WHERE omd_fts MATCH ? ORDER BY rank",(query,))
    except:
        like = "%"+query+"%"
        c.execute("SELECT * FROM omd WHERE description LIKE ? OR classement LIKE ? OR motif LIKE ? OR session LIKE ? OR numero LIKE ?",(like,like,like,like,like))
    results = [dict(r) for r in c.fetchall()]; conn.close(); return results

def search_omd_by_classement(query):
    conn = get_connection(); c = conn.cursor()
    like = "%"+query.upper()+"%"
    c.execute("SELECT * FROM omd WHERE UPPER(classement) LIKE ? ORDER BY classement",(like,))
    results = [dict(r) for r in c.fetchall()]; conn.close(); return results

def get_all_omd():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM omd ORDER BY upload_date DESC")
    results = [dict(r) for r in c.fetchall()]; conn.close(); return results

def get_omd_by_id(doc_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM omd WHERE id=?",(doc_id,))
    row = c.fetchone(); conn.close(); return dict(row) if row else {}

def update_omd(doc_id, data):
    conn = get_connection(); c = conn.cursor()
    c.execute("""UPDATE omd SET numero=:numero,description=:description,
        classement=:classement,motif=:motif,session=:session WHERE id=:id""",
        {**data,"id":doc_id})
    conn.commit(); conn.close()

def delete_omd(doc_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM omd WHERE id=?",(doc_id,))
    conn.commit(); conn.close()

def get_omd_filenames():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT DISTINCT filename FROM omd ORDER BY filename")
    results = [r["filename"] for r in c.fetchall()]; conn.close(); return results

def delete_omd_by_filename(filename):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT COUNT(*) as n FROM omd WHERE filename=?",(filename,))
    n = c.fetchone()["n"]
    c.execute("DELETE FROM omd WHERE filename=?",(filename,))
    conn.commit(); conn.close(); return n

def update_omd_session_by_filename(filename, session):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE omd SET session=? WHERE filename=?",(session,filename))
    updated = conn.total_changes; conn.commit(); conn.close(); return updated

def get_omd_duplicate_count():
    conn = get_connection(); c = conn.cursor()
    c.execute("""SELECT COUNT(*) - COUNT(DISTINCT filename||'|'||classement||'|'||description) as n FROM omd""")
    n = c.fetchone()["n"]; conn.close(); return n or 0

def deduplicate_omd():
    conn = get_connection(); c = conn.cursor()
    c.execute("""DELETE FROM omd WHERE id NOT IN (
        SELECT MIN(id) FROM omd GROUP BY filename, classement, description)""")
    deleted = conn.total_changes; conn.commit(); conn.close(); return deleted


# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 4 — AVIS TARÉS (kap_XX_f.pdf)
# ══════════════════════════════════════════════════════════════════════════════
def insert_avis_tare(data):
    conn = get_connection(); c = conn.cursor()
    c.execute("""INSERT INTO avis_tares(filename,upload_date,hs_code,nom,description,mots_cles,ref_numero)
        VALUES(:filename,:upload_date,:hs_code,:nom,:description,:mots_cles,:ref_numero)""", {
        "filename":    data.get("filename",""),
        "upload_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hs_code":     data.get("hs_code",""),
        "nom":         data.get("nom",""),
        "description": data.get("description",""),
        "mots_cles":   data.get("mots_cles",""),
        "ref_numero":  data.get("ref_numero",""),
    })
    doc_id = c.lastrowid; conn.commit(); conn.close(); return doc_id

def search_avis_tares(query):
    """Recherche par code HS (partiel ou complet parmi plusieurs codes), nom, description, mots-clés."""
    conn = get_connection(); c = conn.cursor()
    q = query.strip()
    like = "%" + q + "%"
    c.execute("""
        SELECT * FROM avis_tares
        WHERE hs_code LIKE ?
           OR LOWER(nom) LIKE LOWER(?)
           OR LOWER(description) LIKE LOWER(?)
           OR LOWER(mots_cles) LIKE LOWER(?)
        ORDER BY
            CASE WHEN hs_code LIKE ? THEN 0 ELSE 1 END,
            hs_code
    """, (like, like, like, like, like))
    # Dédoublonnage par (hs_code, description) — un produit unique = un code HS + une description
    seen = set()
    results = []
    for r in c.fetchall():
        d = dict(r)
        key = (d["hs_code"], (d["description"] or "").strip())
        if key not in seen:
            seen.add(key)
            results.append(d)
    conn.close()
    return results


def deduplicate_avis_tares():
    """Supprime les doublons exacts en base (même hs_code + même description)."""
    conn = get_connection(); c = conn.cursor()
    c.execute("""
        DELETE FROM avis_tares WHERE id NOT IN (
            SELECT MIN(id) FROM avis_tares
            GROUP BY hs_code, TRIM(description)
        )
    """)
    deleted = conn.total_changes
    conn.commit(); conn.close()
    return deleted


def get_avis_tares_duplicate_count():
    conn = get_connection(); c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) - COUNT(DISTINCT hs_code||'|'||TRIM(description)) as n
        FROM avis_tares
    """)
    n = c.fetchone()["n"]; conn.close(); return n or 0

def get_all_avis_tares():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM avis_tares ORDER BY hs_code")
    results = [dict(r) for r in c.fetchall()]; conn.close(); return results

def get_avis_tare_by_id(doc_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT * FROM avis_tares WHERE id=?",(doc_id,))
    row = c.fetchone(); conn.close(); return dict(row) if row else {}

def update_avis_tare(doc_id, data):
    conn = get_connection(); c = conn.cursor()
    c.execute("""UPDATE avis_tares SET hs_code=:hs_code,nom=:nom,description=:description,
        mots_cles=:mots_cles,ref_numero=:ref_numero WHERE id=:id""",
        {**data,"id":doc_id})
    conn.commit(); conn.close()

def delete_avis_tare(doc_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM avis_tares WHERE id=?",(doc_id,))
    conn.commit(); conn.close()

def get_avis_tares_filenames():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT DISTINCT filename FROM avis_tares ORDER BY filename")
    results = [r["filename"] for r in c.fetchall()]; conn.close(); return results

def delete_avis_tares_by_filename(filename):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT COUNT(*) as n FROM avis_tares WHERE filename=?",(filename,))
    n = c.fetchone()["n"]
    c.execute("DELETE FROM avis_tares WHERE filename=?",(filename,))
    conn.commit(); conn.close(); return n


# ══════════════════════════════════════════════════════════════════════════════
#  STATS GLOBALES
# ══════════════════════════════════════════════════════════════════════════════
def get_stats():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT COUNT(*) as n FROM documents");   t1 = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM secretariat"); t2 = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM omd");         t3 = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM avis_tares");  t4 = c.fetchone()["n"]
    conn.close()
    return {"tarifaires": t1, "secretariat": t2, "omd": t3, "avis_tares": t4, "total": t1+t2+t3+t4}