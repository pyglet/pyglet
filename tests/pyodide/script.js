import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.29.4/full/pyodide.mjs";
import { installPygletEmscripten } from "./pyglet_emscripten.js";

async function main() {
    const pyodide = await loadPyodide();
    console.log("Pyodide Loaded.");
    await installPygletEmscripten(pyodide);
    await pyodide.loadPackage(["pillow", "pytest"]);

    const filesToLoad = [
        ["pyglet.zip", "/pyglet.zip"],
        ["tests.zip", "/tests.zip"],
        ["pytest_runner.py", "/pytest_runner.py"],
    ];

    console.log("Loading Pyodide test files.");
    for (const [url, path] of filesToLoad) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`Failed to load ${url}: HTTP ${response.status}`);
        }
        const data = await response.arrayBuffer();
        pyodide.FS.writeFile(path, new Uint8Array(data));
    }

    try {
        await pyodide.runPythonAsync(`
import sys, zipfile
sys.path.append("/")
with zipfile.ZipFile("/pyglet.zip") as archive:
    archive.extractall("/")
with zipfile.ZipFile("/tests.zip") as archive:
    archive.extractall("/")
import pyglet
exec(open("/pytest_runner.py").read())
        `);

        const exitCode = pyodide.globals.get("PYGLET_PYTEST_EXIT_CODE");
        document.getElementById("output").innerText = "Pytest Exit Code: " + exitCode;
    } catch (error) {
        console.error(error);
        document.getElementById("output").innerText = "Error loading tests: " + (error.message || error.toString());
    }
}

main();
