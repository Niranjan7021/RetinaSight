import io
import pytest
from PIL import Image
from app import app, db

@pytest.fixture()
def client(tmp_path):
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI=f'sqlite:///{tmp_path / "test.db"}')
    with app.app_context():
        db.drop_all(); db.create_all()
    with app.test_client() as client:
        yield client
    with app.app_context():
        db.session.remove(); db.drop_all()

def sample_image(fmt='JPEG'):
    image = Image.new('RGB', (256, 256), (100, 80, 70))
    buf = io.BytesIO(); image.save(buf, format=fmt); buf.seek(0)
    return buf

def test_health(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json['status'] == 'ok'

def test_upload_creates_demo_record(client):
    response = client.post('/api/screenings', data={'image': (sample_image(), 'fundus.jpg')}, content_type='multipart/form-data')
    assert response.status_code == 201
    assert response.json['result']['model_status'] == 'NOT_CONFIGURED'
    assert client.get('/api/screenings').json['items'][0]['filename'] == 'fundus.jpg'

def test_rejects_unsupported_file(client):
    response = client.post('/api/screenings', data={'image': (io.BytesIO(b'abc'), 'file.exe')}, content_type='multipart/form-data')
    assert response.status_code == 415

def test_report_download(client):
    created = client.post('/api/screenings', data={'image': (sample_image(), 'fundus.jpg')}, content_type='multipart/form-data')
    response = client.get(f"/api/screenings/{created.json['id']}/report")
    assert response.status_code == 200
    assert b'Screening ID' in response.data
