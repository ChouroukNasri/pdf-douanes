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
            filepath     TEXT,
            full_text    TEXT,
            upload_date  TEXT,
            numero_avis  TEXT,
            objet        TEXT,
            date_avis    TEXT,
            destinataire TEXT,
            reference    TEXT
        )
    """)

    # ── MODULE 3 : Decisions OMD ──────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS omd (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            filename     TEXT NOT NULL,
            filepath     TEXT,
            full_text    TEXT,
            upload_date  TEXT,
            numero_dec   TEXT,
            titre        TEXT,
            date_dec     TEXT,
            chapitre     TEXT,
            code_sh      TEXT
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
            full_text, filename, numero_avis, objet, destinataire, reference,
            content=secretariat, content_rowid=id
        )
    """)
    # FTS pour OMD
    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS omd_fts USING fts5(
            full_text, filename, numero_dec, titre, chapitre, code_sh,
            content=omd, content_rowid=id
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
        INSERT INTO secretariat_fts(rowid,full_text,filename,numero_avis,objet,destinataire,reference)
        VALUES(new.id,new.full_text,new.filename,new.numero_avis,new.objet,new.destinataire,new.reference);
    END""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS sec_ad AFTER DELETE ON secretariat BEGIN
        INSERT INTO secretariat_fts(secretariat_fts,rowid,full_text,filename,numero_avis,objet,destinataire,reference)
        VALUES('delete',old.id,old.full_text,old.filename,old.numero_avis,old.objet,old.destinataire,old.reference);
    END""")

    # Triggers OMD
    c.execute("""CREATE TRIGGER IF NOT EXISTS omd_ai AFTER INSERT ON omd BEGIN
        INSERT INTO omd_fts(rowid,full_text,filename,numero_dec,titre,chapitre,code_sh)
        VALUES(new.id,new.full_text,new.filename,new.numero_dec,new.titre,new.chapitre,new.code_sh);
    END""")
    c.execute("""CREATE TRIGGER IF NOT EXISTS omd_ad AFTER DELETE ON omd BEGIN
        INSERT INTO omd_fts(omd_fts,rowid,full_text,filename,numero_dec,titre,chapitre,code_sh)
        VALUES('delete',old.id,old.full_text,old.filename,old.numero_dec,old.titre,old.chapitre,old.code_sh);
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
    c.execute("""INSERT INTO secretariat(filename,filepath,full_text,upload_date,
        numero_avis,objet,date_avis,destinataire,reference)
        VALUES(:filename,:filepath,:full_text,:upload_date,
        :numero_avis,:objet,:date_avis,:destinataire,:reference)""", {
        "filename":data.get("filename",""), "filepath":data.get("filepath",""),
        "full_text":data.get("full_text",""), "upload_date":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "numero_avis":data.get("numero_avis",""), "objet":data.get("objet",""),
        "date_avis":data.get("date_avis",""), "destinataire":data.get("destinataire",""),
        "reference":data.get("reference",""),
    })
    doc_id = c.lastrowid; conn.commit(); conn.close(); return doc_id

def search_secretariat(query):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("SELECT d.* FROM secretariat d JOIN secretariat_fts f ON d.id=f.rowid WHERE secretariat_fts MATCH ? ORDER BY rank",(query,))
    except:
        like = "%"+query+"%"
        c.execute("SELECT * FROM secretariat WHERE full_text LIKE ? OR numero_avis LIKE ? OR objet LIKE ? OR destinataire LIKE ? OR reference LIKE ?",(like,like,like,like,like))
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
    c.execute("""UPDATE secretariat SET numero_avis=:numero_avis,objet=:objet,
        date_avis=:date_avis,destinataire=:destinataire,reference=:reference WHERE id=:id""",
        {**data,"id":doc_id})
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
    c.execute("""INSERT INTO omd(filename,filepath,full_text,upload_date,
        numero_dec,titre,date_dec,chapitre,code_sh)
        VALUES(:filename,:filepath,:full_text,:upload_date,
        :numero_dec,:titre,:date_dec,:chapitre,:code_sh)""", {
        "filename":data.get("filename",""), "filepath":data.get("filepath",""),
        "full_text":data.get("full_text",""), "upload_date":datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "numero_dec":data.get("numero_dec",""), "titre":data.get("titre",""),
        "date_dec":data.get("date_dec",""), "chapitre":data.get("chapitre",""),
        "code_sh":data.get("code_sh",""),
    })
    doc_id = c.lastrowid; conn.commit(); conn.close(); return doc_id

def search_omd(query):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("SELECT d.* FROM omd d JOIN omd_fts f ON d.id=f.rowid WHERE omd_fts MATCH ? ORDER BY rank",(query,))
    except:
        like = "%"+query+"%"
        c.execute("SELECT * FROM omd WHERE full_text LIKE ? OR numero_dec LIKE ? OR titre LIKE ? OR chapitre LIKE ? OR code_sh LIKE ?",(like,like,like,like,like))
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
    c.execute("""UPDATE omd SET numero_dec=:numero_dec,titre=:titre,
        date_dec=:date_dec,chapitre=:chapitre,code_sh=:code_sh WHERE id=:id""",
        {**data,"id":doc_id})
    conn.commit(); conn.close()

def delete_omd(doc_id):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM omd WHERE id=?",(doc_id,))
    conn.commit(); conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  STATS GLOBALES
# ══════════════════════════════════════════════════════════════════════════════
def get_stats():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT COUNT(*) as n FROM documents");  t1 = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM secretariat"); t2 = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) as n FROM omd");         t3 = c.fetchone()["n"]
    conn.close()
    return {"tarifaires": t1, "secretariat": t2, "omd": t3, "total": t1+t2+t3}