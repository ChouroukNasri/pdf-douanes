"""
auth.py - Gestion des utilisateurs et sessions
"""
import sqlite3
import hashlib
import secrets
import os
from datetime import datetime

AUTH_DB = os.path.join(os.path.dirname(__file__), "data", "users.db")

def get_conn():
    os.makedirs(os.path.dirname(AUTH_DB), exist_ok=True)
    conn = sqlite3.connect(AUTH_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_auth():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            nom        TEXT,
            role       TEXT DEFAULT 'user',
            actif      INTEGER DEFAULT 1,
            created_at TEXT
        )
    """)
    # Creer le compte admin par defaut si aucun utilisateur
    c.execute("SELECT COUNT(*) as n FROM users")
    if c.fetchone()["n"] == 0:
        _create_user(c, "admin@douanes.tn", "Admin1234!", "Administrateur", role="admin")
    conn.commit()
    conn.close()

def _hash(password):
    return hashlib.sha256(password.encode()).hexdigest()

def _create_user(cursor, email, password, nom, role="user"):
    cursor.execute("""
        INSERT INTO users (email, password, nom, role, actif, created_at)
        VALUES (?, ?, ?, ?, 1, ?)
    """, (email.lower().strip(), _hash(password), nom, role, datetime.now().strftime("%Y-%m-%d %H:%M")))

def login(email, password):
    """Retourne l'utilisateur si login correct, sinon None."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=? AND actif=1",
              (email.lower().strip(), _hash(password)))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id, email, nom, role, actif, created_at FROM users ORDER BY created_at DESC")
    users = [dict(row) for row in c.fetchall()]
    conn.close()
    return users

def add_user(email, password, nom, role="user"):
    try:
        conn = get_conn()
        c = conn.cursor()
        _create_user(c, email, password, nom, role)
        conn.commit()
        conn.close()
        return True, "Utilisateur créé avec succès."
    except sqlite3.IntegrityError:
        return False, "Cet email existe déjà."
    except Exception as e:
        return False, str(e)

def delete_user(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id=? AND role != 'admin'", (user_id,))
    conn.commit()
    conn.close()

def toggle_user(user_id, actif):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET actif=? WHERE id=? AND role != 'admin'", (actif, user_id))
    conn.commit()
    conn.close()

def change_password(user_id, new_password):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE id=?", (_hash(new_password), user_id))
    conn.commit()
    conn.close()