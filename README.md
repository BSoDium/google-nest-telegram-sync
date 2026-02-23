# Google Nest camera clips - Telegram channel sync

This project is a fork of [@TamirMa's repository](https://github.com/TamirMa/nest-telegram-sync), implementing support for Python 3.13, fixing scheduling bugs, and exposing the timezone as a configuration option. It features a fully containerized architecture with Docker/Docker Compose support and async/await-based processing.

## Features

- **Google Home Integration**: Get list of Google Nest camera devices through HomeGraph API
- **Event Monitoring**: Retrieve recent Google Nest camera events with automatic polling
- **Video Management**: Download full-quality Google Nest video clips with metadata extraction
- **Telegram Sync**: Automatically send clips to Telegram channels with proper formatting
- **Multi-Device Support**: Monitor and sync clips from multiple Nest camera devices simultaneously
- **Containerized**: Complete Docker/Docker Compose setup with production and development configurations
- **Timezone Support**: Configurable timezone for event timestamps with automatic localization
- **Async Architecture**: Non-blocking async/await-based event loop for efficient resource usage
- **Event Deduplication**: Intelligent tracking to prevent duplicate clips from being sent
- **Video Metadata**: Automatic extraction of video dimensions and duration using FFmpeg for proper playback
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Multi-Service Authentication**: Custom Google authentication handler supporting multiple service tokens

## Installation & Usage

### Quick Start with Docker (Recommended)

The easiest way to run this application is using Docker Compose:

1. Create a `.env` file in the root directory with your configuration (see [Configuration](#configuration) section below)

2. Run with Docker Compose:
   ```bash
   docker compose up -d
   ```

The application will start in the background and begin syncing clips automatically. Check logs with:
   ```bash
   docker compose logs -f nest-telegram-sync
   ```

### Manual Setup

If you prefer to run without Docker:

- Install the required dependencies:
  ```bash
    pip install -r requirements.txt
  ```

- Get a Google "Master Token", using the [ha-google-home_get-token](https://hub.docker.com/r/breph/ha-google-home_get-token) docker image.

  ```bash
    docker run --rm -it breph/ha-google-home_get-token
  ```
> [!TIP]  
> The image will prompt you to provide an app password, which you can retrieve by creating a new app on your [Google account app passwords page](https://myaccount.google.com/apppasswords).

> [!WARNING]  
> The app password is NOT your Google account's password. It is a unique password generated for the app you are creating.

## Configuration

Create a `.env` file in the root directory with the following configuration:

```dotenv
# Google Nest API Credentials
GOOGLE_MASTER_TOKEN="aas_..."              # Master token from ha-google-home_get-token
GOOGLE_USERNAME="youremailaddress@gmail.com"

# Telegram Configuration
TELEGRAM_BOT_TOKEN="token..."              # Bot token from @BotFather
TELEGRAM_CHANNEL_ID="-100..."              # Channel ID (use @username_to_id_bot for private channels)

# Application Settings
TIMEZONE="US/Central"                      # Timezone for event timestamps (optional, defaults to Europe/Paris)
```

### Getting Your Credentials

**Google Master Token:**
Generate using the [ha-google-home_get-token](https://hub.docker.com/r/breph/ha-google-home_get-token) Docker image.

> [!NOTE]
> You'll need to create an app-specific password on your [Google account app passwords page](https://myaccount.google.com/apppasswords). This is NOT your regular Google password.

**Telegram Bot Token:**
Create a new bot using [@BotFather](https://t.me/botfather) and copy the token provided.

**Telegram Channel ID:**
- For **public channels**: The ID is exposed in the URL
- For **private channels**: Use [@username_to_id_bot](https://t.me/username_to_id_bot) to retrieve the ID

**Timezone:**
All available timezones can be found [in this gist by heyalexej](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568). The default is `Europe/Paris`.

## Running

### With Docker (Recommended)
```bash
docker compose up -d
```

### Standalone
```bash
python3 main.py
```

The application will sync events from all connected Nest camera devices every 2 minutes. Use the logs to monitor activity:

```bash
# Docker Compose
docker compose logs -f nest-telegram-sync

# Standalone
# Output will appear in the terminal
```

## Architecture

### Containerization

The project uses a multi-stage Docker build with separate production and development stages:
- **Production**: Minimal image with only runtime dependencies (Python 3.13, FFmpeg)
- **Development**: Includes git and curl for development workflows
- **Dev Container**: Full development environment configured in the Dockerfile for use with VS Code's Dev Containers

### Components

- `main.py`: Application entry point with async event loop and APScheduler scheduler
- `google_auth_wrapper.py`: Handles Google Home Graph API authentication with custom multi-service token management
- `nest_api.py`: NestDoorbellDevice class for interacting with Nest API endpoints
- `telegram_sync.py`: TelegramEventsSync class for managing event synchronization and Telegram delivery
- `models.py`: Pydantic-based models for type-safe data handling (CameraEvent)
- `tools.py`: Utility functions including FFmpeg-based video metadata extraction
- `requirements.txt`: Python dependencies managed via pip

## Development

The repository includes a devcontainer configuration for VS Code development. To use it:

1. Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
2. Open the workspace with the Dev Container: `ctrl/cmd + shift + p` → "Dev Containers: Reopen in Container"
3. The development environment will set up automatically with all dependencies

## Credits

- [Original repository](https://github.com/TamirMa/nest-telegram-sync) by [@TamirMa](https://github.com/TamirMa)
- [glocaltokens](https://github.com/leikoilja/glocaltokens) for Google Home Graph API access
- [ha-google-home_get-token](https://hub.docker.com/r/breph/ha-google-home_get-token) for simplified master token retrieval
- [python-telegram-bot](https://python-telegram-bot.org/) for Telegram API bindings
- [APScheduler](https://apscheduler.readthedocs.io/) for reliable job scheduling
