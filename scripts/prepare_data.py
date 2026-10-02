"""Shared, deterministic cleaning; raw data is never overwritten."""
from pathlib import Path
import ast
import json
import pandas as pd
import numpy as np
from download_data import digest

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["danceability", "energy", "valence", "acousticness", "instrumentalness", "speechiness", "liveness", "loudness", "tempo", "duration_ms"]

def parse_list(value):
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
            return parsed
    except (ValueError, SyntaxError, TypeError):
        pass
    return []

def main():
    source = ROOT / "data/raw/tracks.csv"
    if not source.exists():
        raise SystemExit("Run python scripts/download_data.py first.")
    source_hash = digest(source)
    if source_hash != "8a08c199bd93438783e915470ec3ea1142c1267f2da48b7d1315d2b9f5d39cf9":
        raise ValueError("Raw source changed; restore the pinned snapshot using download_data.py.")
    tracks = pd.read_csv(source)
    required = set(FEATURES + ["id", "name", "artists", "id_artists", "release_date", "popularity"])
    if not required.issubset(tracks.columns):
        raise ValueError(f"Missing source columns: {required - set(tracks.columns)}")
    audit = {"raw_rows": len(tracks), "raw_sha256": source_hash, "missing_before": tracks.isna().sum().to_dict(), "exact_duplicates": int(tracks.duplicated().sum())}
    tracks = tracks.drop_duplicates().copy()
    audit["duplicate_ids"] = int(tracks.id.duplicated().sum())
    tracks = tracks.drop_duplicates("id", keep="first").copy()
    for column in ["id", "name"]:
        tracks[column] = tracks[column].astype("string").str.strip()
        tracks.loc[tracks[column].eq(""), column] = pd.NA
    artists = tracks.artists.map(parse_list)
    artist_ids = tracks.id_artists.map(parse_list)
    tracks["artist"] = artists.str.join("; ")
    tracks["primary_artist_id"] = artist_ids.str[0]
    audit["malformed_or_empty_artist_lists"] = int(artists.str.len().eq(0).sum())
    audit["replacement_character_names"] = int(tracks.name.str.contains("\ufffd", na=False).sum())
    dates = pd.to_datetime(tracks.release_date, format="mixed", errors="coerce")
    tracks["year"] = dates.dt.year
    invalid_date = tracks.year.isna() | ~tracks.year.between(1900, 2022)
    audit["invalid_dates"] = int(invalid_date.sum())
    tracks.loc[invalid_date, "year"] = np.nan
    audit["invalid_numeric"] = {}
    bounds = {feature: (0, 1) for feature in FEATURES[:7]}
    bounds.update({"loudness": (-60, 10), "tempo": (0, 300), "duration_ms": (1, np.inf), "popularity": (0, 100), "key": (-1, 11), "mode": (0, 1), "explicit": (0, 1), "time_signature": (0, 7)})
    for column, (lower, upper) in bounds.items():
        values = pd.to_numeric(tracks[column], errors="coerce")
        invalid = ~values.between(lower, upper) | ~np.isfinite(values)
        if column == "tempo":
            invalid |= values.eq(0)  # unknown tempo, not a measured 0 BPM
        audit["invalid_numeric"][column] = int(invalid.sum())
        tracks[column] = values.mask(invalid)
    unusable = tracks.id.isna() | tracks.name.isna() | tracks.primary_artist_id.isna()
    audit["removed_missing_identity"] = int(unusable.sum())
    tracks = tracks.loc[~unusable].copy()
    tracks["recording_group"] = tracks.artist.str.casefold() + " | " + tracks.name.str.casefold()
    audit["repeated_artist_title_rows"] = int(tracks.recording_group.duplicated().sum())
    tracks["duration_min"] = tracks.duration_ms / 60000
    tracks["decade"] = (tracks.year // 10 * 10).astype("Int64")
    audit["duration_over_20_minutes"] = int(tracks.duration_min.gt(20).sum())
    audit["year_min"] = int(tracks.year.min())
    audit["year_max"] = int(tracks.year.max())
    audit["processed_rows"] = len(tracks)
    audit["missing_after"] = tracks.isna().sum().to_dict()
    output = ROOT / "data/processed"
    output.mkdir(parents=True, exist_ok=True)
    tracks.to_parquet(output / "tracks.parquet", index=False)
    (output / "quality_report.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in audit.items() if not isinstance(value, dict)}, indent=2))

if __name__ == "__main__":
    main()
