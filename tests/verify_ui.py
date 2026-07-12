import sys
import os
import unittest
from PySide6.QtWidgets import QApplication, QPushButton, QRadioButton, QCheckBox, QLineEdit, QDialog
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest

# Ensure project root is in sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from ui.main_window import MainWindow
from database import Database
from pdf_parser import PDFParser

class TestUIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We need a single QApplication instance for UI tests
        cls.app = QApplication.instance() or QApplication(sys.argv)
        cls.db_path = "d:\\Projects\\pdf-exam-simulator\\test_ui_simulator.db"
        cls.pdf_path = "d:\\Projects\\pdf-exam-simulator\\test_ui_mock_exam.pdf"
        
        # Clean previous
        if os.path.exists(cls.db_path):
            os.remove(cls.db_path)
            
        # Create a mock PDF
        doc = fitz_doc = fitz = None
        try:
            import fitz
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)
            page.insert_textbox((50, 50, 545, 750), """
            UI Verification Exam
            
            Question 1. Which language is this application written in?
            A. Java
            B. Python
            C. C++
            D. JavaScript
            Answer: B
            Explanation: The app uses PySide6 with Python 3.13.
            
            Question 2. True or False: This app works completely offline.
            A. True
            B. False
            Answer: A
            Explanation: All processing and DB operations are local.
            """, fontname="helv", fontsize=11)
            doc.save(cls.pdf_path)
            doc.close()
        except Exception as e:
            print(f"Error creating test PDF: {e}")

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.db_path):
            try:
                os.remove(cls.db_path)
            except:
                pass
        if os.path.exists(cls.pdf_path):
            try:
                os.remove(cls.pdf_path)
            except:
                pass

    def setUp(self):
        # Override DB path for MainWindow before spawning
        self.db = Database(self.db_path)
        self.window = MainWindow()
        self.window.db = self.db

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()

    def test_full_application_flow(self):
        # 1. Spawns Dashboard
        self.assertEqual(self.window.stack.currentWidget(), self.window.dashboard_view)
        
        # 2. Add Exam manually (to bypass import file dialog modal blocking)
        exam_id = self.db.create_exam("UI Verification Test", self.pdf_path, 50, 30)
        q1_id = self.db.add_question(exam_id, 1, "General", "Which language is this application written in?", "single")
        self.db.add_choices(q1_id, [("A", "Java", 0), ("B", "Python", 1), ("C", "C++", 0)])
        q2_id = self.db.add_question(exam_id, 2, "General", "True or False: This app works completely offline.", "tf")
        self.db.add_choices(q2_id, [("A", "True", 1), ("B", "False", 0)])
        
        # Reload dashboard
        self.window.dashboard_view.load_data()
        QApplication.processEvents()
        
        # 3. Launch Simulator (Exam Mode, No Shuffling to make answers predictable)
        self.window.load_exam_simulator(exam_id, is_study_mode=False, shuffle_questions=False, shuffle_choices=False)
        QApplication.processEvents()
        
        sim_view = self.window.simulator_view
        self.assertEqual(len(sim_view.questions), 2)
        
        # 4. Answer Question 1 (Select 'B' which is Python)
        # Find radio buttons in answers container
        radios = sim_view.answers_frame.findChildren(QRadioButton)
        self.assertEqual(len(radios), 3)
        
        # Click Radio B (index 1)
        QTest.mouseClick(radios[1], Qt.LeftButton)
        sim_view.save_current_answer()
        
        # 5. Flag Question 1
        QTest.mouseClick(sim_view.flag_btn, Qt.LeftButton)
        self.assertTrue(sim_view.responses[q1_id]["flagged"])
        
        # 6. Navigate to Next Question
        QTest.mouseClick(sim_view.next_btn, Qt.LeftButton)
        QApplication.processEvents()
        self.assertEqual(sim_view.current_index, 1)
        
        # 7. Answer Question 2 (Select 'A' which is True)
        radios_q2 = sim_view.answers_frame.findChildren(QRadioButton)
        self.assertEqual(len(radios_q2), 2)
        QTest.mouseClick(radios_q2[0], Qt.LeftButton)
        sim_view.save_current_answer()
        
        # 8. Submit Exam
        sim_view.end_session()
        QApplication.processEvents()
        
        # 9. Verify Results View
        res_view = self.window.stack.currentWidget()
        self.assertEqual(res_view, self.window.results_view)
        
        # Verify score (100% correct)
        self.assertEqual(res_view.score["correct"], 2)
        self.assertEqual(res_view.score["percentage"], 100.0)
        self.assertTrue(res_view.score["passed"])
        
        # 10. Test CSV and PDF report generation path offline
        csv_path = "d:\\Projects\\pdf-exam-simulator\\test_report.csv"
        pdf_path = "d:\\Projects\\pdf-exam-simulator\\test_report.pdf"
        
        if os.path.exists(csv_path):
            os.remove(csv_path)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
        from unittest.mock import patch
        
        # Run exporters programmatically using mock dialogs
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=(csv_path, "CSV Files (*.csv)")), \
             patch('PySide6.QtWidgets.QMessageBox.information'), \
             patch('PySide6.QtWidgets.QMessageBox.critical', side_effect=lambda *args: print("CRITICAL CSV ERROR:", args)):
            res_view.export_csv()
            
        with patch('PySide6.QtWidgets.QFileDialog.getSaveFileName', return_value=(pdf_path, "PDF Files (*.pdf)")), \
             patch('PySide6.QtWidgets.QMessageBox.information'), \
             patch('PySide6.QtWidgets.QMessageBox.critical', side_effect=lambda *args: print("CRITICAL PDF ERROR:", args)):
            res_view.export_pdf()
            
        # Confirm reports created
        self.assertTrue(os.path.exists(csv_path))
        self.assertTrue(os.path.exists(pdf_path))

if __name__ == "__main__":
    unittest.main()
