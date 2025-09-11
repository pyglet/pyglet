"""Helper script to create a simple pyodide output for testing.

This will zip up the pyglet source directory as well as resources specified in the RESOURCE_LIST and transfer
them to your pyodide directory. (Note: Your script can only access resources that are within the pyodide
virtual directory, which the resources will insert.)

Ensure http is running for pyodide (Run ``python -m http.server`` in your pyodide folder).

Manually launch your browser and visit: http://localhost:8000/index.html?script=name or enable LAUNCH_BROWSER_AFTER
option below.

You can test multiple files by changing the SCRIPT_FILENAME and changing the script=parameter to the script name.
"""
from __future__ import annotations

# ==== Edit the below options
SCRIPT_PATH = "."
SCRIPT_FILENAME = "example.py"

# Resources you want to include with your script (relative from script_path)
RESOURCE_LIST = [
    '../../examples/resources/pyglet.png',
]

# The target path of the pyglet directory.
PYGLET_FOLDER = "../../pyglet"

# The folder with your pyodide install.
PYODIDE_FOLDER = "../../../pyodide"

# Port to use for HTTP (by default, 8000)
PORT = 8000

# Launches default browser after this runs.
LAUNCH_BROWSER_AFTER = True

# ===========================================

import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import zipfile  # noqa: E402
import socket  # noqa: E402
import webbrowser  # noqa: E402

zip_filename = "pyglet.zip"
zip_resource_filename = "resources.zip"

def zip_list(path_list, filename):
    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filepath in path_list:
            path = os.path.join(SCRIPT_PATH, filepath)
            arcname = os.path.basename(path)
            zipf.write(path, arcname)

def zip_folder(folder, zip_filename):
    folder_name = os.path.basename(folder)
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.join(folder_name, os.path.relpath(file_path, folder))
                zipf.write(file_path, arcname)
    print(f"Zipped {folder} -> {zip_filename}")

def move_zip(filename, to_folder):
    os.makedirs(to_folder, exist_ok=True)
    dest = os.path.join(to_folder, filename)
    if os.path.exists(dest):
        os.remove(dest)
    shutil.move(filename, dest)
    print(f"Moved {filename} to {dest}")

def extract_python_script():
    future_lines = []
    code_lines = []
    def format_line(line):
        if re.search(r'f"[^"]*?\n[^"]*?"', line):
            line = line.replace('f"', 'f"""', 1).rstrip().rstrip('"') + '"""'
        return line

    with open(os.path.join(SCRIPT_PATH, SCRIPT_FILENAME), 'r') as s:
        for line in s:
            if line.startswith("from __future__"):
                future_lines.append(line)
            else:
                formatted = line.replace('\\', '\\\\').replace('`', "'")
                code_lines.append(format_line(formatted))

    return "".join(future_lines), "".join(code_lines)

def write_main_py(futures, code):
    with open(os.path.join(PYODIDE_FOLDER, SCRIPT_FILENAME), "w", encoding="utf-8") as f:
        f.write(futures + "\n" + code)
    print(f"{SCRIPT_FILENAME} written.")

gen_path = os.curdir

source_files = ["index.html", "script.js", "dev_style.css"]

def move_file(name):
    src = os.path.join(gen_path, name)
    dst = os.path.join(PYODIDE_FOLDER, name)
    shutil.copyfile(src, dst)
    print(f"{name} copied.")

def is_server_running(port: int = PORT) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0

def launch_browser(script: str) -> None:
    url = f"http://localhost:8000/index.html?script={os.path.splitext(script)[0]}"
    print(f"Opening browser to {url}")
    webbrowser.open(url)


if __name__ == "__main__":
    zip_folder(PYGLET_FOLDER, zip_filename)
    zip_list(RESOURCE_LIST, zip_resource_filename)
    move_zip(zip_filename, PYODIDE_FOLDER)
    move_zip(zip_resource_filename, PYODIDE_FOLDER)

    futures, code = extract_python_script()
    write_main_py(futures, code)

    for filename in source_files:
        move_file(filename)

    if not is_server_running():
        print("HTTP server not detected.")
    else:
        print("HTTP server already running.")

    if LAUNCH_BROWSER_AFTER:
        launch_browser(SCRIPT_FILENAME)
