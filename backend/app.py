from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image, ImageStat, UnidentifiedImageError
from datetime import datetime, timezone
from pathlib import Path
import io, os, uuid, json, csv

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_BYTES = 12 * 1024 * 1024

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{BASE_DIR / "retina_screening.db"}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = MAX_BYTES
db = SQLAlchemy(app)
CORS(app, resources={r'/api/*': {'origins': '*'}})

class Screening(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status = db.Column(db.String(40), nullable=False)
    quality = db.Column(db.String(40), nullable=False)
    image_width = db.Column(db.Integer, nullable=False)
    image_height = db.Column(db.Integer, nullable=False)
    result_json = db.Column(db.Text, nullable=False)
    mode = db.Column(db.String(30), default='demo', nullable=False)

    def as_dict(self):
        return {'id': self.public_id, 'filename': self.filename,
                'created_at': self.created_at.isoformat(), 'status': self.status,
                'quality': self.quality, 'width': self.image_width,
                'height': self.image_height, 'mode': self.mode,
                'result': json.loads(self.result_json)}

def allowed(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def inspect_image(file_storage):
    raw = file_storage.read()
    file_storage.seek(0)
    if not raw:
        raise ValueError('The uploaded file is empty.')
    if len(raw) > MAX_BYTES:
        raise ValueError('Image is too large. Maximum upload size is 12 MB.')
    try:
        image = Image.open(io.BytesIO(raw)).convert('RGB')
        image.load()
    except (UnidentifiedImageError, OSError):
        raise ValueError('Please upload a valid JPG, PNG, or WebP image.')
    width, height = image.size
    if width < 64 or height < 64:
        raise ValueError('Image is too small. Please use an image at least 64 × 64 pixels.')
    stats = ImageStat.Stat(image)
    brightness = sum(stats.mean) / 3
    contrast = sum(stats.stddev) / 3
    # Basic technical checks only; not a clinical image-quality assessment.
    quality = 'Review image quality'
    if 25 <= brightness <= 235 and contrast >= 12 and min(width, height) >= 128:
        quality = 'Basic checks passed'
    return image, width, height, quality

def demo_prediction(image):
    """Transparent placeholder. Replace with a trained, validated model before clinical use."""
    return {
        'mode': 'demo_simulation',
        'model_status': 'NOT_CONFIGURED',
        'headline': 'Demo screening only — no clinical prediction generated',
        'predicted_class': None,
        'confidence': None,
        'severity': 'Not assessed',
        'probabilities': [],
        'visual_notes': [
            'The image passed basic file and dimension checks.' ,
            'No trained retinal disease model is configured in this starter project.',
            'Do not use this demo output for diagnosis, treatment, or referral decisions.'
        ],
        'next_step': 'Connect a validated model and have results reviewed by a qualified eye-care professional.'
    }

@app.errorhandler(413)
def too_large(_error):
    return jsonify({'error': 'Image is too large. Maximum upload size is 12 MB.'}), 413

@app.get('/api/health')
def health():
    return jsonify({'status': 'ok', 'service': 'retina-screening-api', 'model_configured': False,
                    'message': 'API is running. Prediction endpoint currently uses a clearly labelled demo placeholder.'})

@app.post('/api/screenings')
def create_screening():
    if 'image' not in request.files:
        return jsonify({'error': 'Choose a fundus image before submitting.'}), 400
    upload = request.files['image']
    if not upload.filename:
        return jsonify({'error': 'Choose a file before submitting.'}), 400
    if not allowed(upload.filename):
        return jsonify({'error': 'Unsupported file type. Upload JPG, JPEG, PNG, or WebP.'}), 415
    try:
        image, width, height, quality = inspect_image(upload)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400
    public_id = str(uuid.uuid4())
    safe_name = secure_filename(upload.filename) or 'fundus-image'
    # Save a normalized JPEG copy for the local demo; do not expose uploads as public static files.
    image.save(UPLOAD_DIR / f'{public_id}.jpg', format='JPEG', quality=92)
    result = demo_prediction(image)
    record = Screening(public_id=public_id, filename=safe_name, status='demo_complete',
                       quality=quality, image_width=width, image_height=height,
                       result_json=json.dumps(result), mode='demo')
    db.session.add(record)
    db.session.commit()
    return jsonify(record.as_dict()), 201

@app.get('/api/screenings')
def list_screenings():
    rows = Screening.query.order_by(Screening.created_at.desc()).limit(100).all()
    return jsonify({'items': [row.as_dict() for row in rows]})

@app.get('/api/screenings/<public_id>')
def get_screening(public_id):
    row = Screening.query.filter_by(public_id=public_id).first()
    if not row:
        return jsonify({'error': 'Screening record not found.'}), 404
    return jsonify(row.as_dict())

@app.get('/api/screenings/<public_id>/report')
def screening_report(public_id):
    row = Screening.query.filter_by(public_id=public_id).first()
    if not row:
        return jsonify({'error': 'Screening record not found.'}), 404
    result = json.loads(row.result_json)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Field', 'Value'])
    writer.writerow(['Screening ID', row.public_id])
    writer.writerow(['Filename', row.filename])
    writer.writerow(['Created (UTC)', row.created_at.isoformat()])
    writer.writerow(['Image dimensions', f'{row.image_width} x {row.image_height}'])
    writer.writerow(['Basic quality check', row.quality])
    writer.writerow(['Mode', row.mode])
    writer.writerow(['Model status', result.get('model_status', 'unknown')])
    writer.writerow(['Headline', result.get('headline', '')])
    writer.writerow(['Clinical use', 'Not for diagnosis or treatment'])
    data = io.BytesIO(output.getvalue().encode('utf-8-sig'))
    data.seek(0)
    return send_file(data, mimetype='text/csv', as_attachment=True,
                     download_name=f'retina-report-{public_id[:8]}.csv')

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', 5000)), debug=True)
