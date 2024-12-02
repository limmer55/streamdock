# routes.py
import hashlib
import subprocess
import threading
import logging
import os

from flask import render_template, Blueprint, jsonify, request, current_app, send_file, send_from_directory
from .m3u_parser import parse_m3u_channels_and_categories
from .helpers import get_cache_dir
from .utils import clear_stream_cache
import json
import requests
from io import BytesIO

main_bp = Blueprint('main', __name__)

# Globale Variablen zur Verwaltung aktiver Streams
active_stream_hashes = set()
stream_lock = threading.Lock()
transcoding_tasks = {}

@main_bp.route('/')
def index():
    return render_template('index.html')

def transcode_stream(original_url, output_dir, stream_hash):
    """
    Transcode the original stream to HLS using ffmpeg.
    """
    playlist_path = os.path.join(output_dir, 'playlist.m3u8')
    segment_path = os.path.join(output_dir, 'segment_%03d.ts')

    # Stelle sicher, dass das Ausgabeverzeichnis existiert
    os.makedirs(output_dir, exist_ok=True)

    # FFmpeg-Befehl zum Transkodieren in HLS
    ffmpeg_command = [
        'ffmpeg',
        '-loglevel', 'error',
        '-i', original_url,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-ac', '2',
        '-f', 'hls',
        '-hls_time', '5',
        '-hls_list_size', '10',
        '-hls_flags', 'delete_segments',
        '-hls_segment_filename', segment_path,
        playlist_path,
        '-http_persistent', '1',
        '-reconnect', '1',
        '-reconnect_streamed', '1',
        '-reconnect_delay_max', '2',
        '-preset', 'ultrafast'
    ]

    def log_stream(stream, log_level, prefix):
        """
        Liest den Stream und protokolliert jede Zeile mit dem angegebenen Log-Level und Prefix.
        """
        for line in iter(stream.readline, ''):
            if line:
                message = line.strip()
                if log_level == 'stdout':
                    logging.debug(f"{prefix} stdout: {message}")
                    print(f"{prefix} stdout: {message}")
                elif log_level == 'stderr':
                    logging.debug(f"{prefix} stderr: {message}")
                    print(f"{prefix} stderr: {message}")
        stream.close()

    # Füge den Stream zur aktiven Menge hinzu
    with stream_lock:
        active_stream_hashes.add(stream_hash)

    try:
        logging.info(f"Running ffmpeg command: {' '.join(ffmpeg_command)}")
        process = subprocess.Popen(
            ffmpeg_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Starte separate Threads für stdout und stderr
        stdout_thread = threading.Thread(target=log_stream, args=(process.stdout, 'stdout', 'ffmpeg'))
        stderr_thread = threading.Thread(target=log_stream, args=(process.stderr, 'stderr', 'ffmpeg'))

        stdout_thread.start()
        stderr_thread.start()

        # Warte, bis der FFmpeg-Prozess beendet ist
        process.wait()

        # Warte, bis beide Threads abgeschlossen sind
        stdout_thread.join()
        stderr_thread.join()

        return_code = process.returncode
        if return_code != 0:
            logging.error(f"ffmpeg exited with code {return_code}")
            print(f"ffmpeg exited with code {return_code}")
        else:
            logging.info(f"Transcoding completed successfully for stream: {original_url}")
            print(f"Transcoding completed successfully for stream: {original_url}")

    except Exception as e:
        logging.error(f"Error during transcoding: {e}")
        print(f"Error during transcoding: {e}")
    finally:
        # Entfernen des Streams aus der aktiven Menge
        with stream_lock:
            active_stream_hashes.discard(stream_hash)
            transcoding_tasks.pop(stream_hash, None)

@main_bp.route('/transcoded/<stream_hash>/<filename>')
def serve_transcoded(stream_hash, filename):
    """
    Serve the transcoded playlist and segment files.
    """
    logging.info(f"Received request for transcoded file: {stream_hash}/{filename}")

    stream_cache_dir = os.path.join(get_cache_dir(), stream_hash)
    logging.debug(f"Transcoding cache directory: {stream_cache_dir}")

    # Sicherheitsüberprüfung zur Verhinderung von Directory Traversal
    if '..' in filename or filename.startswith('/'):
        logging.warning(f"Invalid filename requested: {filename}")
        return jsonify({"error": "Invalid filename"}), 400

    file_path = os.path.join(stream_cache_dir, filename)
    logging.debug(f"Requested file path: {file_path}")

    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        return jsonify({"error": "File not found"}), 404

    logging.info(f"Serving file: {file_path}")
    return send_from_directory(stream_cache_dir, filename)

@main_bp.route('/api/categories')
def get_categories_api():
    m3u_url = current_app.config.get('M3U_URL', '')
    if not m3u_url:
        logging.error("No M3U URL configured.")
        return jsonify({"categories": []})

    categories = parse_m3u_channels_and_categories(m3u_url)
    return jsonify({"categories": categories})

@main_bp.route('/category/<category_name>')
def get_category_channels(category_name):
    m3u_url = current_app.config.get('M3U_URL', '')
    if not m3u_url:
        logging.error("No M3U URL configured.")
        channels = []
    else:
        categories = parse_m3u_channels_and_categories(m3u_url)

        category = next((cat for cat in categories if cat['name'] == category_name), None)
        channels = category['channels'] if category else []
    return jsonify(channels)

@main_bp.route('/proxy_image')
def proxy_image():
    image_url = request.args.get('url')

    if not image_url:
        return jsonify({"error": "No image URL provided"}), 400

    try:
        response = requests.get(image_url, stream=True, timeout=5)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', 'image/png')

        return send_file(BytesIO(response.content), mimetype=content_type)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error proxying image: {e}")

        default_icon_path = os.path.join(current_app.static_folder, 'default-logo_light.png')
        if os.path.exists(default_icon_path):
            return send_file(default_icon_path, mimetype='image/png')
        else:
            return jsonify({"error": "Default image not found"}), 500

@main_bp.route('/get_stream', methods=['POST'])
def get_stream():
    data = request.get_json()
    stream_url = data.get('stream_url')

    if not stream_url:
        return jsonify({'error': 'No stream URL provided'}), 400

    stream_hash = hashlib.md5(stream_url.encode('utf-8')).hexdigest()
    stream_cache_dir = os.path.join(get_cache_dir(), stream_hash)
    playlist_path = os.path.join(stream_cache_dir, 'playlist.m3u8')

    with stream_lock:
        # Wenn der Stream bereits aktiv ist oder bereits transkodiert wurde
        if stream_hash in active_stream_hashes or os.path.exists(playlist_path):
            if os.path.exists(playlist_path):
                proxied_url = f"{request.host_url}transcoded/{stream_hash}/playlist.m3u8"
                logging.info(f"Serving transcoded stream: {proxied_url}")
                return jsonify({'stream_url': proxied_url}), 200
            else:
                return jsonify({'message': 'Transcoding in progress', 'stream_url': f"/transcoded/{stream_hash}/playlist.m3u8"}), 202

        # Ein neuer Stream wird angefordert
        # Cache löschen, aber aktive Streams ausschließen
        clear_stream_cache(exclude_hashes=active_stream_hashes)

        # Prüfen, ob bereits eine Transkodierung läuft
        if stream_hash not in transcoding_tasks:
            os.makedirs(stream_cache_dir, exist_ok=True)
            logging.info(f"Starting transcoding for stream: {stream_url}")

            thread = threading.Thread(target=transcode_stream, args=(stream_url, stream_cache_dir, stream_hash))
            thread.start()
            transcoding_tasks[stream_hash] = thread

        # Transcoding läuft noch
        return jsonify({'message': 'Transcoding in progress', 'stream_url': f"/transcoded/{stream_hash}/playlist.m3u8"}), 202

@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    if request.method == 'POST':
        m3u_url = request.form.get('m3u_url', '').strip()
        if m3u_url:

            config_data = {"m3u_url": m3u_url}
            try:
                with open(config_path, 'w', encoding='utf-8') as config_file:
                    json.dump(config_data, config_file, indent=4)

                current_app.config['M3U_URL'] = m3u_url
                logging.info(f"M3U URL updated: {m3u_url}")

                playlist_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'playlist.json')
                if os.path.exists(playlist_json_path):
                    os.remove(playlist_json_path)
                    logging.info(f"Existing playlist.json deleted: {playlist_json_path}")
                else:
                    logging.info("No existing playlist.json found to delete.")

                success_message = "M3U URL successfully updated."
                return render_template('settings.html', success=success_message, m3u_url=m3u_url)
            except Exception as e:
                logging.error(f"Error writing config.json: {e}")
                return render_template('settings.html', error="Error updating the M3U URL.", m3u_url=m3u_url)
        else:
            return render_template('settings.html', error="Please provide a valid M3U URL.", m3u_url=m3u_url)
    else:

        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as config_file:
                    config_data = json.load(config_file)
                    m3u_url = config_data.get('m3u_url', '')
            except json.JSONDecodeError:
                m3u_url = ''
                logging.error("Error parsing config.json.")
        else:
            m3u_url = ''
            logging.warning("config.json not found.")
        return render_template('settings.html', m3u_url=m3u_url)
