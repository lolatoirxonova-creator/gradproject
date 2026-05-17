# Streamlit Demo

## Run

From the repo root:

```bash
source .venv/bin/activate
streamlit run app/main.py
```

The app opens at http://localhost:8501.

## Prerequisites

You must have run notebooks 02–04 first to generate the model artefacts:

- `models/content_based_vectorizer.pkl`
- `models/content_based_item_tfidf.npz`
- `models/cf_als_model.pkl`
- `models/hybrid_config.pkl`

If any are missing the app shows a clear error pointing to the missing file.

## Deploy to Streamlit Community Cloud (free)

1. Push the repo to GitHub (the dataset is gitignored — see `.streamlit/config.toml` for memory limits).
2. Go to https://streamlit.io/cloud, connect the GitHub repo, choose `app/main.py` as the entry point.
3. Set `requirements.txt` as the dependency file.
4. **Memory limit on free tier is 1 GB.** Reduce the training sample size in the sidebar if you hit OOM.

## Recording the live demo (backup for the oral defence)

If the cloud demo fails during your viva, you should have a video backup. Record on your local machine with QuickTime (macOS) or OBS:

```bash
streamlit run app/main.py
# in another terminal:
# QuickTime: File > New Screen Recording > select the browser window
```

Save the recording to `outputs/demo_recording.mp4` (gitignored).
