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
    const memoryCaches = new Set();

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
            try {
                await syncIDBFS(true);
            } catch (error) {
                pyodide.FS.unmount(path);
                throw error;
            }
            mountedIDBFS.add(path);
        },

        async mount_cache(path, backend = "idbfs") {
            if (backend === "opfs") {
                await this.mount_opfs(path);
                return;
            }
            if (backend !== "idbfs") {
                throw new Error(`Unknown cache backend: ${backend}; expected idbfs or opfs.`);
            }
            if (memoryCaches.has(path)) {
                return;
            }
            try {
                await this.mount_idbfs(path);
            } catch (error) {
                console.warn(
                    `IndexedDB cache storage unavailable at ${path}: ${error?.message ?? error}. ` +
                    "Falling back to non-persistent memory cache; files will be lost on page reload.",
                );
                memoryCaches.add(path);
            }
        },

        async sync_idbfs() {
            await syncIDBFS(false);
        },

        async mount_opfs(path) {
            if (mountedOPFS.has(path)) {
                return;
            }
            pyodide.FS.mkdirTree(path);
            let mounted = false;
            try {
                if (globalThis.isSecureContext === false) {
                    throw new Error("the page is not a secure context; use HTTPS or localhost");
                }
                if (!globalThis.navigator?.storage?.getDirectory) {
                    throw new Error("the browser does not expose navigator.storage.getDirectory()");
                }
                const directory = await navigator.storage.getDirectory();
                const { syncfs } = await pyodide.mountNativeFS(path, directory);
                mounted = true;
                await syncfs();
                mountedOPFS.set(path, syncfs);
            } catch (error) {
                if (mounted) {
                    pyodide.FS.unmount(path);
                }
                console.warn(
                    `OPFS cache storage unavailable at ${path}: ${error?.message ?? error}. ` +
                    "Falling back to non-persistent memory cache; files will be lost on page reload.",
                );
                mountedOPFS.set(path, async () => {});
            }
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
 * Cache storage defaults to IDBFS. Set cacheBackend to "opfs" to opt into OPFS.
 */
export async function installPygletEmscripten(
    pyodide,
    { dataPath = "/data", cachePath = "/cache", cacheBackend = "idbfs" } = {},
) {
    if (cacheBackend !== "idbfs" && cacheBackend !== "opfs") {
        throw new Error(`Unknown cache backend: ${cacheBackend}; expected idbfs or opfs.`);
    }
    const module = createPygletEmscriptenModule(pyodide);
    pyodide.registerJsModule("pyglet_emscripten", module);

    if (dataPath !== null) {
        await module.mount_idbfs(dataPath);
    }
    if (cachePath !== null) {
        await module.mount_cache(cachePath, cacheBackend);
    }
    return module;
}
