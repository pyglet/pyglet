"""Temporary helper script to convert python script into pyodide for testing.

1) Zips up the pyglet source directory.
2) Zips up the resources defined in inject_resources list.
   Note: Your script can only access resources that are within the pyodide virtual directory, which the resources
   will insert.
3) Moves them to your pyodide folder.
4) Your script name will be created as script_name.html.
5) Make sure your pyodide server is running. (Run python -m http.server in your pyodide folder.)
6) Launch your browser and go to http://localhost:8000/script_name.html


"""
from __future__ import annotations
import re
import shutil
import os
import zipfile

# ==== EDIT THESE PATHS
script_path = "C:\\users\\Admin\\PycharmProjects\\pyglet-wasm\\"
script_filename = "noisy.py"
pyglet_folder = "C:\\Users\\Admin\\PycharmProjects\\pyglet-wasm\\pyglet"
pyodide_folder = "C:\\Users\\Admin\\PycharmProjects\\pyodide"

# Resources are searched from the script directory.
inject_resources = ['examples/media/noisy/ball.png',
                    'examples/media/noisy/ball.wav',
                    'examples/resources/pyglet.png']
# ======================

zip_filename = "pyglet.zip"
zip_resource_filename = "resources.zip"

# List of resources to zip.
def zip_list(path_list, filename):
    with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for filepath in path_list:
            path = os.path.join(script_path, filepath)
            arcname = os.path.basename(path)
            zipf.write(path, arcname)

# Zip pyglet folder
def zip_folder(folder, zip_filename):
    folder_name = os.path.basename(folder)  # Get the folder name itself
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                # Preserve full structure including the root folder
                arcname = os.path.join(folder_name, os.path.relpath(file_path, folder))
                zipf.write(file_path, arcname)
    print(f"Zipped {folder} (including folder) to {zip_filename}")

# Move the zip file
def move_zip(filename, to_folder):
    if not os.path.exists(to_folder):
        os.makedirs(to_folder)

    destination_file = os.path.join(to_folder, filename)

    # Remove existing file if it exists
    if os.path.exists(destination_file):
        os.remove(destination_file)

    shutil.move(filename, destination_file)
    print(f"Moved {filename} to {destination_file}")

zip_folder(pyglet_folder, zip_filename)
zip_list(inject_resources, zip_resource_filename)
move_zip(zip_filename, pyodide_folder)
move_zip(zip_resource_filename, pyodide_folder)

header_string = """
<!DOCTYPE html>
<html>
<head>

  <style>
    body {{
      background-color: #313338;
    }}
  </style>
<script type="module">
    import {{ loadPyodide }} from "https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.mjs";

    async function loadFont(fontUrl, fontName) {{
        const font = new FontFace(fontName, `url(${{fontUrl}})`);
        await font.load();
        document.fonts.add(font);
        return font;
    }}

    async function main() {{
        let pyodide = await loadPyodide();
        console.log("Pyodide Loaded!");
        await pyodide.loadPackage("pillow")

        // Mount local folder (requires a local server)
        let response = await fetch("pyglet.zip", {{ cache: "no-store" }});
        let arrayBuffer = await response.arrayBuffer();
        let uint8Array = new Uint8Array(arrayBuffer);

        // Write to Pyodide's filesystem
        pyodide.FS.writeFile("/pyglet.zip", uint8Array);

        // Mount local folder
        let response2 = await fetch("resources.zip", {{ cache: "no-store" }});
        let arrayBuffer2 = await response2.arrayBuffer();
        let uint8Array2 = new Uint8Array(arrayBuffer2);

        // Write to Pyodide's filesystem
        pyodide.FS.writeFile("/resources.zip", uint8Array2);

    await pyodide.runPythonAsync(`
{future_imports}
import sys, zipfile, shutil, os, js, pyodide
sys.path.append("/")

with zipfile.ZipFile("/pyglet.zip", "r") as zip_ref:
    zip_ref.extractall("/")  # Extracts mypackage/

with zipfile.ZipFile("/resources.zip", "r") as zip_ref:
    zip_ref.extractall("/home/pyodide/")

{python_code}
    `);

     let result = pyodide.runPython(`
        import pyglet
        pyglet.version
    `);

    console.log("Pyglet Loop has started.")

    document.getElementById("output").innerText = "Pyglet Version: " + result;
    }}

    main();
</script>

</head>
<body>
    <h2>Pyglet Pyodide Test</h2>
    <p id="output">Loading...</p>
</body>
</html>
"""

python_code_lines = []
future_lines = []

def format_line(line):
    # Check if it's an f-string with an embedded newline
    if re.search(r'f"[^"]*?\n[^"]*?"', line):
        # Change to f"""...""" and close it properly
        line = line.replace('f"', 'f"""', 1).rstrip().rstrip('"') + '"""'
    return line

with open(os.path.join(script_path, script_filename), 'r') as s:
    for line in s.readlines():
        if line.startswith("from __future__"):
            future_lines.append(line.replace('`', "'"))
            continue
        # Replace backticks so it doesn't interfere with pyodide.
        formatted = line.replace('\\', '\\\\').replace('`', "'")

        # Check and fix multiline f-strings
        formatted = format_line(formatted)

        # Add to parsed lines
        python_code_lines.append(formatted)

basename = os.path.splitext(script_filename)
destination_script_file = os.path.join(pyodide_folder, f"{basename[0]}.html")

joined = "".join(python_code_lines)
futures = "".join(future_lines)

with open(destination_script_file, "w") as f:
    f.write(header_string.format(python_code=joined, future_imports=futures))
