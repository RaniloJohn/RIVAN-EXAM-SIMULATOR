from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QScrollArea, QGridLayout, 
                             QMessageBox, QDialog, QFormLayout, QSpinBox)
from PySide6.QtCore import Qt, QSize
import os

class DashboardView(QWidget):
    def __init__(self, parent_window):
        super().__init__(parent_window)
        self.main_window = parent_window
        self.db = parent_window.db
        
        self._init_ui()
        self.load_data()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        
        # Title Banner
        banner = QHBoxLayout()
        title_box = QVBoxLayout()
        self.title_lbl = QLabel("Welcome to Rivan Exam Simulator", self)
        self.title_lbl.setObjectName("title")
        self.title_lbl.setStyleSheet("font-size: 24px; font-weight: 800;")
        title_box.addWidget(self.title_lbl)
        
        self.subtitle_lbl = QLabel("Prepare for your certifications offline using your local PDF assets.", self)
        self.subtitle_lbl.setObjectName("subtitle")
        title_box.addWidget(self.subtitle_lbl)
        banner.addLayout(title_box)
        
        # Quick Import Button on Banner
        self.quick_import_btn = QPushButton("➕ Import New PDF", self)
        self.quick_import_btn.setObjectName("primary_btn")
        self.quick_import_btn.clicked.connect(self.main_window.open_import_dialog)
        banner.addWidget(self.quick_import_btn)
        layout.addLayout(banner)
        
        # Main Dashboard Sections (Split Left/Right)
        sections = QHBoxLayout()
        sections.setSpacing(25)
        
        # Left Panel - Exams List
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        exams_label = QLabel("Your Question Pools / Exams", self)
        exams_label.setStyleSheet("font-size: 16px; font-weight: 700;")
        left_layout.addWidget(exams_label)
        
        # Scroll area for exams
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.exams_list_layout = QVBoxLayout(self.scroll_widget)
        self.exams_list_layout.setContentsMargins(0, 0, 0, 0)
        self.exams_list_layout.setSpacing(15)
        self.exams_list_layout.addStretch()
        self.scroll_area.setWidget(self.scroll_widget)
        left_layout.addWidget(self.scroll_area)
        
        sections.addLayout(left_layout, stretch=2)
        
        # Right Panel - Recent Stats & Resume
        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)
        
        stats_label = QLabel("Recent Activity & Progress", self)
        stats_label.setStyleSheet("font-size: 16px; font-weight: 700;")
        right_layout.addWidget(stats_label)
        
        # Stats container
        self.stats_frame = QFrame(self)
        self.stats_frame.setObjectName("card")
        self.stats_layout = QVBoxLayout(self.stats_frame)
        self.stats_layout.setContentsMargins(20, 20, 20, 20)
        self.stats_layout.setSpacing(15)
        
        self.no_stats_lbl = QLabel("No exam attempts recorded yet.", self.stats_frame)
        self.no_stats_lbl.setStyleSheet("color: #94a3b8; font-style: italic;")
        self.stats_layout.addWidget(self.no_stats_lbl)
        
        right_layout.addWidget(self.stats_frame)
        right_layout.addStretch()
        
        sections.addLayout(right_layout, stretch=1)
        layout.addLayout(sections)

    def load_data(self):
        # 1. Load Exams
        # Clear previous widgets
        for i in reversed(range(self.exams_list_layout.count())):
            widget = self.exams_list_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        exams = self.db.get_exams()
        
        if not exams:
            no_exams_card = QFrame()
            no_exams_card.setObjectName("card")
            no_exams_layout = QVBoxLayout(no_exams_card)
            no_exams_layout.setContentsMargins(30, 40, 30, 40)
            no_exams_layout.setAlignment(Qt.AlignCenter)
            
            msg = QLabel("No exams imported yet.\nImport a PDF file to begin generating your practice exam.", no_exams_card)
            msg.setAlignment(Qt.AlignCenter)
            msg.setStyleSheet("font-size: 14px; color: #94a3b8; line-height: 1.5;")
            no_exams_layout.addWidget(msg)
            
            import_btn = QPushButton("Import PDF File", no_exams_card)
            import_btn.setObjectName("primary_btn")
            import_btn.clicked.connect(self.main_window.open_import_dialog)
            no_exams_layout.addWidget(import_btn, alignment=Qt.AlignCenter)
            
            self.exams_list_layout.insertWidget(0, no_exams_card)
        else:
            for exam in exams:
                card = self._create_exam_card(exam)
                self.exams_list_layout.insertWidget(self.exams_list_layout.count() - 1, card)

        # 2. Load Stats
        recent_sessions = self.db.get_recent_sessions(limit=5)
        if recent_sessions:
            self.no_stats_lbl.setParent(None)
            self.no_stats_lbl.deleteLater()
            
            # Clear stats frame layout
            for i in reversed(range(self.stats_layout.count())):
                item = self.stats_layout.itemAt(i)
                if item.widget():
                    item.widget().setParent(None)
            
            for session in recent_sessions:
                sess_card = QFrame()
                sess_card.setStyleSheet("border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 5px;")
                sess_layout = QVBoxLayout(sess_card)
                sess_layout.setContentsMargins(0, 0, 0, 0)
                
                name_lbl = QLabel(f"<b>{session['exam_name']}</b>")
                sess_layout.addWidget(name_lbl)
                
                mode_str = "Study Mode" if session["is_study_mode"] else "Exam Mode"
                date_str = session["started_at"][:16].replace("T", " ")
                
                if session["is_completed"]:
                    score = self.db.calculate_score(session["id"])
                    pass_str = "<font color='#10b981'>Passed</font>" if score["passed"] else "<font color='#ef4444'>Failed</font>"
                    info_lbl = QLabel(f"{mode_str} • {date_str}<br>Score: {score['percentage']}% ({score['correct']}/{score['total']}) • {pass_str}")
                    sess_layout.addWidget(info_lbl)
                    
                    review_btn = QPushButton("Review Results")
                    review_btn.clicked.connect(lambda _, s_id=session["id"]: self.main_window.load_results_view(s_id))
                    sess_layout.addWidget(review_btn)
                else:
                    info_lbl = QLabel(f"<font color='#f59e0b'>In Progress</font> • {mode_str} • {date_str}")
                    sess_layout.addWidget(info_lbl)
                    
                    resume_btn = QPushButton("Resume Attempt")
                    resume_btn.setObjectName("primary_btn")
                    resume_btn.clicked.connect(lambda _, e_id=session["exam_id"], s_id=session["id"], study=session["is_study_mode"]: 
                                              self.main_window.load_exam_simulator(e_id, study, s_id))
                    sess_layout.addWidget(resume_btn)
                
                self.stats_layout.addWidget(sess_card)

    def _create_exam_card(self, exam):
        card = QFrame()
        card.setObjectName("card")
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)
        
        # Meta Row
        meta_layout = QHBoxLayout()
        exam_title = QLabel(exam["name"])
        exam_title.setStyleSheet("font-size: 16px; font-weight: 700;")
        meta_layout.addWidget(exam_title)
        
        meta_layout.addStretch()
        
        q_count = exam["question_count"]
        questions_lbl = QLabel(f"📄 {q_count} Questions")
        questions_lbl.setStyleSheet("color: #38bdf8; font-weight: 600;")
        meta_layout.addWidget(questions_lbl)
        card_layout.addLayout(meta_layout)
        
        # Detail line
        detail_lbl = QLabel(f"Passing Score: {exam['passing_score']}%  •  Time Limit: {exam['time_limit']} minutes")
        detail_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
        card_layout.addWidget(detail_lbl)
        
        # Action Buttons Row
        actions = QHBoxLayout()
        
        # Check if there is an active session
        active_session = self.db.get_active_session(exam["id"])
        
        if active_session:
            resume_btn = QPushButton("Resume Exam")
            resume_btn.setObjectName("primary_btn")
            resume_btn.clicked.connect(lambda _, e_id=exam["id"], s_id=active_session["id"], study=active_session["is_study_mode"]: 
                                      self.main_window.load_exam_simulator(e_id, study, s_id))
            actions.addWidget(resume_btn)
            
            # Allow restarting too
            restart_btn = QPushButton("New Attempt")
            restart_btn.clicked.connect(lambda _, e_id=exam["id"]: self._show_start_options(e_id))
            actions.addWidget(restart_btn)
        else:
            start_btn = QPushButton("🚀 Start Practice")
            start_btn.setObjectName("primary_btn")
            start_btn.clicked.connect(lambda _, e_id=exam["id"]: self._show_start_options(e_id))
            actions.addWidget(start_btn)
            
        edit_btn = QPushButton("📝 Edit Questions")
        edit_btn.clicked.connect(lambda _, e_id=exam["id"]: self._open_question_editor(e_id))
        actions.addWidget(edit_btn)
        
        settings_btn = QPushButton("⚙️ Settings")
        settings_btn.clicked.connect(lambda _, ex=exam: self._open_exam_settings(ex))
        actions.addWidget(settings_btn)
        
        actions.addStretch()
        
        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setStyleSheet("color: #ef4444; border: 1px solid #ef4444;")
        delete_btn.clicked.connect(lambda _, e_id=exam["id"]: self._delete_exam(e_id))
        actions.addWidget(delete_btn)
        
        card_layout.addLayout(actions)
        return card

    def _show_start_options(self, exam_id):
        dialog = QDialog(self)
        dialog.setWindowTitle("Select Mode")
        dialog.setMinimumWidth(400)
        
        # Fetch question count
        questions = self.db.get_questions(exam_id)
        total_q = len(questions)
        
        if total_q == 0:
            QMessageBox.warning(self, "No Questions", "This exam pool has no questions. Please edit or re-import.")
            return

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("Choose Practice Mode", dialog)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        desc = QLabel("<b>Exam Mode</b> simulates the actual test experience (timer, hide answers until submission).\n\n<b>Study Mode</b> offers immediate feedback and detailed correct answer explanations.", dialog)
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        # Shuffling Checkboxes
        from PySide6.QtWidgets import QCheckBox, QRadioButton, QSpinBox, QGroupBox, QFormLayout
        
        shuffling_box = QGroupBox("Shuffling Options", dialog)
        shuffling_layout = QVBoxLayout(shuffling_box)
        shuffle_q_chk = QCheckBox("Randomize question order", shuffling_box)
        shuffle_q_chk.setChecked(True)
        shuffling_layout.addWidget(shuffle_q_chk)
        
        shuffle_c_chk = QCheckBox("Randomize choice/answer options order", shuffling_box)
        shuffle_c_chk.setChecked(True)
        shuffling_layout.addWidget(shuffle_c_chk)
        layout.addWidget(shuffling_box)
        
        # Subset Selection Group
        subset_box = QGroupBox("Question Range & Count", dialog)
        subset_layout = QVBoxLayout(subset_box)
        
        all_radio = QRadioButton(f"All Questions (1 to {total_q})", subset_box)
        all_radio.setChecked(True)
        subset_layout.addWidget(all_radio)
        
        # Range option
        range_radio = QRadioButton("Practice specific range:", subset_box)
        subset_layout.addWidget(range_radio)
        
        range_inputs = QHBoxLayout()
        range_inputs.addWidget(QLabel("From:"))
        from_spin = QSpinBox(subset_box)
        from_spin.setRange(1, total_q)
        from_spin.setValue(1)
        range_inputs.addWidget(from_spin)
        
        range_inputs.addWidget(QLabel("To:"))
        to_spin = QSpinBox(subset_box)
        to_spin.setRange(1, total_q)
        to_spin.setValue(min(total_q, 100))
        range_inputs.addWidget(to_spin)
        subset_layout.addLayout(range_inputs)
        
        # Random count option
        random_radio = QRadioButton("Select random subset of questions:", subset_box)
        subset_layout.addWidget(random_radio)
        
        count_inputs = QHBoxLayout()
        count_inputs.addWidget(QLabel("Number of Questions:"))
        count_spin = QSpinBox(subset_box)
        count_spin.setRange(1, total_q)
        count_spin.setValue(min(total_q, 50))
        count_inputs.addWidget(count_spin)
        subset_layout.addLayout(count_inputs)
        
        layout.addWidget(subset_box)
        
        # Control enable/disable of spinboxes based on radio state
        def update_subset_ui():
            from_spin.setEnabled(range_radio.isChecked())
            to_spin.setEnabled(range_radio.isChecked())
            count_spin.setEnabled(random_radio.isChecked())
            
        all_radio.toggled.connect(update_subset_ui)
        range_radio.toggled.connect(update_subset_ui)
        random_radio.toggled.connect(update_subset_ui)
        update_subset_ui()
        
        buttons = QHBoxLayout()
        exam_btn = QPushButton("Exam Mode", dialog)
        
        def start_exam(is_study):
            # Parse parameters
            subset_type = "all"
            if range_radio.isChecked():
                subset_type = "range"
            elif random_radio.isChecked():
                subset_type = "random"
                
            dialog.accept()
            self.main_window.load_exam_simulator(
                exam_id=exam_id, 
                is_study_mode=is_study, 
                shuffle_questions=shuffle_q_chk.isChecked(),
                shuffle_choices=shuffle_c_chk.isChecked(),
                subset_type=subset_type,
                range_from=from_spin.value(),
                range_to=to_spin.value(),
                random_count=count_spin.value()
            )
            
        exam_btn.clicked.connect(lambda: start_exam(False))
        buttons.addWidget(exam_btn)
        
        study_btn = QPushButton("Study Mode", dialog)
        study_btn.setObjectName("primary_btn")
        study_btn.clicked.connect(lambda: start_exam(True))
        buttons.addWidget(study_btn)
        
        layout.addLayout(buttons)
        dialog.exec()
        
        layout.addLayout(buttons)
        dialog.exec()

    def _open_question_editor(self, exam_id):
        from ui.question_editor import QuestionEditorView
        editor = QuestionEditorView(self.main_window, exam_id)
        self.main_window.stack.addWidget(editor)
        self.main_window.stack.setCurrentWidget(editor)

    def _open_exam_settings(self, exam):
        dialog = QDialog(self)
        dialog.setWindowTitle("Exam Settings")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        form = QFormLayout()
        
        pass_spin = QSpinBox(dialog)
        pass_spin.setRange(1, 100)
        pass_spin.setValue(exam["passing_score"])
        form.addRow("Passing Score (%):", pass_spin)
        
        time_spin = QSpinBox(dialog)
        time_spin.setRange(1, 1440)
        time_spin.setValue(exam["time_limit"])
        form.addRow("Time Limit (minutes):", time_spin)
        
        layout.addLayout(form)
        
        save_btn = QPushButton("Save Settings", dialog)
        save_btn.setObjectName("primary_btn")
        save_btn.clicked.connect(lambda: [
            self.db.update_exam_settings(exam["id"], pass_spin.value(), time_spin.value()),
            dialog.accept(),
            self.load_data()
        ])
        layout.addWidget(save_btn)
        dialog.exec()

    def _delete_exam(self, exam_id):
        reply = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to permanently delete this exam pool, including all questions, images, and history?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_exam(exam_id)
            self.load_data()
