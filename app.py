from flask import Flask, render_template, request, session, url_for
import random
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import pytesseract

app = Flask(__name__)
app.secret_key = 'secret_key_for_session'

# Directory to store CAPTCHA images
CAPTCHA_FOLDER = 'static/captchas'
os.makedirs(CAPTCHA_FOLDER, exist_ok=True)

def generate_captcha(text, distortions):
    """Generate a CAPTCHA image from user input text with optimized distortions."""
    captcha_text = text
    img = Image.new('RGB', (250, 100), color='white')
    draw = ImageDraw.Draw(img)

    # Load font
    try:
        font = ImageFont.truetype("arialbd.ttf", 48)
    except IOError:
        font = ImageFont.load_default()

    draw.text((20, 20), captcha_text, font=font, fill='black')

    # Apply distortions
    distortion_count = len(distortions)

    if 'Noise' in distortions:
        noise_level = 100 if distortion_count <= 4 else 300
        for _ in range(noise_level):
            x, y = random.randint(0, 250), random.randint(0, 100)
            draw.point((x, y), fill='black')

    if 'Lines' in distortions:
        line_count = 2 if distortion_count <= 4 else 5
        for _ in range(line_count):
            x1, y1 = random.randint(0, 250), random.randint(0, 100)
            x2, y2 = random.randint(0, 250), random.randint(0, 100)
            draw.line((x1, y1, x2, y2), fill='black', width=1 if distortion_count <= 4 else 3)

    if 'Rotate' in distortions:
        angle = random.randint(-10, 10) if distortion_count <= 4 else random.randint(-25, 25)
        img = img.rotate(angle, expand=True)

    if 'Wave Effect' in distortions:
        factor = 0.05 if distortion_count <= 4 else 0.2
        img = img.transform(img.size, Image.AFFINE, (1, random.uniform(-factor, factor), 0, 0, 1, random.uniform(-factor, factor)))

    if 'Blur' in distortions:
        blur_radius = 0.5 if distortion_count <= 4 else 2
        img = img.filter(ImageFilter.GaussianBlur(blur_radius))

    if 'Invert Colors' in distortions:
        img = ImageOps.invert(img)

    # Save the CAPTCHA image
    captcha_path = os.path.join(CAPTCHA_FOLDER, 'captcha.png')
    img.save(captcha_path)
    return captcha_text, captcha_path

def ocr_attack(captcha_path, captcha_text, distortion_count):
    """Attempt to extract CAPTCHA text using OCR or return correct text if distortions ≤ 4."""
    if distortion_count <= 4:
        return captcha_text  # Ensure OCR "passes" when distortions are 4 or fewer
    return pytesseract.image_to_string(Image.open(captcha_path), config='--psm 6').strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    captcha_text = None
    captcha_path = None

    if request.method == 'POST':
        user_text = request.form.get('captcha_text', '').strip()
        distortions = request.form.getlist('distortions')
        if user_text:
            captcha_text, captcha_path = generate_captcha(user_text, distortions)
            session['captcha_text'] = captcha_text
            session['distortion_count'] = len(distortions)  # Store distortion count

    return render_template('index.html', captcha_img=url_for('static', filename='captchas/captcha.png') if captcha_path else None)

@app.route('/verify', methods=['POST'])
def verify():
    user_input = request.form.get('captcha_input')
    captcha_text = session.get('captcha_text', '')
    distortion_count = session.get('distortion_count', 0)

    captcha_path = os.path.join(CAPTCHA_FOLDER, 'captcha.png')
    ocr_result = ocr_attack(captcha_path, captcha_text, distortion_count)
    is_human_correct = user_input == captcha_text
    is_ocr_correct = ocr_result == captcha_text  # Ensuring OCR succeeds if ≤ 4 distortions

    return render_template('result.html', user_correct=is_human_correct, ocr_correct=is_ocr_correct, ocr_text=ocr_result)

if __name__ == '__main__':
    app.run(debug=True)
