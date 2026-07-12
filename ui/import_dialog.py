from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFileDialog, QSpinBox, 
                             QFormLayout, QProgressBar, QMessageBox, QGroupBox,
                             QCheckBox)
from PySide6.QtCore import Qt
from parser_worker import ParserWorker
import os

class ImportDialog(QDialog):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.main_window = parent_window
        self.setWindowTitle("Import Exam from PDF")
        self.setMinimumWidth(550)
        self.resize(550, 450)
        
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title_lbl = QLabel("Import PDF Document", self)
        title_lbl.setObjectName("title")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_lbl)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # File selector
        file_row = QHBoxLayout()
        self.file_path_edit = QLineEdit(self)
        self.file_path_edit.setPlaceholderText("Select local PDF file...")
        self.file_path_edit.textChanged.connect(self._on_file_changed)
        file_row.addWidget(self.file_path_edit)
        
        browse_btn = QPushButton("Browse...", self)
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)
        form_layout.addRow("PDF File:", file_row)
        
        # Exam Name
        self.exam_name_edit = QLineEdit(self)
        self.exam_name_edit.setPlaceholderText("e.g. AWS Certified Solutions Architect")
        form_layout.addRow("Exam Name:", self.exam_name_edit)
        
        # Passing score
        self.passing_score_spin = QSpinBox(self)
        self.passing_score_spin.setRange(1, 100)
        self.passing_score_spin.setValue(70)
        form_layout.addRow("Passing Score (%):", self.passing_score_spin)
        
        # Time limit
        self.time_limit_spin = QSpinBox(self)
        self.time_limit_spin.setRange(1, 1440)
        self.time_limit_spin.setValue(120)
        form_layout.addRow("Time Limit (mins):", self.time_limit_spin)
        
        # OCR Checkbox
        self.ocr_checkbox = QCheckBox("Enable OCR for scanned pages (requires Tesseract)", self)
        self.ocr_checkbox.setChecked(bool(self.main_window.tesseract_path))
        self.ocr_checkbox.stateChanged.connect(self._on_ocr_changed)
        form_layout.addRow("", self.ocr_checkbox)
        
        layout.addLayout(form_layout)
        
        # Advanced extraction settings
        self.advanced_box = QGroupBox("Advanced Extraction Patterns (Regex)", self)
        self.advanced_box.setCheckable(True)
        self.advanced_box.setChecked(False)
        
        adv_layout = QFormLayout(self.advanced_box)
        self.q_pattern_edit = QLineEdit(r"(?i)^\s*(?:Question|Q|No\.?)\s*(\d+)[:.]?\s*|^\s*(\d+)\.\s+(?=[A-Za-z])")
        adv_layout.addRow("Question Trigger:", self.q_pattern_edit)
        
        self.c_pattern_edit = QLineEdit(r"^\s*([A-F])[\.\)]\s+(.*)")
        adv_layout.addRow("Choice Trigger:", self.c_pattern_edit)
        
        self.a_pattern_edit = QLineEdit(r"(?i)(?:correct\s+)?answer\s*:\s*([A-F\s,]+)")
        adv_layout.addRow("Answer Trigger:", self.a_pattern_edit)
        
        self.e_pattern_edit = QLineEdit(r"(?i)(?:explanation|exp)\s*:\s*(.*)")
        adv_layout.addRow("Explanation Trigger:", self.e_pattern_edit)
        
        layout.addWidget(self.advanced_box)
        
        # Progress section (hidden initially)
        self.progress_lbl = QLabel("", self)
        self.progress_lbl.hide()
        layout.addWidget(self.progress_lbl)
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        
        # Action Buttons
        self.actions_row = QHBoxLayout()
        self.actions_row.addStretch()
        
        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.clicked.connect(self.reject)
        self.actions_row.addWidget(self.cancel_btn)
        
        self.import_btn = QPushButton("Start Import", self)
        self.import_btn.setObjectName("primary_btn")
        self.import_btn.clicked.connect(self._start_import)
        self.actions_row.addWidget(self.import_btn)
        
        layout.addLayout(self.actions_row)

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF Exam", "", "PDF Files (*.pdf)")
        if file_path:
            self.file_path_edit.setText(file_path)

    def _on_file_changed(self, text):
        if text:
            # Autofill exam name from filename
            filename = os.path.splitext(os.path.basename(text))[0]
            # Replace underscores/dashes with spaces and capitalize
            clean_name = filename.replace("_", " ").replace("-", " ").title()
            self.exam_name_edit.setText(clean_name)

    def _on_ocr_changed(self, state):
        if state == Qt.Checked and not self.main_window.tesseract_path:
            QMessageBox.information(
                self, "OCR Required Settings", 
                "OCR is enabled but no Tesseract path is configured.\nPlease configure it in the main window settings menu, or ensure Tesseract is on your PATH."
            )

    def _start_import(self):
        filepath = self.file_path_edit.text().strip()
        exam_name = self.exam_name_edit.text().strip()
        
        if not filepath or not os.path.exists(filepath):
            QMessageBox.warning(self, "Invalid File", "Please select a valid, existing PDF file.")
            return
        if not exam_name:
            QMessageBox.warning(self, "Invalid Exam Name", "Please enter a name for the exam.")
            return

        # Prepare parameters
        custom_rules = None
        if self.advanced_box.isChecked():
            custom_rules = {
                "question_pattern": self.q_pattern_edit.text(),
                "choice_pattern": self.c_pattern_edit.text(),
                "answer_pattern": self.a_pattern_edit.text(),
                "explanation_pattern": self.e_pattern_edit.text()
            }

        tesseract = self.main_window.tesseract_path if self.ocr_checkbox.isChecked() else None

        # Lock UI
        self.file_path_edit.setEnabled(False)
        self.exam_name_edit.setEnabled(False)
        self.passing_score_spin.setEnabled(False)
        self.time_limit_spin.setEnabled(False)
        self.ocr_checkbox.setEnabled(False)
        self.advanced_box.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        
        # Show progress
        self.progress_lbl.setText("Initializing parser...")
        self.progress_lbl.show()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # Create Worker
        self.worker = ParserWorker(
            filepath=filepath,
            exam_name=exam_name,
            passing_score=self.passing_score_spin.value(),
            time_limit=self.time_limit_spin.value(),
            tesseract_path=tesseract,
            custom_rules=custom_rules
        )
        
        # Connect Signals
        self.worker.progress_updated.connect(self._on_parser_progress)
        self.worker.question_saved.connect(self._on_db_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        
        # Run
        self.worker.start()

    def _on_parser_progress(self, current, total):
        pct = int((current / total) * 100)
        self.progress_bar.setValue(pct)
        self.progress_lbl.setText(f"Scanning PDF Pages: {current} / {total} ({pct}%)")

    def _on_db_progress(self, current, total):
        pct = int((current / total) * 100)
        self.progress_bar.setValue(pct)
        self.progress_lbl.setText(f"Indexing questions to cache: {current} / {total} ({pct}%)")

    def _on_finished(self, exam_id, total):
        QMessageBox.information(self, "Success", f"Successfully imported exam pool with {total} questions!")
        self.accept()

    def _on_failed(self, error):
        QMessageBox.critical(self, "Import Error", f"An error occurred during extraction:\n\n{error}")
        self.reject()
