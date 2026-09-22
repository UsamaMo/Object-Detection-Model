# Object Lab

A browser GUI for the CP467 object recognition project by **Usama, Duc Minh Nguyen, and Quang Quynh Anh Lam**. Uses the existing 15 reference object images and 20 scene images with OpenCV SIFT matching and RANSAC homography verification. Runs on CPU; no training, GPU, API key, or model download is required.

## Run locally

Use Python 3.12–3.13. From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open **http://localhost:8000**. Keep the terminal running; press Ctrl+C to stop. In the environment already prepared by Codex, start directly with `.venv/bin/python app.py`.

On Windows, use `py` instead of `python3` and `.venv\Scripts\activate` instead of `source .venv/bin/activate`.

If port 8000 is occupied, use `PORT=8001 python app.py` on macOS/Linux and visit `http://localhost:8001`.

## Present the project

1. Open **Object detection**, select **Scene 1**, and click **Run detection**.
2. Switch between **Detection**, **Original**, and **Keypoints** to explain the pipeline.
3. Open **Matches** or a result row's **View matches** to inspect geometric inliers for each reference object.
4. Use **Download image** and **Export JSON** to save results for a report or presentation.
5. Open **Reference library** to show the 15 original object photos.
6. In **Panorama studio**, choose 2–6 overlapping scenes and click **Stitch selected scenes**. Uses affine stitching for the tabletop dataset. Success depends on overlap and camera viewpoint; failures explain how to try another selection.

You can upload a PNG, JPEG, or WebP scene (under 20 MB and at most 25 megapixels). Uploads are decoded in memory and are not stored on the server. Browser results are cleared on reload. Uploaded scenes are compared with the existing reference library.

## How detection works

`detector.py` resizes scenes to a maximum side of 1600 pixels, extracts SIFT features, applies Lowe's ratio test, removes duplicate destination matches, and estimates a RANSAC homography. A detection needs at least 7 inliers by default, an inlier ratio of at least 40%, and a finite, convex, plausible projected outline. The GUI exposes the match ratio and minimum inlier count.

The app identifies **these particular reference objects**, not arbitrary categories such as every cup or phone. Low texture, occlusion, reflections, large viewpoint changes, and nonplanar objects can cause missed or incorrect detections. An inlier ratio is geometric agreement, **not calibrated confidence**. JSON coordinates refer to the resized processing image, whose dimensions are included in the report.

Evaluation is optional: select the reference objects actually present in your scene to calculate precision, recall, F1, and object-presence accuracy over the 15-object library. The original notebooks' inconsistent ground truth is not treated as verified. No benchmark accuracy is claimed.

## Host the application

This app needs a Python server; GitHub Pages and other static-only hosts cannot run OpenCV. Hosting configuration uses Gunicorn, following [Flask's deployment guidance](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/).

For a Linux Python web service, set:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn --config gunicorn.conf.py app:app`
- Health check: `/health`
- Python: 3.13
- Port: supplied via the `PORT` environment variable (defaults to 8000)

Include `Objects/` and `Scenes/` in the deployed repository. A `Procfile` is provided for hosts that use it. Start with at least 1 GB RAM and increase it if needed for panoramas. The configured single worker allows one vision task at a time while serving other requests through threads; another concurrent analysis receives a retry message. No persistent volume is required. Use your host's HTTPS endpoint for sharing.

Alternatively, build and run the provided Docker image:

```bash
docker build -t object-lab .
docker run --rm -p 8000:8000 object-lab
```

Then open `http://localhost:8000`. The container runs as an unprivileged user. Docker packaging is supplied separately from the locally tested Python launch; building it requires Docker and network access. No public deployment has been created automatically.

## Notebooks and project layout

The notebooks now use the shared pipeline and work from either the project root or `Code/Code`. They can display and save detection, keypoint, matching, and panorama images. To use them:

```bash
python -m pip install -r Code/requirements.txt
jupyter lab
```

Select the virtual environment's Python kernel and open `Code/Code/Main.ipynb` or `Main_1.ipynb`.

- `app.py`: Flask API and local launcher.
- `detector.py`: image validation, SIFT matching, geometry checks, stitching, evaluation.
- `templates/`, `static/`: responsive web GUI; no JavaScript build step or external CDN required.
- `Objects/`, `Scenes/`: original datasets.
- `Detected_Objects/`, `Keypoints/`, `Matches/`: notebook export destinations. Their existing empty `test.py` files are placeholders, not launch scripts.
- `Code/Code/`: runnable notebooks. Original experiments remain available in Git history.
- `tests/`: regression tests.

## Verify

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Tests include controlled object localization, featureless scenes, malformed uploads/settings, invalid geometry, metric arithmetic, and panorama input/failure handling.

Algorithm reference: [OpenCV feature matching and homography tutorial](https://docs.opencv.org/4.12.0/d1/de0/tutorial_py_feature_homography.html).

For the optional browser smoke test, run the app in another terminal, then:

```bash
python -m pip install playwright
python -m playwright install chromium
python tests/browser_smoke.py
```

This checks detection, view switching, exports, evaluation, the object library, panorama stitching, uploads, and mobile overflow. It saves screenshots to ignored `artifacts/`.
