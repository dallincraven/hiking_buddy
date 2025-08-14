import os
import uuid
import shutil
import tempfile
from pathlib import Path
from typing import List
from flask import Flask, render_template, request, url_for, redirect, send_from_directory, abort
from werkzeug.utils import secure_filename

from utils.gpx_parser import parse_gpx_to_df
from utils.chart_maker import make_elevation_chart, make_pace_chart
from utils.pdf_generator import create_hike_pdf

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
CHARTS_DIR = BASE_DIR / "charts"   # we’ll nest per-job inside here
REPORTS_DIR = BASE_DIR / "reports"

for d in (UPLOAD_DIR, CHARTS_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)
    
ALLOWED_GPX_EXTS = {".gpx"}
ALLOWED_IMG_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
app.config["UPLOAD_FOLDER"] = str(UPLOAD_DIR)
app.config["REPORTS_FOLDER"] = str(REPORTS_DIR)

def allowed_ext(filename: str, allowed: set) -> bool:
    return Path(filename).suffix.lower() in allowed
    
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 *1024 #50 MB max upload

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    # form fields
    title = request.form.get("title", "Untitled Hike").strip()
    notes = request.form.get("notes", "").strip()
    author = request.form.get("author", "").strip()

    # files
    gpx_file = request.files.get("gpx")
    images: List = request.files.getlist("images")  # requires <input type="file" name="images" multiple>

    if not gpx_file or not gpx_file.filename:
        return "No GPX file uploaded", 400

    if not allowed_ext(gpx_file.filename, ALLOWED_GPX_EXTS):
        return "Only .gpx files are allowed", 400

    job_id = str(uuid.uuid4())

    # per-job working dirs
    job_dir = UPLOAD_DIR / job_id
    charts_job_dir = CHARTS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    charts_job_dir.mkdir(parents=True, exist_ok=True)

    # ensure we always clean up job_dir on error
    try:
        # save GPX
        gpx_name = secure_filename(gpx_file.filename)
        gpx_ext = Path(gpx_name).suffix.lower() or ".gpx"
        gpx_path = job_dir / f"track{gpx_ext}"
        gpx_file.save(gpx_path)

        # save images (limit to, say, 20)
        image_paths: List[str] = []
        for i, img in enumerate(images[:20]):
            if not img or not img.filename:
                continue
            if not allowed_ext(img.filename, ALLOWED_IMG_EXTS):
                continue
            img_name = secure_filename(img.filename)
            img_ext = Path(img_name).suffix.lower()
            img_path = job_dir / f"photo_{i}{img_ext}"
            img.save(img_path)
            image_paths.append(str(img_path))

        # parse GPX -> df
        df = parse_gpx_to_df(str(gpx_path))

        # make charts; assume your utils accept (df, out_dir, job_id) per your original call
        # ensure charts are unique per job_id
        elev_chart = make_elevation_chart(df, str(CHARTS_DIR), job_id)
        pace_chart = make_pace_chart(df, str(CHARTS_DIR), job_id)

        # build pdf
        pdf_filename = f"hike_report_{job_id}.pdf"
        pdf_path = REPORTS_DIR / pdf_filename
        stats = {
            "title": title,
            "author": author,
            "notes": notes,
        }
        create_hike_pdf(str(pdf_path), df, [elev_chart, pace_chart], image_paths, stats)

        # optionally: cleanup job_dir and charts after PDF generation
        # shutil.rmtree(job_dir, ignore_errors=True)
        # shutil.rmtree(charts_job_dir, ignore_errors=True)

        return redirect(url_for("result", job_id=job_id, pdf=pdf_filename))

    except Exception as e:
        # log server-side, don’t leak stack to user in prod
        app.logger.exception("Error processing upload")
        shutil.rmtree(job_dir, ignore_errors=True)
        shutil.rmtree(charts_job_dir, ignore_errors=True)
        return "Error processing file", 500
    
@app.route("/result")
def result():
    job_id = request.args.get("job_id")
    pdf = request.args.get("pdf")
    if not job_id or not pdf:
        abort(400)
    return render_template("result.html", job_id=job_id, pdf=pdf)

@app.route("/reports/<path:filename>")
def download_report(filename):
    # sends from reports directory safely
    return send_from_directory(app.config["REPORTS_FOLDER"], filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
    