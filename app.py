from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from models import db, Asset

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'stl', 'mp4', 'mov', 'avi'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI']  = 'sqlite:///assets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']  = False


CORS(app)
db.init_app(app)


# Ensure the uploads folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        
        url= f'/uploads/{filename}'
        
        asset = Asset(filename=filename, filetype=file_ext, url=url)
        db.session.add(asset)
        db.session.commit()
        
        return jsonify({'url': f'/uploads/{filename}'})
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/current', methods=['GET'])
def get_current_assets():
    latest_stl = Asset.query.filter_by(filetype='stl').order_by(Asset.uploaded_at.desc()).first()
    latest_video = Asset.query.filter(Asset.filetype.in_(['mp4', 'mov', 'avi'])).order_by(Asset.uploaded_at.desc()).first()

    result = {
        'stl': {
            'filename': latest_stl.filename,
            'url': latest_stl.url,
            'uploaded_at': latest_stl.uploaded_at.isoformat()
        } if latest_stl else None,
        'video': {
            'filename': latest_video.filename,
            'url': latest_video.url,
            'uploaded_at': latest_video.uploaded_at.isoformat()
        } if latest_video else None
    }
    
    return jsonify(result)
    
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5555)
