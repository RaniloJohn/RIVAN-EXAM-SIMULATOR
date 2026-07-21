import unittest
import os
import random
from database import Database

class TestChoiceShuffling(unittest.TestCase):
    def setUp(self):
        self.db_path = "d:\\Projects\\pdf-exam-simulator\\test_shuffling.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = Database(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

    def test_shuffled_choices_mapping(self):
        # Create exam and question with DB choice order: A=Wrong, B=Correct, C=Wrong
        exam_id = self.db.create_exam("Test Exam")
        q_id = self.db.add_question(exam_id, 1, "Sec", "Q1", "single")
        self.db.add_choices(q_id, [("A", "Port 22", 0), ("B", "Port 80", 1), ("C", "Port 443", 0)])

        questions = self.db.get_questions(exam_id)
        q = questions[0]

        # Simulate choice shuffling: shuffle list of choices in memory
        shuffled_choices = list(q["choices"])
        # Ensure B is not first so display letter differs from canonical letter
        shuffled_choices.sort(key=lambda c: c["choice_text"]) # Port 22 (A), Port 443 (C), Port 80 (B)
        
        # Display letters assigned sequentially:
        # Index 0: Port 22 (DB letter A, display A)
        # Index 1: Port 443 (DB letter C, display B)
        # Index 2: Port 80 (DB letter B, display C)
        letters = [chr(ord('A') + i) for i in range(len(shuffled_choices))]
        display_to_canonical = {}
        for display_letter, c in zip(letters, shuffled_choices):
            display_to_canonical[display_letter] = c["choice_letter"]

        # User sees "C. Port 80" on screen and clicks option C.
        selected_display_option = "C" # User selected Port 80 displayed as C
        saved_canonical_letter = display_to_canonical[selected_display_option] # Should be 'B'

        # Store answer in DB
        session_id = self.db.start_session(exam_id)
        self.db.set_session_answer(session_id, q_id, saved_canonical_letter)

        # Verify database score calculation
        score = self.db.calculate_score(session_id)
        self.assertEqual(score["correct"], 1)
        self.assertEqual(score["total"], 1)
        self.assertEqual(score["percentage"], 100.0)
        self.assertTrue(score["passed"])

if __name__ == "__main__":
    unittest.main()
