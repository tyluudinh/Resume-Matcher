from flask import Flask, request, jsonify

from scripts.similarity.get_score import *

from scripts.utils.logger import init_logging_config

from pypdf import PdfReader

init_logging_config(basic_log_level=logging.INFO)
# Get the logger
logger = logging.getLogger(__name__)

# Set the logging level
logger.setLevel(logging.INFO)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Resume Matcher API!"

@app.route('/get_score', methods=['POST'])
def get_score_api():
    # Parse the incoming JSON request body
    
    # if the request is application/json

    data = {}
    
    if request.is_json:
        data = request.get_json()
    # if the request is application/x-www-form-urlencoded
    elif request.form:
        data = request.form.to_dict()

    jd = data.get('jd', {})
    resume = data.get('resume', {})

    if 'file' in request.files:
        pdf_file = request.files['file']
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Only PDF files are allowed."}), 400
        try:
            pdf_text = extract_pdf_content(pdf_file)
            resume.update({"content_pdf_file": pdf_text})
        
        except Exception as e:
            return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500
    
    # Basic validation to ensure required fields are present
    if not jd or not resume:
        logger.error("Job description and resume data are required.")
        return jsonify({"error": "Job description and resume data are required."}), 400
    
    
    # Validate file type
    
    if type(jd) == str:
        jd = {
            "content": jd
        }
    
    score = calculate_score(jd, resume)
    
    # Return the score as a JSON response
    return jsonify({"score": score})

def extract_pdf_content(pdf_file):
    """
    Extracts text content from a PDF file.
    
    Parameters:
    - pdf_file: A file-like object containing the PDF.

    Returns:
    - str: Extracted text content from the PDF.
    """
    pdf_text = ""
    reader = PdfReader(pdf_file)

    for page in reader.pages:
        pdf_text += page.extract_text() + "\n"

    return pdf_text.strip()

def calculate_score(jd, resume):
    
    jd_text = extract_plaintext(jd)
    resume_text = extract_plaintext(resume)

    logger.info(f"JD Text: {jd_text}")
    logger.info(f"Resume Text: {resume_text}")

    result = get_score(resume_text, jd_text)
    logger.info(f"Result get_score: {result}")
    similarity_score = round(result[0].score * 100, 2)

    logger.info(f"Similarity Score: {similarity_score}%")
    
    return similarity_score

def extract_plaintext(object):
    """
    Extracts and concatenates all values from the object into a single plain text string.
    
    Parameters:
    - object (dict): A dictionary containing different sections of a object.

    Returns:
    - str: Plain text representation of the object content.
    """
    object_text = ""
    
    for section, content in object.items():
        if isinstance(content, str):
            object_text += content + "\n"
        elif isinstance(content, list):
            # Join list items if the section is a list of items (e.g., skills or projects)
            object_text += " ".join(content) + "\n"
        elif isinstance(content, dict):
            # Join sub-items if the section is a nested dictionary (e.g., employment_history details)
            object_text += " ".join([str(value) for value in content.values()]) + "\n"

    return object_text.strip()

if __name__ == '__main__':
    logger.info("Starting the API server...")
    app.run(debug=True, port=5000, host='0.0.0.0')
