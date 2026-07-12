import sys
import traceback
import datetime
from PySide6.QtWidgets import QApplication, QMessageBox

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
        
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = "".join(tb_lines)
    
    # Output to terminal/stderr
    print(tb_text, file=sys.stderr)
    
    # Write to local file
    try:
        with open("crash_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\n--- Crash occurred at {datetime.datetime.now()} ---\n")
            f.write(tb_text)
            f.write("-" * 50 + "\n")
    except:
        pass
        
    # Show user-friendly QMessageBox popup if QApplication exists
    app = QApplication.instance()
    if app:
        # Temporarily restore original hook to avoid recursive loops
        sys.excepthook = sys.__excepthook__
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Application Error")
        msg.setText("An unexpected error occurred in the application.")
        msg.setInformativeText(f"A detailed error log has been saved to crash_log.txt.\n\nError: {exc_value}")
        msg.setDetailedText(tb_text)
        msg.exec()
        sys.exit(1)

# Register the global exception hook
sys.excepthook = handle_exception

def main():
    app = QApplication(sys.argv)
    
    # Launch main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    from ui.main_window import MainWindow
    main()
