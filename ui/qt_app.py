"""Qt-based prototype UI for SpeedTake."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from controller import ExtractionResult, SpeedTakeController


def open_path(path: str, parent: Optional[QWidget] = None) -> None:
    """Open a file or folder with the system default handler."""

    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=True)
        else:
            subprocess.run(["xdg-open", path], check=True)
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(parent, "Error", f"Could not open path: {path}\n{exc}")


class ExtractionWorker(QThread):
    """Runs the extraction on a background thread."""

    status_updated = Signal(str)
    progress_updated = Signal(int, int)
    completed = Signal(ExtractionResult)

    def __init__(self, controller: SpeedTakeController) -> None:
        super().__init__()
        self.controller = controller

    def run(self) -> None:  # noqa: D401
        """Execute the extraction workflow."""

        def status_callback(index: int, total: int, filename: str) -> None:
            self.status_updated.emit(f"Processing {index}/{total}: {filename}")
            self.progress_updated.emit(index, total)

        def error_callback(path: str, error: Exception) -> None:
            print(f"Error processing {path}: {error}")

        result = self.controller.extract_audio_files(
            status_callback=status_callback,
            error_callback=error_callback,
        )
        self.completed.emit(result)


class SpeedTakeQtMainWindow(QMainWindow):
    """Main window for the Qt prototype."""

    def __init__(self) -> None:
        super().__init__()
        self.controller = SpeedTakeController()
        self.controller.set_output_format("mp3")

        self.setWindowTitle("SpeedTake Audio Extractor (Qt Prototype)")
        self.resize(700, 650)
        self.worker: Optional[ExtractionWorker] = None

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        self._build_header()
        self._build_file_selection()
        self._build_output_options()
        self._build_extraction_controls()
        self._build_status_area()

    # ------------------------------------------------------------------
    # UI builders
    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        title = QLabel("SpeedTake Audio Extractor", self)
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("font-size: 20pt; font-weight: bold;")
        self.main_layout.addWidget(title)

    def _build_file_selection(self) -> None:
        group = QGroupBox("1. Select Video Files", self)
        layout = QVBoxLayout(group)

        self.file_list = QListWidget(group)
        layout.addWidget(self.file_list)

        button_row = QHBoxLayout()
        self.add_files_btn = QPushButton("Add Files", group)
        self.add_files_btn.clicked.connect(self.add_files)
        button_row.addWidget(self.add_files_btn)

        self.add_folder_btn = QPushButton("Add Folder", group)
        self.add_folder_btn.clicked.connect(self.add_folder)
        button_row.addWidget(self.add_folder_btn)

        self.clear_list_btn = QPushButton("Clear List", group)
        self.clear_list_btn.clicked.connect(self.clear_files)
        button_row.addWidget(self.clear_list_btn)

        button_row.addStretch(1)
        layout.addLayout(button_row)

        self.main_layout.addWidget(group)

    def _build_output_options(self) -> None:
        group = QGroupBox("2. Set Output Options", self)
        layout = QVBoxLayout(group)

        folder_row = QHBoxLayout()
        folder_label = QLabel("Output Folder:", group)
        folder_row.addWidget(folder_label)

        self.folder_edit = QLineEdit(group)
        self.folder_edit.textChanged.connect(self.on_output_folder_changed)
        folder_row.addWidget(self.folder_edit, stretch=1)

        browse_btn = QPushButton("Browse", group)
        browse_btn.clicked.connect(self.browse_output_folder)
        folder_row.addWidget(browse_btn)

        layout.addLayout(folder_row)

        format_label = QLabel("Output Format:", group)
        layout.addWidget(format_label)

        format_row = QHBoxLayout()
        self.format_group = QButtonGroup(group)
        self.format_group.setExclusive(True)
        formats = [("MP3", "mp3"), ("WAV", "wav"), ("FLAC", "flac"), ("AAC", "aac")]
        for text, value in formats:
            button = QRadioButton(text, group)
            if value == "mp3":
                button.setChecked(True)
            button.toggled.connect(lambda checked, fmt=value: self.on_output_format_changed(fmt) if checked else None)
            self.format_group.addButton(button)
            format_row.addWidget(button)

        format_row.addStretch(1)
        layout.addLayout(format_row)

        self.main_layout.addWidget(group)

    def _build_extraction_controls(self) -> None:
        group = QGroupBox("3. Extract Audio", self)
        layout = QVBoxLayout(group)

        self.start_button = QPushButton("Start Extraction", group)
        self.start_button.clicked.connect(self.start_extraction)
        self.start_button.setStyleSheet("font-weight: bold; padding: 8px;")
        layout.addWidget(self.start_button)

        self.main_layout.addWidget(group)

    def _build_status_area(self) -> None:
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

        self.status_label = QLabel("Ready", self)
        self.status_label.setStyleSheet("color: grey;")

        self.main_layout.addWidget(self.progress_bar)
        self.main_layout.addWidget(self.status_label)

    # ------------------------------------------------------------------
    # Interaction handlers
    # ------------------------------------------------------------------
    def add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(self, "Select Video Files", "", "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v);;All Files (*.*)")
        new_files = self.controller.add_files(files)
        for file in new_files:
            item = QListWidgetItem(Path(file).name)
            item.setToolTip(file)
            self.file_list.addItem(item)

    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Video Files")
        if not folder:
            return

        try:
            new_files, total_found = self.controller.add_folder(folder)
        except FileNotFoundError:
            QMessageBox.critical(self, "Folder Not Found", "The selected folder could not be found.")
            return

        if total_found == 0:
            QMessageBox.information(self, "No Videos Found", "No video files found in the selected folder.")
            return

        if not new_files:
            QMessageBox.information(self, "No New Files", "All supported video files in this folder are already listed.")
            return

        for file in new_files:
            item = QListWidgetItem(Path(file).name)
            item.setToolTip(file)
            self.file_list.addItem(item)

    def clear_files(self) -> None:
        self.controller.clear_files()
        self.file_list.clear()

    def browse_output_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.folder_edit.setText(folder)

    def on_output_folder_changed(self, text: str) -> None:
        self.controller.set_output_folder(text.strip() or None)

    def on_output_format_changed(self, fmt: str) -> None:
        try:
            self.controller.set_output_format(fmt)
        except ValueError:
            QMessageBox.critical(self, "Unsupported Format", f"The selected format '{fmt}' is not supported.")

    def start_extraction(self) -> None:
        if not self.controller.selected_files:
            QMessageBox.warning(self, "No Files Selected", "Please select one or more video files first.")
            return

        current_folder = self.folder_edit.text().strip()
        self.controller.set_output_folder(current_folder or None)

        if not self.controller.ffmpeg_path:
            exe_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path().cwd()
            if not self.controller.check_ffmpeg(exe_dir):
                QMessageBox.warning(
                    self,
                    "FFmpeg Not Found",
                    "FFmpeg is required but was not found. Please install it and ensure it is on the PATH.",
                )
                return

        total_files = len(self.controller.selected_files)
        self.progress_bar.setRange(0, total_files)
        self.progress_bar.setValue(0)
        self.update_status("Extracting audio...")
        self.start_button.setEnabled(False)
        self.add_files_btn.setEnabled(False)
        self.add_folder_btn.setEnabled(False)
        self.clear_list_btn.setEnabled(False)

        self.worker = ExtractionWorker(self.controller)
        self.worker.status_updated.connect(self.update_status)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.completed.connect(self.on_extraction_complete)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.on_worker_finished)
        self.worker.start()

    def update_status(self, message: str) -> None:
        self.status_label.setText(message)

    def update_progress(self, index: int, total: int) -> None:
        if total == 0:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(0)
        else:
            self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(index)

    def on_worker_finished(self) -> None:
        self.worker = None
        self.start_button.setEnabled(True)
        self.add_files_btn.setEnabled(True)
        self.add_folder_btn.setEnabled(True)
        self.clear_list_btn.setEnabled(True)

    def on_extraction_complete(self, result: ExtractionResult) -> None:
        output_folder = Path(result.last_output_path).parent if result.last_output_path else None

        if result.total_files == 0:
            self.update_status("No files to process.")
            return

        total = result.total_files if result.total_files else 1
        self.progress_bar.setRange(0, total)

        if result.success_count == result.total_files:
            message = f"Success! Extracted audio from all {result.total_files} files."
            self.update_status(message)
            self.progress_bar.setValue(result.total_files)
            self.show_completion_dialog(
                "Extraction Complete",
                message,
                str(output_folder) if output_folder else None,
                result.last_output_path if result.total_files == 1 else None,
            )
        elif result.success_count > 0:
            message = f"Completed with issues: {result.success_count}/{result.total_files} successful."
            self.update_status(message)
            self.progress_bar.setValue(result.success_count)
            self.show_completion_dialog(
                "Partial Success",
                message,
                str(output_folder) if output_folder else None,
                None,
            )
        else:
            message = f"Failed to extract audio from any of the {result.total_files} files."
            self.update_status(message)
            self.progress_bar.setValue(0)
            QMessageBox.critical(self, "Extraction Failed", "Could not extract audio from any file. Check console for details.")

        if result.errors:
            for error in result.errors:
                print(error)

    def show_completion_dialog(
        self,
        title: str,
        message: str,
        output_folder: Optional[str],
        output_file: Optional[str],
    ) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setText(message)
        dialog.setIcon(QMessageBox.Information)

        play_button = None
        open_folder_button = None

        dialog.addButton(QMessageBox.Close)
        if output_file:
            play_button = dialog.addButton("Play File", QMessageBox.AcceptRole)
        if output_folder:
            open_folder_button = dialog.addButton("Open Folder", QMessageBox.ActionRole)

        dialog.exec()
        clicked = dialog.clickedButton()

        if clicked == play_button and output_file:
            open_path(output_file, self)
        elif clicked == open_folder_button and output_folder:
            open_path(output_folder, self)
        else:
            dialog.close()


def main() -> None:
    app = QApplication(sys.argv)
    window = SpeedTakeQtMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
