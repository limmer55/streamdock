import re
import requests
import logging
import os
import json

def download_m3u_content(m3u_url):
    try:
        response = requests.get(m3u_url)
        if response.status_code == 200:
            logging.info(f"Successfully downloaded M3U content from {m3u_url}.")
            return response.text
        else:
            logging.error(f"Failed to download M3U file. Status code: {response.status_code}")
            return ""
    except Exception as e:
        logging.error(f"Exception occurred while downloading M3U file: {e}")
        return ""

def parse_m3u_channels_and_categories(m3u_url, progress_callback=None):
    playlist_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'playlist.json')

    # Check if the local JSON file exists
    if os.path.exists(playlist_json_path):
        logging.info("Loading playlist from local JSON file.")
        try:
            with open(playlist_json_path, 'r', encoding='utf-8') as json_file:
                categories = json.load(json_file)
                return categories
        except Exception as e:
            logging.error(f"Failed to load playlist from JSON file: {e}")
    else:
        logging.info("Local playlist JSON file not found. Downloading and parsing M3U playlist.")

    categories = []
    category_map = {}

    m3u_content = download_m3u_content(m3u_url)
    if not m3u_content:
        logging.error("No M3U content available for parsing.")
        return categories

    # Calculate the total number of channels for progress tracking
    total_channels = sum(1 for line in m3u_content.splitlines() if line.strip().startswith("#EXTINF"))
    processed_channels = 0

    channel_info = {}
    category = "Uncategorized"
    for line in m3u_content.splitlines():
        line = line.strip()
        if line.startswith("#EXTINF"):
            # Extract channel name and category from the line
            info = line.split("#EXTINF:")[1].split(",", 1)
            channel_info['name'] = info[1].strip() if len(info) > 1 else "Unknown Channel"

            match = re.search(r'group-title="([^"]+)"', line)
            category = match.group(1) if match else "Uncategorized"

            # Extract channel icon URL if available
            icon_match = re.search(r'tvg-logo="([^"]+)"', line)
            icon_url = icon_match.group(1) if icon_match else None

            channel_info['icon'] = icon_url

        elif line and not line.startswith("#"):
            # Extract channel URL
            channel_info['url'] = line

            # Add channel to the appropriate category
            if category not in category_map:
                category_entry = {
                    'name': category,
                    'channels': []
                }
                categories.append(category_entry)
                category_map[category] = category_entry

            category_map[category]['channels'].append(channel_info)
            channel_info = {}

            processed_channels += 1
            # Call the progress callback function if provided
            if progress_callback and total_channels > 0:
                progress_callback(processed_channels, total_channels)

    # Save the parsed categories to a local JSON file
    try:
        with open(playlist_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(categories, json_file, ensure_ascii=False, indent=4)
        logging.info(f"Playlist saved to local JSON file: {playlist_json_path}")
    except Exception as e:
        logging.error(f"Failed to save playlist to JSON file: {e}")

    return categories
