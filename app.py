import os
import logging
from flask import Flask, render_template, send_file, request, redirect, url_for
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from PIL import Image
from io import BytesIO
from urllib.parse import unquote
import requests
from openai import OpenAI

app = Flask(__name__)

# Configure caching
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Configure rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per minute"],
    storage_uri="memory://"
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.route('/')
def index():
    return render_template('index.html')

@cache.memoize(timeout=300)  # Cache for 5 minutes
def generate_image_with_text(prompt, width=1024, height=1024, style="vivid"):
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=f"{width}x{height}",
            quality="standard",
            n=1,
            style=style
        )

        image_url = response.data[0].url
        image_data = requests.get(image_url).content
        image = Image.open(BytesIO(image_data))
        return image
    except Exception as e:
        logger.error(f"Error generating image with DALL-E 3: {str(e)}")
        raise

@app.route('/generate', methods=['GET', 'POST'])
@app.route('/generate/<path:prompt>', methods=['GET'])
@limiter.limit("5 per minute")
def generate_image(prompt=None):
    try:
        if request.method == 'POST':
            prompt = request.form['prompt']
            width = int(request.form.get('width', 1024))
            height = int(request.form.get('height', 1024))
            style = request.form.get('style', 'vivid')
            return redirect(url_for('generate_image', prompt=prompt, width=width, height=height, style=style))

        # Get parameters from URL for GET requests
        width = int(request.args.get('width', 1024))
        height = int(request.args.get('height', 1024))
        style = request.args.get('style', 'vivid')

        # If prompt is not in the URL path, check if it's in the query string
        if prompt is None:
            prompt = request.args.get('prompt')

        # If prompt is still None, return an error
        if prompt is None:
            return "Error: No prompt provided", 400

        # Decode the URL-encoded prompt
        decoded_prompt = unquote(prompt)
        
        # Generate the image using the cached function
        image = generate_image_with_text(decoded_prompt, width, height, style)
        
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
    return render_template('index.html', error="Invalid path. Please use /generate/<prompt> or /generate?prompt=<prompt> to generate an image."), 404

@app.errorhandler(429)
def ratelimit_handler(e):
    return "Rate limit exceeded. Please try again later.", 429

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
