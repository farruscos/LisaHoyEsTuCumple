from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import os
import io
import traceback
from audio_processor import AudioProcessor

app = Flask(__name__)
CORS(app)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Initialize the audio processor (will auto-extract if needed)
print("\n" + "="*60)
print("Initializing Audio Customization API")
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

print("="*60 + "\n")

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

@app.route('/api/generate', methods=['POST'])
def generate_audio():
    """Generate customized audio with the provided name"""
    try:
        if processor is None or processor.original_audio is None:
            return jsonify({
                'error': 'Audio not available. Please extract audio from video first.',
                'info': 'Run: python extract_audio.py'
            }), 503
        
        data = request.get_json()
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Missing required field: name'}), 400
        
        custom_name = data['name'].strip()
        
        if not custom_name or len(custom_name) > 50:
            return jsonify({'error': 'Invalid name. Length must be between 1 and 50 characters'}), 400
        
        print(f"\n[Request] Generating audio for name: {custom_name}")
        
        audio_buffer = processor.generate_custom_audio(custom_name)
        
        return send_file(
            audio_buffer,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f'customized_{custom_name.lower()}.mp3'
        )
    
    except Exception as e:
        print(f"\n[Error] Failed to generate audio: {str(e)}")
        traceback.print_exc()
        return jsonify({'error': f'Failed to generate audio: {str(e)}'}), 500

@app.route('/api/status', methods=['GET'])
def status():
    """Get API status"""
    return jsonify({
        'status': 'ok' if processor and audio_ready else 'degraded',
        'audio_loaded': audio_ready,
        'message': 'Audio API is running' if audio_ready else 'Waiting for audio file'
    }), 200 if audio_ready else 503

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok', 'message': 'Audio API is running'}), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", "5000"))
    print(f"\nStarting Flask server on http://localhost:{port}")
    print(f"Frontend available at: http://localhost:{port}")
    print("Press Ctrl+C to stop\n")
    app.run(debug=True, host='0.0.0.0', port=port)
