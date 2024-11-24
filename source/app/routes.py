import hashlib
import subprocess
import threading
import time

from flask import render_template, Blueprint, jsonify, request, current_app, send_file, Response, send_from_directory
from .m3u_parser import parse_m3u_channels_and_categories
import os
import logging
import json
import requests
from io import BytesIO
import urllib.parse
import re

import m3u8

main_bp = Blueprint('main', __name__)

# Verwenden Sie den Cache-Pfad aus der App-Konfiguration
def get_cache_dir():
    return current_app.config.get('STREAM_CACHE_PATH', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache'))

# Dictionary to keep track of ongoing transcodings
transcoding_tasks = {}

@main_bp.route('/')
def index():
    return render_template('index.html')


import os
import subprocess
import logging
import hashlib

# Beispielhafte globale Variable für laufende Transcodierungsaufgaben
transcoding_tasks = {}

def transcode_stream(original_url, output_dir):
    """
    Transcode the original stream to HLS using ffmpeg.
    """
    playlist_path = os.path.join(output_dir, 'playlist.m3u8')
    segment_path = os.path.join(output_dir, 'segment_%03d.ts')

    # Stelle sicher, dass das Ausgabeverzeichnis existiert
    os.makedirs(output_dir, exist_ok=True)

    # ffmpeg command to transcode to HLS mit beschränkter Anzahl von Segmenten
    ffmpeg_command = [
        'ffmpeg',
        '-i', original_url,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-ac', '2',  # Erzwingt Stereo-Audio
        '-f', 'hls',
        '-hls_time', '4',
        '-hls_list_size', '5',          # Beschränkt die Playlist auf 5 Segmente
        '-hls_flags', 'delete_segments', # Löscht ältere Segmente
        '-hls_segment_filename', segment_path,
        playlist_path
    ]

    try:
        logging.info(f"Running ffmpeg command: {' '.join(ffmpeg_command)}")
        process = subprocess.Popen(
            ffmpeg_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Stream ffmpeg output in Echtzeit
        while True:
            output = process.stdout.readline()
            error = process.stderr.readline()
            if output:
                logging.debug(f"ffmpeg stdout: {output.strip()}")
            if error:
                logging.debug(f"ffmpeg stderr: {error.strip()}")
            if output == '' and process.poll() is not None:
                break

        return_code = process.poll()
        if return_code != 0:
            logging.error(f"ffmpeg exited with code {return_code}")
            logging.error(f"ffmpeg stderr: {error.strip()}")
        else:
            logging.info(f"Transcoding completed successfully for stream: {original_url}")

    except Exception as e:
        logging.error(f"Error during transcoding: {e}")
    finally:
        # Entfernen aus den laufenden Transcodierungsaufgaben
        stream_hash = hashlib.md5(original_url.encode('utf-8')).hexdigest()
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
def get_categories():
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
    """
    Endpoint to get the proxied stream URL for a given stream URL.
    Expects JSON data with 'stream_url'.
    """
    data = request.get_json()
    stream_url = data.get('stream_url')

    if not stream_url:
        return jsonify({'error': 'No stream URL provided'}), 400

    # Compute hash and check if transcoded playlist exists
    stream_hash = hashlib.md5(stream_url.encode('utf-8')).hexdigest()
    stream_cache_dir = os.path.join(get_cache_dir(), stream_hash)
    playlist_path = os.path.join(stream_cache_dir, 'playlist.m3u8')

    if not os.path.exists(playlist_path):
        # Initiate transcoding
        if stream_hash not in transcoding_tasks:
            os.makedirs(stream_cache_dir, exist_ok=True)
            logging.info(f"Starting transcoding for stream: {stream_url}")

            thread = threading.Thread(target=transcode_stream, args=(stream_url, stream_cache_dir))
            thread.start()
            transcoding_tasks[stream_hash] = thread

        # Transcoding in progress
        return jsonify({'message': 'Transcoding in progress', 'stream_url': f"/transcoded/{stream_hash}/playlist.m3u8"}), 202
    else:
        # Transcoding is complete, provide the stream URL
        proxied_url = f"{request.host_url}transcoded/{stream_hash}/playlist.m3u8"
        logging.info(f"Serving transcoded stream: {proxied_url}")
        return jsonify({'stream_url': proxied_url}), 200



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
