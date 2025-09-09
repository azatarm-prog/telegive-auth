# Telegive Authentication Service API Documentation

## Overview

The Telegive Authentication Service provides secure bot token management, user authentication, and session handling for the Telegive platform. All API endpoints return JSON responses and follow RESTful conventions.

**Base URL**: `https://your-auth-service.railway.app`  
**API Version**: 1.0.0  
**Content-Type**: `application/json`



## Authentication

The service uses session-based authentication with secure HTTP cookies. After successful login, a session cookie is set that must be included in subsequent requests requiring authentication.

### Session Cookie
- **Name**: `session`
- **Security**: HttpOnly, Secure (in production)
- **Expiration**: 24 hours (configurable)



## Rate Limiting

The API implements rate limiting to prevent abuse:

- **Registration**: 5 requests per minute per IP
- **Login**: 10 requests per minute per IP  
- **Session Verification**: 100 requests per minute per service
- **Token Decryption**: 50 requests per minute per service
- **General**: 1000 requests per hour per IP

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets


## Error Handling

All API responses follow a consistent error format:

```json
{
  "success": false,
  "error": "Human readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "details": {
    "field": "Additional error details (optional)"
  }
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or invalid
- `403 Forbidden`: Access denied
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
- `502 Bad Gateway`: External service error
- `503 Service Unavailable`: Service temporarily unavailable


## Authentication Endpoints

### Register Account

Register a new bot account with the service.

**Endpoint**: `POST /api/auth/register`  
**Authentication**: None required  
**Rate Limit**: 5 requests per minute per IP

#### Request

```json
{
  "bot_token": "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890"
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bot_token` | string | Yes | Valid Telegram bot token |

#### Success Response (201 Created)

```json
{
  "success": true,
  "account_id": 123,
  "bot_info": {
    "id": 1234567890,
    "username": "my_awesome_bot",
    "first_name": "My Awesome Bot"
  },
  "requires_channel_setup": true
}
```

#### Error Responses

**Invalid Token Format (400 Bad Request)**
```json
{
  "success": false,
  "error": "Invalid bot token format",
  "error_code": "INVALID_TOKEN_FORMAT"
}
```

**Token Validation Failed (401 Unauthorized)**
```json
{
  "success": false,
  "error": "Invalid bot token",
  "error_code": "INVALID_TOKEN"
}
```

**Account Already Exists (400 Bad Request)**
```json
{
  "success": false,
  "error": "Account with this bot already exists",
  "error_code": "ACCOUNT_EXISTS"
}
```


### Login

Authenticate a user and create a session.

**Endpoint**: `POST /api/auth/login`  
**Authentication**: None required  
**Rate Limit**: 10 requests per minute per IP

#### Request

```json
{
  "bot_token": "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890"
}
```

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `bot_token` | string | Yes | Valid Telegram bot token |

#### Success Response (200 OK)

```json
{
  "success": true,
  "session_id": "sess_abc123def456ghi789jkl012mno345pqr",
  "account_info": {
    "id": 123,
    "bot_username": "my_awesome_bot",
    "bot_name": "My Awesome Bot",
    "channel_username": "my_channel",
    "channel_title": "My Channel",
    "channel_member_count": 1500,
    "channel_verified": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Error Responses

**Invalid Credentials (401 Unauthorized)**
```json
{
  "success": false,
  "error": "Invalid bot token",
  "error_code": "INVALID_CREDENTIALS"
}
```

**Account Deactivated (400 Bad Request)**
```json
{
  "success": false,
  "error": "Account is deactivated",
  "error_code": "ACCOUNT_DEACTIVATED"
}
```


### Verify Session

Verify the validity of a user session.

**Endpoint**: `GET /api/auth/verify-session`  
**Authentication**: Session cookie required  
**Rate Limit**: 100 requests per minute per service

#### Request

No request body required. Session information is passed via HTTP cookies.

#### Success Response (200 OK)

```json
{
  "valid": true,
  "account_id": 123,
  "account_info": {
    "id": 123,
    "bot_username": "my_awesome_bot",
    "bot_name": "My Awesome Bot",
    "channel_username": "my_channel",
    "channel_title": "My Channel",
    "channel_member_count": 1500,
    "channel_verified": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

#### Error Responses

**No Session (401 Unauthorized)**
```json
{
  "valid": false,
  "error": "No session found",
  "error_code": "NO_SESSION"
}
```

**Invalid Session (401 Unauthorized)**
```json
{
  "valid": false,
  "error": "Invalid or expired session",
  "error_code": "INVALID_SESSION"
}
```

**Account Inactive (401 Unauthorized)**
```json
{
  "valid": false,
  "error": "Account not found or inactive",
  "error_code": "ACCOUNT_INACTIVE"
}
```


### Get Account Information

Retrieve detailed account information by account ID.

**Endpoint**: `GET /api/auth/account/{account_id}`  
**Authentication**: None required (for inter-service communication)  
**Rate Limit**: 100 requests per minute per service

#### URL Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | integer | Yes | Unique account identifier |

#### Success Response (200 OK)

```json
{
  "success": true,
  "account": {
    "id": 123,
    "bot_username": "my_awesome_bot",
    "bot_name": "My Awesome Bot",
    "bot_id": 1234567890,
    "channel_id": -1001234567890,
    "channel_username": "my_channel",
    "channel_title": "My Channel",
    "channel_member_count": 1500,
    "can_post_messages": true,
    "can_edit_messages": true,
    "can_send_media": true,
    "is_active": true,
    "bot_verified": true,
    "channel_verified": true,
    "created_at": "2024-01-15T10:30:00Z",
    "last_login_at": "2024-01-20T14:45:00Z",
    "last_bot_check_at": "2024-01-20T14:45:00Z"
  }
}
```

#### Error Responses

**Account Not Found (404 Not Found)**
```json
{
  "success": false,
  "error": "Account not found",
  "error_code": "ACCOUNT_NOT_FOUND"
}
```

**Invalid Account ID (400 Bad Request)**
```json
{
  "success": false,
  "error": "Account ID must be a positive number",
  "error_code": "INVALID_ACCOUNT_ID"
}
```


### Decrypt Bot Token

Retrieve the decrypted bot token for API calls (for inter-service communication).

**Endpoint**: `GET /api/auth/decrypt-token/{account_id}`  
**Authentication**: Service authentication required  
**Rate Limit**: 50 requests per minute per service

#### URL Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `account_id` | integer | Yes | Unique account identifier |

#### Success Response (200 OK)

```json
{
  "success": true,
  "bot_token": "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890"
}
```

#### Error Responses

**Account Not Found (404 Not Found)**
```json
{
  "success": false,
  "error": "Account not found",
  "error_code": "ACCOUNT_NOT_FOUND"
}
```

**Account Inactive (400 Bad Request)**
```json
{
  "success": false,
  "error": "Account is inactive",
  "error_code": "ACCOUNT_INACTIVE"
}
```

**Decryption Failed (500 Internal Server Error)**
```json
{
  "success": false,
  "error": "Failed to decrypt token",
  "error_code": "DECRYPTION_ERROR"
}
```


### Logout

Invalidate the current user session.

**Endpoint**: `POST /api/auth/logout`  
**Authentication**: Session cookie required  
**Rate Limit**: 10 requests per minute per IP

#### Request

No request body required. Session information is passed via HTTP cookies.

#### Success Response (200 OK)

```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

#### Notes

- This endpoint always returns success, even if no valid session exists
- The session cookie is cleared after logout
- The session is marked as inactive in the database


## Health Check Endpoints

### Basic Health Check

Check the basic health status of the service.

**Endpoint**: `GET /health`  
**Authentication**: None required  
**Rate Limit**: No limit

#### Success Response (200 OK)

```json
{
  "status": "healthy",
  "service": "auth-service",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2024-01-20T15:30:00Z"
}
```

#### Unhealthy Response (503 Service Unavailable)

```json
{
  "status": "unhealthy",
  "service": "auth-service",
  "version": "1.0.0",
  "database": "disconnected",
  "timestamp": "2024-01-20T15:30:00Z"
}
```

### Detailed Health Check

Get detailed health information including statistics.

**Endpoint**: `GET /health/detailed`  
**Authentication**: None required  
**Rate Limit**: No limit

#### Success Response (200 OK)

```json
{
  "status": "healthy",
  "service": "auth-service",
  "version": "1.0.0",
  "timestamp": "2024-01-20T15:30:00Z",
  "database": {
    "status": "connected",
    "account_count": 150,
    "active_sessions": 45
  },
  "external_services": {
    "telegram_api": "available"
  },
  "uptime": "N/A"
}
```


## Service Information Endpoints

### Root Endpoint

Get basic service information.

**Endpoint**: `GET /`  
**Authentication**: None required

#### Response (200 OK)

```json
{
  "service": "Telegive Authentication Service",
  "version": "1.0.0",
  "status": "running",
  "endpoints": {
    "health": "/health",
    "auth": "/api/auth/*"
  }
}
```

### API Information

Get information about available API endpoints.

**Endpoint**: `GET /api`  
**Authentication**: None required

#### Response (200 OK)

```json
{
  "service": "Telegive Authentication Service API",
  "version": "1.0.0",
  "endpoints": {
    "register": "POST /api/auth/register",
    "login": "POST /api/auth/login",
    "verify_session": "GET /api/auth/verify-session",
    "get_account": "GET /api/auth/account/{account_id}",
    "decrypt_token": "GET /api/auth/decrypt-token/{account_id}",
    "logout": "POST /api/auth/logout"
  }
}
```


## Error Codes Reference

### Authentication Errors
- `MISSING_TOKEN`: Bot token is required but not provided
- `INVALID_TOKEN_FORMAT`: Bot token format is invalid
- `INVALID_TOKEN`: Bot token is not valid or unauthorized
- `INVALID_CREDENTIALS`: Login credentials are incorrect
- `NOT_A_BOT`: Token belongs to a user account, not a bot

### Account Errors
- `ACCOUNT_EXISTS`: Account with this bot already exists
- `ACCOUNT_NOT_FOUND`: Account with specified ID does not exist
- `ACCOUNT_DEACTIVATED`: Account has been deactivated
- `ACCOUNT_INACTIVE`: Account is not active

### Session Errors
- `NO_SESSION`: No session cookie found
- `INVALID_SESSION`: Session is invalid or expired
- `SESSION_ERROR`: General session-related error

### Validation Errors
- `VALIDATION_ERROR`: Input validation failed
- `MISSING_FIELD`: Required field is missing
- `INVALID_TYPE`: Invalid data type provided
- `INVALID_ACCOUNT_ID`: Account ID is invalid

### System Errors
- `INTERNAL_ERROR`: Internal server error
- `DATABASE_ERROR`: Database operation failed
- `DECRYPTION_ERROR`: Token decryption failed
- `TELEGRAM_API_ERROR`: Telegram API request failed
- `RATE_LIMIT_EXCEEDED`: Rate limit has been exceeded

### External Service Errors
- `TIMEOUT`: Request to external service timed out
- `CONNECTION_ERROR`: Failed to connect to external service
- `API_ERROR`: External API returned an error


## Usage Examples

### Complete Authentication Flow

#### 1. Register a New Account

```bash
curl -X POST https://your-auth-service.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "bot_token": "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890"
  }'
```

#### 2. Login with Bot Token

```bash
curl -X POST https://your-auth-service.railway.app/api/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "bot_token": "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ1234567890"
  }'
```

#### 3. Verify Session

```bash
curl -X GET https://your-auth-service.railway.app/api/auth/verify-session \
  -b cookies.txt
```

#### 4. Logout

```bash
curl -X POST https://your-auth-service.railway.app/api/auth/logout \
  -b cookies.txt
```

### Inter-Service Communication

#### Get Account Information

```bash
curl -X GET https://your-auth-service.railway.app/api/auth/account/123 \
  -H "Authorization: Bearer <service-token>" \
  -H "X-Service-Name: giveaway-service"
```

#### Decrypt Bot Token

```bash
curl -X GET https://your-auth-service.railway.app/api/auth/decrypt-token/123 \
  -H "Authorization: Bearer <service-token>" \
  -H "X-Service-Name: bot-service"
```


### JavaScript SDK Examples

#### Frontend Registration

```javascript
// Register a new account
async function registerAccount(botToken) {
  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        bot_token: botToken
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log('Account registered:', data.account_id);
      return data;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Registration failed:', error.message);
    throw error;
  }
}
```

#### Frontend Login

```javascript
// Login with bot token
async function login(botToken) {
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Include cookies
      body: JSON.stringify({
        bot_token: botToken
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      console.log('Login successful:', data.account_info);
      return data;
    } else {
      throw new Error(data.error);
    }
  } catch (error) {
    console.error('Login failed:', error.message);
    throw error;
  }
}
```

#### Session Verification

```javascript
// Verify current session
async function verifySession() {
  try {
    const response = await fetch('/api/auth/verify-session', {
      method: 'GET',
      credentials: 'include' // Include cookies
    });
    
    const data = await response.json();
    
    if (data.valid) {
      console.log('Session valid:', data.account_info);
      return data;
    } else {
      console.log('Session invalid:', data.error);
      return null;
    }
  } catch (error) {
    console.error('Session verification failed:', error.message);
    return null;
  }
}
```


### Python SDK Examples

#### Service-to-Service Communication

```python
import requests
import os

class AuthServiceClient:
    def __init__(self, base_url, service_name, service_token=None):
        self.base_url = base_url.rstrip('/')
        self.service_name = service_name
        self.service_token = service_token
        self.session = requests.Session()
        
        # Set default headers
        if service_token:
            self.session.headers.update({
                'Authorization': f'Bearer {service_token}',
                'X-Service-Name': service_name
            })
    
    def get_account(self, account_id):
        """Get account information by ID"""
        response = self.session.get(f'{self.base_url}/api/auth/account/{account_id}')
        response.raise_for_status()
        return response.json()
    
    def decrypt_token(self, account_id):
        """Get decrypted bot token for account"""
        response = self.session.get(f'{self.base_url}/api/auth/decrypt-token/{account_id}')
        response.raise_for_status()
        data = response.json()
        return data.get('bot_token')
    
    def verify_session(self, session_cookie):
        """Verify a user session"""
        headers = {'Cookie': f'session={session_cookie}'}
        response = self.session.get(f'{self.base_url}/api/auth/verify-session', headers=headers)
        return response.json()

# Usage example
auth_client = AuthServiceClient(
    base_url='https://your-auth-service.railway.app',
    service_name='giveaway-service',
    service_token=os.getenv('SERVICE_TOKEN')
)

# Get account information
account = auth_client.get_account(123)
print(f"Account: {account['account']['bot_username']}")

# Get bot token for API calls
bot_token = auth_client.decrypt_token(123)
print(f"Bot token: {bot_token[:10]}...")
```


## Security Considerations

### Bot Token Security
- Bot tokens are encrypted using AES-256 before storage
- Tokens are never logged or exposed in error messages
- Decrypted tokens are only provided to authorized services

### Session Security
- Sessions use secure, HttpOnly cookies in production
- Session IDs are cryptographically secure random strings
- Sessions automatically expire after 24 hours
- Invalid sessions are cleaned up automatically

### Rate Limiting
- Different endpoints have appropriate rate limits
- Rate limiting prevents brute force attacks
- Limits are enforced per IP address and per service

### Input Validation
- All inputs are validated and sanitized
- Bot token format is strictly validated
- SQL injection protection through parameterized queries

### CORS Configuration
- CORS is configured to allow cross-origin requests
- Credentials are supported for session-based authentication
- Appropriate headers are allowed for inter-service communication

## Best Practices

### For Frontend Applications
1. Always include `credentials: 'include'` in fetch requests
2. Handle authentication errors gracefully
3. Implement proper session timeout handling
4. Store sensitive data securely (avoid localStorage for tokens)

### For Backend Services
1. Use service authentication headers for inter-service calls
2. Implement proper error handling and retries
3. Cache account information when appropriate
4. Monitor rate limits and implement backoff strategies

### For Bot Token Management
1. Never expose bot tokens in client-side code
2. Rotate bot tokens regularly if compromised
3. Use the decrypt endpoint only when necessary
4. Implement proper access controls for token decryption

## Monitoring and Logging

### Health Monitoring
- Use `/health` endpoint for basic health checks
- Use `/health/detailed` for comprehensive monitoring
- Monitor response times and error rates

### Error Tracking
- All errors include machine-readable error codes
- Implement proper error tracking and alerting
- Monitor rate limit violations

### Performance Metrics
- Track authentication success/failure rates
- Monitor session creation and validation performance
- Track database connection health

