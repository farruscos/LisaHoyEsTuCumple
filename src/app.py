from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import io
import traceback
from audio_processor import AudioProcessor
from share_storage import (
    ShareStorage,
    create_share_id,
    is_share_expired,
    parse_share_expiry,
)
from video_processor import VideoProcessor

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_MB", "12")) * 1024 * 1024
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SHARE_TTL_HOURS = int(os.environ.get("SHARE_TTL_HOURS", "24"))
PUBLIC_BASE_URL = os.environ.get("PUBLIC_BASE_URL")

# Initialize media processors (audio can auto-extract if needed)
print("\n" + "="*60)
print("Initializing Lisa Hoy Es Tu Cumple API")
print("="*60)

try:
    processor = AudioProcessor()
    audio_ready = processor.original_audio is not None
except Exception as e:
    print(f"[Error] Failed to initialize processor: {e}")
    processor = None
    audio_ready = False

if not audio_ready:
    print("\n[Warning] Audio is not available!")
    print("Make sure to:")
    print("  1. Set AUDIO_URL to a public audio URL")
    print("  2. Or set AUDIO_PATH to the audio file location")
    print("  3. Or extract audio from video: python extract_audio.py")
    print("  4. Or place song.mp3/song.wav in the project root")

try:
    video_processor = VideoProcessor()
    video_ready = video_processor.original_video is not None
except Exception as e:
    print(f"[Error] Failed to initialize video processor: {e}")
    video_processor = None
    video_ready = False

if not video_ready:
    print("\n[Warning] Video is not available!")
    print("Make sure to:")
    print("  1. Set VIDEO_URL to a public MP4 URL")
    print("  2. Or set VIDEO_PATH to the video file location")
    print("  3. Or place the source MP4 in the project root")

print("="*60 + "\n")

share_storage = ShareStorage.from_env()
if share_storage:
    print("[Info] R2 share storage is enabled")
else:
    print("[Info] R2 share storage is not configured; generated media will be returned directly")


def public_url(path):
    base_url = PUBLIC_BASE_URL or request.host_url.rstrip("/")
    return f"{base_url}{path}"


def download_name(custom_name):
    safe_name = "".join(
        char.lower() if char.isalnum() else "-"
        for char in custom_name.strip()
    ).strip("-")
    return f"cumple-{safe_name or 'personalizado'}.mp3"


def video_download_name(custom_name):
    safe_name = "".join(
        char.lower() if char.isalnum() else "-"
        for char in custom_name.strip()
    ).strip("-")
    return f"cumple-{safe_name or 'personalizado'}.mp4"


def validate_custom_name(custom_name):
    if not custom_name or len(custom_name) > 50:
        return None
    return custom_name

@app.route('/', methods=['GET'])
def index():
    """Serve the web app."""
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/style.css', methods=['GET'])
def styles():
    """Serve frontend styles."""
    return send_from_directory(BASE_DIR, 'style.css')

@app.route('/script.js', methods=['GET'])
def script():
    """Serve frontend JavaScript."""
    return send_from_directory(BASE_DIR, 'script.js')

@app.route('/share.js', methods=['GET'])
def share_script():
    """Serve share page JavaScript."""
    return send_from_directory(BASE_DIR, 'share.js')

@app.route('/video-share.js', methods=['GET'])
def video_share_script():
    """Serve video share page JavaScript."""
    return send_from_directory(BASE_DIR, 'video-share.js')

@app.route('/s/<share_id>', methods=['GET'])
def shared_audio_page(share_id):
    """Serve the public shared-audio page."""
    return send_from_directory(BASE_DIR, 'share.html')

@app.route('/v/<share_id>', methods=['GET'])
def shared_video_page(share_id):
    """Serve the public shared-video page."""
    return send_from_directory(BASE_DIR, 'video-share.html')

@app.route('/api/share/<share_id>', methods=['GET'])
def share_status(share_id):
    """Return metadata for a shared audio link."""
    if not share_storage:
        return jsonify({'error': 'Sharing is not configured'}), 404

    expires_at = parse_share_expiry(share_id)
    if expires_at is None or is_share_expired(share_id):
        return jsonify({'error': 'Este enlace ha caducado'}), 410

    return jsonify({
        'share_id': share_id,
        'share_url': public_url(f'/s/{share_id}'),
        'audio_url': public_url(f'/s/{share_id}/audio'),
        'expires_at': expires_at.isoformat(),
    })

@app.route('/s/<share_id>/audio', methods=['GET'])
def shared_audio_file(share_id):
    """Stream a generated shared MP3 from R2."""
    if not share_storage:
        return jsonify({'error': 'Sharing is not configured'}), 404

    if is_share_expired(share_id):
        return jsonify({'error': 'Este enlace ha caducado'}), 410

    try:
        stored_audio = share_storage.get_audio(share_id)
        audio_data = stored_audio['Body'].read()
        as_attachment = request.args.get('download') == '1'
        return send_file(
            io.BytesIO(audio_data),
            mimetype='audio/mpeg',
            as_attachment=as_attachment,
            download_name='cumple-personalizado.mp3'
        )
    except FileNotFoundError:
        return jsonify({'error': 'Audio no encontrado'}), 404

@app.route('/api/video/<share_id>', methods=['GET'])
def video_status(share_id):
    """Return metadata for a shared video link."""
    if not share_storage:
        return jsonify({'error': 'Sharing is not configured'}), 404

    expires_at = parse_share_expiry(share_id)
    if expires_at is None or is_share_expired(share_id):
        return jsonify({'error': 'Este enlace ha caducado'}), 410

    return jsonify({
        'share_id': share_id,
        'share_url': public_url(f'/v/{share_id}'),
        'video_url': public_url(f'/v/{share_id}/video'),
        'expires_at': expires_at.isoformat(),
    })

@app.route('/v/<share_id>/video', methods=['GET'])
def shared_video_file(share_id):
    """Stream a generated shared MP4 from R2."""
    if not share_storage:
        return jsonify({'error': 'Sharing is not configured'}), 404

    if is_share_expired(share_id):
        return jsonify({'error': 'Este enlace ha caducado'}), 410

    try:
        stored_video = share_storage.get_video(share_id)
        video_data = stored_video['Body'].read()
        as_attachment = request.args.get('download') == '1'
        return send_file(
            io.BytesIO(video_data),
            mimetype='video/mp4',
            as_attachment=as_attachment,
            download_name='cumple-personalizado.mp4'
        )
    except FileNotFoundError:
        return jsonify({'error': 'Vídeo no encontrado'}), 404

@app.route('/api/generate', methods=['POST'])
def generate_audio():
    """Generate customized audio with the provided name"""
    try:
        if processor is None or processor.original_audio is None:
            return jsonify({
                'error': 'El audio original no está disponible.',
                'info': 'Configura AUDIO_URL, AUDIO_PATH o añade song.mp3.'
            }), 503
        
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Falta el campo obligatorio: name'}), 400
        
        custom_name = data['name'].strip()
        
        if not validate_custom_name(custom_name):
            return jsonify({'error': 'Nombre no válido. Debe tener entre 1 y 50 caracteres.'}), 400
        
        print(f"\n[Request] Generating audio for name: {custom_name}")
        
        audio_buffer = processor.generate_custom_audio(custom_name)

        if share_storage:
            audio_data = audio_buffer.getvalue()
            share_id, expires_at = create_share_id(SHARE_TTL_HOURS)
            share_storage.upload_audio(
                share_id=share_id,
                audio_bytes=audio_data,
                expires_at=expires_at,
                custom_name=custom_name,
            )

            return jsonify({
                'audio_url': public_url(f'/s/{share_id}/audio'),
                'download_url': public_url(f'/s/{share_id}/audio?download=1'),
                'share_url': public_url(f'/s/{share_id}'),
                'expires_at': expires_at.isoformat(),
                'download_name': download_name(custom_name),
            })
        
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=download_name(custom_name)
        )
    
    except Exception as e:
        print(f"\n[Error] Failed to generate audio: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'No se pudo generar el audio: {str(e)}'}), 500

@app.route('/api/generate-video', methods=['POST'])
def generate_video():
    """Generate a customized MP4 with the provided name and optional photo."""
    try:
        if processor is None or processor.original_audio is None:
            return jsonify({
                'error': 'El audio original no está disponible.',
                'info': 'Configura AUDIO_URL, AUDIO_PATH o añade song.mp3.'
            }), 503

        if video_processor is None or video_processor.original_video is None:
            return jsonify({
                'error': 'El vídeo original no está disponible.',
                'info': 'Configura VIDEO_URL, VIDEO_PATH o añade el MP4 base.'
            }), 503

        custom_name = request.form.get('name', '').strip()
        if not validate_custom_name(custom_name):
            return jsonify({'error': 'Nombre no válido. Debe tener entre 1 y 50 caracteres.'}), 400

        photo_file = request.files.get('photo')
        if photo_file and not photo_file.filename:
            photo_file = None

        print(f"\n[Request] Generating video for name: {custom_name}")

        audio_buffer = processor.generate_custom_audio(custom_name)
        video_buffer = video_processor.generate_custom_video(
            audio_buffer=audio_buffer,
            custom_name=custom_name,
            photo_file=photo_file,
        )

        if share_storage:
            video_data = video_buffer.getvalue()
            share_id, expires_at = create_share_id(SHARE_TTL_HOURS)
            share_storage.upload_video(
                share_id=share_id,
                video_bytes=video_data,
                expires_at=expires_at,
                custom_name=custom_name,
            )

            return jsonify({
                'video_url': public_url(f'/v/{share_id}/video'),
                'download_url': public_url(f'/v/{share_id}/video?download=1'),
                'share_url': public_url(f'/v/{share_id}'),
                'expires_at': expires_at.isoformat(),
                'download_name': video_download_name(custom_name),
            })

        return send_file(
            video_buffer,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=video_download_name(custom_name)
        )

    except Exception as e:
        print(f"\n[Error] Failed to generate video: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'No se pudo generar el vídeo: {str(e)}'}), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Get API status"""
    ready = bool(processor and audio_ready and video_processor and video_ready)
    return jsonify({
        'status': 'ok' if ready else 'degraded',
        'audio_loaded': audio_ready,
        'video_loaded': video_ready,
        'sharing_enabled': share_storage is not None,
        'message': 'Video API is running' if ready else 'Waiting for source media'
    }), 200 if ready else 503

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Lisa API is running'}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", "5000"))
    print(f"\nStarting Flask server on http://localhost:{port}")
    print(f"Frontend available at: http://localhost:{port}")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=port)
