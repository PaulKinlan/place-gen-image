import os
import logging
from flask import Flask, render_template, send_file, request, redirect, url_for
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from urllib.parse import unquote

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def generate_image_with_text(prompt, width=400, height=300):
    # Create a new image with a white background
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)

    # Use a default font
    font = ImageFont.load_default()

    # Draw the prompt text on the image
    draw.text((10, 10), prompt, fill='black', font=font)

    return image

@app.route('/generate', methods=['GET', 'POST'])
@app.route('/generate/<path:prompt>', methods=['GET'])
def generate_image(prompt=None):
    try:
        if request.method == 'POST':
            prompt = request.form['prompt']
            return redirect(url_for('generate_image', prompt=prompt))

        # Decode the URL-encoded prompt
        decoded_prompt = unquote(prompt) if prompt else "No prompt provided"
        
        # Generate the image using Pillow
        image = generate_image_with_text(decoded_prompt)
        
        # Convert the image to bytes
        img_io = BytesIO()
        image.save(img_io, 'PNG')
        img_io.seek(0)
        
        # Send the image as a response
        return send_file(img_io, mimetype='image/png')
    except Exception as e:
        logger.error(f"Error generating image: {str(e)}")
        return f"Error generating image: {str(e)}", 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('index.html', error="Invalid path. Please use /generate/<prompt> to generate an image."), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
