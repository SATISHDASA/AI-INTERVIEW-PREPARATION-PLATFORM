import sqlite3
import os
from datetime import datetime

DB_PATH = "interview_bot.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            total_sessions INTEGER DEFAULT 0,
            avg_score REAL DEFAULT 0.0
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT,
            domain TEXT,
            difficulty TEXT,
            experience TEXT,
            company TEXT,
            total_questions INTEGER DEFAULT 0,
            total_score REAL DEFAULT 0.0,
            avg_score REAL DEFAULT 0.0,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            ended_at TEXT,
            status TEXT DEFAULT 'active',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            question TEXT NOT NULL,
            question_type TEXT,
            user_answer TEXT,
            score REAL,
            feedback TEXT,
            correct_answer TEXT,
            improvements TEXT,
            time_taken INTEGER,
            answered_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    conn.commit()
    conn.close()

def create_user(username, email, password_hash):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                  (username, email, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_email(email):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def create_session(user_id, role, domain, difficulty, experience, company="General"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO sessions (user_id, role, domain, difficulty, experience, company)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, role, domain, difficulty, experience, company))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id

def save_answer(session_id, user_id, question, question_type, user_answer,
                score, feedback, correct_answer, improvements, time_taken):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO answers
        (session_id, user_id, question, question_type, user_answer, score,
         feedback, correct_answer, improvements, time_taken)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (session_id, user_id, question, question_type, user_answer,
          score, feedback, correct_answer, improvements, time_taken))
    # Update session running totals
    c.execute("""
        UPDATE sessions SET
            total_questions = total_questions + 1,
            total_score     = total_score + ?,
            avg_score       = (total_score + ?) / (total_questions + 1)
        WHERE id = ?
    """, (score, score, session_id))
    conn.commit()
    conn.close()

def end_session(session_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE sessions SET status='completed', ended_at=? WHERE id=?",
              (datetime.now().isoformat(), session_id))
    conn.commit()
    row = conn.execute("SELECT user_id, total_score, total_questions FROM sessions WHERE id=?",
                       (session_id,)).fetchone()
    if row and row["total_questions"] > 0:
        uid = row["user_id"]
        c.execute("""
            UPDATE users SET
                total_sessions = total_sessions + 1,
                avg_score = (SELECT AVG(avg_score) FROM sessions
                             WHERE user_id=? AND status='completed')
            WHERE id=?
        """, (uid, uid))
        conn.commit()
    conn.close()

def get_user_sessions(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sessions WHERE user_id=? ORDER BY started_at DESC", (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_session_answers(session_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM answers WHERE session_id=? ORDER BY answered_at", (session_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_user_stats(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT COUNT(*) as total_sessions,
               AVG(avg_score) as overall_avg,
               MAX(avg_score) as best_score,
               SUM(total_questions) as total_questions
        FROM sessions WHERE user_id=? AND status='completed'
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else {}

def get_score_history(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT started_at, avg_score, role, domain, company
        FROM sessions WHERE user_id=? AND status='completed'
        ORDER BY started_at
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]
