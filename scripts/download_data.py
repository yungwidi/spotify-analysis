"""Retrieve and verify the immutable version-1 Kaggle snapshot (no credentials)."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
URL = "https://www.kaggle.com/api/v1/datasets/download/yamaerenay/spotify-dataset-19212020-600k-tracks?datasetVersionNumber=1"
SHA256 = "bf134f6d3087c311c1b80a9ef7d56d868dc8b076197008eb344c138a4f14e865"

def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()

def main():
    raw = ROOT / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    archive = raw / "spotify-v1.zip"
    if not archive.exists():
        temporary = archive.with_suffix(".part")
        print("Downloading public Kaggle dataset version 1...")
        try:
            request = urllib.request.Request(URL, headers={"User-Agent": "spotify-analysis/1.0"})
            with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
            if digest(temporary) != SHA256:
                raise ValueError("Snapshot checksum mismatch. Source may have changed; do not bypass verification.")
            temporary.replace(archive)
        finally:
            temporary.unlink(missing_ok=True)
    if digest(archive) != SHA256:
        raise ValueError("Existing archive checksum mismatch. Move the corrupt file aside and retry.")
    with zipfile.ZipFile(archive) as source:
        target = raw / "tracks.csv"
        expected = hashlib.sha256(source.read("tracks.csv")).hexdigest()
        if target.exists():
            if digest(target) != expected:
                raise ValueError("Raw tracks.csv changed: restore it from the verified archive.")
        else:
            with source.open("tracks.csv") as stream, target.open("wb") as output:
                shutil.copyfileobj(stream, output)
    manifest = raw / "manifest.json"
    metadata = {"url": URL, "version": 1, "archive_sha256": SHA256,
                "tracks_sha256": expected, "archive_bytes": archive.stat().st_size,
                "tracks_bytes": target.stat().st_size}
    serialized = json.dumps(metadata, indent=2)
    if not manifest.exists() or manifest.read_text(encoding="utf-8") != serialized:
        manifest.write_text(serialized, encoding="utf-8")
    print("Verified archive and original tracks.csv; existing raw data preserved.")

if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        sys.exit(f"Download failed: {error}. Check connectivity and the source URL in README.md.")
