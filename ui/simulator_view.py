from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QSplitter, QListWidget, QListWidgetItem,
                             QTextBrowser, QRadioButton, QCheckBox, QLineEdit, 
                             QButtonGroup, QMessageBox, QComboBox, QProgressBar, QSpinBox)
from PySide6.QtCore import Qt, QTimer, QMimeData
from PySide6.QtGui import QDrag, QPixmap
from styles import Styles
import random
import os

class DragToken(QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            background-color: #0ea5e9;
            color: white;
            border-radius: 6px;
            padding: 8px;
            font-weight: bold;
            border: 1px solid #0284c7;
        """)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.OpenHandCursor)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(self.text())
            drag.setMimeData(mime)
            
            # Draw shadow pixmap
            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.position().toPoint())
            
            drag.exec(Qt.MoveAction)

class DropSlot(QFrame):
    def __init__(self, label_text, on_changed_callback, parent=None):
        super().__init__(parent)
        self.on_changed_callback = on_changed_callback
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #334155;
                border-radius: 8px;
                min-height: 45px;
                background-color: #1e293b;
            }
        """)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(8, 6, 8, 6)
        
        self.label = QLabel(label_text, self)
        self.label.setStyleSheet("color: #94a3b8; font-weight: bold;")
        self.layout.addWidget(self.label)
        
        self.content_label = None
        
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    border: 2px dashed #0ea5e9;
                    border-radius: 8px;
                    min-height: 45px;
                    background-color: #1e293b;
                }
            """)
            
    def dragLeaveEvent(self, event):
        self.update_appearance()
        
    def dropEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()
            text = event.mimeData().text()
            self.set_token(text)
            self.on_changed_callback()
            
    def set_token(self, text):
        if self.content_label:
            self.content_label.setParent(None)
            self.content_label.deleteLater()
            
        if text:
            self.content_label = QLabel(text, self)
            self.content_label.setStyleSheet("""
                background-color: #0ea5e9;
                color: white;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
            """)
            self.layout.addWidget(self.content_label)
        else:
            self.content_label = None
        self.update_appearance()
        
    def update_appearance(self):
        if self.content_label:
            self.setStyleSheet("""
                QFrame {
                    border: 2px solid #0ea5e9;
                    border-radius: 8px;
                    min-height: 45px;
                    background-color: #0ea5e911;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 2px dashed #334155;
                    border-radius: 8px;
                    min-height: 45px;
                    background-color: #1e293b;
                }
            """)
            
    def get_token(self):
        return self.content_label.text() if self.content_label else ""

class DragDropContainer(QWidget):
    def __init__(self, on_changed_callback, parent=None):
        super().__init__(parent)
        self.on_changed_callback = on_changed_callback
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Configuration Row
        config_row = QHBoxLayout()
        config_row.addWidget(QLabel("Drag Items:"))
        self.items_spin = QSpinBox(self)
        self.items_spin.setRange(1, 10)
        self.items_spin.setValue(5)
        self.items_spin.valueChanged.connect(self.rebuild_ui)
        config_row.addWidget(self.items_spin)
        
        config_row.addWidget(QLabel("Drop Slots:"))
        self.slots_spin = QSpinBox(self)
        self.slots_spin.setRange(1, 10)
        self.slots_spin.setValue(5)
        self.slots_spin.valueChanged.connect(self.rebuild_ui)
        config_row.addWidget(self.slots_spin)
        
        # Reset / Clear Button
        self.clear_btn = QPushButton("Clear Drops", self)
        self.clear_btn.clicked.connect(self.clear_drops)
        config_row.addWidget(self.clear_btn)
        
        main_layout.addLayout(config_row)
        
        # Splitter for Left (Drag Items) and Right (Drop Slots)
        content_layout = QHBoxLayout()
        
        # Left Panel (Drag source list)
        left_box = QFrame(self)
        left_box.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px;")
        self.left_layout = QVBoxLayout(left_box)
        self.left_layout.addWidget(QLabel("Drag Tokens:", left_box))
        
        # Right Panel (Drop targets list)
        right_box = QFrame(self)
        right_box.setStyleSheet("background-color: #1e293b; border: 1px solid #334155; border-radius: 8px;")
        self.right_layout = QVBoxLayout(right_box)
        self.right_layout.addWidget(QLabel("Drop Targets:", right_box))
        
        content_layout.addWidget(left_box, 1)
        content_layout.addWidget(right_box, 2)
        main_layout.addLayout(content_layout)
        
        self.slots = []
        self.rebuild_ui()
        
    def rebuild_ui(self):
        # Clean layouts
        for i in reversed(range(self.left_layout.count())):
            w = self.left_layout.itemAt(i).widget()
            if w and not isinstance(w, QLabel):
                w.setParent(None)
                w.deleteLater()
                
        for i in reversed(range(self.right_layout.count())):
            w = self.right_layout.itemAt(i).widget()
            if w and not isinstance(w, QLabel):
                w.setParent(None)
                w.deleteLater()
                
        # Build Left Items
        num_items = self.items_spin.value()
        for idx in range(num_items):
            token = DragToken(f"Item {idx+1}", self)
            self.left_layout.addWidget(token)
            
        # Build Right Slots
        num_slots = self.slots_spin.value()
        self.slots = []
        for idx in range(num_slots):
            letter = chr(ord('A') + idx)
            slot = DropSlot(f"Slot {letter}", self.on_changed_callback, self)
            self.right_layout.addWidget(slot)
            self.slots.append(slot)
            
    def clear_drops(self):
        for slot in self.slots:
            slot.set_token("")
        self.on_changed_callback()
        
    def get_state_string(self):
        num_items = self.items_spin.value()
        num_slots = self.slots_spin.value()
        slot_parts = []
        for idx, slot in enumerate(self.slots):
            letter = chr(ord('A') + idx)
            token = slot.get_token()
            slot_parts.append(f"{letter}:{token}")
        return f"{num_items},{num_slots}|" + ";".join(slot_parts)
        
    def set_state_string(self, state_str):
        if not state_str or "|" not in state_str:
            self.clear_drops()
            return
            
        try:
            config, mapping = state_str.split("|", 1)
            num_items, num_slots = map(int, config.split(","))
            
            # Temporarily block signals
            self.items_spin.blockSignals(True)
            self.slots_spin.blockSignals(True)
            self.items_spin.setValue(num_items)
            self.slots_spin.setValue(num_slots)
            self.items_spin.blockSignals(False)
            self.slots_spin.blockSignals(False)
            
            self.rebuild_ui()
            
            mappings = {}
            for part in mapping.split(";"):
                if ":" in part:
                    letter, token = part.split(":", 1)
                    mappings[letter] = token
                    
            for idx, slot in enumerate(self.slots):
                letter = chr(ord('A') + idx)
                if letter in mappings:
                    slot.set_token(mappings[letter])
        except Exception as e:
            print("Error restoring drag drop state:", e)

class SimulatorView(QWidget):
    def __init__(self, parent_window, exam_id, is_study_mode=False, resume_session_id=None,
                 shuffle_questions=False, shuffle_choices=False,
                 subset_type="all", range_from=1, range_to=100, random_count=50):
        super().__init__(parent_window)
        self.main_window = parent_window
        self.db = parent_window.db
        self.exam_id = exam_id
        self.is_study_mode = is_study_mode
        self.session_id = resume_session_id
        
        self.shuffle_questions = shuffle_questions
        self.shuffle_choices = shuffle_choices
        self.subset_type = subset_type
        self.range_from = range_from
        self.range_to = range_to
        self.random_count = random_count
        
        # Load Exam
        self.exam = self.db.get_exam(self.exam_id)
        
        # State Variables
        self.questions = []
        self.current_index = 0
        self.responses = {}          # maps q_id -> {'selected': str, 'flagged': bool}
        self.font_size = 14          # Default font size for zoom
        self.time_remaining = 0      # Seconds remaining
        self.time_spent = 0          # Seconds spent
        self.is_submitted = {}       # maps q_id -> bool (Study Mode immediate submit status)
        
        self._init_ui()
        self._setup_session()
        self._setup_timer()
        self.load_question(0)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # --- Top Bar ---
        top_bar = QHBoxLayout()
        self.title_lbl = QLabel(f"{self.exam['name']} - {'Study Mode' if self.is_study_mode else 'Exam Mode'}", self)
        self.title_lbl.setStyleSheet("font-size: 16px; font-weight: bold;")
        top_bar.addWidget(self.title_lbl)
        
        top_bar.addStretch()
        
        # Timer Label
        self.timer_lbl = QLabel("Time: 00:00:00", self)
        self.timer_lbl.setObjectName("timer_lbl")
        self.timer_lbl.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px 15px; border-radius: 6px; background-color: #1e293b;")
        top_bar.addWidget(self.timer_lbl)
        
        # Zoom Controls
        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(2)
        zoom_lbl = QLabel("Zoom:")
        zoom_layout.addWidget(zoom_lbl)
        
        zoom_out_btn = QPushButton("-", self)
        zoom_out_btn.setFixedSize(30, 30)
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(zoom_out_btn)
        
        zoom_in_btn = QPushButton("+", self)
        zoom_in_btn.setFixedSize(30, 30)
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(zoom_in_btn)
        top_bar.addLayout(zoom_layout)
        
        # Action Buttons
        self.end_btn = QPushButton("End Exam & Submit" if not self.is_study_mode else "Exit Session", self)
        self.end_btn.setObjectName("primary_btn")
        self.end_btn.clicked.connect(self.confirm_end_session)
        top_bar.addWidget(self.end_btn)
        
        layout.addLayout(top_bar)
        
        # --- Splitter (Left Sidebar / Right Display) ---
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.setStyleSheet("QSplitter::handle { background-color: #334155; }")
        
        # Left Panel (Question Nav)
        left_panel = QFrame(self.splitter)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.setSpacing(10)
        
        # Filtering dropdown for Study Mode
        if self.is_study_mode:
            left_layout.addWidget(QLabel("Filter Questions:", left_panel))
            self.filter_combo = QComboBox(left_panel)
            self.filter_combo.addItems(["All Questions", "Bookmarked Only", "Incorrect Only", "Unanswered Only"])
            self.filter_combo.currentIndexChanged.connect(self.apply_filter)
            left_layout.addWidget(self.filter_combo)
            
        left_layout.addWidget(QLabel("Questions List:", left_panel))
        self.q_list = QListWidget(left_panel)
        self.q_list.currentRowChanged.connect(self.load_question)
        left_layout.addWidget(self.q_list)
        
        # Progress Info
        self.progress_lbl = QLabel("Answered: 0 / 0", left_panel)
        left_layout.addWidget(self.progress_lbl)
        
        self.progress_bar = QProgressBar(left_panel)
        self.progress_bar.setRange(0, 100)
        left_layout.addWidget(self.progress_bar)
        
        self.splitter.addWidget(left_panel)
        
        # Right Panel (Main Content)
        right_panel = QFrame(self.splitter)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(15)
        
        # Question Metadata row (Flags / Bookmarks)
        meta_row = QHBoxLayout()
        self.q_num_lbl = QLabel("Question 1 of 1", right_panel)
        self.q_num_lbl.setStyleSheet("font-size: 15px; font-weight: 700;")
        meta_row.addWidget(self.q_num_lbl)
        
        meta_row.addStretch()
        
        # Bookmark button (Persistent)
        self.bookmark_btn = QPushButton("⭐ Bookmark", right_panel)
        self.bookmark_btn.setObjectName("bookmark_btn")
        self.bookmark_btn.clicked.connect(self.toggle_bookmark)
        meta_row.addWidget(self.bookmark_btn)
        
        # Flag button (Session specific)
        self.flag_btn = QPushButton("🚩 Flag for Review", right_panel)
        self.flag_btn.setObjectName("flag_btn")
        self.flag_btn.clicked.connect(self.toggle_flag)
        meta_row.addWidget(self.flag_btn)
        
        right_layout.addLayout(meta_row)
        
        # QTextBrowser for HTML display
        self.browser = QTextBrowser(right_panel)
        self.browser.setMinimumHeight(250)
        # Search path includes current working directory and project root to load local cached images
        import sys
        if getattr(sys, 'frozen', False):
            project_root = os.path.dirname(os.path.dirname(sys.executable))
        else:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.browser.setSearchPaths([os.getcwd(), project_root])
        self.browser.document().setDefaultStyleSheet(Styles.get_html_css(self.main_window.dark_mode))
        right_layout.addWidget(self.browser)
        
        # Answers Box
        self.answers_frame = QFrame(right_panel)
        self.answers_layout = QVBoxLayout(self.answers_frame)
        self.answers_layout.setContentsMargins(10, 10, 10, 10)
        self.answers_layout.setSpacing(10)
        right_layout.addWidget(self.answers_frame)
        
        # Actions Row (Prev / Submit / Next)
        nav_row = QHBoxLayout()
        self.prev_btn = QPushButton("◀ Previous", right_panel)
        self.prev_btn.clicked.connect(self.prev_question)
        nav_row.addWidget(self.prev_btn)
        
        nav_row.addStretch()
        
        self.study_submit_btn = QPushButton("Submit Answer", right_panel)
        self.study_submit_btn.setObjectName("primary_btn")
        self.study_submit_btn.clicked.connect(self.submit_study_answer)
        if not self.is_study_mode:
            self.study_submit_btn.hide()
        nav_row.addWidget(self.study_submit_btn)
        
        self.next_btn = QPushButton("Next ▶", right_panel)
        self.next_btn.clicked.connect(self.next_question)
        nav_row.addWidget(self.next_btn)
        
        right_layout.addLayout(nav_row)
        
        self.splitter.addWidget(right_panel)
        
        # Proportions
        self.splitter.setSizes([250, 750])
        layout.addWidget(self.splitter)
        
        # Keyboard Shortcuts
        self.setFocusPolicy(Qt.StrongFocus)

    # --- Session Setup ---
    def _setup_session(self):
        raw_questions = self.db.get_questions(self.exam_id)
        
        if self.session_id:
            # Resuming session
            session = self.db.get_session(self.session_id)
            self.is_study_mode = bool(session["is_study_mode"])
            self.time_spent = session["time_spent"]
            
            # Restore shuffled order if it exists
            order_str = session.get("question_order")
            if order_str:
                q_id_order = [int(x) for x in order_str.split(",") if x.strip()]
                # Reorder raw questions based on order
                q_dict = {q["id"]: q for q in raw_questions}
                self.questions = [q_dict[qid] for qid in q_id_order if qid in q_dict]
            else:
                self.questions = raw_questions
                
            self.responses = self.db.get_session_responses(self.session_id)
            
            # If resuming study mode, pre-mark already-answered questions as submitted
            if self.is_study_mode:
                for q_id, resp in self.responses.items():
                    if resp["selected"]:
                        self.is_submitted[q_id] = True
        else:
            # New Session
            self.questions = list(raw_questions)
            
            # Apply Subset selection (e.g. Range or Random counts)
            if self.subset_type == "range":
                start_idx = max(0, self.range_from - 1)
                end_idx = min(len(self.questions), self.range_to)
                if start_idx < end_idx:
                    self.questions = self.questions[start_idx:end_idx]
            elif self.subset_type == "random":
                count = min(len(self.questions), self.random_count)
                if count > 0:
                    self.questions = random.sample(self.questions, count)
                    if not self.shuffle_questions:
                        # Restore original relative order
                        self.questions.sort(key=lambda x: (x.get("question_num", 0), x.get("id", 0)))
            
            # Shuffle logic
            if self.shuffle_questions:
                random.shuffle(self.questions)
                
            # Shuffling choices in each question object if enabled
            if self.shuffle_choices:
                for q in self.questions:
                    # choices is list of dicts: [ {id, choice_letter, choice_text, is_correct}, ... ]
                    shuffled_choices = list(q["choices"])
                    random.shuffle(shuffled_choices)
                    # Rewrite choice_letter to maintain A, B, C order in UI display
                    letters = [chr(ord('A') + i) for i in range(len(shuffled_choices))]
                    updated_choices = []
                    for letter, c in zip(letters, shuffled_choices):
                        # Construct choices formatted as database rows for evaluate
                        updated_choices.append({
                            "id": c["id"],
                            "choice_letter": letter,
                            "choice_text": c["choice_text"],
                            "is_correct": c["is_correct"]
                        })
                    q["choices"] = updated_choices
            
            # Save session order
            order_str = ",".join(str(q["id"]) for q in self.questions)
            self.session_id = self.db.start_session(self.exam_id, int(self.is_study_mode), order_str)
            self.responses = {}

        # Set up Navigation List items
        self.refresh_sidebar_list()
        self.update_progress()

    def refresh_sidebar_list(self, filter_text=None):
        self.q_list.blockSignals(True)
        self.q_list.clear()
        
        filter_idx = self.filter_combo.currentIndex() if self.is_study_mode else 0
        
        filtered_index = 0
        self.filtered_questions = []
        
        for idx, q in enumerate(self.questions):
            q_id = q["id"]
            resp = self.responses.get(q_id, {"selected": None, "flagged": False})
            
            is_bookmarked = q["is_bookmarked"] or self.db.is_bookmarked(q_id)
            is_answered = bool(resp["selected"])
            
            # Filtering rules (Study mode only)
            if self.is_study_mode:
                if filter_idx == 1 and not is_bookmarked: # Bookmarked
                    continue
                if filter_idx == 2: # Incorrect (based on evaluation)
                    if not is_answered or self.db._evaluate_correctness(q, resp["selected"]):
                        continue
                if filter_idx == 3 and is_answered: # Unanswered
                    continue
            
            # Create list item
            label_text = f"Q{idx + 1}"
            if resp["flagged"]:
                label_text += " 🚩"
            if is_bookmarked:
                label_text += " ⭐"
            if is_answered:
                if self.is_study_mode:
                    is_correct = self.db._evaluate_correctness(q, resp["selected"])
                    label_text += " (✓)" if is_correct else " (✗)"
                else:
                    label_text += " (A)"
                    
            item = QListWidgetItem(label_text)
            item.setData(Qt.UserRole, idx) # Store index in real questions list
            self.q_list.addItem(item)
            
            self.filtered_questions.append(q)
            
        self.q_list.blockSignals(False)

    # --- Timer ---
    def _setup_timer(self):
        # Time remaining calculation
        if not self.is_study_mode:
            # Exam Mode is countdown
            total_seconds = self.exam["time_limit"] * 60
            self.time_remaining = max(0, total_seconds - self.time_spent)
        else:
            self.timer_lbl.setText("Study Mode")
            # In study mode, we track elapsed time instead of counting down
            self.time_remaining = 0
            
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._on_timer_tick)
        self.timer.start(1000)
        self.update_timer_label()

    def _on_timer_tick(self):
        self.time_spent += 1
        
        if not self.is_study_mode:
            if self.time_remaining > 0:
                self.time_remaining -= 1
                self.update_timer_label()
                if self.time_remaining == 0:
                    self.timer.stop()
                    QMessageBox.warning(self, "Time's Up", "The time limit has been reached! Your exam will be submitted automatically.")
                    self.end_session()
            else:
                self.timer.stop()
        else:
            self.update_timer_label()
            
        # Periodically save time spent (every 10 seconds)
        if self.time_spent % 10 == 0:
            self.db.update_session_time(self.session_id, self.time_spent)

    def update_timer_label(self):
        if self.is_study_mode:
            h = self.time_spent // 3600
            m = (self.time_spent % 3600) // 60
            s = self.time_spent % 60
            self.timer_lbl.setText(f"Elapsed: {h:02d}:{m:02d}:{s:02d}")
        else:
            h = self.time_remaining // 3600
            m = (self.time_remaining % 3600) // 60
            s = self.time_remaining % 60
            self.timer_lbl.setText(f"Time: {h:02d}:{m:02d}:{s:02d}")

    # --- Load Question ---
    def _clear_question_view(self):
        self.q_num_lbl.setText("No questions match the current filter.")
        self.browser.setHtml("")
        self._clear_choices_layout()
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        if self.is_study_mode:
            self.study_submit_btn.setEnabled(False)

    def load_question(self, list_index):
        if list_index < 0 or list_index >= self.q_list.count():
            return
            
        # Block signals to prevent infinite loop
        self.q_list.blockSignals(True)
        self.q_list.setCurrentRow(list_index)
        self.q_list.blockSignals(False)
        
        item = self.q_list.item(list_index)
        if not item:
            return
        abs_index = item.data(Qt.UserRole)
        self.load_question_by_abs_index(abs_index)

    def load_question_by_abs_index(self, abs_index):
        if abs_index < 0 or abs_index >= len(self.questions):
            return
            
        self.current_index = abs_index
        q = self.questions[abs_index]
        q_id = q["id"]
        
        # Update labels
        self.q_num_lbl.setText(f"Question {abs_index + 1} of {len(self.questions)} (No. {q['question_num']})")
        
        # Load Flags and Bookmarks
        resp = self.responses.get(q_id, {"selected": None, "flagged": False})
        self.bookmark_btn.setProperty("active", "true" if self.db.is_bookmarked(q_id) else "false")
        self.flag_btn.setProperty("active", "true" if resp["flagged"] else "false")
        self.bookmark_btn.setStyle(self.bookmark_btn.style())
        self.flag_btn.setStyle(self.flag_btn.style())

        # Load Text in QTextBrowser
        html_content = q["question_text"]
        
        # In Study mode, if submitted, append explanation
        if self.is_study_mode and self.is_submitted.get(q_id):
            is_correct = self.db._evaluate_correctness(q, resp["selected"])
            status_text = "<font color='#10b981'><b>✓ CORRECT</b></font>" if is_correct else f"<font color='#ef4444'><b>✗ INCORRECT</b></font>"
            correct_letters = ", ".join([c["choice_letter"] for c in q["choices"] if c["is_correct"]])
            
            exp_box = f"""
            <div class="explanation-box">
                <p>{status_text}</p>
                <p><b>Correct Answer:</b> {correct_letters}</p>
                <p><b>Explanation:</b> {q['explanation'] or 'No explanation available.'}</p>
            </div>
            """
            html_content += exp_box

        # Format HTML with body wrappers
        full_html = f"<html><body>{html_content}</body></html>"
        self.browser.setHtml(full_html)
        self.browser.setFont(self.browser.font()) # Reset font
        self.apply_zoom()

        # Clear answer inputs
        self._clear_choices_layout()
        
        # Load Choice selectors
        self._load_choices_input(q, resp["selected"])
        
        # Find list_index in q_list to update nav buttons
        list_index = -1
        for row in range(self.q_list.count()):
            item = self.q_list.item(row)
            if item and item.data(Qt.UserRole) == abs_index:
                list_index = row
                break
                
        # Update Nav Button state
        if list_index >= 0:
            self.prev_btn.setEnabled(list_index > 0)
            self.next_btn.setEnabled(list_index < self.q_list.count() - 1)
        else:
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            
        # Study Submit Button Update
        if self.is_study_mode:
            if self.is_submitted.get(q_id):
                self.study_submit_btn.setText("Show Explanation")
                self.study_submit_btn.setEnabled(False)
            else:
                self.study_submit_btn.setText("Submit Answer")
                self.study_submit_btn.setEnabled(True)

    def _clear_choices_layout(self):
        # Delete all widgets from the answers layout
        for i in reversed(range(self.answers_layout.count())):
            widget = self.answers_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
                
        self.choice_radios = []
        self.choice_checkboxes = []
        self.fill_line_edit = None
        self.drag_drop_container = None

    def _load_choices_input(self, q, selected_val):
        q_type = q["question_type"]
        q_id = q["id"]
        is_disabled = self.is_study_mode and self.is_submitted.get(q_id)
        
        if q_type == "single" or q_type == "tf":
            self.choice_radios = []
            for c in q["choices"]:
                letter = c["choice_letter"]
                text = c["choice_text"]
                
                # Format: "A. Option Text"
                radio = QRadioButton(f"{letter}.  {text}", self.answers_frame)
                radio.setEnabled(not is_disabled)
                radio.setAutoExclusive(True)
                
                if selected_val == letter:
                    radio.setChecked(True)
                
                # In Study Mode (after submit), highlight answer
                if is_disabled:
                    if c["is_correct"]:
                        radio.setStyleSheet("color: #10b981; font-weight: bold;")
                    elif selected_val == letter:
                        radio.setStyleSheet("color: #ef4444; font-weight: bold;")
                
                self.answers_layout.addWidget(radio)
                self.choice_radios.append(radio)
                
                # Save mapping
                radio.letter = letter
                
        elif q_type == "multiple":
            self.choice_checkboxes = []
            selected_letters = selected_val.split(",") if selected_val else []
            selected_letters = [x.strip() for x in selected_letters]
            
            for c in q["choices"]:
                letter = c["choice_letter"]
                text = c["choice_text"]
                
                chk = QCheckBox(f"{letter}.  {text}", self.answers_frame)
                chk.setEnabled(not is_disabled)
                
                if letter in selected_letters:
                    chk.setChecked(True)
                    
                if is_disabled:
                    if c["is_correct"]:
                        chk.setStyleSheet("color: #10b981; font-weight: bold;")
                    elif letter in selected_letters:
                        chk.setStyleSheet("color: #ef4444; font-weight: bold;")
                        
                self.answers_layout.addWidget(chk)
                self.choice_checkboxes.append(chk)
                chk.letter = letter
                
        elif q_type == "fill":
            self.answers_layout.addWidget(QLabel("Type your answer below:"))
            self.fill_line_edit = QLineEdit(self.answers_frame)
            self.fill_line_edit.setEnabled(not is_disabled)
            if selected_val:
                self.fill_line_edit.setText(selected_val)
            
            if is_disabled:
                is_correct = self.db._evaluate_correctness(q, selected_val)
                text_color = "#10b981" if is_correct else "#ef4444"
                self.fill_line_edit.setStyleSheet(f"color: {text_color}; font-weight: bold;")
                
            self.answers_layout.addWidget(self.fill_line_edit)

        elif q_type == "drag_drop":
            self.answers_layout.addWidget(QLabel("Drag-and-Drop / Interactive Question:"))
            self.answers_layout.addWidget(QLabel("Solve the matching layout in the exhibit above by dragging the items below. Compare with the correct answer diagram after submitting."))
            
            # Instantiate the DragDropContainer
            # We pass a callback to save the current answer automatically when drops change!
            self.drag_drop_container = DragDropContainer(self.save_current_answer, self.answers_frame)
            self.answers_layout.addWidget(self.drag_drop_container)
            
            # Map selected_val to retrieve drag-drop state
            drag_drop_state_str = ""
            graded_status = None
            if selected_val:
                if "|" in selected_val:
                    parts = selected_val.split("|", 1)
                    if parts[0] in ["CORRECT", "INCORRECT", "PENDING"]:
                        graded_status = parts[0]
                        drag_drop_state_str = parts[1]
                    else:
                        drag_drop_state_str = selected_val
                else:
                    if selected_val in ["CORRECT", "INCORRECT", "PENDING"]:
                        graded_status = selected_val
                    else:
                        drag_drop_state_str = selected_val
                        
            # Restore state
            if drag_drop_state_str:
                self.drag_drop_container.set_state_string(drag_drop_state_str)
                
            # Disable drag drop if already submitted
            if is_disabled:
                self.drag_drop_container.setEnabled(False)
                
                # Show self-grading buttons in study mode after submission
                grade_layout = QHBoxLayout()
                btn_correct = QPushButton("✓ I Got It Right", self.answers_frame)
                btn_incorrect = QPushButton("✗ I Got It Wrong", self.answers_frame)
                
                if graded_status == "CORRECT":
                    btn_correct.setStyleSheet("background-color: #10b981; color: white; font-weight: bold; border-color: #10b981;")
                    btn_incorrect.setStyleSheet("background-color: #334155; color: #94a3b8;")
                elif graded_status == "INCORRECT":
                    btn_correct.setStyleSheet("background-color: #334155; color: #94a3b8;")
                    btn_incorrect.setStyleSheet("background-color: #ef4444; color: white; font-weight: bold; border-color: #ef4444;")
                else:
                    btn_correct.setStyleSheet("background-color: #10b981; color: white;")
                    btn_incorrect.setStyleSheet("background-color: #ef4444; color: white;")
                    
                btn_correct.clicked.connect(lambda: self.grade_drag_drop_answer(True))
                btn_incorrect.clicked.connect(lambda: self.grade_drag_drop_answer(False))
                
                grade_layout.addWidget(btn_correct)
                grade_layout.addWidget(btn_incorrect)
                self.answers_layout.addLayout(grade_layout)

    def grade_drag_drop_answer(self, correct_bool):
        q = self.questions[self.current_index]
        q_id = q["id"]
        
        status_str = "CORRECT" if correct_bool else "INCORRECT"
        drag_state = self.drag_drop_container.get_state_string() if self.drag_drop_container else ""
        combined_val = f"{status_str}|{drag_state}"
        
        if q_id not in self.responses:
            self.responses[q_id] = {"selected": combined_val, "flagged": False}
        else:
            self.responses[q_id]["selected"] = combined_val
            
        self.db.set_session_answer(self.session_id, q_id, combined_val)
        self.update_progress()
        
        # Reload question
        curr_row = self.q_list.currentRow()
        self.refresh_sidebar_list()
        self.load_question(curr_row)

    # --- Save Answer State ---
    def save_current_answer(self):
        if self.current_index >= len(self.questions):
            return
            
        q = self.questions[self.current_index]
        q_id = q["id"]
        
        # Don't overwrite if study mode already submitted
        if self.is_study_mode and self.is_submitted.get(q_id):
            return
            
        selected_str = ""
        
        if q["question_type"] in ["single", "tf"]:
            for radio in self.choice_radios:
                if radio.isChecked():
                    selected_str = radio.letter
                    break
        elif q["question_type"] == "multiple":
            selected_list = []
            for chk in self.choice_checkboxes:
                if chk.isChecked():
                    selected_list.append(chk.letter)
            selected_str = ",".join(selected_list)
        elif q["question_type"] == "fill":
            if self.fill_line_edit:
                selected_str = self.fill_line_edit.text().strip()
        elif q["question_type"] == "drag_drop":
            if self.drag_drop_container:
                selected_str = self.drag_drop_container.get_state_string()
                
        if selected_str:
            # Update cache
            if q_id not in self.responses:
                self.responses[q_id] = {"selected": None, "flagged": False}
            self.responses[q_id]["selected"] = selected_str
            self.db.set_session_answer(self.session_id, q_id, selected_str)
            self.update_progress()

    def update_progress(self):
        total = len(self.questions)
        answered = 0
        for q in self.questions:
            resp = self.responses.get(q["id"])
            if resp and resp["selected"]:
                answered += 1
                
        self.progress_lbl.setText(f"Answered: {answered} / {total}")
        pct = int((answered / total) * 100) if total > 0 else 0
        self.progress_bar.setValue(pct)

    # --- Actions / Events ---
    def prev_question(self):
        self.save_current_answer()
        row = self.q_list.currentRow()
        if row > 0:
            self.load_question(row - 1)

    def next_question(self):
        self.save_current_answer()
        row = self.q_list.currentRow()
        if row < self.q_list.count() - 1:
            self.load_question(row + 1)

    def _update_list_item_text(self, idx):
        if idx < 0 or idx >= len(self.questions):
            return
            
        q = self.questions[idx]
        q_id = q["id"]
        resp = self.responses.get(q_id, {"selected": None, "flagged": False})
        is_bookmarked = q["is_bookmarked"] or self.db.is_bookmarked(q_id)
        is_answered = bool(resp["selected"])
        
        # Find item in the list
        for row in range(self.q_list.count()):
            item = self.q_list.item(row)
            if item and item.data(Qt.UserRole) == idx:
                # Update item label in place
                label_text = f"Q{idx + 1}"
                if resp["flagged"]:
                    label_text += " 🚩"
                if is_bookmarked:
                    label_text += " ⭐"
                if is_answered:
                    if self.is_study_mode:
                        is_correct = self.db._evaluate_correctness(q, resp["selected"])
                        label_text += " (✓)" if is_correct else " (✗)"
                    else:
                        label_text += " (A)"
                item.setText(label_text)
                
                # Check if it needs to be filtered out
                if self.is_study_mode:
                    filter_idx = self.filter_combo.currentIndex()
                    should_remove = False
                    if filter_idx == 3 and is_answered: # Unanswered Filter
                        should_remove = True
                    elif filter_idx == 2: # Incorrect Filter
                        if not is_answered or self.db._evaluate_correctness(q, resp["selected"]):
                            should_remove = True
                    elif filter_idx == 1 and not is_bookmarked: # Bookmarked Filter
                        should_remove = True
                            
                    if should_remove:
                        self.q_list.blockSignals(True)
                        self.q_list.takeItem(row)
                        self.q_list.blockSignals(False)
                break

    def toggle_flag(self):
        if self.current_index >= len(self.questions):
            return
        q_id = self.questions[self.current_index]["id"]
        
        # Toggle flagged
        new_flag = self.db.toggle_flag(self.session_id, q_id)
        if q_id not in self.responses:
            self.responses[q_id] = {"selected": None, "flagged": False}
        self.responses[q_id]["flagged"] = new_flag
        
        # Update sidebar item in place
        self._update_list_item_text(self.current_index)
        
        # Update active button property style
        self.flag_btn.setProperty("active", "true" if new_flag else "false")
        self.flag_btn.setStyle(self.flag_btn.style())

    def toggle_bookmark(self):
        if self.current_index >= len(self.questions):
            return
        q_id = self.questions[self.current_index]["id"]
        
        # Toggle persistent bookmark
        is_bookmarked = self.db.toggle_bookmark(self.exam_id, q_id)
        
        # Update sidebar item in place
        self._update_list_item_text(self.current_index)
        
        # Update active button property style
        self.bookmark_btn.setProperty("active", "true" if is_bookmarked else "false")
        self.bookmark_btn.setStyle(self.bookmark_btn.style())

    def submit_study_answer(self):
        # Study Mode Only: Immediate check
        if not self.is_study_mode:
            return
            
        q = self.questions[self.current_index]
        q_id = q["id"]
        
        # Save response first
        self.save_current_answer()
        
        resp = self.responses.get(q_id)
        if not resp or not resp["selected"]:
            QMessageBox.information(self, "Answer Required", "Please select or type an answer first.")
            return
            
        self.is_submitted[q_id] = True
        
        # Update current item text in place and remove it if filtered out
        self._update_list_item_text(self.current_index)
        
        # Check if the current question is still in the sidebar list
        still_exists = False
        still_row = -1
        for row in range(self.q_list.count()):
            item = self.q_list.item(row)
            if item and item.data(Qt.UserRole) == self.current_index:
                still_exists = True
                still_row = row
                break
                
        if still_exists:
            # Item is still in list, select it and reload view
            self.q_list.blockSignals(True)
            self.q_list.setCurrentRow(still_row)
            self.q_list.blockSignals(False)
            self.load_question_by_abs_index(self.current_index)
        else:
            # Item was removed (filtered out). Load first item remaining in the list, or clear if empty.
            if self.q_list.count() > 0:
                self.q_list.blockSignals(True)
                self.q_list.setCurrentRow(0)
                self.q_list.blockSignals(False)
                item = self.q_list.item(0)
                if item:
                    abs_idx = item.data(Qt.UserRole)
                    self.load_question_by_abs_index(abs_idx)
            else:
                self._clear_question_view()

    def apply_filter(self, index):
        curr_row = self.q_list.currentRow()
        self.refresh_sidebar_list()
        if self.q_list.count() > 0:
            self.load_question(0)
        else:
            self._clear_choices_layout()
            self.browser.setHtml("<html><body><h3>No questions match the current filter.</h3></body></html>")
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)

    # --- Zoom Controls ---
    def zoom_in(self):
        self.font_size = min(36, self.font_size + 2)
        self.apply_zoom()

    def zoom_out(self):
        self.font_size = max(10, self.font_size - 2)
        self.apply_zoom()

    def apply_zoom(self):
        self.browser.setStyleSheet(f"font-size: {self.font_size}px;")

    # --- Keyboard Shortcuts Override ---
    def keyPressEvent(self, event):
        # Allow shortcuts for selection A, B, C, D...
        key = event.key()
        if key == Qt.Key_Left:
            self.prev_question()
        elif key == Qt.Key_Right:
            self.next_question()
        elif key == Qt.Key_F:
            self.toggle_flag()
        elif key == Qt.Key_B:
            self.toggle_bookmark()
        elif key == Qt.Key_Space and self.is_study_mode:
            self.submit_study_answer()
        elif key in [Qt.Key_A, Qt.Key_B, Qt.Key_C, Qt.Key_D, Qt.Key_E, Qt.Key_F]:
            letter = chr(key)
            self._select_letter_shortcut(letter)
        else:
            super().keyPressEvent(event)

    def _select_letter_shortcut(self, letter):
        if self.current_index >= len(self.questions):
            return
        q = self.questions[self.current_index]
        is_disabled = self.is_study_mode and self.is_submitted.get(q["id"])
        if is_disabled:
            return
            
        if q["question_type"] in ["single", "tf"]:
            for btn in self.choice_radios:
                if btn.letter == letter:
                    btn.setChecked(True)
                    break
        elif q["question_type"] == "multiple":
            for chk in self.choice_checkboxes:
                if chk.letter == letter:
                    chk.setChecked(not chk.isChecked())
                    break

    # --- End Session ---
    def confirm_end_session(self):
        if self.is_study_mode:
            self.end_session()
            return
            
        # Count unanswered
        total = len(self.questions)
        answered = 0
        for q in self.questions:
            resp = self.responses.get(q["id"])
            if resp and resp["selected"]:
                answered += 1
                
        unanswered = total - answered
        msg = "Are you sure you want to end this exam and submit for grading?"
        if unanswered > 0:
            msg = f"You have {unanswered} unanswered questions. " + msg
            
        reply = QMessageBox.question(self, "End Exam", msg, QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.end_session()

    def end_session(self):
        # Save last answer
        self.save_current_answer()
        
        # Stop timer
        self.timer.stop()
        
        # Complete session in DB
        self.db.complete_session(self.session_id)
        
        # Redirect to results view
        self.main_window.load_results_view(self.session_id)

    def closeEvent(self, event):
        # Auto-save time spent on close
        self.db.update_session_time(self.session_id, self.time_spent)
        super().closeEvent(event)
