from flask import render_template, Blueprint, jsonify, request, current_app, send_file, Response
from .m3u_parser import parse_m3u_channels_and_categories
import os
import logging
import json
import requests
from io import BytesIO
import urllib.parse
import re


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

from flask import Response
import m3u8
import urllib.parse

@main_bp.route('/proxy_stream')
def proxy_stream():
    stream_url = request.args.get('url')
    if not stream_url:
        return jsonify({"error": "No stream URL provided"}), 400

    try:
        # Abrufen der Original-Stream-URL
        response = requests.get(stream_url, stream=True, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        logging.info(f"Proxying URL: {stream_url}")
        logging.info(f"Original Content-Type: {content_type}")

        # Überprüfen, ob es sich um eine M3U8-Playlist handelt
        if 'application/vnd.apple.mpegurl' in content_type or stream_url.endswith('.m3u8'):
            playlist_content = response.text

            logging.debug("Original Playlist Content:")
            logging.debug(playlist_content)

            # Parse der Playlist
            parsed_playlist = m3u8.loads(playlist_content)

            # Basis-URL für relative Pfade
            base_url = response.url  # Berücksichtigt Weiterleitungen

            # Funktion zum Umschreiben von URIs
            def rewrite_uri(uri):
                if not uri or uri.startswith('#'):
                    return uri  # Kommentare und leere Zeilen unverändert lassen

                # Überprüfen, ob die URI bereits über den Proxy läuft
                parsed_uri = urllib.parse.urlparse(uri)
                if parsed_uri.netloc == request.host and parsed_uri.path.startswith('/proxy_stream'):
                    logging.debug(f"URI already proxied: {uri}")
                    return uri  # Bereits geproxied, unverändert zurückgeben

                # Basis-URL für relative Pfade
                base_parsed = urllib.parse.urlparse(base_url)
                base_domain = f"{base_parsed.scheme}://{base_parsed.netloc}"

                if uri.startswith('http://') or uri.startswith('https://'):
                    absolute_uri = uri
                elif uri.startswith('/'):
                    # URIs, die mit '/' beginnen, relativ zum Domain-Root
                    absolute_uri = urllib.parse.urljoin(base_domain, uri)
                else:
                    # Relative URIs ohne führendes '/'
                    absolute_uri = urllib.parse.urljoin(base_url, uri)

                proxied_uri = f"/proxy_stream?url={urllib.parse.quote(absolute_uri, safe='')}"
                logging.debug(f"Rewriting URI: {uri} -> {proxied_uri}")
                return proxied_uri

            # Durchgehen aller Segmente, Playlists und Media-Einträge
            for segment in parsed_playlist.segments:
                old_uri = segment.uri
                segment.uri = rewrite_uri(segment.uri)
                logging.debug(f"Rewriting segment URI: {old_uri} -> {segment.uri}")

            for playlist in parsed_playlist.playlists:
                old_uri = playlist.uri
                playlist.uri = rewrite_uri(playlist.uri)
                logging.debug(f"Rewriting playlist URI: {old_uri} -> {playlist.uri}")

            for media in parsed_playlist.media:
                if media.uri:
                    old_uri = media.uri
                    media.uri = rewrite_uri(media.uri)
                    logging.debug(f"Rewriting media URI: {old_uri} -> {media.uri}")

            # Serialisieren der modifizierten Playlist
            modified_playlist = parsed_playlist.dumps()

            logging.debug("Modified Playlist Content:")
            logging.debug(modified_playlist)

            return Response(
                modified_playlist,
                content_type=content_type
            )
        else:
            # Bestimmen des MIME-Typs für verschiedene Medien
            if stream_url.endswith('.ts'):
                content_type = 'video/MP2T'
            elif stream_url.endswith('.aac'):
                content_type = 'audio/aac'
            elif stream_url.endswith('.mp3'):
                content_type = 'audio/mpeg'
            # Fügen Sie weitere Dateiendungen und MIME-Typen nach Bedarf hinzu
            else:
                content_type = 'application/octet-stream'  # Fallback

            logging.debug(f"Serving non-playlist content with Content-Type: {content_type}")

            return Response(
                response.iter_content(chunk_size=8192),
                content_type=content_type
            )
    except requests.exceptions.RequestException as e:
        logging.error(f"Error proxying stream: {e}")
        return jsonify({"error": "Failed to proxy the stream."}), 500





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
        #logging.error(f"Error proxying image: {e}")
        
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

    proxied_url = f"{request.host_url}proxy_stream?url={requests.utils.quote(stream_url, safe='')}"
    
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
