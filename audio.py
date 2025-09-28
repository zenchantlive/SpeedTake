#!/usr/bin/env python3
"""
SpeedTake - Audio Extractor GUI
"""

import tkinter as tk
from tkinter import font
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from tkinter import filedialog
import subprocess
import threading
from pathlib import Path
import os
import sys

def open_path(path: str):
    """Opens a file or directory in the default application."""
    try:
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", path], check=True)
        else:  # Linux
            subprocess.run(["xdg-open", path], check=True)
    except Exception as e:
        Messagebox.show_error(f"Could not open path: {path}\n{e}", title="Error")

class SpeedTakeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SpeedTake Audio Extractor")
        self.root.geometry("700x650")
        self.root.minsize(600, 550)

        # Variables
        self.selected_files = []
        self.output_format = tk.StringVar(value="mp3")
        self.output_folder = tk.StringVar()
        self.ffmpeg_path = None
        self.dark_mode = tk.BooleanVar(value=False)

        self.setup_styles()
        self.setup_ui()
        self.check_ffmpeg()

    def setup_styles(self, theme_name=None):
        """Configure ttk styles for a clean, modern look."""
        if theme_name:
            self.root.style.theme_use(theme_name)
            
        style = self.root.style
        
        # Define fonts
        self.title_font = font.Font(family="Helvetica", size=20, weight="bold")
        self.heading_font = font.Font(family="Helvetica", size=12, weight="bold")
        self.body_font = font.Font(family="Helvetica", size=10)

        # Configure custom styles
        style.configure("TFrame", background=style.colors.get("bg"))
        style.configure("Title.TLabel", font=self.title_font, background=style.colors.get("bg"), foreground=style.colors.primary)
        style.configure("Heading.TLabelframe", background=style.colors.get("bg"), bordercolor=style.colors.border, borderwidth=1)
        style.configure("Heading.TLabelframe.Label", font=self.heading_font, background=style.colors.get("bg"), foreground=style.colors.secondary)
        style.configure("Options.TLabel", font=self.body_font, background=style.colors.get("bg"))
        style.configure("TButton", font=self.body_font, padding=(10, 5), anchor="center")
        style.configure("Primary.TButton", font=(self.body_font.cget("family"), self.body_font.cget("size"), "bold"))
        style.configure("Tool.TButton", padding=(5, 5))
        style.configure("TRadiobutton", font=self.body_font, background=style.colors.get("bg"))

        # Style for hover effects on buttons
        style.map("Outline.TButton",
            bordercolor=[("active", style.colors.primary)],
            foreground=[("active", style.colors.primary)])

        # Update listbox colors
        if hasattr(self, 'file_listbox'):
            is_dark = style.theme.type == 'dark'
            bg_color = style.colors.bg if is_dark else "#ffffff"
            fg_color = style.colors.fg if is_dark else "#000000"
            self.file_listbox.config(bg=bg_color, fg=fg_color, relief=tk.SOLID, borderwidth=1, highlightthickness=1, highlightbackground=style.colors.border, highlightcolor=style.colors.primary)

    def setup_ui(self):
        """Setup the user interface"""
        self.main_frame = ttk.Frame(self.root, padding=20)
        self.main_frame.pack(fill=BOTH, expand=YES)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(4, weight=1) # Allow status frame to stick to bottom

        # --- Title & Theme Switcher --- #
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 25))
        header_frame.columnconfigure(0, weight=1)

        title_label = ttk.Label(header_frame, text="SpeedTake Audio Extractor", style="Title.TLabel")
        title_label.grid(row=0, column=0, sticky="w")

        theme_switcher = ttk.Checkbutton(header_frame, text="Dark Mode", variable=self.dark_mode, command=self.toggle_theme, style="Switch.TCheckbutton")
        theme_switcher.grid(row=0, column=1, sticky="e")

        # --- File Selection (Step 1) --- #
        file_frame = ttk.Labelframe(self.main_frame, text="1. Select Video Files", style="Heading.TLabelframe", padding=15)
        file_frame.grid(row=1, column=0, sticky="ew", pady=10)
        file_frame.columnconfigure(0, weight=1)

        list_frame = ttk.Frame(file_frame)
        list_frame.grid(row=0, column=0, columnspan=3, sticky="ew")
        list_frame.columnconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(list_frame, height=8, selectmode=EXTENDED, font=self.body_font)
        self.file_listbox.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.file_listbox.yview, style="Round.Vertical.TScrollbar")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.file_listbox.configure(yscrollcommand=scrollbar.set)

        file_buttons_frame = ttk.Frame(file_frame)
        file_buttons_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=(15, 0))

        ttk.Button(file_buttons_frame, text="Add Files", command=self.add_files, style="Outline.TButton").pack(side=LEFT, padx=(0, 10))
        ttk.Button(file_buttons_frame, text="Add Folder", command=self.add_folder, style="Outline.TButton").pack(side=LEFT, padx=(0, 10))
        ttk.Button(file_buttons_frame, text="Clear List", command=self.clear_files, style="Outline.TButton", bootstyle="danger").pack(side=LEFT)

        # --- Output Options (Step 2) --- #
        options_frame = ttk.Labelframe(self.main_frame, text="2. Set Output Options", style="Heading.TLabelframe", padding=15)
        options_frame.grid(row=2, column=0, sticky="ew", pady=10)
        options_frame.columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="Output Folder:", style="Options.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10), pady=(5,10))
        self.folder_entry = ttk.Entry(options_frame, textvariable=self.output_folder, font=self.body_font)
        self.folder_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(5,10))
        ttk.Button(options_frame, text="Browse", command=self.browse_output_folder, style="Tool.TButton").grid(row=0, column=2, sticky="e", pady=(5,10))

        ttk.Label(options_frame, text="Output Format:", style="Options.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 10), pady=(10,5))
        format_frame = ttk.Frame(options_frame)
        format_frame.grid(row=1, column=1, columnspan=2, sticky="w", pady=(10,5))
        formats = [("MP3", "mp3"), ("WAV", "wav"), ("FLAC", "flac"), ("AAC", "aac")]
        for i, (text, value) in enumerate(formats):
            ttk.Radiobutton(format_frame, text=text, variable=self.output_format, value=value).pack(side=LEFT, padx=(0, 20))

        # --- Extraction (Step 3) --- #
        extract_frame = ttk.Labelframe(self.main_frame, text="3. Extract Audio", style="Heading.TLabelframe", padding=15)
        extract_frame.grid(row=3, column=0, sticky="ew", pady=10)
        extract_frame.columnconfigure(0, weight=1)

        self.extract_button = ttk.Button(extract_frame, text="Start Extraction", command=self.start_extraction, style="Primary.TButton", bootstyle="success")
        self.extract_button.grid(row=0, column=0, sticky="ew", ipady=8)

        # --- Status & Progress --- #
        status_frame = ttk.Frame(self.main_frame, padding=(0, 10))
        status_frame.grid(row=5, column=0, sticky="sew")
        status_frame.columnconfigure(0, weight=1)
        
        self.progress = ttk.Progressbar(status_frame, mode="indeterminate", bootstyle="success-striped")
        self.progress.grid(row=0, column=0, sticky="ew", pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Ready", font=self.body_font, bootstyle="secondary")
        self.status_label.grid(row=1, column=0, sticky="w")
        
        self.toggle_theme() # Apply initial theme

    def toggle_theme(self):
        theme = "superhero" if self.dark_mode.get() else "sandstone"
        self.setup_styles(theme)

    def check_ffmpeg(self):
        """Check if ffmpeg is available"""
        try:
            exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path().cwd()
            ffmpeg_path = exe_dir / 'ffmpeg.exe'
            if not ffmpeg_path.exists():
                ffmpeg_path = 'ffmpeg'

            subprocess.run([str(ffmpeg_path), '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            self.ffmpeg_path = str(ffmpeg_path)
            self.status_label.config(text="FFmpeg found - Ready to extract audio", bootstyle="success")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.ffmpeg_path = None
            self.status_label.config(text="WARNING: FFmpeg not found! Please install it and ensure it's in the PATH.", bootstyle="danger")
            Messagebox.show_warning("FFmpeg is required but not found.\n\nPlease install FFmpeg from https://ffmpeg.org/download.html", "FFmpeg Not Found")

    def add_files(self):
        filetypes = [("Video files", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Select Video Files", filetypes=filetypes)
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
                self.file_listbox.insert(tk.END, Path(file).name)

    def add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Video Files")
        if folder:
            video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
            video_files = [str(f) for f in Path(folder).glob("**/*") if f.suffix.lower() in video_extensions]
            if not video_files:
                Messagebox.show_info("No video files found in the selected folder.", "No Videos Found")
                return
            for file in video_files:
                if file not in self.selected_files:
                    self.selected_files.append(file)
                    self.file_listbox.insert(tk.END, Path(file).name)

    def clear_files(self):
        self.selected_files.clear()
        self.file_listbox.delete(0, tk.END)

    def browse_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder.set(folder)

    def start_extraction(self):
        if not self.selected_files:
            Messagebox.show_warning("Please select one or more video files first.", "No Files Selected")
            return
        if not self.ffmpeg_path:
            self.check_ffmpeg()
            if not self.ffmpeg_path:
                return

        self.extract_button.config(state='disabled')
        self.progress.start(10)
        self.status_label.config(text="Extracting audio...", bootstyle="info")
        threading.Thread(target=self.extract_audio_files, daemon=True).start()

    def extract_audio_files(self):
        success_count = 0
        total_files = len(self.selected_files)
        last_output_path = None
        output_dir = self.output_folder.get() or None

        for i, input_file in enumerate(self.selected_files):
            try:
                input_path = Path(input_file)
                out_path = Path(output_dir) if output_dir else input_path.parent
                out_path.mkdir(parents=True, exist_ok=True)
                output_file = out_path / f"{input_path.stem}.{self.output_format.get()}"

                status_msg = f"Processing {i+1}/{total_files}: {input_path.name}"
                self.root.after(0, self.status_label.config, {"text": status_msg})

                cmd = [self.ffmpeg_path, '-i', str(input_path), '-vn', '-y']
                acodec_map = {'mp3': 'libmp3lame', 'wav': 'pcm_s16le', 'flac': 'flac', 'aac': 'aac'}
                codec = acodec_map.get(self.output_format.get())
                if codec: cmd.extend(['-acodec', codec])
                cmd.append(str(output_file))

                result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)

                if result.returncode == 0:
                    success_count += 1
                    last_output_path = str(output_file)
                else:
                    self.root.after(0, lambda err=result.stderr: print(f"Error processing {input_file}: {err}"))
            except Exception as e:
                self.root.after(0, lambda err=e: print(f"Error processing {input_file}: {err}"))

        self.root.after(0, self.extraction_complete, success_count, total_files, last_output_path)

    def extraction_complete(self, success_count, total_files, last_output_path):
        self.progress.stop()
        self.extract_button.config(state='normal')
        output_folder = str(Path(last_output_path).parent) if last_output_path else None

        if success_count == total_files and success_count > 0:
            status_text = f"Success! Extracted audio from all {total_files} files."
            self.status_label.config(text=status_text, bootstyle="success")
            self.show_completion_dialog("Extraction Complete", status_text, output_folder, last_output_path if total_files == 1 else None)
        elif success_count > 0:
            status_text = f"Completed with issues: {success_count}/{total_files} successful."
            self.status_label.config(text=status_text, bootstyle="warning")
            self.show_completion_dialog("Partial Success", f"Extracted {success_count}/{total_files} files.", output_folder, None)
        else: # success_count == 0
            status_text = f"Failed to extract audio from any of the {total_files} files."
            self.status_label.config(text=status_text, bootstyle="danger")
            Messagebox.show_error("Could not extract audio from any file. Check console for details.", "Extraction Failed")

    def show_completion_dialog(self, title, message, output_folder, output_file):
        buttons = []
        if output_file:
            buttons.append("Play File:primary")
        if output_folder:
            buttons.append("Open Folder:secondary")
        buttons.append("Close:light")
        
        dialog = Messagebox.show_question(message, title=title, buttons=buttons)

        if dialog == "Play File":
            if output_file: open_path(output_file)
        elif dialog == "Open Folder":
            if output_folder: open_path(output_folder)

def main():
    # Use a modern, light theme initially
    root = ttk.Window(themename="sandstone")
    app = SpeedTakeGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
