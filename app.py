import os
import uuid
import shutil
from flask import Flask, render_template, request, url_for, redirect
from utils.gpx_parser import parse_gpx_to_df
from utils.chart_maker import make_elevation_chart, make_pace_chart
from utils.pdf_generator import create_hike_pdf

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

for d in (UPLOAD_DIR, CHARTS_DIR, REPORTS_DIR):
    os.makedirs(d, exist_ok=True)
    
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 *1024 #50 MB max upload

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    gpx_file = request.files.get("gpx")
    images = request.files.get("title", "Untitled Hike")
    notes = request.form.get("notes","")
    author = request.form.get("author","")
    
    if not gpx_file:
        return "No GPX file uploaded", 400
    
    #create unique working directory for this job
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(UPLOAD_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    try:
        gpx_path = os.path.join(job_dir, f"track{os.path.splitext(gpxfile.filename)[1]}")
        gpx_file.save(gpx_path)
        
        #save images
        image_paths = []
        for i, img in enumerate(images):
            if img and img.filename:
                ext = os.path.splitext(img.filename)[1]
                img_path = os.path.join(job_dir, f"photo_{i}{ext}")
                img.save(img_path)
                image_paths.append(img_path)
                
        df = parse_gpx_to_df(gpx_path)
        
        #make charts
        elev_chart = make_elevation_chart(df, CHARTS_DIR, job_id)
        pace_chart = make_pace_chart(df, CHARTS_DIR, job_id)
        
        #generate pdf
        pdf_filename = f"hike_report_{job_id}.pdf"
        pdf_path = os.path.join(REPORTS_DIR, pdf_filename)
        stats = {
            "title": title,
            "author": author,
            "notes": notees
        }
        create_hike_pdf(pdf_path, df, [elev_chart, pace_chart], image_paths, stats)
        return redirect(url_for("result", job_id=job_id, pdf=pdf_filename))
    except Exception as e:
        shutil.rmtree(job_dir, ignore_errors=True)
        return f"Error processing file: {e}", 500
    