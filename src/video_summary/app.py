from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QLabel,
    QProgressBar,
    QMessageBox,
)
from PyQt6.QtCore import QThread, pyqtSignal
from youtube_summary import YouTubeSummarizer
import sys
import webbrowser


class SummaryWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            summarizer = YouTubeSummarizer()
            result = summarizer.summarize_video(self.url)
            print("Summarizer result:", result)  # For debugging

            if not isinstance(result, dict):
                self.error.emit(f"Invalid result type: {type(result)}")
                return

            if "status" not in result:
                self.error.emit("Missing status in result")
                return

            if result["status"] == "success":
                self.finished.emit(result)
            else:
                self.error.emit(result.get("message", "Unknown error"))
        except Exception as e:
            print("Error in run:", str(e))  # For debugging
            self.error.emit(str(e))


def check_ollama_installation():
    try:
        # Test Ollama service connection
        _ = YouTubeSummarizer()
        return True
    except Exception:
        return False


def show_installation_guide():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle("Installation Required")
    msg.setText("Ollama and LLM model are required to run this application.")
    msg.setInformativeText(
        "Please follow these steps:\n\n"
        "1. Install Ollama from https://ollama.ai\n"
        "2. Open terminal and run: ollama pull llama3.2\n\n"
        "After installation, restart the application."
    )
    msg.exec()


def install_ollama():
    platform = sys.platform
    try:
        if platform == "win32":
            # Windows installation guide
            webbrowser.open("https://ollama.ai/download/windows")
        elif platform == "darwin":
            # macOS installation guide
            webbrowser.open("https://ollama.ai/download/mac")
        elif platform == "linux":
            # Linux installation guide
            webbrowser.open("https://ollama.ai/download/linux")

        # Installation guide message
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Ollama Installation")
        msg.setText("Please install Ollama using the opened browser.")
        msg.setInformativeText(
            "After installation, open terminal and run:\n"
            "ollama pull llama3.2\n\n"
            "Then restart this application."
        )
        msg.exec()

    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to open browser: {str(e)}")


class YouTubeSummaryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Video Summarizer")
        self.setMinimumSize(800, 600)

        # Check Ollama installation
        if not check_ollama_installation():
            show_installation_guide()
            sys.exit()

        self.setup_ui()

    def setup_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # URL input section
        url_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube URL...")
        self.summarize_btn = QPushButton("Summarize")
        self.summarize_btn.clicked.connect(self.start_summarization)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(self.summarize_btn)
        layout.addLayout(url_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Summary sections
        self.main_topic_label = QLabel("Main Topic:")
        self.main_topic_text = QTextEdit()
        self.main_topic_text.setReadOnly(True)
        self.main_topic_text.setMaximumHeight(60)
        layout.addWidget(self.main_topic_label)
        layout.addWidget(self.main_topic_text)

        self.key_points_label = QLabel("Key Points:")
        self.key_points_text = QTextEdit()
        self.key_points_text.setReadOnly(True)
        layout.addWidget(self.key_points_label)
        layout.addWidget(self.key_points_text)

        self.details_label = QLabel("Important Details:")
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        layout.addWidget(self.details_label)
        layout.addWidget(self.details_text)

        self.takeaways_label = QLabel("Takeaways:")
        self.takeaways_text = QTextEdit()
        self.takeaways_text.setReadOnly(True)
        layout.addWidget(self.takeaways_label)
        layout.addWidget(self.takeaways_text)

        self.current_summary = None

    def start_summarization(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a YouTube URL")
            return

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.summarize_btn.setEnabled(False)

        self.worker = SummaryWorker(url)
        self.worker.finished.connect(self.handle_summary)
        self.worker.error.connect(self.handle_error)
        self.worker.start()

    def handle_summary(self, result):
        print("Received result:", result)  # For debugging

        try:
            # Check if result is dictionary
            if not isinstance(result, dict):
                self.handle_error(f"Invalid result type: {type(result)}")
                return

            # Check if summary key exists
            if "summary" not in result:
                self.handle_error("Missing 'summary' key in result")
                return

            self.current_summary = result["summary"]
            print("Current summary:", self.current_summary)  # For debugging

            # Check if summary is dictionary
            if not isinstance(self.current_summary, dict):
                self.handle_error(f"Invalid summary type: {type(self.current_summary)}")
                return

            self.display_summary(self.current_summary)
            self.progress.setVisible(False)
            self.progress.setRange(0, 100)
            self.summarize_btn.setEnabled(True)

        except Exception as e:
            self.handle_error(f"Error in handle_summary: {str(e)}")

    def handle_error(self, error_message):
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")
        self.progress.setVisible(False)
        self.progress.setRange(0, 100)
        self.summarize_btn.setEnabled(True)

    def display_summary(self, summary):
        print("Displaying summary:", summary)  # For debugging

        try:
            # Safely display each section
            self.main_topic_text.setText(
                str(summary.get("main_topic", "No main topic available"))
            )

            # Key Points
            key_points = summary.get("key_points", [])
            if isinstance(key_points, list):
                points_text = "\n".join(f"• {str(point)}" for point in key_points)
            else:
                points_text = str(key_points)
            self.key_points_text.setText(points_text)

            # Important Details
            details = summary.get("important_details", [])
            if isinstance(details, list):
                details_text = "\n".join(f"• {str(detail)}" for detail in details)
            else:
                details_text = str(details)
            self.details_text.setText(details_text)

            # Takeaways
            takeaways = summary.get("takeaways", [])
            if isinstance(takeaways, list):
                takeaways_text = "\n".join(
                    f"• {str(takeaway)}" for takeaway in takeaways
                )
            else:
                takeaways_text = str(takeaways)
            self.takeaways_text.setText(takeaways_text)

        except Exception as e:
            raise Exception(f"Error in display_summary: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = YouTubeSummaryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
