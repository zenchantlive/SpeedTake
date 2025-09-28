# SpeedTake Audio Extractor

SpeedTake is an extremely fast, simple, modern, and cross-platform graphical tool for quickly extracting audio from video files. Built with Python and `ttkbootstrap`, it offers a clean and intuitive user interface with both light and dark themes.

<img width="702" height="694" alt="image" src="https://github.com/user-attachments/assets/bed63019-ac99-4b0f-a5bc-489654f5ee28" />
 <!-- Replace with an actual screenshot URL -->

## Features

- **Simple & Fast:** Extract audio with just a few clicks.
- **Batch Processing:** Convert multiple files from a folder at once.
- **Multiple Formats:** Supports exporting to MP3, WAV, FLAC, and AAC.
- **Cross-Platform:** Works on Windows, macOS, and Linux.
- **Modern UI:** Clean, responsive interface with light and dark modes.
- **Standalone:** Can be run from a pre-built executable (for Windows) or directly from the Python script.
- **Dependency-Free (Almost):** Relies on the powerful and widely-available **FFmpeg** for audio processing.

---

## Getting Started

There are two ways to use SpeedTake: by running the Python script directly or by using the pre-built executable (Windows only).

### Method 1: Running the Python Script (Windows, macOS, Linux)

This is the recommended method for macOS and Linux users, and for Windows users who have Python installed.

#### **Step 1: Install FFmpeg**

FFmpeg is a crucial dependency that handles the audio extraction. You must install it on your system first.

**On Windows:**
- **Recommended (using a package manager):**
  1. Open PowerShell or Command Prompt.
  2. Use [Chocolatey](https://chocolatey.org/install): `choco install ffmpeg`
  3. Or use [Scoop](https://scoop.sh/): `scoop install ffmpeg`
- **Manual:**
  1. Download the latest "release" build from the [FFmpeg official website](https://ffmpeg.org/download.html).
  2. Unzip the downloaded file into a folder, for example, `C:\FFmpeg`.
  3. Add the `bin` directory from that folder (e.g., `C:\FFmpeg\bin`) to your system's `PATH` environment variable.

**On macOS:**
- **Recommended (using Homebrew):**
  1. Open the Terminal app.
  2. If you don't have Homebrew, install it from [brew.sh](https://brew.sh/).
  3. Run the command: `brew install ffmpeg`

**On Linux:**
- Open your terminal and use your distribution's package manager.
- **Debian/Ubuntu:** `sudo apt update && sudo apt install ffmpeg`
- **Fedora:** `sudo dnf install ffmpeg`
- **Arch Linux:** `sudo pacman -S ffmpeg`

#### **Step 2: Clone the Repository**

Open your terminal or command prompt and run the following command to download the application files:
```bash
git clone https://github.com/zenchantlive/SpeedTake.git
cd SpeedTake
```

#### **Step 3: Set Up a Virtual Environment**

It's best practice to create a virtual environment to manage the project's dependencies.

```bash
# Create the virtual environment
python -m venv .venv

# Activate it
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

#### **Step 4: Install Python Dependencies**

Install the required Python libraries using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

#### **Step 5: Run the Application**

You're all set! Launch the application by running:
```bash
python audio.py
```

---

### Method 2: Using the Executable (Windows Only)

If you are on Windows and prefer not to install Python, you can use the pre-built `.exe` file.

1.  **Install FFmpeg:** You still need to install FFmpeg as described in **Step 1** for Windows above. The application will not work without it.
2.  **Download the Executable:** Go to the [Releases page](https://github.com/zenchantlive/SpeedTake/releases) on this GitHub repository.
3.  **Run:** Download the `SpeedTake.exe` file and run it. No installation is needed.

## How to Use

1.  **Select Files:**
    - Click **"Add Files"** to select one or more video files.
    - Click **"Add Folder"** to add all video files from a specific folder.
    - Click **"Clear List"** to remove all files from the list.
2.  **Set Output Options:**
    - **Output Folder (Optional):** Choose a folder to save the extracted audio. If left blank, the audio files will be saved in the same directory as their source video files.
    - **Output Format:** Select your desired audio format (MP3, WAV, FLAC, or AAC).
3.  **Extract Audio:**
    - Click the **"Start Extraction"** button.
    - The progress bar will activate, and the status label will show which file is being processed.
4.  **Completion:**
    - Once finished, a dialog will appear confirming the result.
    - You will have the option to directly open the created file (if only one was processed) or the output folder.

## For Developers

If you want to build the executable from the source code yourself, you can use `pyinstaller`.

1.  Make sure you are in the activated virtual environment.
2.  Install `pyinstaller`: `pip install pyinstaller`
3.  Run the build command from the project root:
    ```bash
    pyinstaller --onefile --windowed --name SpeedTake --icon=your_icon.ico audio.py
    ```
    *(You will need to provide an icon file or remove the `--icon` flag.)*
