from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
from PIL import Image
import fitz
import os
import zipfile
import time

app = Flask(__name__)

os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)


@app.route("/")
def home():
    return render_template("index.html")


# ---------------- IMAGES TO PDF ----------------
@app.route("/img_to_pdf", methods=["POST"])
def img_to_pdf():
    files = request.files.getlist("images")
    image_list = []

    for file in files:
        path = os.path.join("uploads", file.filename)
        file.save(path)
        img = Image.open(path).convert("RGB")
        image_list.append(img)

    output_path = os.path.join("outputs", f"images_to_pdf_{int(time.time())}.pdf")
    image_list[0].save(output_path, save_all=True, append_images=image_list[1:])

    return send_file(output_path, as_attachment=True)


# ---------------- PDF TO IMAGES (RANGE) ----------------
@app.route("/pdf_to_img", methods=["POST"])
def pdf_to_img():
    pdf_file = request.files["pdf"]
    start = int(request.form["start"])
    end = int(request.form["end"])

    input_path = os.path.join("uploads", pdf_file.filename)
    pdf_file.save(input_path)

    doc = fitz.open(input_path)

    if start < 1 or end > len(doc):
        return "Invalid page range"

    zip_path = os.path.join("outputs", f"pdf_images_{int(time.time())}.zip")
    zipf = zipfile.ZipFile(zip_path, "w")

    for page_number in range(start - 1, end):
        page = doc.load_page(page_number)
        pix = page.get_pixmap()
        img_path = os.path.join("outputs", f"page_{page_number+1}.png")
        pix.save(img_path)
        zipf.write(img_path, os.path.basename(img_path))

    zipf.close()
    doc.close()

    return send_file(zip_path, as_attachment=True)


# ---------------- MERGE PDF ----------------
@app.route("/merge_pdf", methods=["POST"])
def merge_pdf():
    files = request.files.getlist("pdfs")
    writer = PdfWriter()

    for file in files:
        path = os.path.join("uploads", file.filename)
        file.save(path)
        reader = PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)

    output_path = os.path.join("outputs", f"merged_{int(time.time())}.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)

    return send_file(output_path, as_attachment=True)


# ---------------- SPLIT PDF (RANGE SINGLE FILE) ----------------
@app.route("/split_pdf", methods=["POST"])
def split_pdf():
    pdf_file = request.files["pdf"]
    start = int(request.form["start"])
    end = int(request.form["end"])

    input_path = os.path.join("uploads", pdf_file.filename)
    pdf_file.save(input_path)

    reader = PdfReader(input_path)
    writer = PdfWriter()

    if start < 1 or end > len(reader.pages):
        return "Invalid page range"

    for i in range(start - 1, end):
        writer.add_page(reader.pages[i])

    output_path = os.path.join("outputs", f"split_{int(time.time())}.pdf")
    with open(output_path, "wb") as f:
        writer.write(f)

    return send_file(output_path, as_attachment=True)


# ---------------- COMPRESS PDF ----------------
@app.route("/compress_pdf", methods=["POST"])
def compress_pdf():
    pdf_file = request.files["pdf"]
    level = request.form["level"]

    input_path = os.path.join("uploads", pdf_file.filename)
    pdf_file.save(input_path)

    doc = fitz.open(input_path)

    if level == "low":
        quality = 90
    elif level == "medium":
        quality = 70
    else:
        quality = 50

    output_path = os.path.join("outputs", f"compressed_{int(time.time())}.pdf")
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    return send_file(output_path, as_attachment=True)

#--------------- Footer--------------------

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")



if __name__ == "__main__":
    app.run(debug=True)
