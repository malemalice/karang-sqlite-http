# Technical Requirements Document (TRD)
## SQLite HTTP CSV API

### 1. Project Overview

This project provides a lightweight REST API service that exposes SQLite databases via HTTP endpoints, returning query results in CSV format. The service is containerized using Docker and can be easily deployed using Docker Compose.

### 2. Objectives

- Provide a simple HTTP REST API to query SQLite databases
- Return query results in CSV format
- Support query execution via GET request parameters
- Containerize the service for easy deployment
- Ensure basic security by restricting to SELECT queries only

### 3. Functional Requirements

#### 3.1 Core Functionality
- **FR-1**: The service shall accept HTTP GET requests with SQL query parameters
- **FR-2**: The service shall execute SELECT queries against a SQLite database
- **FR-3**: The service shall return query results in CSV format
- **FR-4**: The service shall support customizable CSV delimiter (default: comma)
- **FR-5**: The service shall include column headers in the CSV output
- **FR-6**: The service shall provide a health check endpoint

#### 3.2 Security Requirements
- **FR-7**: The service shall only accept SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
- **FR-8**: The service shall validate SQL query format before execution
- **FR-9**: The service shall handle SQLite errors gracefully and return appropriate error messages

#### 3.3 API Endpoints

##### 3.3.1 Root Endpoint
- **Path**: `/`
- **Method**: GET
- **Description**: Returns API information and available endpoints
- **Response**: JSON object with service metadata

##### 3.3.2 Health Check Endpoint
- **Path**: `/health`
- **Method**: GET
- **Description**: Checks database connectivity and service health
- **Response**: JSON object with status and database path

##### 3.3.3 Query Endpoint
- **Path**: `/query`
- **Method**: GET
- **Query Parameters**:
  - `sql` (required): SQL SELECT query to execute
  - `delimiter` (optional): CSV delimiter character (default: `,`)
- **Response**: CSV file with query results
- **Example**: `/query?sql=SELECT * FROM users&delimiter=,`

### 4. Non-Functional Requirements

#### 4.1 Performance
- **NFR-1**: The service shall handle concurrent requests efficiently
- **NFR-2**: Query execution time shall be dependent on SQLite database performance

#### 4.2 Reliability
- **NFR-3**: The service shall handle database connection failures gracefully
- **NFR-4**: The service shall return appropriate HTTP status codes for errors
- **NFR-5**: The service shall implement health checks for container orchestration

#### 4.3 Deployment
- **NFR-6**: The service shall be containerized using Docker
- **NFR-7**: The service shall include Docker Compose configuration for easy deployment
- **NFR-8**: Database file path shall be configurable via environment variables

#### 4.4 Compatibility
- **NFR-9**: The service shall use Python 3.11+
- **NFR-10**: The service shall use FastAPI framework for REST API implementation
- **NFR-11**: The service shall be compatible with standard SQLite database files

### 5. Technical Architecture

#### 5.1 Technology Stack
- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Database**: SQLite3 (Python standard library)
- **Containerization**: Docker
- **Orchestration**: Docker Compose

#### 5.2 System Components

1. **API Server**: FastAPI application handling HTTP requests
2. **Query Executor**: SQLite connection and query execution module
3. **CSV Generator**: Converts query results to CSV format
4. **Error Handler**: Manages errors and returns appropriate HTTP responses

#### 5.3 Data Flow

```
Client Request (GET /query?sql=SELECT...)
    ↓
FastAPI Route Handler
    ↓
SQL Query Validation (SELECT only)
    ↓
SQLite Connection
    ↓
Query Execution
    ↓
Result Fetching
    ↓
CSV Formatting
    ↓
HTTP Response (CSV file)
```

### 6. Configuration

#### 6.1 Environment Variables
- `SQLITE_DB_PATH`: Path to SQLite database file (default: `/data/database.db`)
- `PORT`: HTTP server port (default: `8000`)

#### 6.2 Volume Mounts
- Database directory: Mount local directory containing SQLite database file(s) to `/data` in container

### 7. Deployment Architecture

#### 7.1 Docker Container
- Base image: `python:3.11-slim`
- Working directory: `/app`
- Exposed port: `8000`
- Data directory: `/data`

#### 7.2 Docker Compose
- Service name: `sqllite-http-csv`
- Port mapping: `8000:8000`
- Volume mount: `./data:/data`
- Health check: HTTP GET `/health` endpoint

### 8. Error Handling

#### 8.1 Error Types and Responses

| Error Condition | HTTP Status | Response |
|----------------|-------------|----------|
| Database file not found | 404 | JSON error message |
| Invalid SQL (non-SELECT) | 400 | JSON error message |
| SQLite execution error | 400 | JSON error message with SQLite error details |
| Database connection failure | 503 | JSON error message |
| Unexpected server error | 500 | JSON error message |

### 9. Security Considerations

1. **Query Restrictions**: Only SELECT queries are permitted to prevent data modification
2. **Input Validation**: SQL queries are validated before execution
3. **Error Information**: Error messages should not expose sensitive database information in production
4. **Network Security**: Service should be deployed behind a reverse proxy/firewall in production
5. **Database Access**: Limit file system access to the database directory only

### 10. Limitations

1. **Read-Only Operations**: Service only supports SELECT queries (read-only)
2. **Single Database**: Service connects to one SQLite database file at a time
3. **No Authentication**: Service does not implement authentication/authorization (should be added for production)
4. **No Query Caching**: Each request executes the query fresh (no caching mechanism)
5. **No Rate Limiting**: No built-in rate limiting (should be added for production)

### 11. Future Enhancements

- Add authentication and authorization (API keys, JWT tokens)
- Implement query result caching
- Add rate limiting
- Support multiple database connections
- Add query logging and monitoring
- Implement pagination for large result sets
- Add support for JSON response format option
- Add Swagger/OpenAPI documentation endpoint

### 12. Testing Recommendations

1. Unit tests for SQL validation
2. Integration tests for database queries
3. CSV format validation tests
4. Error handling tests
5. Health check endpoint tests
6. Docker container build and run tests

### 13. Maintenance and Operations

1. **Logging**: Implement structured logging for query execution and errors
2. **Monitoring**: Add metrics collection for request count, response times, error rates
3. **Backup**: Ensure SQLite database files are backed up regularly
4. **Updates**: Keep Python dependencies and Docker base images updated for security patches

---

**Document Version**: 1.0  
**Last Updated**: 2024  
**Author**: Development Team

