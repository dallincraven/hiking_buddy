from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from PIL import Image as PILImage

def create_hike_pdf(output_path, df, chart_paths, photo_paths, stats):
    doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    story = []
    # Cover
    story.append(Paragraph(stats.get("title", "Hike Report"), styles["Title"]))
    if stats.get("author"):
        story.append(Paragraph(f"By {stats['author']}", styles["Normal"]))
    story.append(Spacer(1, 12))
    from datetime import datetime
    story.append(Paragraph(f"Generated: {datetime.today().strftime('%B %d, %Y')}", styles["Normal"]))
    story.append(Spacer(1, 18))
    if stats.get("notes"):
        story.append(Paragraph("Notes:", styles["Heading2"]))
        story.append(Paragraph(stats["notes"], styles["BodyText"]))
    story.append(PageBreak())
    # Key stats
    story.append(Paragraph("Hike Summary", styles["Heading1"]))
    total_km = df['cum_km'].max() if 'cum_km' in df else 0
    elev_gain = (df['elevation'].dropna().max() - df['elevation'].dropna().min()) if 'elevation' in df else 0
    avg_speed = df['speed_kmh'].mean() if 'speed_kmh' in df else None
    data_table = [
        ["Distance (km)", f"{total_km:.2f}"],
        ["Elevation range (m)", f"{elev_gain:.0f}"],
        ["Average speed (km/h)", f"{avg_speed:.2f}" if avg_speed else "N/A"]
    ]
    t = Table(data_table, colWidths=[2.5*inch, 3.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e6f2ea')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(t)
    story.append(Spacer(1, 12))
    # Charts
    story.append(Paragraph("Charts", styles["Heading1"]))
    for cp in chart_paths:
        if cp:
            story.append(Image(cp, width=6.5*inch, height=3*inch))
            story.append(Spacer(1, 12))
    story.append(PageBreak())
    # Photos
    if photo_paths:
        story.append(Paragraph("Photos", styles["Heading1"]))
        for p in photo_paths:
            try:
                # resize image for PDF to max width
                im = PILImage.open(p)
                w, h = im.size
                ratio = w / float(h)
                desired_w = 6.5*inch
                desired_h = desired_w / ratio
                story.append(Image(p, width=desired_w, height=desired_h))
                story.append(Spacer(1, 12))
            except Exception:
                continue
    doc.build(story)






