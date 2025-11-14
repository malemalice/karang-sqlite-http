# SQLite HTTP CSV API

A lightweight REST API service that exposes SQLite databases via HTTP endpoints, returning query results in CSV format.

## Features

- Query SQLite databases via HTTP POST requests
- Returns results in **CSV or JSON format** (streaming for large result sets)
- Supports custom CSV delimiters
- **Performance optimized for large databases (3GB+)**:
  - Streaming response (no memory overload)
  - Batch processing for efficient memory usage
  - SQLite WAL mode and cache optimizations
  - Query timeout protection
  - Progress logging and performance metrics
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

5. **Query the database (CSV format - default):**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM actor LIMIT 5", "format": "csv"}'
```

   **Or query as JSON:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM actor LIMIT 5", "format": "json"}'
```

6. **View logs (with performance debugging):**
```bash
# View all logs
docker-compose logs -f

# View only recent logs with timestamps
docker-compose logs -f --tail=100

# Follow logs in real-time (great for monitoring query performance)
docker-compose logs -f sqllite-http-csv
```

   The logs will show detailed performance information:
   - Query execution times
   - Connection times
   - Progress updates every 5 seconds for long-running queries
   - Rows processed per second
   - Memory usage indicators

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
Execute a SQL SELECT query and return results as CSV or JSON.

**Request Body (JSON):**
```json
{
  "sql": "SELECT * FROM table_name WHERE condition",
  "delimiter": ",",
  "format": "csv"
}
```

**Parameters:**
- `sql` (required): SQL SELECT query to execute
- `delimiter` (optional): CSV delimiter character (default: `,`) - only used for CSV format
- `format` (optional): Response format - `"csv"` or `"json"` (default: `"csv"`)

**Example 1: List all available tables (CSV)**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT name FROM sqlite_master WHERE type=\"table\" ORDER BY name", "format": "csv"}'
```

**Example 1b: List all available tables (JSON)**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT name FROM sqlite_master WHERE type=\"table\" ORDER BY name", "format": "json"}'
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

**Example 8: Complex JOIN with date range filter**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT a.first_name, a.last_name, f.title, f.release_year FROM actor a INNER JOIN film_actor fa ON a.actor_id = fa.actor_id INNER JOIN film f ON fa.film_id = f.film_id WHERE f.release_year BETWEEN 2005 AND 2006 ORDER BY f.release_year, a.last_name"
  }'
```

**Example 9: Complex query with multiple JOINs and date WHERE clause**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT c.first_name, c.last_name, r.rental_date, f.title, p.amount FROM customer c INNER JOIN rental r ON c.customer_id = r.customer_id INNER JOIN inventory i ON r.inventory_id = i.inventory_id INNER JOIN film f ON i.film_id = f.film_id INNER JOIN payment p ON r.rental_id = p.rental_id WHERE DATE(r.rental_date) >= \"2005-05-24\" AND DATE(r.rental_date) <= \"2005-06-30\" ORDER BY r.rental_date DESC"
  }'
```

**Example 10: Query with tab delimiter**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT * FROM actor LIMIT 5",
    "delimiter": "\t"
  }'
```

**Example using Python requests (CSV):**
```python
import requests

url = "http://localhost:8000/query"
payload = {
    "sql": "SELECT * FROM actor WHERE first_name = 'PENELOPE'",
    "delimiter": ",",
    "format": "csv"
}

response = requests.post(url, json=payload)
print(response.text)  # CSV output
```

**Example using Python requests (JSON):**
```python
import requests
import json

url = "http://localhost:8000/query"
payload = {
    "sql": "SELECT * FROM actor WHERE first_name = 'PENELOPE'",
    "format": "json"
}

response = requests.post(url, json=payload)
data = response.json()  # Parse JSON response
print(json.dumps(data, indent=2))  # Pretty print JSON
```

**Example using JavaScript (fetch - CSV):**
```javascript
fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    sql: 'SELECT * FROM actor LIMIT 10',
    delimiter: ',',
    format: 'csv'
  })
})
.then(response => response.text())
.then(csv => console.log(csv));
```

**Example using JavaScript (fetch - JSON):**
```javascript
fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    sql: 'SELECT * FROM actor LIMIT 10',
    format: 'json'
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

## Configuration

### Environment Variables

- `SQLITE_DB_PATH`: Path to SQLite database file (default: `/data/database.db`)
- `PORT`: HTTP server port (default: `8000`)
- `QUERY_TIMEOUT`: Query execution timeout in seconds (default: `300` = 5 minutes)
- `BATCH_SIZE`: Number of rows to process per batch for streaming (default: `10000`)
- `LOG_QUERY_TIMING`: Enable detailed query timing logs (default: `true`)

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

- `200 OK`: Successful query execution (streaming CSV response)
- `400 Bad Request`: Invalid SQL query (non-SELECT) or SQLite error
- `404 Not Found`: Database file not found
- `408 Request Timeout`: Query execution exceeded timeout limit (default: 5 minutes)
- `500 Internal Server Error`: Unexpected server error
- `503 Service Unavailable`: Database connection failure

**Response Headers:**
- `X-Query-Time`: Query execution time in seconds
- `X-Total-Time`: Total request processing time in seconds
- `X-Format`: Response format used (`csv` or `json`)

## Performance Optimizations

For large databases (3GB+), the service includes several performance optimizations:

### Streaming Response
- Results are streamed to the client instead of loading everything into memory
- Processes rows in batches (configurable via `BATCH_SIZE`)
- Reduces memory usage and enables faster response start time

### SQLite Optimizations
- **WAL Mode**: Write-Ahead Logging for better concurrency
- **Cache Size**: 64MB cache for faster reads
- **Memory-Mapped I/O**: 256MB for efficient large file access
- **Temporary Storage**: Uses memory for temporary tables
- **Query Timeout**: Prevents runaway queries (default: 5 minutes)

### Logging and Monitoring
- Detailed timing information for each query phase
- Progress logging every 5 seconds for long-running queries
- Performance metrics in response headers (`X-Query-Time`, `X-Total-Time`)
- Logs rows/second processing rate

**Example log output:**
```
2024-01-01 10:00:00 - INFO - Query received: SELECT * FROM large_table WHERE ...
2024-01-01 10:00:00 - INFO - Connection time: 0.125s
2024-01-01 10:00:05 - INFO - Query execution time: 4.876s
2024-01-01 10:00:10 - INFO - Progress: 50,000 rows processed | Batch 5 (10,000 rows) in 0.234s | Rate: 42,735 rows/sec
```

## Limitations

- Read-only operations (SELECT queries only)
- Single database connection per request
- No authentication/authorization (should be added for production)
- No query result caching
- No rate limiting (should be added for production)
- Query timeout only works on Unix systems (not Windows)

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

