# SQLite HTTP CSV API

A lightweight REST API service that exposes SQLite databases via HTTP endpoints, returning query results in CSV format.

## Features

- Query SQLite databases via HTTP POST requests
- Returns results in CSV format
- Supports custom CSV delimiters
- Containerized with Docker and Docker Compose
- Read-only operations (SELECT queries only)

## Quick Start

### Using Docker Compose

1. **Build and start the service:**
```bash
docker-compose up -d --build
```

   Or start without building (if already built):
```bash
docker-compose up -d
```

2. **Force rebuild (no cache) when code changes:**
```bash
docker-compose build --no-cache
docker-compose up -d
```

   Or in one command:
```bash
docker-compose up -d --build --force-recreate
```

3. **Update and restart after code changes:**
```bash
# Stop the service
docker-compose down

# Rebuild with no cache (ensures fresh build)
docker-compose build --no-cache

# Start with rebuild
docker-compose up -d --build
```

   Or quick update (if using volume mounts for development):
```bash
# Restart to pick up changes
docker-compose restart
```

4. **Check if the service is running:**
```bash
curl http://localhost:8000/health
```

5. **Query the database:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM actor LIMIT 5"}'
```

6. **View logs:**
```bash
docker-compose logs -f
```

7. **Stop the service:**
```bash
docker-compose down
```

### Using Docker

1. **Build the image:**
```bash
docker build -t sqllite-http-csv .
```

2. **Force rebuild (no cache) after code changes:**
```bash
docker build --no-cache -t sqllite-http-csv .
```

3. **Run the container:**
```bash
docker run -d \
  -p 8000:8000 \
  -v /Users/kebohitam/Downloads:/data \
  -e SQLITE_DB_PATH=/data/sakila.db \
  sqllite-http-csv
```

4. **Update after code changes:**
```bash
# Stop and remove the container
docker stop sqllite-http-csv
docker rm sqllite-http-csv

# Rebuild the image
docker build --no-cache -t sqllite-http-csv .

# Run again
docker run -d \
  -p 8000:8000 \
  -v /Users/kebohitam/Downloads:/data \
  -e SQLITE_DB_PATH=/data/sakila.db \
  sqllite-http-csv
```

### Using Python Directly

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set environment variable and run:**
```bash
export SQLITE_DB_PATH=/Users/kebohitam/Downloads/sakila.db
python app.py
```

## API Endpoints

### GET `/`
Returns API information and available endpoints.

**Example:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "service": "SQLite HTTP CSV API",
  "version": "1.0.0",
  "endpoints": {
    "/query": "Query the database using POST with JSON body",
    "/health": "Health check endpoint"
  }
}
```

### GET `/health`
Checks database connectivity and service health.

**Example:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "/data/sakila.db"
}
```

### POST `/query`
Execute a SQL SELECT query and return results as CSV.

**Request Body (JSON):**
```json
{
  "sql": "SELECT * FROM table_name WHERE condition",
  "delimiter": ","
}
```

**Parameters:**
- `sql` (required): SQL SELECT query to execute
- `delimiter` (optional): CSV delimiter character (default: `,`)

**Example 1: List all available tables**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT name FROM sqlite_master WHERE type=\"table\" ORDER BY name"}'
```

**Example 2: List tables with schema information**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT name, sql FROM sqlite_master WHERE type=\"table\" ORDER BY name"}'
```

**Example 3: Simple SELECT query**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM actor LIMIT 10"}'
```

**Example 4: SELECT with WHERE clause (using single quotes in SQL)**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT first_name, last_name FROM actor WHERE first_name = \"PENELOPE\""}'
```

**Example 5: SELECT with JOIN and custom delimiter**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT a.first_name, a.last_name, f.title FROM actor a JOIN film_actor fa ON a.actor_id = fa.actor_id JOIN film f ON fa.film_id = f.film_id LIMIT 5",
    "delimiter": ";"
  }'
```

**Example 6: Complex query with multiple conditions**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT first_name, last_name, email FROM customer WHERE active = 1 AND store_id = 1 ORDER BY last_name LIMIT 20"
  }'
```

**Example 7: Query with aggregation**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT COUNT(*) as total_actors, first_name FROM actor GROUP BY first_name ORDER BY total_actors DESC LIMIT 10"
  }'
```

**Example 8: Query with tab delimiter**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM actor LIMIT 5",
    "delimiter": "\t"
  }'
```

**Example using Python requests:**
```python
import requests

url = "http://localhost:8000/query"
payload = {
    "sql": "SELECT * FROM actor WHERE first_name = 'PENELOPE'",
    "delimiter": ","
}

response = requests.post(url, json=payload)
print(response.text)  # CSV output
```

**Example using JavaScript (fetch):**
```javascript
fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    sql: 'SELECT * FROM actor LIMIT 10',
    delimiter: ','
  })
})
.then(response => response.text())
.then(csv => console.log(csv));
```

## Configuration

### Environment Variables

- `SQLITE_DB_PATH`: Path to SQLite database file (default: `/data/database.db`)
- `PORT`: HTTP server port (default: `8000`)

### Docker Compose Configuration

Edit `docker-compose.yml` to customize:
- Database file path
- Port mapping
- Volume mounts

## Security Notes

- Only SELECT queries are allowed (read-only)
- No authentication is implemented (add in production)
- Consider using a reverse proxy with authentication for production use
- Limit network access appropriately

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Successful query execution
- `400 Bad Request`: Invalid SQL query (non-SELECT) or SQLite error
- `404 Not Found`: Database file not found
- `500 Internal Server Error`: Unexpected server error
- `503 Service Unavailable`: Database connection failure

## Limitations

- Read-only operations (SELECT queries only)
- Single database connection at a time
- No authentication/authorization (should be added for production)
- No query result caching
- No rate limiting (should be added for production)

## Development

### Project Structure

```
.
├── app.py                 # FastAPI application
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker image definition
├── docker-compose.yml    # Docker Compose configuration
├── TRD.md               # Technical Requirements Document
└── README.md            # This file
```

### Updating After Code Changes

When you make changes to the code (`app.py`, `requirements.txt`, `Dockerfile`, etc.), you need to rebuild the Docker image to see the changes:

**Using Docker Compose (Recommended):**
```bash
# Option 1: Quick rebuild and restart
docker-compose up -d --build

# Option 2: Force rebuild without cache (clean build)
docker-compose build --no-cache
docker-compose up -d

# Option 3: Full reset (stop, rebuild, start)
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Using Docker directly:**
```bash
# Stop existing container (if running)
docker stop sqllite-http-csv
docker rm sqllite-http-csv

# Rebuild image
docker build --no-cache -t sqllite-http-csv .

# Run container again
docker run -d \
  -p 8000:8000 \
  -v /Users/kebohitam/Downloads:/data \
  -e SQLITE_DB_PATH=/data/sakila.db \
  sqllite-http-csv
```

**Tips:**
- Use `--no-cache` to ensure a completely fresh build and avoid cached layers
- Use `docker-compose logs -f` to monitor logs and see if changes are applied
- After rebuilding, always check the health endpoint to verify the service is running correctly

### Running Tests

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test query endpoint
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT 1 as test"}'
```

## License

This project is provided as-is for demonstration purposes.

