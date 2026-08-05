/**
 * Create the JavaScript module used by pyglet's Python-side Emscripten bridge.
 *
 * The returned object can be registered manually with
 * `pyodide.registerJsModule("pyglet_emscripten", module)`. Most launchers can
 * use `installPygletEmscripten` below instead.
 */
export function createPygletEmscriptenModule(pyodide) {
    const mountedIDBFS = new Set();
    const mountedOPFS = new Map();

    const syncIDBFS = (populate) => new Promise((resolve, reject) => {
        pyodide.FS.syncfs(populate, error => error ? reject(error) : resolve());
    });

    return {
        async mount_idbfs(path) {
            if (mountedIDBFS.has(path)) {
                return;
            }
            pyodide.FS.mkdirTree(path);
            pyodide.FS.mount(pyodide.FS.filesystems.IDBFS, {}, path);
            await syncIDBFS(true);
            mountedIDBFS.add(path);
        },

        async sync_idbfs() {
            await syncIDBFS(false);
        },

        async mount_opfs(path) {
            if (mountedOPFS.has(path)) {
                return;
            }
            if (!navigator.storage?.getDirectory) {
                throw new Error("This browser does not support OPFS cache storage.");
            }
            pyodide.FS.mkdirTree(path);
            const directory = await navigator.storage.getDirectory();
            const { syncfs } = await pyodide.mountNativeFS(path, directory);
            await syncfs();
            mountedOPFS.set(path, syncfs);
        },

        async sync_opfs() {
            await Promise.all([...mountedOPFS.values()].map(syncfs => syncfs()));
        },

        unmount_idbfs(path) {
            if (!mountedIDBFS.delete(path)) {
                return;
            }
            pyodide.FS.unmount(path);
        },
    };
}

/**
 * Register pyglet's JavaScript bridge and prepare its standard storage mounts.
 *
 * Set either path to `null` when a launcher wants to configure that storage
 * area itself. Mounting completes before this function returns, so Python can
 * immediately read previously saved data.
 */
export async function installPygletEmscripten(
    pyodide,
    { dataPath = "/data", cachePath = "/cache" } = {},
) {
    const module = createPygletEmscriptenModule(pyodide);
    pyodide.registerJsModule("pyglet_emscripten", module);

    if (dataPath !== null) {
        await module.mount_idbfs(dataPath);
    }
    if (cachePath !== null) {
        await module.mount_opfs(cachePath);
    }
    return module;
}
