import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            import sys
            if getattr(sys, 'frozen', False):
                project_root = os.path.dirname(os.path.dirname(sys.executable))
            else:
                project_root = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(project_root, "exam_simulator.db")
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            # Exams Table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                filepath TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                passing_score INTEGER DEFAULT 70,
                time_limit INTEGER DEFAULT 60
            );
            """)

            # Questions Table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                question_num INTEGER,
                section TEXT,
                question_text TEXT NOT NULL,
                question_type TEXT NOT NULL,
                explanation TEXT,
                confidence REAL DEFAULT 1.0,
                FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
            );
            """)

            # Choices Table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS choices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id INTEGER NOT NULL,
                choice_letter TEXT NOT NULL,
                choice_text TEXT NOT NULL,
                is_correct INTEGER DEFAULT 0,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
            """)

            # Sessions Table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS exam_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                time_limit INTEGER,
                time_spent INTEGER DEFAULT 0,
                is_study_mode INTEGER DEFAULT 0,
                is_completed INTEGER DEFAULT 0,
                question_order TEXT,
                FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE
            );
            """)

            # Session Answers Table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS session_answers (
                session_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                selected_answers TEXT,
                is_flagged INTEGER DEFAULT 0,
                PRIMARY KEY (session_id, question_id),
                FOREIGN KEY (session_id) REFERENCES exam_sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
            """)

            # Persistent Bookmarks Table
            conn.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                exam_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                PRIMARY KEY (exam_id, question_id),
                FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
            );
            """)
            
            # Clean up/remove any legacy drag_drop or fill questions
            conn.execute("DELETE FROM questions WHERE question_type IN ('drag_drop', 'fill');")
            conn.commit()

    # --- Exams CRUD ---
    def create_exam(self, name, filepath=None, passing_score=70, time_limit=60):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO exams (name, filepath, passing_score, time_limit) VALUES (?, ?, ?, ?)",
                (name, filepath, passing_score, time_limit)
            )
            conn.commit()
            return cursor.lastrowid

    def get_exams(self):
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT e.*, 
                       (SELECT COUNT(*) FROM questions q WHERE q.exam_id = e.id) as question_count
                FROM exams e
                ORDER BY e.created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_exam(self, exam_id):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM exams WHERE id = ?", (exam_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def delete_exam(self, exam_id):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM exams WHERE id = ?", (exam_id,))
            conn.commit()

    def update_exam_settings(self, exam_id, passing_score, time_limit):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE exams SET passing_score = ?, time_limit = ? WHERE id = ?",
                (passing_score, time_limit, exam_id)
            )
            conn.commit()

    # --- Questions & Choices CRUD ---
    def add_question(self, exam_id, question_num, section, question_text, question_type, explanation=None, confidence=1.0):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO questions (exam_id, question_num, section, question_text, question_type, explanation, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (exam_id, question_num, section, question_text, question_type, explanation, confidence))
            conn.commit()
            return cursor.lastrowid

    def add_choices(self, question_id, choices_list):
        # choices_list is a list of tuples: (choice_letter, choice_text, is_correct)
        with self._get_connection() as conn:
            conn.executemany("""
                INSERT INTO choices (question_id, choice_letter, choice_text, is_correct)
                VALUES (?, ?, ?, ?)
            """, [(question_id, letter, text, is_correct) for letter, text, is_correct in choices_list])
            conn.commit()

    def update_question(self, question_id, question_text, question_type, explanation=None):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE questions 
                SET question_text = ?, question_type = ?, explanation = ?
                WHERE id = ?
            """, (question_text, question_type, explanation, question_id))
            conn.commit()

    def update_choices(self, question_id, choices_list):
        # choices_list is list of tuples: (choice_letter, choice_text, is_correct)
        with self._get_connection() as conn:
            conn.execute("DELETE FROM choices WHERE question_id = ?", (question_id,))
            conn.executemany("""
                INSERT INTO choices (question_id, choice_letter, choice_text, is_correct)
                VALUES (?, ?, ?, ?)
            """, [(question_id, letter, text, is_correct) for letter, text, is_correct in choices_list])
            conn.commit()

    def get_questions(self, exam_id):
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT q.*, 
                       EXISTS(SELECT 1 FROM bookmarks b WHERE b.question_id = q.id) as is_bookmarked
                FROM questions q 
                WHERE q.exam_id = ?
                ORDER BY q.question_num ASC, q.id ASC
            """, (exam_id,))
            questions = [dict(row) for row in cursor.fetchall()]
            
            for q in questions:
                choices_cursor = conn.execute(
                    "SELECT id, choice_letter, choice_text, is_correct FROM choices WHERE question_id = ? ORDER BY choice_letter ASC",
                    (q['id'],)
                )
                q['choices'] = [dict(c) for c in choices_cursor.fetchall()]
            return questions

    def get_question(self, question_id):
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT q.*, 
                       EXISTS(SELECT 1 FROM bookmarks b WHERE b.question_id = q.id) as is_bookmarked
                FROM questions q 
                WHERE q.id = ?
            """, (question_id,))
            row = cursor.fetchone()
            if not row:
                return None
            q = dict(row)
            choices_cursor = conn.execute(
                "SELECT id, choice_letter, choice_text, is_correct FROM choices WHERE question_id = ? ORDER BY choice_letter ASC",
                (q['id'],)
            )
            q['choices'] = [dict(c) for c in choices_cursor.fetchall()]
            return q

    # --- Bookmarks CRUD ---
    def toggle_bookmark(self, exam_id, question_id):
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM bookmarks WHERE exam_id = ? AND question_id = ?",
                (exam_id, question_id)
            )
            exists = cursor.fetchone()
            if exists:
                conn.execute(
                    "DELETE FROM bookmarks WHERE exam_id = ? AND question_id = ?",
                    (exam_id, question_id)
                )
                bookmarked = False
            else:
                conn.execute(
                    "INSERT INTO bookmarks (exam_id, question_id) VALUES (?, ?)",
                    (exam_id, question_id)
                )
                bookmarked = True
            conn.commit()
            return bookmarked

    def is_bookmarked(self, question_id):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT 1 FROM bookmarks WHERE question_id = ?", (question_id,))
            return cursor.fetchone() is not None

    def get_bookmarked_question_ids(self, exam_id):
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT question_id FROM bookmarks WHERE exam_id = ?", (exam_id,))
            return [row['question_id'] for row in cursor.fetchall()]

    # --- Exam Sessions CRUD ---
    def start_session(self, exam_id, is_study_mode=0, question_order=None):
        # Retrieve settings
        exam = self.get_exam(exam_id)
        time_limit = exam['time_limit'] if exam else 60
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO exam_sessions (exam_id, time_limit, is_study_mode, is_completed, question_order)
                VALUES (?, ?, ?, 0, ?)
            """, (exam_id, time_limit, is_study_mode, question_order))
            conn.commit()
            return cursor.lastrowid

    def get_active_session(self, exam_id):
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM exam_sessions 
                WHERE exam_id = ? AND is_completed = 0
                ORDER BY started_at DESC LIMIT 1
            """, (exam_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_session_time(self, session_id, time_spent_seconds):
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE exam_sessions SET time_spent = ? WHERE id = ?",
                (time_spent_seconds, session_id)
            )
            conn.commit()

    def complete_session(self, session_id):
        completed_at = datetime.now().isoformat()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE exam_sessions SET is_completed = 1, completed_at = ? WHERE id = ?",
                (completed_at, session_id)
            )
            conn.commit()

    def get_session(self, session_id):
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT s.*, e.name as exam_name, e.passing_score
                FROM exam_sessions s
                JOIN exams e ON s.exam_id = e.id
                WHERE s.id = ?
            """, (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_recent_sessions(self, limit=5):
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT s.*, e.name as exam_name,
                       (SELECT COUNT(*) FROM questions q WHERE q.exam_id = s.exam_id) as total_questions
                FROM exam_sessions s
                JOIN exams e ON s.exam_id = e.id
                ORDER BY s.started_at DESC LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # --- Session Answers CRUD ---
    def set_session_answer(self, session_id, question_id, selected_answers):
        # selected_answers is a string (e.g. "A" or "A,C" or text)
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM session_answers WHERE session_id = ? AND question_id = ?",
                (session_id, question_id)
            )
            exists = cursor.fetchone()
            if exists:
                conn.execute("""
                    UPDATE session_answers 
                    SET selected_answers = ? 
                    WHERE session_id = ? AND question_id = ?
                """, (selected_answers, session_id, question_id))
            else:
                conn.execute("""
                    INSERT INTO session_answers (session_id, question_id, selected_answers, is_flagged)
                    VALUES (?, ?, ?, 0)
                """, (session_id, question_id, selected_answers))
            conn.commit()

    def toggle_flag(self, session_id, question_id):
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT is_flagged FROM session_answers WHERE session_id = ? AND question_id = ?",
                (session_id, question_id)
            )
            row = cursor.fetchone()
            if row:
                new_flag = 0 if row['is_flagged'] else 1
                conn.execute("""
                    UPDATE session_answers SET is_flagged = ? 
                    WHERE session_id = ? AND question_id = ?
                """, (new_flag, session_id, question_id))
            else:
                new_flag = 1
                conn.execute("""
                    INSERT INTO session_answers (session_id, question_id, selected_answers, is_flagged)
                    VALUES (?, ?, NULL, 1)
                """, (session_id, question_id))
            conn.commit()
            return new_flag == 1

    def get_session_responses(self, session_id):
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT question_id, selected_answers, is_flagged
                FROM session_answers 
                WHERE session_id = ?
            """, (session_id,))
            return {row['question_id']: {'selected': row['selected_answers'], 'flagged': bool(row['is_flagged'])}
                    for row in cursor.fetchall()}

    def get_incorrect_question_ids_from_session(self, session_id):
        # To identify incorrect, we fetch all questions for this session and compare choices
        session = self.get_session(session_id)
        if not session:
            return []
        exam_id = session['exam_id']
        questions = self.get_questions(exam_id)
        responses = self.get_session_responses(session_id)
        
        incorrect_ids = []
        for q in questions:
            resp = responses.get(q['id'])
            user_sel = resp['selected'] if resp else None
            
            # evaluate correctness
            is_correct = self._evaluate_correctness(q, user_sel)
            if not is_correct:
                incorrect_ids.append(q['id'])
        return incorrect_ids

    def _evaluate_correctness(self, question, user_sel):
        if not user_sel:
            return False
        
        q_type = question['question_type']
        choices = question['choices']
        correct_letters = sorted([c['choice_letter'] for c in choices if c['is_correct']])
        
        if q_type == 'single' or q_type == 'tf':
            return user_sel.strip() in correct_letters
        elif q_type == 'multiple':
            user_letters = sorted([x.strip() for x in user_sel.split(',') if x.strip()])
            return user_letters == correct_letters
        elif q_type == 'fill':
            # For fill-in-the-blank, choices.choice_text contains correct answers (lowercase compare)
            user_val = user_sel.strip().lower()
            correct_vals = [c['choice_text'].strip().lower() for c in choices]
            return user_val in correct_vals
        elif q_type == 'drag_drop':
            return user_sel.strip().upper() == 'CORRECT'
        return False

    def calculate_score(self, session_id):
        session = self.get_session(session_id)
        if not session:
            return {'score': 0, 'total': 0, 'percentage': 0.0, 'passed': False}
        
        exam_id = session['exam_id']
        questions = self.get_questions(exam_id)
        
        # Filter questions based on session's specific question order if present
        order_str = session.get('question_order')
        if order_str:
            q_id_order = [int(x) for x in order_str.split(",") if x.strip()]
            q_dict = {q["id"]: q for q in questions}
            questions = [q_dict[qid] for qid in q_id_order if qid in q_dict]
            
        responses = self.get_session_responses(session_id)
        
        correct_count = 0
        total_questions = len(questions)
        
        for q in questions:
            resp = responses.get(q['id'])
            user_sel = resp['selected'] if resp else None
            if self._evaluate_correctness(q, user_sel):
                correct_count += 1
                
        percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0.0
        passing_score = session['passing_score']
        passed = percentage >= passing_score
        
        return {
            'correct': correct_count,
            'total': total_questions,
            'percentage': round(percentage, 1),
            'passed': passed
        }
