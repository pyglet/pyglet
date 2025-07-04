import { loadPyodide } from "https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.mjs";

async function main() {
    const params = new URLSearchParams(window.location.search);
    const scriptName = params.get("script") || "main";
    const scriptPath = `/${scriptName}.py`;
    let pyodide = await loadPyodide();
    console.log("Pyodide Loaded.");
    await pyodide.loadPackage("pillow")

    const filesToLoad = [
        ["pyglet.zip", "/pyglet.zip"],
        ["resources.zip", "/resources.zip"],
        [scriptPath, `/${scriptPath}`],
    ];

    console.log("Loading project files.");
    for (const [url, path] of filesToLoad) {
        const res = await fetch(url);
        const data = await res.arrayBuffer();
        pyodide.FS.writeFile(path, new Uint8Array(data));
    }

    console.log("Loading python script.");

    try {
        const pythonBoot = `
import sys, zipfile, os
sys.path.append("/")
with zipfile.ZipFile("/pyglet.zip") as z: z.extractall("/")
with zipfile.ZipFile("/resources.zip") as z: z.extractall("/home/pyodide/")
exec(open("/${scriptPath}").read())
    `;

        await pyodide.runPythonAsync(pythonBoot);

        console.log("Pyglet finished loading.")

        let result = pyodide.runPython(`
        import pyglet
        pyglet.version
    `);

        document.getElementById("output").innerText = "Pyglet Version: " + result;
    } catch (err) {
        console.error(err)
        document.getElementById("output").innerText = "Error loading script: " + (err.message || err.toString());
    }
}

main();