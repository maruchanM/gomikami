/// <reference lib="webworker" />
import harnessSrc from "./python/harness.py?raw";

const PYODIDE_URL = "https://cdn.jsdelivr.net/pyodide/v314.0.7/full/";

const pyodideReady = (async () => {
  const { loadPyodide } = await import(/* @vite-ignore */ `${PYODIDE_URL}pyodide.mjs`);
  const py = await loadPyodide({ indexURL: PYODIDE_URL });
  py.FS.writeFile("/home/pyodide/gk_harness.py", harnessSrc);
  py.runPython("import sys; sys.path.insert(0, '/home/pyodide')");
  const harness = py.pyimport("gk_harness");
  postMessage({ type: "ready" });
  return harness;
})();
pyodideReady.catch((err) => postMessage({ type: "load-error", error: String(err) }));

self.onmessage = async (e: MessageEvent) => {
  const { id, kind, payload } = e.data;
  try {
    const harness = await pyodideReady;
    const out: string = kind === "run" ? harness.js_run(JSON.stringify(payload)) : harness.js_analyze(payload);
    postMessage({ type: "result", id, ok: true, result: JSON.parse(out) });
  } catch (err) {
    postMessage({ type: "result", id, ok: false, error: String(err) });
  }
};
