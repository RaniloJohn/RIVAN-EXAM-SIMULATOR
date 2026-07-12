import unittest
import os
import fitz  # PyMuPDF
from pdf_parser import PDFParser

class TestPDFParser(unittest.TestCase):
    def setUp(self):
        self.pdf_path = "d:\\Projects\\pdf-exam-simulator\\test_mock_exam.pdf"
        self.image_dir = "d:\\Projects\\pdf-exam-simulator\\test_cache_images"
        
        # 1. Create a mock PDF with structured exam text using PyMuPDF
        doc = fitz.open()
        
        # Page 1: Questions
        page1 = doc.new_page(width=595, height=842)
        text_content = """
        Practice Exam Document
        
        Question 1. What is the port number for HTTPS?
        A. Port 80
        B. Port 443
        C. Port 21
        D. Port 22
        Answer: B
        Explanation: HTTPS runs on port 443 by default. HTTP uses 80.
        
        Question 2. Which of the following are primary colors? (Select 2 correct answers)
        A. Green
        B. Red
        C. Blue
        D. Yellow
        Answer: B, C
        Explanation: Red, Blue, and Yellow are traditional subtractive primary colors, but Red, Green, and Blue (RGB) are additive primaries. In standard questions, Red and Blue are correct.
        
        Q3. True or False: Python is compiled by default.
        A. True
        B. False
        Answer: B
        Explanation: Python is generally executed as an interpreted bytecode language.
        """
        page1.insert_textbox((50, 50, 545, 750), text_content, fontname="helv", fontsize=11)
        
        # Page 2: Table & Answer Key
        page2 = doc.new_page(width=595, height=842)
        page2.insert_text((50, 50), "Question 4. Look at the key value pair below.", fontsize=11, fontname="helv")
        # Draw a line representing a table element (to test vector layout extraction)
        shape = page2.new_shape()
        shape.draw_rect((50, 100, 300, 150))
        shape.finish()
        shape.commit()
        
        page2.insert_text((50, 200), "What is the answer for Q4?", fontsize=11, fontname="helv")
        
        # Add answer sheet text
        answer_sheet = """
        Answer Key
        1. B
        2. B, C
        3. B
        4. A
        """
        page2.insert_textbox((50, 250, 300, 450), answer_sheet, fontname="helv", fontsize=11)
        
        doc.save(self.pdf_path)
        doc.close()

    def tearDown(self):
        if os.path.exists(self.pdf_path):
            try:
                os.remove(self.pdf_path)
            except:
                pass
        
        # Clean up image dir if created
        if os.path.exists(self.image_dir):
            try:
                for f in os.listdir(self.image_dir):
                    os.remove(os.path.join(self.image_dir, f))
                os.rmdir(self.image_dir)
            except:
                pass

    def test_regex_extraction_logic(self):
        parser = PDFParser(self.pdf_path)
        questions = parser.parse_pdf(image_dir=self.image_dir)
        
        # Check total questions parsed
        self.assertGreaterEqual(len(questions), 3)
        
        # Validate Question 1
        q1 = questions[0]
        self.assertEqual(q1["question_num"], 1)
        self.assertEqual(q1["question_type"], "single")
        self.assertEqual(len(q1["choices"]), 4)
        self.assertEqual(q1["choices"][1][0], "B") # Choice B letter
        self.assertEqual(q1["choices"][1][2], 1)   # Choice B is_correct
        self.assertIn("HTTPS", q1["question_text"])
        self.assertIn("HTTPS runs on port 443", q1["explanation"])

        # Validate Question 2 (Multiple Response)
        q2 = questions[1]
        self.assertEqual(q2["question_num"], 2)
        self.assertEqual(q2["question_type"], "multiple")
        correct_choices = [c[0] for c in q2["choices"] if c[2] == 1]
        self.assertEqual(sorted(correct_choices), ["B", "C"])

        # Validate Question 3 (True/False)
        q3 = questions[2]
        self.assertEqual(q3["question_num"], 3)
        self.assertEqual(q3["question_type"], "tf")
        self.assertEqual(len(q3["choices"]), 2)

if __name__ == "__main__":
    unittest.main()
