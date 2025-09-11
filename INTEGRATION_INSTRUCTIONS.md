# Telegive Authentication Service Integration Instructions

This document provides instructions for integrating other services with the Telegive Authentication Service. The service is deployed and accessible at the following URL:

**Service URL:** https://web-production-ddd7e.up.railway.app




## Authentication Flow

The authentication service supports two primary authentication flows:

1.  **Bot Authentication:** This flow is used to register new bots with the service and obtain a bot token. This token is then used to authenticate the bot for subsequent requests.
2.  **Service-to-Service Authentication:** This flow is used for communication between the authentication service and other internal services. It uses a pre-shared secret key for authentication.




## API Endpoints

The following are the key API endpoints for the authentication service:

### Bot Registration

*   **Endpoint:** `/api/v1/bots/register`
*   **Method:** `POST`
*   **Description:** Registers a new bot with the service.
*   **Request Body:**
    ```json
    {
        "bot_token": "YOUR_TELEGRAM_BOT_TOKEN"
    }
    ```
*   **Response:**
    ```json
    {
        "message": "Bot registered successfully",
        "bot_id": "<bot_id>",
        "access_token": "<access_token>"
    }
    ```

### Service-to-Service Communication

*   **Endpoint:** `/api/v1/service/status`
*   **Method:** `GET`
*   **Description:** Checks the status of the authentication service.
*   **Headers:**
    *   `X-Service-Token`: `YOUR_SERVICE_TO_SERVICE_SECRET`
*   **Response:**
    ```json
    {
        "status": "ok"
    }
    ```




## Integration Code Examples

Below are Python code examples demonstrating how to interact with the Telegive Authentication Service.

### Bot Registration Example

```python
import requests

auth_service_url = "https://web-production-ddd7e.up.railway.app"
bot_token = "YOUR_TELEGRAM_BOT_TOKEN"  # Replace with your bot's Telegram token

url = f"{auth_service_url}/api/v1/bots/register"

headers = {
    "Content-Type": "application/json"
}

data = {
    "bot_token": bot_token
}

try:
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()  # Raise an exception for bad status codes

    registration_data = response.json()
    print("Bot registered successfully:")
    print(f"  Bot ID: {registration_data.get('bot_id')}")
    print(f"  Access Token: {registration_data.get('access_token')}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred during bot registration: {e}")
    if e.response:
        print(f"Error response: {e.response.text}")

```

### Service-to-Service Communication Example

```python
import requests

auth_service_url = "https://web-production-ddd7e.up.railway.app"
service_token = "YOUR_SERVICE_TO_SERVICE_SECRET"  # Replace with your shared secret

url = f"{auth_service_url}/api/v1/service/status"

headers = {
    "X-Service-Token": service_token
}

try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an exception for bad status codes

    status_data = response.json()
    print("Service status check successful:")
    print(f"  Status: {status_data.get('status')}")

except requests.exceptions.RequestException as e:
    print(f"An error occurred during service status check: {e}")
    if e.response:
        print(f"Error response: {e.response.text}")

```




## Error Handling

The authentication service returns standard HTTP error codes to indicate the success or failure of an API request. The response body will contain a JSON object with a `message` field providing more details about the error.

Common error codes include:

*   `400 Bad Request`: The request was malformed or missing required parameters.
*   `401 Unauthorized`: The request is missing a valid authentication token.
*   `403 Forbidden`: The authenticated user does not have permission to perform the requested action.
*   `404 Not Found`: The requested resource was not found.
*   `500 Internal Server Error`: An unexpected error occurred on the server.




## Testing

To test the integration with the authentication service, you can use the following `curl` commands:

### Bot Registration

```bash
curl -X POST \
  https://web-production-ddd7e.up.railway.app/api/v1/bots/register \
  -H 'Content-Type: application/json' \
  -d '{
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN"
  }'
```

### Service-to-Service Communication

```bash
curl -X GET \
  https://web-production-ddd7e.up.railway.app/api/v1/service/status \
  -H 'X-Service-Token: YOUR_SERVICE_TO_SERVICE_SECRET'
```




## Environment Setup

To run the integration examples, you will need to set the following environment variables:

*   `TELEGRAM_BOT_TOKEN`: Your Telegram bot token.
*   `SERVICE_TO_SERVICE_SECRET`: The pre-shared secret for service-to-service communication.

You can set these variables in your environment or in a `.env` file in your project's root directory.


