"""Execute all notebooks independently using the spotify kernel; fail on errors."""
from pathlib import Path
import base64
import json
import platform
import time
import os
import asyncio
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]

def main():
    # Keep transient execution state inside this checkout, including on Windows.
    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True)
    os.environ["IPYTHONDIR"] = str(runtime / "ipython")
    os.environ["JUPYTER_RUNTIME_DIR"] = str(runtime / "jupyter")
    os.environ["MPLCONFIGDIR"] = str(runtime / "matplotlib")
    report_dir = ROOT / "reports"
    report_dir.mkdir(exist_ok=True)
    results = {"python": platform.python_version(), "notebooks": []}
    for path in sorted(ROOT.glob("0[1-4]_*.ipynb")):
        print(f"Executing {path.name}", flush=True)
        started = time.monotonic()
        notebook = nbformat.read(path, as_version=4)
        for cell in notebook.cells:
            cell.metadata.pop("execution", None)
        client = NotebookClient(notebook, timeout=900, kernel_name="spotify", record_timing=False, resources={"metadata": {"path": str(ROOT)}})
        client.km = client.create_kernel_manager()
        client.km.transport_encryption = "auto"
        if os.name == "nt":
            with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:
                runner.run(client.async_execute())
        else:
            client.execute()
        nbformat.validate(notebook)
        figures = 0
        stderr = []
        for cell in notebook.cells:
            for output in cell.get("outputs", []):
                if output.output_type == "stream" and output.name == "stderr":
                    stderr.append(output.text)
                if "image/png" in output.get("data", {}):
                    figures += 1
                    (report_dir / f"{path.stem}_{figures}.png").write_bytes(base64.b64decode(output.data["image/png"]))
        nbformat.write(notebook, path)
        result = {"notebook": path.name, "seconds": round(time.monotonic()-started, 1), "figures": figures, "stderr": stderr, "status": "passed"}
        results["notebooks"].append(result)
        print(json.dumps(result), flush=True)
    if len(results["notebooks"]) != 4:
        raise RuntimeError("Expected exactly four notebooks.")
    (report_dir / "validation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
