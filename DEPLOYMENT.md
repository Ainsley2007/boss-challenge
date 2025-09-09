# Deployment Guide

## Docker Deployment on Linux Server

### Prerequisites
- Docker and Docker Compose installed on your Linux server
- A Discord bot token

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd boss-challenge
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your Discord bot token
   nano .env
   ```

3. **Deploy using Docker Compose:**
   ```bash
   docker-compose up -d
   ```

4. **Check logs:**
   ```bash
   docker-compose logs -f discord-bot
   ```

### Using Pre-built Container from GitHub

Instead of building locally, you can use the pre-built container from GitHub Container Registry:

1. **Create a docker-compose.override.yml:**
   ```yaml
   version: '3.8'
   services:
     discord-bot:
       image: ghcr.io/YOUR_USERNAME/boss-challenge:latest
       build: null
   ```

2. **Pull and run:**
   ```bash
   docker-compose pull
   docker-compose up -d
   ```

### Container Registry

The GitHub Actions workflow automatically builds and pushes container images to:
- `ghcr.io/YOUR_USERNAME/boss-challenge:latest` (main branch)
- `ghcr.io/YOUR_USERNAME/boss-challenge:v1.0.0` (version tags)

### Updating the Bot

To update to the latest version:
```bash
docker-compose pull
docker-compose up -d
```

### Data Persistence

The bot data is stored in `./data` directory and is mounted as a volume in the container, ensuring data persistence across container restarts.

### Troubleshooting

- Check container logs: `docker-compose logs discord-bot`
- Restart the bot: `docker-compose restart discord-bot`
- View running containers: `docker ps`
- Access container shell: `docker-compose exec discord-bot bash`
