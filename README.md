# <img height="100px" src="./images/logo.png" />
## 📺 A Web-IPTV Player
> [!WARNING]
> Streamdock is still in its early stages. I've received a lot of valuable feedback, most of which highlights that certain codecs aren't running. Because of this, I’ve decided to implement transcoding (along with hardware acceleration) in future builds. Thank you for your patience.


![screenshot](https://github.com/Limmer55/streamdock/blob/main/images/Screenshot1.png?raw=true)
## Features
- 📺 **Watch from everywhere**: No client required. Just use your browser.
- 🔍 **Search Functionality**: Find channels by name.
- 🌙 **Darkmode Support**: Automatically switches between light and dark modes based on your system preferences.
- 📡 **Similar Channels**: View and navigate to similar channels based on normalized channel names. 
- 🌍 [**iptv-org Playlists**](https://github.com/iptv-org/iptv): If you don’t have an IPTV provider, choose a playlist for your country.
- 📽️ **Picture-In-Picture Mode**: Watch videos in a floating window.

**⚠️ It might not be very stable. Safari is currently not supported.**

## Installation
### Using docker
```bash
docker run -d --name streamdock --network host --restart unless-stopped ghcr.io/limmer55/streamdock:latest

```
### Docker Compose
#### Create a docker-compose.yml file with the following content
```bash
version: "3.8"
services:
  streamdock:
    image: ghcr.io/limmer55/streamdock:stable
    container_name: streamdock
    network_mode: host
    environment:
      M3U_URL: "https://iptv-org.github.io/iptv/index.m3u" # optional, can be set in settings later
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
If you don't set a M3U_URL, open settings page and set it there.


## Why?
I'm not really a programmer, and I don't claim to do it better.
But other IPTV apps always seem a bit overloaded, unintuitive to use, or have hidden costs.
I just want to watch sports while sitting at my PC.
Also, "real projects" are best to learn programming!

## Support
If you like the project, I would be happy if you left a ⭐️ in the repo.

<div align="end">
    <a href="https://github.com/limmer55/streamdock/actions/workflows/docker-image.yml">
    <img alt="GitHub Actions Workflow Status" src="https://img.shields.io/github/actions/workflow/status/limmer55/streamdock/docker-image.yml" />
</a>

</div>
