from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QStackedWidget, QPushButton, QLabel, QFrame, 
                             QFileDialog, QInputDialog, QMessageBox, QDialog)
from PySide6.QtCore import Qt, QSize
from database import Database
from styles import Styles
from ui.dashboard import DashboardView
from ui.import_dialog import ImportDialog
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Rivan Exam Simulator (PDF-VCE)")
        self.resize(1100, 750)
        self.setMinimumSize(950, 650)
        
        # Core State
        self.dark_mode = True
        self.db = Database()
        self.tesseract_path = self._load_settings()

        # UI Initialization
        self._init_ui()
        self.apply_theme()
        self.show_dashboard()

    def _load_settings(self):
        # Settings path helper
        settings_file = "d:\\Projects\\pdf-exam-simulator\\settings.txt"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as f:
                    return f.read().strip()
            except:
                pass
        return ""

    def save_settings(self, tesseract_path):
        self.tesseract_path = tesseract_path
        settings_file = "d:\\Projects\\pdf-exam-simulator\\settings.txt"
        try:
            with open(settings_file, "w") as f:
                f.write(tesseract_path)
        except Exception as e:
            QMessageBox.warning(self, "Settings Error", f"Could not save settings: {e}")

    def _init_ui(self):
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- Create Navigation Header ---
        self.header = QFrame(self.central_widget)
        self.header.setObjectName("header")
        self.header.setMinimumHeight(60)
        self.header.setMaximumHeight(60)
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Logo text
        self.logo_label = QLabel("RIVAN EXAM SIMULATOR", self.header)
        self.logo_label.setObjectName("title")
        self.logo_label.setStyleSheet("font-weight: 800; letter-spacing: 1px; font-size: 16px;")
        header_layout.addWidget(self.logo_label)
        
        header_layout.addStretch()
        
        # Header Controls
        self.home_btn = QPushButton("Dashboard", self.header)
        self.home_btn.clicked.connect(self.show_dashboard)
        header_layout.addWidget(self.home_btn)
        
        self.import_btn = QPushButton("Import Exam PDF", self.header)
        self.import_btn.setObjectName("primary_btn")
        self.import_btn.clicked.connect(self.open_import_dialog)
        header_layout.addWidget(self.import_btn)
        
        self.theme_btn = QPushButton("☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode", self.header)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)
        
        self.settings_btn = QPushButton("⚙️ Settings", self.header)
        self.settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(self.settings_btn)
        
        self.main_layout.addWidget(self.header)
        
        # --- Central QStackedWidget ---
        self.stack = QStackedWidget(self.central_widget)
        self.main_layout.addWidget(self.stack)

    def apply_theme(self):
        qss = Styles.get_qss(self.dark_mode)
        self.setStyleSheet(qss)
        
        # Trigger theme updates in active views if necessary
        for i in range(self.stack.count()):
            widget = self.stack.widget(i)
            if hasattr(widget, "update_theme"):
                widget.update_theme(self.dark_mode)

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme_btn.setText("☀️ Light Mode" if self.dark_mode else "🌙 Dark Mode")
        self.apply_theme()

    def _clear_simulator(self):
        if hasattr(self, "simulator_view") and self.simulator_view is not None:
            try:
                # Save any pending answer selection
                self.simulator_view.save_current_answer()
            except Exception as e:
                print("Error saving current answer on clear:", e)
                
            try:
                # Explicitly stop the timer
                if hasattr(self.simulator_view, "timer") and self.simulator_view.timer:
                    self.simulator_view.timer.stop()
            except Exception as e:
                print("Error stopping timer on clear:", e)
                
            try:
                # Save elapsed time spent
                if hasattr(self.simulator_view, "db") and self.simulator_view.db:
                    self.simulator_view.db.update_session_time(self.simulator_view.session_id, self.simulator_view.time_spent)
            except Exception as e:
                print("Error updating session time on clear:", e)
                
            # Remove widget and schedule for deletion
            self.stack.removeWidget(self.simulator_view)
            self.simulator_view.deleteLater()
            self.simulator_view = None

    def _clear_stack(self):
        # Clean up simulator first
        self._clear_simulator()
        
        # Remove and delete all remaining widgets from the stacked widget
        while self.stack.count() > 0:
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()

    def closeEvent(self, event):
        self._clear_simulator()
        super().closeEvent(event)

    def show_dashboard(self):
        self._clear_stack()
        self.dashboard_view = DashboardView(self)
        self.stack.addWidget(self.dashboard_view)
        self.stack.setCurrentWidget(self.dashboard_view)

    def open_import_dialog(self):
        dialog = ImportDialog(self)
        dialog.exec()
        # Refresh dashboard lists after import
        self.show_dashboard()

    def open_settings(self):
        path, ok = QInputDialog.getText(
            self, "Tesseract OCR Configuration", 
            "Enter path to tesseract.exe (leave blank to disable OCR):",
            text=self.tesseract_path
        )
        if ok:
            self.save_settings(path.strip())
            QMessageBox.information(self, "Settings Saved", "Tesseract configuration saved successfully.")
            
    def load_exam_simulator(self, exam_id, is_study_mode=False, resume_session_id=None,
                            shuffle_questions=False, shuffle_choices=False,
                            subset_type="all", range_from=1, range_to=100, random_count=50):
        self._clear_stack()
        from ui.simulator_view import SimulatorView
        self.simulator_view = SimulatorView(
            self, exam_id, is_study_mode, resume_session_id,
            shuffle_questions, shuffle_choices,
            subset_type, range_from, range_to, random_count
        )
        self.stack.addWidget(self.simulator_view)
        self.stack.setCurrentWidget(self.simulator_view)
        
    def load_results_view(self, session_id):
        self._clear_stack()
        from ui.results_view import ResultsView
        self.results_view = ResultsView(self, session_id)
        self.stack.addWidget(self.results_view)
        self.stack.setCurrentWidget(self.results_view)
