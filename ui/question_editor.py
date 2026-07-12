from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                             QLabel, QTextEdit, QComboBox, QPushButton, 
                             QCheckBox, QFrame, QSplitter, QFormLayout, 
                             QLineEdit, QScrollArea, QMessageBox, QListWidgetItem)
from PySide6.QtCore import Qt

class QuestionEditorView(QWidget):
    def __init__(self, parent_window, exam_id):
        super().__init__(parent_window)
        self.main_window = parent_window
        self.db = parent_window.db
        self.exam_id = exam_id
        
        # Load Exam Info
        self.exam = self.db.get_exam(self.exam_id)
        
        self.questions = []
        self.selected_question = None
        self.choice_widgets = []
        
        self._init_ui()
        self.load_questions()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Top Title Bar
        header = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Dashboard", self)
        back_btn.clicked.connect(self.main_window.show_dashboard)
        header.addWidget(back_btn)
        
        title_lbl = QLabel(f"Question Editor: {self.exam['name']}", self)
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; margin-left: 15px;")
        header.addWidget(title_lbl)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Splitter Layout
        splitter = QSplitter(Qt.Horizontal, self)
        splitter.setStyleSheet("QSplitter::handle { background-color: #334155; }")
        
        # Left Panel - Question list
        left_panel = QFrame(splitter)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)
        
        list_lbl = QLabel("Questions Index", left_panel)
        list_lbl.setStyleSheet("font-weight: bold;")
        left_layout.addWidget(list_lbl)
        
        self.q_list = QListWidget(left_panel)
        self.q_list.currentItemChanged.connect(self._on_question_selected)
        left_layout.addWidget(self.q_list)
        
        splitter.addWidget(left_panel)
        
        # Right Panel - Form Editor
        right_panel = QFrame(splitter)
        self.right_layout = QVBoxLayout(right_panel)
        self.right_layout.setContentsMargins(10, 0, 0, 0)
        self.right_layout.setSpacing(15)
        
        # Form Container
        self.scroll_area = QScrollArea(right_panel)
        self.scroll_area.setWidgetResizable(True)
        self.form_widget = QWidget()
        self.form_layout = QVBoxLayout(self.form_widget)
        self.form_layout.setSpacing(15)
        
        # Question Text Area
        self.form_layout.addWidget(QLabel("Question HTML Text:"))
        self.q_text_edit = QTextEdit(self.form_widget)
        self.q_text_edit.setMinimumHeight(150)
        self.form_layout.addWidget(self.q_text_edit)
        
        # Question Type
        type_row = QHBoxLayout()
        type_row.addWidget(QLabel("Question Type:"))
        self.type_combo = QComboBox(self.form_widget)
        self.type_combo.addItems([
            "Multiple Choice (Single Answer)", 
            "Multiple Response (Multiple Answers)", 
            "True/False", 
            "Fill-in-the-blank"
        ])
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_row.addWidget(self.type_combo)
        type_row.addStretch()
        self.form_layout.addLayout(type_row)
        
        # Choices Section
        self.choices_title = QLabel("Choices / Answers:")
        self.choices_title.setStyleSheet("font-weight: bold;")
        self.form_layout.addWidget(self.choices_title)
        
        self.choices_container = QFrame(self.form_widget)
        self.choices_box_layout = QVBoxLayout(self.choices_container)
        self.choices_box_layout.setContentsMargins(0, 0, 0, 0)
        self.choices_box_layout.setSpacing(8)
        self.form_layout.addWidget(self.choices_container)
        
        # Choices action buttons
        self.choices_actions = QHBoxLayout()
        self.add_choice_btn = QPushButton("+ Add Choice", self.form_widget)
        self.add_choice_btn.clicked.connect(self._add_choice_row)
        self.choices_actions.addWidget(self.add_choice_btn)
        
        self.choices_actions.addStretch()
        self.form_layout.addLayout(self.choices_actions)
        
        # Explanation Text Area
        self.form_layout.addWidget(QLabel("Explanation / Answers Key Explanation:"))
        self.exp_text_edit = QTextEdit(self.form_widget)
        self.exp_text_edit.setMinimumHeight(100)
        self.form_layout.addWidget(self.exp_text_edit)
        
        self.scroll_area.setWidget(self.form_widget)
        self.right_layout.addWidget(self.scroll_area)
        
        # Save Panel
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.save_btn = QPushButton("Save Question Modifications", self)
        self.save_btn.setObjectName("primary_btn")
        self.save_btn.clicked.connect(self._save_question)
        save_layout.addWidget(self.save_btn)
        self.right_layout.addLayout(save_layout)
        
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 700])
        layout.addWidget(splitter)
        
        # Initially disable right panel inputs if nothing is selected
        self._toggle_form_enabled(False)

    def load_questions(self):
        self.q_list.clear()
        self.questions = self.db.get_questions(self.exam_id)
        
        for q in self.questions:
            item = QListWidgetItem(f"Question {q['question_num']}")
            
            # Highlight low confidence questions
            if q["confidence"] < 0.5:
                item.setText(f"⚠️ Question {q['question_num']} (Low Confidence)")
                item.setForeground(Qt.red)
            elif q["confidence"] < 0.8:
                item.setText(f"⚡ Question {q['question_num']} (Check Answers)")
                item.setForeground(Qt.yellow)
                
            item.setData(Qt.UserRole, q)
            self.q_list.addItem(item)
            
        if self.q_list.count() > 0:
            self.q_list.setCurrentRow(0)

    def _toggle_form_enabled(self, enabled):
        self.q_text_edit.setEnabled(enabled)
        self.type_combo.setEnabled(enabled)
        self.add_choice_btn.setEnabled(enabled)
        self.exp_text_edit.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        if not enabled:
            # Clear fields
            self.q_text_edit.clear()
            self.exp_text_edit.clear()
            self._clear_choices()

    def _clear_choices(self):
        for w in self.choice_widgets:
            w.setParent(None)
            w.deleteLater()
        self.choice_widgets.clear()

    def _on_question_selected(self, current, previous):
        if not current:
            self.selected_question = None
            self._toggle_form_enabled(False)
            return
            
        q = current.data(Qt.UserRole)
        self.selected_question = q
        self._toggle_form_enabled(True)
        
        # Load details
        self.q_text_edit.setText(q["question_text"])
        self.exp_text_edit.setText(q["explanation"] or "")
        
        # Question Type combo index mapping
        type_mapping = {"single": 0, "multiple": 1, "tf": 2, "fill": 3}
        self.type_combo.setCurrentIndex(type_mapping.get(q["question_type"], 0))
        
        # Load choices
        self._clear_choices()
        self._load_choices_rows(q)

    def _load_choices_rows(self, q):
        q_type = q["question_type"]
        if q_type == "fill":
            # For fill, correct answer is stored as choice
            for idx, c in enumerate(q["choices"]):
                self._add_choice_row(c[1], True, c[0])
        elif q_type == "tf":
            # True/False choices
            for idx, c in enumerate(q["choices"]):
                self._add_choice_row(c[1], bool(c[2]), c[0])
            self.add_choice_btn.setEnabled(False)  # Lock choice insertion
        else:
            # MC or MR
            for c in q["choices"]:
                self._add_choice_row(c[1], bool(c[2]), c[0])
            self.add_choice_btn.setEnabled(True)

    def _on_type_changed(self, index):
        if not self.selected_question:
            return
        
        # A change in type updates the buttons and rules
        q_type = ["single", "multiple", "tf", "fill"][index]
        self._clear_choices()
        
        if q_type == "tf":
            self.add_choice_btn.setEnabled(False)
            self._add_choice_row("True", True, "A")
            self._add_choice_row("False", False, "B")
        elif q_type == "fill":
            self.add_choice_btn.setEnabled(True)
            self._add_choice_row("", True, "A")
        else:
            self.add_choice_btn.setEnabled(True)
            self._add_choice_row("", False, "A")
            self._add_choice_row("", False, "B")

    def _add_choice_row(self, text="", is_correct=False, letter=None):
        row = QFrame(self.choices_container)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        
        # Determine Letter
        if not letter:
            idx = len(self.choice_widgets)
            letter = chr(ord('A') + idx)
            
        letter_lbl = QLabel(f"<b>{letter}</b>", row)
        letter_lbl.setFixedWidth(20)
        row_layout.addWidget(letter_lbl)
        
        # Correct indicator
        correct_chk = QCheckBox("Correct", row)
        correct_chk.setChecked(is_correct)
        row_layout.addWidget(correct_chk)
        
        # Choice Edit Line
        edit = QLineEdit(row)
        edit.setText(text)
        row_layout.addWidget(edit)
        
        # Remove button
        remove_btn = QPushButton("Remove", row)
        remove_btn.clicked.connect(lambda: self._remove_choice_row(row))
        # Lock remove if TF
        if self.type_combo.currentIndex() == 2:
            remove_btn.setEnabled(False)
        row_layout.addWidget(remove_btn)
        
        # Reference mapping
        row.letter = letter
        row.correct_chk = correct_chk
        row.edit = edit
        
        self.choices_box_layout.addWidget(row)
        self.choice_widgets.append(row)

    def _remove_choice_row(self, row_widget):
        if row_widget in self.choice_widgets:
            self.choice_widgets.remove(row_widget)
            row_widget.setParent(None)
            row_widget.deleteLater()
            
            # Recalculate letters
            for idx, r in enumerate(self.choice_widgets):
                r.letter = chr(ord('A') + idx)
                for w in r.children():
                    if isinstance(w, QLabel) and w.text().startswith("<b>"):
                        w.setText(f"<b>{r.letter}</b>")

    def _save_question(self):
        if not self.selected_question:
            return
            
        q_id = self.selected_question["id"]
        q_text = self.q_text_edit.toPlainText().strip()
        explanation = self.exp_text_edit.toPlainText().strip()
        
        # Get selected type
        q_type = ["single", "multiple", "tf", "fill"][self.type_combo.currentIndex()]
        
        if not q_text:
            QMessageBox.warning(self, "Validation Error", "Question text cannot be empty.")
            return
            
        choices_list = []
        for idx, row in enumerate(self.choice_widgets):
            choice_text = row.edit.text().strip()
            is_correct = 1 if row.correct_chk.isChecked() else 0
            
            if q_type != "fill" and not choice_text:
                QMessageBox.warning(self, "Validation Error", f"Choice {row.letter} text cannot be empty.")
                return
                
            choices_list.append((row.letter, choice_text, is_correct))
            
        # Extra Validation
        correct_count = sum(c[2] for c in choices_list)
        if q_type == "single" and correct_count != 1:
            QMessageBox.warning(self, "Validation Error", "Single choice question must have exactly 1 correct option.")
            return
        elif q_type == "multiple" and correct_count < 1:
            QMessageBox.warning(self, "Validation Error", "Multiple response question must have at least 1 correct option.")
            return
        elif q_type == "tf" and correct_count != 1:
            QMessageBox.warning(self, "Validation Error", "True/False question must have exactly 1 correct answer.")
            return
        elif q_type == "fill" and len(choices_list) == 0:
            QMessageBox.warning(self, "Validation Error", "Fill-in-the-blank question must specify at least 1 correct answer value.")
            return
            
        # Update Database
        self.db.update_question(q_id, q_text, q_type, explanation)
        self.db.update_choices(q_id, choices_list)
        
        QMessageBox.information(self, "Saved", "Question changes successfully saved to local SQLite cache.")
        
        # Reload questions list to reflect changes (and clear warnings)
        current_row = self.q_list.currentRow()
        self.load_questions()
        self.q_list.setCurrentRow(current_row)
