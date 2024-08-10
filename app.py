from flask import Flask, render_template, request, redirect, url_for
import os
import fitz
from PIL import Image
import google.generativeai as genai
import PIL.Image
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# GenerativeAI model setup
genai.configure(api_key=apikey)
model = genai.GenerativeModel('models/gemini-1.5-flash')
result_text = None
# PDF to images function
def pdf_to_images(pdf_path, image_format="png", output_dir="images"):
    pdf_document = fitz.open(pdf_path)
    image_paths = []
    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        image = convert_pdf_page_to_image(page)
        filename = os.path.join(output_dir, f"page_{page_num + 1}.{image_format}")
        image.save(filename, format=image_format.upper())
        image_paths.append(filename)
    return image_paths

def convert_pdf_page_to_image(pdf_page):
    pix = pdf_page.get_pixmap()
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

# Route for homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for file upload
@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        pdf_file = request.files['pdf_file']
        if pdf_file and pdf_file.filename.endswith('.pdf'):
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
            pdf_file.save(pdf_path)
            # Convert PDF to images
            image_paths = pdf_to_images(pdf_path)
            # Generate MCQ questions
            string = ''
            model = genai.GenerativeModel('models/gemini-1.5-flash')
            for image_path in image_paths:
                result = model.generate_content(["""
                    Make MCQ questions for the given images with question, options and correctAnswer
                    """,PIL.Image.open(image_path)
                ])
                string+=result.text
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = '''send the given string in a proper format. Using this JSON schema:
                        Q = {"question": str,"options": list, "correctAnswer": str}. Return `list[Q]`''' + string
            response = model.generate_content(prompt)
            questions = json.loads(response.text[8:-4])
            global result_text 
            result_text = questions
            print(questions)
            return render_template('selection.html', questions = questions)
    return redirect(url_for('index'))

@app.route('/test_paper')
def test_paper():
    return render_template('test_paper.html', questions=result_text)

# Route for practice
@app.route('/practice')
def practice():
    return render_template('practice.html', questions=result_text)

if __name__ == '__main__':
    app.run(debug=True)
