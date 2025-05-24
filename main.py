from flask import Flask, request, render_template, jsonify, send_file
import html2text
import markdown
import pandas as pd
import io
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure Flask for large file uploads
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB in bytes
app.config['MAX_CONTENT_PATH'] = None  # No path length limit
app.config['UPLOAD_FOLDER'] = '/tmp'  # Temporary storage for uploads

def clean_email_html(html):
    if not isinstance(html, str):
        return ""
    
    try:
        handler = html2text.HTML2Text()
        handler.ignore_links = True
        handler.ignore_images = True
        handler.ignore_emphasis = False  # Keeps bold/italic if needed
        handler.body_width = 0  # Prevents line wrapping
        
        # Pre-process HTML to handle problematic content
        html = html.replace("</' + 'script>", "</script>")  # Fix broken script tags
        html = html.replace("' + '", "")  # Remove string concatenation artifacts
        
        return handler.handle(html).strip()
    except Exception as e:
        print(f"Error processing HTML: {str(e)}")
        return str(html)  # Return original content if processing fails

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/clean', methods=['POST'])
def clean_html_api():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if 'html' not in data:
        return jsonify({"error": "No HTML content provided"}), 400
    
    cleaned_text = clean_email_html(data['html'])
    rendered_html = markdown.markdown(cleaned_text)
    return jsonify({
        "cleaned_text": cleaned_text,
        "rendered_html": rendered_html
    })

@app.route('/clean', methods=['POST'])
def clean_html_web():
    html_content = request.form.get('html', '')
    if not html_content:
        return render_template('index.html', error="No HTML content provided")
    
    cleaned_text = clean_email_html(html_content)
    rendered_html = markdown.markdown(cleaned_text)
    return render_template('index.html', 
                         cleaned_text=cleaned_text,
                         rendered_html=rendered_html)

@app.route('/process-file', methods=['POST'])
def process_file():
    if 'file' not in request.files:
        return render_template('index.html', error="No file uploaded")
    
    file = request.files['file']
    column_name = request.form.get('column_name', 'raw_html')
    
    if file.filename == '':
        return render_template('index.html', error="No file selected")
    
    # Read the file based on its extension
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file)
    elif file.filename.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(file)
    else:
        return render_template('index.html', error="Unsupported file format. Please upload CSV or Excel file.")
    
    if column_name not in df.columns:
        return render_template('index.html', error=f"Column '{column_name}' not found in the file")
    
    # Process each row in the specified column
    df[f'Human Readable {column_name}'] = df[column_name].apply(clean_email_html)
    
    # Create output file
    output = io.BytesIO()
    if file.filename.endswith('.csv'):
        df.to_csv(output, index=False)
        mimetype = 'text/csv'
        extension = 'csv'
    else:
        df.to_excel(output, index=False)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        extension = 'xlsx'
    
    output.seek(0)
    
    # Generate a safe filename for download
    original_filename = secure_filename(file.filename)
    base_name = os.path.splitext(original_filename)[0]
    download_filename = f"{base_name}_processed.{extension}"
    
    return send_file(
        output,
        mimetype=mimetype,
        as_attachment=True,
        download_name=download_filename
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Default to 5000 if PORT not set
    app.run(host='0.0.0.0', port=port)

