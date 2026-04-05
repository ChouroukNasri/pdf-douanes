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
    # Ajouter la colonne usage_text si elle n'existe pas (migration)
    try:
        c.execute("ALTER TABLE documents ADD COLUMN usage_text TEXT DEFAULT ''")
    except Exception:
        pass

    c.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
            full_text, filename, numero_avis, designation, usage_text, tarif_number, ndp,
            content=documents, content_rowid=id
        )
    """)
    c.execute("""
        CREATE TRIGGER IF NOT EXISTS docs_ai AFTER INSERT ON documents BEGIN
            INSERT INTO documents_fts(rowid, full_text, filename, numero_avis, designation, usage_text, tarif_number, ndp)
            VALUES (new.id, new.full_text, new.filename, new.numero_avis, new.designation, new.usage_text, new.tarif_number, new.ndp);
        END
    """)
    c.execute("""
        CREATE TRIGGER IF NOT EXISTS docs_ad AFTER DELETE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, rowid, full_text, filename, numero_avis, designation, usage_text, tarif_number, ndp)
            VALUES ('delete', old.id, old.full_text, old.filename, old.numero_avis, old.designation, old.usage_text, old.tarif_number, old.ndp);
        END
    """)
    c.execute("""
        CREATE TRIGGER IF NOT EXISTS docs_au AFTER UPDATE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, rowid, full_text, filename, numero_avis, designation, usage_text, tarif_number, ndp)
            VALUES ('delete', old.id, old.full_text, old.filename, old.numero_avis, old.designation, old.usage_text, old.tarif_number, old.ndp);
            INSERT INTO documents_fts(rowid, full_text, filename, numero_avis, designation, usage_text, tarif_number, ndp)
            VALUES (new.id, new.full_text, new.filename, new.numero_avis, new.designation, new.usage_text, new.tarif_number, new.ndp);
        END
    """)
    conn.commit()
    conn.close()


def insert_document(data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO documents (filename, filepath, full_text, upload_date,
            numero_avis, designation, usage_text, tarif_number, ndp)
        VALUES (:filename, :filepath, :full_text, :upload_date,
            :numero_avis, :designation, :usage_text, :tarif_number, :ndp)
    """, {
        "filename":     data.get("filename", ""),
        "filepath":     data.get("filepath", ""),
        "full_text":    data.get("full_text", ""),
        "upload_date":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "numero_avis":  data.get("numero_avis", ""),
        "designation":  data.get("designation", ""),
        "usage_text":   data.get("usage_text", ""),
        "tarif_number": data.get("tarif_number", ""),
        "ndp":          data.get("ndp", ""),
    })
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    return doc_id


def search_documents(query):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            SELECT d.* FROM documents d
            JOIN documents_fts fts ON d.id = fts.rowid
            WHERE documents_fts MATCH ? ORDER BY rank
        """, (query,))
    except Exception:
        like = "%" + query + "%"
        c.execute("""
            SELECT * FROM documents
            WHERE full_text LIKE ? OR numero_avis LIKE ?
               OR designation LIKE ? OR usage_text LIKE ?
               OR tarif_number LIKE ? OR ndp LIKE ?
        """, (like, like, like, like, like, like))
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results


def get_all_documents():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM documents ORDER BY upload_date DESC")
    results = [dict(row) for row in c.fetchall()]
    conn.close()
    return results


def get_document_by_id(doc_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {}


def update_document(doc_id, data):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        UPDATE documents SET
            numero_avis  = :numero_avis,
            designation  = :designation,
            usage_text   = :usage_text,
            tarif_number = :tarif_number,
            ndp          = :ndp
        WHERE id = :id
    """, {**data, "id": doc_id})
    conn.commit()
    conn.close()


def delete_document(doc_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()


def get_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM documents")
    total = c.fetchone()["total"]
    c.execute("SELECT COUNT(DISTINCT tarif_number) as unique_tarifs FROM documents WHERE tarif_number != ''")
    unique_tarifs = c.fetchone()["unique_tarifs"]
    c.execute("SELECT COUNT(DISTINCT ndp) as unique_ndp FROM documents WHERE ndp != ''")
    unique_ndp = c.fetchone()["unique_ndp"]
    conn.close()
    return {"total": total, "unique_tarifs": unique_tarifs, "unique_ndp": unique_ndp}