# Rivan Exam Simulator (PDF-VCE)

Rivan Exam Simulator is a clean, modern, and highly stable desktop application designed for offline certification preparation using local PDF assets.

## Where to Locate the Executable (`.exe`)

The compiled standalone executable is located in the `dist` directory of this repository:

**Executable Path**: [dist/RivanExamSimulator.exe](dist/RivanExamSimulator.exe)

### How to Run:
1. Clone or download this repository.
2. Navigate to the `dist` folder.
3. Double-click `RivanExamSimulator.exe` to run the application instantly (no Python installation required).

*Note: On launch, the application will automatically create a local database `exam_simulator.db` in its directory to store your imported exams, progress, session history, bookmarks, and flags.*

---

## Features
- **PDF-to-Exam Parser**: Drag-and-drop or select any practice exam PDF to automatically parse questions, choices, answers, and reference images.
- **Multiple Choice Support**: Complete support for single-choice and multiple-choice questions.
- **Study Mode**: Check answers instantly with explanations, flags, and persistent bookmarks.
- **Exam Mode**: Practice under time constraints to simulate real test conditions.
- **In-place Sidebars**: Fast and stable sidebar transitions optimized for large exam sets (1,000+ questions).
- **Responsive Theme**: Curated dark mode styling built using PySide6.