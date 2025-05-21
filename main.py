from flask import Flask, request, render_template, jsonify
import html2text
import markdown

app = Flask(__name__)

def clean_email_html(html):
    handler = html2text.HTML2Text()
    handler.ignore_links = True
    handler.ignore_images = True
    handler.ignore_emphasis = False  # Keeps bold/italic if needed
    handler.body_width = 0  # Prevents line wrapping

    return handler.handle(html).strip()

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

