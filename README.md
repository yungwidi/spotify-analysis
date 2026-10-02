# Spotify: from catalog data to musical patterns

Four executed, independent Jupyter notebooks demonstrate reproducible acquisition and cleaning, Pandas and SQL, statistics, PCA, clustering, content recommendations, regression, and model explainability. The project emphasizes honest evaluation over impressive-looking scores.

## Start here

Use a Conda-capable terminal (Anaconda Prompt on Windows). The project repository is [yungwidi/spotify-analysis](https://github.com/yungwidi/spotify-analysis).

```bash
git clone https://github.com/yungwidi/spotify-analysis.git spotify_analysis
cd spotify_analysis
conda env create -f environment.yml
conda activate spotify
python -m ipykernel install --sys-prefix --name spotify --display-name "Python (spotify)"
python scripts/download_data.py
python scripts/prepare_data.py
python scripts/validate_project.py
jupyter lab
```

Select **Python (spotify)** in Jupyter. Launch from the root. Notebooks verify the environment name. Scripts locate the root from their own file location and may be invoked from another working directory. No source code or notebook depends on a laptop-specific path. The assigned folder was `spotify_analysis`; the spelling `spotify_anaysis` in the request was treated as a typo, not a request to create a second project.

The downloader currently needs **no authentication or manual license acceptance**. It retrieves a pinned public Kaggle version over HTTPS, verifies SHA-256, extracts only `tracks.csv`, and reuses verified existing files. If connectivity fails, retry. If the hash changes, investigate the upstream version rather than disabling validation. The original archive is retained, including unused artist metadata; no unrelated datasets are joined. No Spotify API key is needed.

## Notebooks

| Notebook | Question and approach |
|---|---|
| [01 — Music trends](01_spotify_music_trends_analysis.ipynb) | How do audio characteristics and duration vary by release decade? Full-catalog Pandas and DuckDB aggregation, rank correlations, coverage plots, paired artist test and confidence interval. |
| [02 — Musical eras / clustering](02_spotify_musical_eras_clustering.ipynb) | Do audio groups resemble eras? Median imputation, scaling, PCA loadings and variance, K-Means for k=2–8, inertia/silhouette, original-unit profiles, decade composition, seed stability. |
| [03 — Recommendation engine](03_spotify_recommendation_engine.ipynb) | What sounds similar? Reusable `recommend_tracks(track_id, n, different_artist)` over 524,208 distinct artist/title entries, standardized cosine nearest neighbors, three examples, withheld-valence proxy versus random retrieval. |
| [04 — Popularity / hit modeling](04_spotify_popularity_hit_modeling.ipynb) | How much snapshot popularity is predictable? Artist-disjoint train/validation/test, median baseline, Ridge, gradient boosting with/without year, MAE/RMSE/R², error bands, permutation importance, artist-bootstrap uncertainty. |

All notebooks contain methodology, interpretations, caveats, and saved outputs. Run them in any order. Notebook 4 uses continuous popularity rather than inventing a universal hit threshold. They write small machine-readable summaries into `reports/`; PNGs and runtime validation records are generated locally and ignored by Git.

## Project structure

```text
spotify_analysis/
├── data/
│   ├── raw/                 # immutable archive, tracks.csv, manifest.json; ignored
│   └── processed/           # tracks.parquet and quality_report.json; ignored
├── scripts/
│   ├── download_data.py
│   ├── prepare_data.py
│   └── validate_project.py
├── 01_spotify_music_trends_analysis.ipynb
├── 02_spotify_musical_eras_clustering.ipynb
├── 03_spotify_recommendation_engine.ipynb
├── 04_spotify_popularity_hit_modeling.ipynb
├── reports/                 # small result/provenance JSON files; generated plots ignored
├── environment.yml
├── requirements.txt
├── .gitignore
└── README.md
```

## Dataset selection and provenance

Public candidates were compared for release history, a useful feature set, and a reproducible original source rather than maximum size or recency alone.

| Candidate | Strengths | Decision |
|---|---|---|
| [Yamac Eren Ay: Spotify Dataset 1921–2020, 600k+ Tracks, Kaggle](https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks) | Release dates, stable track/artist IDs, popularity, numeric audio descriptors; versioned public download | Selected as one coherent source for all four analyses. Historical, not current. |
| [Maharshi Pandya: Spotify Tracks, Hugging Face](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset) | 114,000 rows, genre and album metadata, audio descriptors, easy CSV access | No release date/year in the published schema; insufficient for era analysis without an extra source. |
| [Nidula Elgiriyewithana: Most Streamed Spotify Songs 2024, Kaggle](https://www.kaggle.com/dsv/8700156) | Newer streaming, playlist and reach metadata | Top-song selection and emphasis on platform success indicators are less suitable for broad audio clustering and would encourage leakage in popularity prediction. |

**Selected source:** Yamac Eren Ay, Kaggle version **1**. The actual table contains **586,672 rows** with release years **1900–2021**, despite the dataset title. A year of 1900 is retained as source metadata, not asserted to be a trustworthy original recording date. Charts suppress decade aggregates with fewer than 100 rows, while the SQL audit includes all rows with dates. The 2020s are incomplete.

**Important columns:** `id`, `name`, `artists`, `id_artists`, `release_date`, `popularity`, `duration_ms`, `explicit`, danceability, energy, key, loudness, mode, speechiness, acousticness, instrumentalness, liveness, valence, tempo, time signature. There is no track genre, album name, listening history, or popularity observation timestamp. Unused artist files are not extracted or joined.

**License metadata:** Kaggle lists **Community Data License Agreement – Sharing – Version 1.0**. See the [source listing](https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks) and [license text](https://cdla.dev/sharing-1-0/). Attribution and the listed license should accompany any redistribution of the data; this repository distributes acquisition code rather than the dataset. Public access is not a grant to redistribute audio; no audio files are downloaded.

**Local sizes (decimal MB):** archive **201.98 MB**, extracted original CSV **111.37 MB**, processed Parquet **75.47 MB**; total data storage approximately **388.82 MB**. The automatic manifest records the source URL, version, hashes, and exact bytes.

| Artifact | SHA-256 |
|---|---|
| Version-1 ZIP | `bf134f6d3087c311c1b80a9ef7d56d868dc8b076197008eb344c138a4f14e865` |
| Original tracks.csv | `8a08c199bd93438783e915470ec3ea1142c1267f2da48b7d1315d2b9f5d39cf9` |

## Cleaning and analytical decisions

`prepare_data.py` checks the raw hash and required schema, normalizes text spacing, parses artist lists and mixed-precision dates, audits duplicates and numeric ranges, and writes a separate Parquet table. It does not fit statistical preprocessing globally for supervised use.

- **586,672 → 586,601 rows:** 71 missing names removed; no exact-row or Spotify-ID duplicates found.
- **328 zero tempos** become missing; each notebook's pipeline imputes medians when appropriate. All other checked numerical values pass configured plausibility ranges. Integer key/mode are excluded from continuous distance models rather than treated as ordinal music features.
- **62,393 repeated artist/title rows** are retained in shared data, then deduplicated by first source occurrence for modeling and recommendation. Titles are case-folded for this grouping, but remasters with different names and hidden repeated recordings can remain. No acoustic fingerprints are available.
- **1,089 recordings exceed 20 minutes**; these may be real recordings and are retained. The duration histogram pools its visual tail, recommendation/modeling log-transform duration, and clustering excludes duration.
- **Three names contain replacement characters**; retain and flag them rather than inventing repairs. No invalid date parses were found. The source has no separate release-year column to cross-check; derived year comes solely from the date.
- Genre consistency cannot be audited because track genres are absent. No genre labels are inferred from cluster numbers.
- Clustering uses a seeded **30,000**-track sample; the recommender uses the whole deduplicated catalog. These are disclosed computational choices, not arbitrary dataset download limits.
- Regression restricts to single-artist recordings so group splitting prevents every modeled artist from crossing sets. There are **479,685** single-artist rows and **427,392** unique labeled artist/title entries before a seeded **100,000**-row sample. Training/validation/test contain **70,228 / 15,125 / 14,647** tracks and **21,345 / 4,575 / 4,575** artists.
- Models are selected using validation MAE. Test results and permutation diagnostics are not used for tuning. Training-only preprocessing is implemented inside pipelines. Year is available metadata but primarily captures cross-sectional recency effects; it is not a safe substitute for a prospective forecast design.

## Results from the executed snapshot

- **Trends:** acousticness falls and energy rises across much of the post-1940 catalog. Among **1,200** artists present in both the 1980s and 2010s, mean energy change is **+0.0491**, 95% paired-artist interval **[0.0387, 0.0594]**, p ≈ **7.36×10⁻²⁰**. This conditional association is not causal and may include reissue/survivorship effects.
- **Clustering:** **3 clusters**, silhouette **0.254**. Two PCA components explain **48.2%** of variance. Groups broadly reflect acoustic/low-energy, speech-heavy, and louder/energetic recordings. Decade/group normalized mutual information is **0.078**, so groups are weakly aligned with eras. Initialization stability ARI is **0.999**, which does not establish resampling stability.
- **Recommendation:** withheld-valence absolute difference averages **0.191** for retrieved tracks versus **0.318** for random eligible tracks across 80 queries. Query-bootstrap improvement interval is **[0.095, 0.157]**. This is a musical coherence proxy, not listener relevance or accuracy.
- **Popularity:** validation selected histogram gradient boosting with audio features and year. Test **MAE 10.232**, **RMSE 13.252**, **R² 0.407**; median baseline **MAE 14.302**, **RMSE 17.281**. Permuting year increases MAE by about **4.76**, far more than any audio feature. Test errors are much larger for rare highly popular tracks. Artist-weighted MAE is **10.434**, with bootstrap interval **[10.215, 10.651]**; this is a different weighting from headline track-level MAE.

## Environment and Python 3.14 compatibility

The actual environment is **Conda `spotify`, CPython 3.14.7 (standard GIL build)**. Python 3.14 was usable; no fallback was necessary. [Conda-forge documents Python 3.14 availability](https://conda-forge.org/blog/2025/10/09/python-314/), and [scikit-learn documents support](https://scikit-learn.org/stable/install). Compatibility was established by installing binary wheels successfully, checking dependency consistency, and executing every notebook with the installed kernel—not merely by assuming a Python version range.

Pinned direct dependencies: NumPy 2.5.3, Pandas 3.0.6, Matplotlib 3.11.2, SciPy 1.18.1, scikit-learn 1.9.1, DuckDB 1.5.6, PyArrow 25.0.1, JupyterLab 4.6.4, ipykernel 7.3.0, nbformat 5.11.1, nbclient 0.11.0, and threadpoolctl 3.7.0. Explainability uses permutation importance, so SHAP and its additional dependency chain are unnecessary.

`environment.yml` defines Python, pip, and the same direct dependency versions as `requirements.txt`. The latter supports reinstalling packages in an existing Python 3.14.7 environment:

```bash
conda activate spotify
python -m pip install -r requirements.txt
python -m pip check
```

These are portable direct-version pins, not an operating-system-specific Conda export or a fully locked transitive dependency graph. Dependencies and wheels must remain available upstream. BLAS/platform differences may slightly alter numerical results. No other computer has been physically tested; the environment recipe was solved on this Windows host. Allow roughly 3 GB free space for environment/cache/data and preferably 8 GB RAM. This run took under one minute for notebook execution after setup, but machine performance varies.

## Git and reproducibility

Raw and processed datasets are deliberately ignored: the 111 MB CSV is impractical for ordinary GitHub Git storage, and the archive/Parquet would inflate history unnecessarily. They can be reconstructed from a versioned original source. `.gitkeep` preserves directories. Source code, environment definitions, notebooks (about 1 MB combined, including figures), small provenance and result summaries, and this README are the intended version-controlled artifacts. Git LFS is unnecessary.

The repository also ignores notebook checkpoints, Python caches, editor state, `.env` files, generated PNGs/HTML, and `.runtime/`. Automated notebook execution creates project-local transient Jupyter/IPython/Matplotlib state inside `.runtime/`; kernel connection files must never be committed. The environment and kernelspec are local installations and are recreated on the next machine.

Before publishing updates, review `git status`, add the intended source files, commit, and push to your remote. After cloning or pulling on the other PC, use the setup workflow above. If `spotify` already exists there, use `conda env update -n spotify -f environment.yml` and reinstall the kernel rather than attempting to create a duplicate environment.

## Validation and known limits

Validation completed:

1. Verified source accessibility and successfully tested the script's actual fresh-download branch in an empty project-local directory, then its verified-cache path.
2. Parsed the original CSV, ran preparation, checked raw immutability, generated Parquet and audited row counts/ranges.
3. Installed and registered the named environment/kernel; dependency consistency check passed.
4. Executed all four notebooks independently from top to bottom. SQL/Pandas counts and artist-disjoint splits are asserted. Recommender self-exclusion and unknown-ID handling are checked.
5. Inspected analytical outputs and charts; corrected execution issues and reran affected notebooks. The final validation record reports cell stderr as well as status and figure counts.
6. Checked relative-path portability, environment pins, Git exclusions, and source files for accidental secrets and machine-specific paths.
7. Reconstructed the project in a separate empty local folder using freshly downloaded raw data and copies of the source files. All four notebooks passed there; processed Parquet bytes and all analytical result JSON files matched exactly. This used the same installed environment and is not a second-OS validation. The temporary reconstruction folder was removed afterward; `reports/reproducibility.json` preserves the outcome.

Repeat with `python scripts/validate_project.py`. It stops on the first failed cell, saves executed notebooks, extracts plots for inspection, and writes `reports/validation.json`. All randomness uses seed 42 except the explicitly labeled clustering seed-stability comparison (43). The validator uses the Windows selector event loop where needed and requests supported kernel transport encryption; these avoid runtime warnings without changing system configuration.

The source is historical and selected, not a probability sample. Popularity collection time is not provided. Metadata may misdate reissues, duplicated recordings can survive title-based matching, and spoken audio is present. Confidence intervals are conditional on this catalog and stated sampling unit. No causation, true-genre recovery, user-preference accuracy, or prospective hit-detection claim is justified. A future study should add dated listening outcomes and human recommendation judgments using defensible identifiers.
