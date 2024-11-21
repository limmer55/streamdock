# <img height="100px" src="./images/logo.png" />
A simple IPTV player you can host using Docker and stream via a website.
![screenshot](https://github.com/Limmer55/streamdock/blob/main/images/Screenshot1.png?raw=true)
## Features
- 📺 **Watch from everywhere**: No client required. Simply use your browser.
- 🔍 **Search Functionality**: Search for channels by name.
- 🌙 **Darkmode Support**: Automatically switches between light and dark modes based on system preferences.
- **Similar Channels**: View and navigate to similar channels based on normalized channel names. 
- 🌍 [**iptv-org Playlists**](https://github.com/iptv-org/iptv): If you don't have an IPTV-Provider, choose a playlist for your country.
- **Picture-In-Picture Mode**: Allows you to watch videos in a floating window


## Installation
### Using docker
```bash
docker run -d --name streamdock --network host --restart unless-stopped ghcr.io/lkenner/m3u8player:latest

```
### Docker Compose
#### Create a docker-compose.yml file with the following content
```bash
version: "3.8"
services:
  streamdock:
    image: ghcr.io/limmer55/streamdock:latest
    container_name: streamdock
    network_mode: host
    #environment:
    #  - M3U_URL=https://iptv-org.github.io/iptv/index.m3u # optional, can be set in app-settings
    restart: unless-stopped
```
#### Start the service using Docker Compose
```bash
docker-compose up -d
```

### Once the service is running, open your browser and navigate to
```bash
http://[IPADDRESS/HOSTNAME]:6050/
```
When you don't set a M3U_URL, open settings page and set it there.


## Why?
I'm not really a programmer, and I don't claim to do it better.
But other IPTV apps always seem a bit overloaded, unintuitive to use, or have hidden costs.
I just want to watch sports while sitting at my PC.
Also, "real projects" are best to learn programming!

## Support
If you like the project, I would be happy if you left a ⭐️ in the repo.
