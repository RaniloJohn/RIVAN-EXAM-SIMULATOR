from PySide6.QtCore import QThread, Signal
from pdf_parser import PDFParser
from database import Database

class ParserWorker(QThread):
    # Signals to communicate with the GUI thread
    progress_updated = Signal(int, int)      # current_page, total_pages
    question_saved = Signal(int, int)        # current_question_index, total_questions
    finished = Signal(int, int)              # exam_id, total_questions
    failed = Signal(str)                     # error_message

    def __init__(self, filepath, exam_name, passing_score=70, time_limit=60, tesseract_path=None, custom_rules=None):
        super().__init__()
        self.filepath = filepath
        self.exam_name = exam_name
        self.passing_score = passing_score
        self.time_limit = time_limit
        self.tesseract_path = tesseract_path
        self.custom_rules = custom_rules
        self.db = Database()

    def run(self):
        try:
            # 1. Parse the PDF
            parser = PDFParser(
                filepath=self.filepath, 
                tesseract_path=self.tesseract_path, 
                custom_rules=self.custom_rules
            )
            
            # Progress callback for the parser
            def on_progress(current, total):
                self.progress_updated.emit(current, total)

            # Extract list of raw question objects
            questions_list = parser.parse_pdf(progress_callback=on_progress)
            
            if not questions_list:
                self.failed.emit("No questions could be extracted from the PDF. Please check your file or custom regex patterns.")
                return

            # 2. Save to SQLite database
            exam_id = self.db.create_exam(
                name=self.exam_name, 
                filepath=self.filepath, 
                passing_score=self.passing_score, 
                time_limit=self.time_limit
            )
            
            total_questions = len(questions_list)
            for idx, q in enumerate(questions_list):
                q_id = self.db.add_question(
                    exam_id=exam_id,
                    question_num=q["question_num"],
                    section=q["section"],
                    question_text=q["question_text"],
                    question_type=q["question_type"],
                    explanation=q["explanation"],
                    confidence=q["confidence"]
                )
                if q["choices"]:
                    self.db.add_choices(q_id, q["choices"])
                self.question_saved.emit(idx + 1, total_questions)

            # Complete!
            self.finished.emit(exam_id, total_questions)
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            self.failed.emit(f"Failed to ingest PDF: {str(e)}\n\n{error_trace}")
