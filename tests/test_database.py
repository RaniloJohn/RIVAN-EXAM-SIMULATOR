import unittest
import os
from database import Database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Use a temporary file path for tests
        self.db_path = "d:\\Projects\\pdf-exam-simulator\\test_exam_simulator.db"
        # Ensure clean state
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

    def test_exam_crud(self):
        exam_id = self.db.create_exam("AWS Solutions Architect", "test.pdf", 72, 90)
        self.assertIsNotNone(exam_id)
        
        exams = self.db.get_exams()
        self.assertEqual(len(exams), 1)
        self.assertEqual(exams[0]["name"], "AWS Solutions Architect")
        self.assertEqual(exams[0]["passing_score"], 72)
        
        exam = self.db.get_exam(exam_id)
        self.assertEqual(exam["time_limit"], 90)
        
        self.db.update_exam_settings(exam_id, 80, 100)
        exam = self.db.get_exam(exam_id)
        self.assertEqual(exam["passing_score"], 80)
        self.assertEqual(exam["time_limit"], 100)
        
        self.db.delete_exam(exam_id)
        self.assertIsNone(self.db.get_exam(exam_id))

    def test_questions_and_choices(self):
        exam_id = self.db.create_exam("Test Exam")
        
        # Add MC Question
        q_id = self.db.add_question(
            exam_id=exam_id,
            question_num=1,
            section="Network",
            question_text="What is HTTP port?",
            question_type="single"
        )
        
        choices = [
            ("A", "Port 80", 1),
            ("B", "Port 443", 0),
            ("C", "Port 22", 0)
        ]
        self.db.add_choices(q_id, choices)
        
        # Retrieve
        questions = self.db.get_questions(exam_id)
        self.assertEqual(len(questions), 1)
        self.assertEqual(len(questions[0]["choices"]), 3)
        self.assertEqual(questions[0]["choices"][0]["choice_letter"], "A")
        self.assertEqual(questions[0]["choices"][0]["is_correct"], 1)

    def test_bookmarking(self):
        exam_id = self.db.create_exam("Test Exam")
        q_id = self.db.add_question(exam_id, 1, "Sec", "Q Text", "single")
        
        # Test Toggle Bookmarking
        is_bm = self.db.toggle_bookmark(exam_id, q_id)
        self.assertTrue(is_bm)
        self.assertTrue(self.db.is_bookmarked(q_id))
        
        is_bm = self.db.toggle_bookmark(exam_id, q_id)
        self.assertFalse(is_bm)
        self.assertFalse(self.db.is_bookmarked(q_id))

    def test_session_scoring(self):
        exam_id = self.db.create_exam("Scoring Exam", passing_score=75)
        
        # Q1: Single choice (Correct: A)
        q1_id = self.db.add_question(exam_id, 1, "Sec", "Q1", "single")
        self.db.add_choices(q1_id, [("A", "C1", 1), ("B", "C2", 0)])
        
        # Q2: Multiple response (Correct: B, C)
        q2_id = self.db.add_question(exam_id, 2, "Sec", "Q2", "multiple")
        self.db.add_choices(q2_id, [("A", "C1", 0), ("B", "C2", 1), ("C", "C3", 1)])
        
        # Q3: Fill in the blank (Correct answer value: "python")
        q3_id = self.db.add_question(exam_id, 3, "Sec", "Q3", "fill")
        self.db.add_choices(q3_id, [("A", "python", 1)])

        # Start session
        session_id = self.db.start_session(exam_id)
        self.assertIsNotNone(session_id)
        
        # Set Answers
        self.db.set_session_answer(session_id, q1_id, "A")       # Correct
        self.db.set_session_answer(session_id, q2_id, "B,C")     # Correct
        self.db.set_session_answer(session_id, q3_id, "java")    # Incorrect
        
        # Evaluate scoring
        score = self.db.calculate_score(session_id)
        self.assertEqual(score["correct"], 2)
        self.assertEqual(score["total"], 3)
        self.assertEqual(score["percentage"], 66.7)
        self.assertFalse(score["passed"]) # 66.7% < 75% required
        
        # Correct last answer
        self.db.set_session_answer(session_id, q3_id, "python")  # Correct
        score = self.db.calculate_score(session_id)
        self.assertEqual(score["correct"], 3)
        self.assertTrue(score["passed"])

if __name__ == "__main__":
    unittest.main()
