


# Telegive Authentication Service

This is the authentication service for the Telegive platform. It handles bot token authentication, encryption, session management, and account registration.

## Features

- **Bot Token Management**: Encrypts and decrypts Telegram bot tokens using AES-256.
- **Authentication**: Validates bot tokens with the Telegram API.
- **Session Management**: Creates and manages user sessions with secure cookies.
- **Account Registration**: Registers new bot accounts with validation.
- **Account Information**: Provides account details to other services.




## Technology Stack

- **Framework**: Flask (Python)
- **Database**: PostgreSQL
- **Encryption**: AES-256 via `cryptography` library
- **External API**: Telegram Bot API
- **Session Storage**: Flask sessions with secure cookies
- **Deployment**: Railway




## API Endpoints

### Authentication

- `POST /api/auth/register`: Register a new bot account.
- `POST /api/auth/login`: Authenticate a user and create a session.
- `GET /api/auth/verify-session`: Verify the validity of a session.
- `GET /api/auth/account/{account_id}`: Get account information.
- `GET /api/auth/decrypt-token/{account_id}`: Get a decrypted bot token for API calls.
- `POST /api/auth/logout`: Invalidate a session.

### Health Check

- `GET /health`: Health check endpoint.




## Deployment

This service is designed to be deployed on Railway. The following files are included for deployment:

- `Procfile`: Specifies the command to run the application.
- `railway.json`: Railway configuration file.
- `requirements.txt`: Python dependencies.

### Environment Variables

The following environment variables are required for deployment:

- `DATABASE_URL`: The URL of the PostgreSQL database.
- `SECRET_KEY`: A secret key for the Flask application.
- `ENCRYPTION_KEY`: A key for encrypting and decrypting bot tokens.
- `SERVICE_NAME`: The name of the service (e.g., `auth-service`).
- `SERVICE_PORT`: The port the service should run on (e.g., `8001`).
- `TELEGRAM_API_BASE`: The base URL for the Telegram API.
- `TELEGIVE_CHANNEL_URL`: The URL of the Telegive Channel service.
- `TELEGIVE_GIVEAWAY_URL`: The URL of the Telegive Giveaway service.
- `REDIS_URL`: The URL of the Redis server for rate limiting (optional).




## Testing

The project includes a comprehensive test suite using `pytest`. To run the tests, first install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

Then, run the tests:

```bash
pytest
```

To run slow tests, use the `--runslow` flag:

```bash
pytest --runslow
```

To run load tests, use the `--runload` flag:

```bash
pytest --runload
```

## Development Setup

For local development:

1. Clone the repository
2. Install development dependencies: `pip install -r requirements-dev.txt`
3. Set up environment variables (copy `.env.example` to `.env`)
4. Run the application: `python app.py`


# Updated Thu Sep 11 07:41:20 EDT 2025
# Trigger redeploy Sat Sep 13 09:58:35 EDT 2025
