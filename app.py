import os
import logging
from flask import Flask, render_template, send_file, request
from diffusers import StableDiffusionPipeline
import torch
from io import BytesIO
from urllib.parse import unquote

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Stable Diffusion pipeline
model_id = "runwayml/stable-diffusion-v1-5"
pipe = None

def load_model():
    global pipe
    try:
        pipe = StableDiffusionPipeline.from_pretrained(model_id, torch_dtype=torch.float16)
        if torch.cuda.is_available():
            pipe = pipe.to("cuda")
        else:
            pipe = pipe.to("cpu")
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        pipe = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate/<path:prompt>')
def generate_image(prompt):
    global pipe
    if pipe is None:
        load_model()
    
    if pipe is None:
        return "Error: Unable to load the model. Please try again later.", 500

    try:
        # Decode the URL-encoded prompt
        decoded_prompt = unquote(prompt)
        
        # Generate the image
        image = pipe(decoded_prompt).images[0]
        
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
    load_model()
    app.run(host='0.0.0.0', port=5000, debug=True)
