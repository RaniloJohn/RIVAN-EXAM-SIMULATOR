from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QSplitter, QListWidget, 
                             QTextBrowser, QMessageBox, QFileDialog, QListWidgetItem)
from PySide6.QtCore import Qt
from styles import Styles
import csv
import os
import fitz  # PyMuPDF for offline PDF export

class ResultsView(QWidget):
    def __init__(self, parent_window, session_id):
        super().__init__(parent_window)
        self.main_window = parent_window
        self.db = parent_window.db
        self.session_id = session_id
        
        # Load Session Data
        self.session = self.db.get_session(self.session_id)
        self.exam_id = self.session["exam_id"]
        self.questions = self.db.get_questions(self.exam_id)
        self.responses = self.db.get_session_responses(self.session_id)
        self.score = self.db.calculate_score(self.session_id)
        
        # Restore session question order
        order_str = self.session.get("question_order")
        if order_str:
            q_id_order = [int(x) for x in order_str.split(",") if x.strip()]
            q_dict = {q["id"]: q for q in self.questions}
            self.questions = [q_dict[qid] for qid in q_id_order if qid in q_dict]

        self._init_ui()
        self.load_results()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # --- Header Banner ---
        header = QHBoxLayout()
        title_lbl = QLabel(f"Results Summary: {self.session['exam_name']}", self)
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        header.addWidget(title_lbl)
        
        header.addStretch()
        
        # Export Buttons
        self.export_csv_btn = QPushButton("Export CSV Report", self)
        self.export_csv_btn.clicked.connect(self.export_csv)
        header.addWidget(self.export_csv_btn)
        
        self.export_pdf_btn = QPushButton("Export PDF Report", self)
        self.export_pdf_btn.setObjectName("primary_btn")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        header.addWidget(self.export_pdf_btn)
        
        self.done_btn = QPushButton("Done (Dashboard)", self)
        self.done_btn.clicked.connect(self.main_window.show_dashboard)
        header.addWidget(self.done_btn)
        
        layout.addLayout(header)
        
        # --- Score Banner (Passed / Failed indicator) ---
        self.banner_frame = QFrame(self)
        self.banner_frame.setObjectName("card")
        
        banner_layout = QHBoxLayout(self.banner_frame)
        banner_layout.setContentsMargins(25, 20, 25, 20)
        
        score_layout = QVBoxLayout()
        self.banner_status_lbl = QLabel("PASSED", self.banner_frame)
        self.banner_status_lbl.setStyleSheet("font-size: 24px; font-weight: 800;")
        score_layout.addWidget(self.banner_status_lbl)
        
        self.score_lbl = QLabel("Score: 0.0% (0/0 questions)", self.banner_frame)
        self.score_lbl.setStyleSheet("font-size: 16px; font-weight: 600; color: #94a3b8;")
        score_layout.addWidget(self.score_lbl)
        banner_layout.addLayout(score_layout)
        
        banner_layout.addStretch()
        
        # Time and settings detail
        stats_layout = QVBoxLayout()
        stats_layout.setAlignment(Qt.AlignRight)
        
        self.time_lbl = QLabel("Time Spent: 00:00:00", self.banner_frame)
        self.time_lbl.setStyleSheet("font-weight: 600; font-size: 14px;")
        stats_layout.addWidget(self.time_lbl)
        
        self.passing_score_lbl = QLabel("Passing Score Required: 70%", self.banner_frame)
        self.passing_score_lbl.setStyleSheet("color: #94a3b8;")
        stats_layout.addWidget(self.passing_score_lbl)
        
        banner_layout.addLayout(stats_layout)
        layout.addWidget(self.banner_frame)
        
        # --- Question Review Splitter ---
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setStyleSheet("QSplitter::handle { background-color: #334155; }")
        
        # Left sidebar index
        left_panel = QFrame(splitter)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.addWidget(QLabel("Review Questions:", left_panel))
        
        self.q_list = QListWidget(left_panel)
        self.q_list.currentRowChanged.connect(self.view_question_details)
        left_layout.addWidget(self.q_list)
        splitter.addWidget(left_panel)
        
        # Right detail browser
        right_panel = QFrame(splitter)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        right_layout.addWidget(QLabel("Answer Review Detail:", right_panel))
        self.detail_browser = QTextBrowser(right_panel)
        import sys
        if getattr(sys, 'frozen', False):
            project_root = os.path.dirname(os.path.dirname(sys.executable))
        else:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.detail_browser.setSearchPaths([os.getcwd(), project_root])
        self.detail_browser.document().setDefaultStyleSheet(Styles.get_html_css(self.main_window.dark_mode))
        right_layout.addWidget(self.detail_browser)
        splitter.addWidget(right_panel)
        
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)

    def load_results(self):
        # 1. Update Banner
        pct = self.score["percentage"]
        correct = self.score["correct"]
        total = self.score["total"]
        passed = self.score["passed"]
        
        # Style banner depending on status
        bg_color = "#069669" if passed else "#dc2626"
        self.banner_frame.setStyleSheet(f"background-color: {bg_color}; border: none; border-radius: 12px;")
        self.banner_status_lbl.setText("PASSED" if passed else "FAILED")
        self.banner_status_lbl.setStyleSheet("font-size: 26px; font-weight: 800; color: #ffffff;")
        self.score_lbl.setText(f"Score: {pct}% ({correct} / {total} questions)")
        self.score_lbl.setStyleSheet("font-size: 15px; font-weight: 600; color: #f1f5f9;")
        
        # Time Display
        spent = self.session["time_spent"]
        h = spent // 3600
        m = (spent % 3600) // 60
        s = spent % 60
        self.time_lbl.setText(f"Time Spent: {h:02d}:{m:02d}:{s:02d}")
        self.time_lbl.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 14px;")
        self.passing_score_lbl.setText(f"Passing Score Target: {self.session['passing_score']}%")
        self.passing_score_lbl.setStyleSheet("color: #f1f5f9;")

        # 2. Populate Questions List
        self.q_list.clear()
        for idx, q in enumerate(self.questions):
            q_id = q["id"]
            resp = self.responses.get(q_id)
            user_sel = resp["selected"] if resp else None
            
            is_correct = self.db._evaluate_correctness(q, user_sel)
            
            item_text = f"Question {idx + 1}"
            if not user_sel:
                item_text += " [Unanswered]"
                color_code = "#94a3b8"  # grey
            elif is_correct:
                item_text += " [Correct]"
                color_code = "#10b981"  # green
            else:
                item_text += " [Incorrect]"
                color_code = "#ef4444"  # red
                
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, idx)
            # Use styling for colors
            item.setForeground(Qt.white if self.main_window.dark_mode else Qt.black)
            self.q_list.addItem(item)
            
        if self.q_list.count() > 0:
            self.q_list.setCurrentRow(0)

    def view_question_details(self, list_index):
        if list_index < 0 or list_index >= len(self.questions):
            return
            
        item = self.q_list.item(list_index)
        abs_index = item.data(Qt.UserRole)
        q = self.questions[abs_index]
        q_id = q["id"]
        
        # Load user answer
        resp = self.responses.get(q_id)
        user_sel = resp["selected"] if resp else None
        is_correct = self.db._evaluate_correctness(q, user_sel)
        
        # Build explanation view HTML
        html = f"<h3>Question {abs_index + 1} (No. {q['question_num']})</h3>"
        html += q["question_text"]
        
        # Render choices with highlights
        html += "<h4>Choices:</h4>"
        html += "<ul>"
        
        q_type = q["question_type"]
        if q_type in ["single", "multiple", "tf"]:
            for c in q["choices"]:
                letter = c["choice_letter"]
                text = c["choice_text"]
                correct_class = ""
                selected_marker = ""
                
                # Check correct and selected states
                is_choice_correct = bool(c["is_correct"])
                is_selected = user_sel and letter in [x.strip() for x in user_sel.split(",")]
                
                if is_choice_correct:
                    correct_class = "class='correct-highlight'"
                elif is_selected:
                    correct_class = "class='incorrect-highlight'"
                    
                if is_selected:
                    selected_marker = " <b>(Selected)</b>"
                if is_choice_correct:
                    selected_marker += " <b>[Correct Answer]</b>"
                    
                html += f"<li style='margin-bottom: 8px;'><span {correct_class}>{letter}. {text}</span>{selected_marker}</li>"
        elif q_type == "fill":
            correct_vals = ", ".join([c["choice_text"] for c in q["choices"]])
            user_val = user_sel if user_sel else "[No Answer Typed]"
            color_class = "correct-highlight" if is_correct else "incorrect-highlight"
            
            html += f"<p><b>Your Typed Value:</b> <span class='{color_class}'>{user_val}</span></p>"
            html += f"<p><b>Accepted Correct Answers:</b> <span class='correct-highlight'>{correct_vals}</span></p>"
        elif q_type == "drag_drop":
            user_val = "Correct (Self-Graded)" if user_sel == "CORRECT" else ("Incorrect (Self-Graded)" if user_sel == "INCORRECT" else "[Not Graded / Unanswered]")
            color_class = "correct-highlight" if is_correct else "incorrect-highlight"
            if not user_sel or user_sel == "PENDING":
                color_class = "text-secondary"
            html += f"<p><b>Your Grading:</b> <span class='{color_class}'>{user_val}</span></p>"
            
        html += "</ul>"
        
        # Status block
        status_text = "<font color='#10b981'><b>✓ CORRECT</b></font>" if is_correct else f"<font color='#ef4444'><b>✗ INCORRECT</b></font>"
        if not user_sel:
            status_text = "<font color='#94a3b8'><b>UNANSWERED</b></font>"
            
        html += f"""
        <div class="explanation-box">
            <p><b>Question Status:</b> {status_text}</p>
            <p><b>Explanation:</b> {q['explanation'] or 'No explanation available.'}</p>
        </div>
        """
        
        self.detail_browser.setHtml(f"<html><body>{html}</body></html>")

    # --- Exporters ---
    def export_csv(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export CSV Report", "", "CSV Files (*.csv)")
        if not filepath:
            return
            
        try:
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Question Number", "Question Type", "Your Selection", "Correct Answer Key", "Result", "Explanation"])
                
                for idx, q in enumerate(self.questions):
                    resp = self.responses.get(q["id"])
                    user_sel = resp["selected"] if resp and resp["selected"] is not None else ""
                    
                    correct_letters = ",".join([c["choice_letter"] for c in q["choices"] if c["is_correct"]])
                    if q["question_type"] == "fill":
                        correct_letters = "|".join([c["choice_text"] for c in q["choices"]])
                        
                    is_correct = self.db._evaluate_correctness(q, user_sel)
                    result_str = "Correct" if is_correct else ("Unanswered" if not user_sel else "Incorrect")
                    
                    writer.writerow([
                        q["question_num"],
                        q["question_type"],
                        user_sel,
                        correct_letters,
                        result_str,
                        q["explanation"] or ""
                    ])
                    
            QMessageBox.information(self, "Export Success", "Exam results successfully exported to CSV file.")
        except Exception as e:
            QMessageBox.critical(self, "Export Failure", f"Failed to export CSV: {e}")

    def export_pdf(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export PDF Report", "", "PDF Files (*.pdf)")
        if not filepath:
            return
            
        try:
            # Generate a new PDF document using PyMuPDF
            doc = fitz.open()
            
            # Page 1: Cover / Summary Sheet
            page = doc.new_page(width=595, height=842) # A4 Size
            
            # Print Summary
            page.insert_text((50, 60), "EXAM ATTEMPT REPORT", fontsize=20, fontname="hebo", color=(0.09, 0.59, 0.41))
            page.insert_text((50, 100), f"Exam: {self.session['exam_name']}", fontsize=14, fontname="hebo")
            page.insert_text((50, 125), f"Date Taken: {self.session['started_at']}", fontsize=11, fontname="helv")
            page.insert_text((50, 145), f"Passing Requirement: {self.session['passing_score']}%", fontsize=11, fontname="helv")
            
            # Score card border box
            rect = fitz.Rect(50, 180, 545, 290)
            fill_color = (0.9, 0.98, 0.95) if self.score["passed"] else (0.99, 0.94, 0.94)
            border_color = (0.04, 0.72, 0.5) if self.score["passed"] else (0.94, 0.27, 0.27)
            
            # Draw score box
            shape = page.new_shape()
            shape.draw_rect(rect)
            shape.finish(color=border_color, fill=fill_color, width=1.5)
            shape.commit()
            
            status_txt = "PASSED" if self.score["passed"] else "FAILED"
            status_color = (0.04, 0.72, 0.5) if self.score["passed"] else (0.94, 0.27, 0.27)
            page.insert_text((70, 215), status_txt, fontsize=18, fontname="hebo", color=status_color)
            
            page.insert_text((70, 245), f"Your Score: {self.score['percentage']}%", fontsize=14, fontname="hebo")
            page.insert_text((70, 270), f"Questions: {self.score['correct']} Correct out of {self.score['total']} Total", fontsize=11, fontname="helv")
            
            # Time statistics
            spent = self.session["time_spent"]
            h = spent // 3600
            m = (spent % 3600) // 60
            s = spent % 60
            page.insert_text((350, 245), f"Time Elapsed: {h:02d}:{m:02d}:{s:02d}", fontsize=12, fontname="helv")
            
            # Questions Table Header
            page.insert_text((50, 330), "QUESTION BY QUESTION REVIEW SUMMARY", fontsize=12, fontname="hebo")
            
            y_offset = 360
            # Header Row
            page.insert_text((50, y_offset), "Q.No.", fontsize=10, fontname="hebo")
            page.insert_text((100, y_offset), "Type", fontsize=10, fontname="hebo")
            page.insert_text((200, y_offset), "Your Answer", fontsize=10, fontname="hebo")
            page.insert_text((320, y_offset), "Correct Answer", fontsize=10, fontname="hebo")
            page.insert_text((450, y_offset), "Result", fontsize=10, fontname="hebo")
            
            shape = page.new_shape()
            shape.draw_line((50, y_offset + 5), (545, y_offset + 5))
            shape.finish(color=(0.7, 0.7, 0.7), width=1)
            shape.commit()
            
            y_offset += 25
            
            for idx, q in enumerate(self.questions):
                # Check page overflow
                if y_offset > 800:
                    page = doc.new_page(width=595, height=842)
                    y_offset = 50
                
                resp = self.responses.get(q["id"])
                user_sel = resp["selected"] if resp and resp["selected"] is not None else ""
                
                correct_letters = ",".join([c["choice_letter"] for c in q["choices"] if c["is_correct"]])
                if q["question_type"] == "fill":
                    correct_letters = "|".join([c["choice_text"] for c in q["choices"]])
                    
                is_correct = self.db._evaluate_correctness(q, user_sel)
                result_str = "Correct" if is_correct else ("Unanswered" if not user_sel else "Incorrect")
                res_color = (0.04, 0.72, 0.5) if is_correct else ((0.5, 0.5, 0.5) if not user_sel else (0.94, 0.27, 0.27))
                
                # Truncate text if needed
                user_sel_trunc = (user_sel[:20] + '...') if len(user_sel) > 20 else user_sel
                correct_trunc = (correct_letters[:20] + '...') if len(correct_letters) > 20 else correct_letters
                
                page.insert_text((50, y_offset), f"Q {idx+1}", fontsize=9, fontname="helv")
                page.insert_text((100, y_offset), q["question_type"].title(), fontsize=9, fontname="helv")
                page.insert_text((200, y_offset), user_sel_trunc if user_sel_trunc else "-", fontsize=9, fontname="helv")
                page.insert_text((320, y_offset), correct_trunc, fontsize=9, fontname="helv")
                page.insert_text((450, y_offset), result_str, fontsize=9, fontname="hebo", color=res_color)
                
                y_offset += 20
                
            # Save document
            doc.save(filepath)
            doc.close()
            
            QMessageBox.information(self, "Export Success", "Report successfully exported to PDF.")
        except Exception as e:
            QMessageBox.critical(self, "Export Failure", f"Failed to export PDF: {e}")
