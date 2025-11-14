from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import sqlite3
import csv
import io
import os
import logging
import time
import signal
import json
from contextlib import contextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SQLite HTTP API", description="Expose SQLite database via HTTP REST API with CSV or JSON responses")

# SQLite database path - can be overridden via environment variable
DB_PATH = os.getenv("SQLITE_DB_PATH", "/data/database.db")
QUERY_TIMEOUT = int(os.getenv("QUERY_TIMEOUT", "300"))  # Default 5 minutes
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10000"))  # Rows to process per batch
LOG_QUERY_TIMING = os.getenv("LOG_QUERY_TIMING", "true").lower() == "true"


class QueryRequest(BaseModel):
    sql: str
    delimiter: Optional[str] = ","
    format: Optional[str] = "csv"  # "csv" or "json"


class TimeoutError(Exception):
    """Custom timeout exception"""
    pass


@contextmanager
def timeout_handler(seconds):
    """Context manager for query timeout"""
    def timeout_signal(signum, frame):
        raise TimeoutError(f"Query execution exceeded {seconds} seconds")
    
    # Set up signal handler (Unix only)
    old_handler = signal.signal(signal.SIGALRM, timeout_signal)
    signal.alarm(seconds)
    
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def get_db_connection():
    """Create and return an optimized SQLite database connection."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail=f"Database file not found: {DB_PATH}")
    
    start_time = time.time()
    try:
        conn = sqlite3.connect(DB_PATH, timeout=60.0)
        
        # Optimize for large database queries
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        conn.execute("PRAGMA cache_size=-64000")  # 64MB cache (negative means KB)
        conn.execute("PRAGMA temp_store=MEMORY")  # Store temp tables in memory
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O
        conn.execute("PRAGMA synchronous=NORMAL")  # Faster writes, still safe
        conn.execute("PRAGMA foreign_keys=OFF")  # Faster for SELECT queries
        
        conn.row_factory = sqlite3.Row  # This allows column access by name
        
        conn_time = time.time() - start_time
        if LOG_QUERY_TIMING:
            logger.info(f"Database connection established in {conn_time:.3f}s")
        
        return conn
    except Exception as e:
        conn_time = time.time() - start_time
        logger.error(f"Failed to connect to database after {conn_time:.3f}s: {str(e)}")
        raise


def stream_csv_rows(all_rows, column_names, delimiter):
    """Generator function to stream CSV rows from pre-fetched data."""
    try:
        # Write header
        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)
        writer.writerow(column_names)
        yield output.getvalue()
        output.close()
        
        # Process rows in batches
        batch_count = 0
        row_count = 0
        total_rows = len(all_rows)
        
        logger.info(f"Starting to stream {total_rows:,} rows (batch size: {BATCH_SIZE})")
        
        for i in range(0, total_rows, BATCH_SIZE):
            batch = all_rows[i:i + BATCH_SIZE]
            batch_count += 1
            batch_size = len(batch)
            row_count += batch_size
            
            # Process batch
            output = io.StringIO()
            writer = csv.writer(output, delimiter=delimiter)
            for row in batch:
                writer.writerow(row)
            csv_batch = output.getvalue()
            output.close()
            
            yield csv_batch
            
            # Log progress every 5 batches or at the end
            if batch_count % 5 == 0 or i + BATCH_SIZE >= total_rows:
                logger.info(f"Progress: {row_count:,}/{total_rows:,} rows streamed ({batch_count} batches)")
        
        logger.info(f"Query complete: {row_count:,} total rows streamed in {batch_count} batches")
        
    except Exception as e:
        logger.error(f"Error streaming CSV rows: {str(e)}")
        raise


def stream_json_rows(all_rows, column_names):
    """Generator function to stream JSON rows from pre-fetched data."""
    try:
        # Start JSON array
        yield "[\n"
        
        total_rows = len(all_rows)
        first_row = True
        
        logger.info(f"Starting to stream {total_rows:,} rows as JSON")
        
        # Process rows in batches
        for i, row in enumerate(all_rows):
            # Convert row to dictionary
            row_dict = {column_names[j]: row[j] for j in range(len(column_names))}
            json_str = json.dumps(row_dict, ensure_ascii=False)
            
            # Yield JSON with proper formatting
            if not first_row:
                yield ",\n"
            else:
                first_row = False
            yield "  " + json_str
            
            # Log progress every 1000 rows or at the end
            if (i + 1) % 1000 == 0 or i + 1 == total_rows:
                logger.info(f"Progress: {i + 1:,}/{total_rows:,} rows streamed")
        
        # Close JSON array
        yield "\n]"
        
        logger.info(f"Query complete: {total_rows:,} total rows streamed as JSON")
        
    except Exception as e:
        logger.error(f"Error streaming JSON rows: {str(e)}")
        raise


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "SQLite HTTP API",
        "version": "2.1.0",
        "endpoints": {
            "/query": "Query the database using POST with JSON body (supports CSV or JSON output)",
            "/health": "Health check endpoint"
        },
        "features": {
            "formats": ["csv", "json"],
            "streaming": True,
            "query_timeout": QUERY_TIMEOUT,
            "batch_size": BATCH_SIZE,
            "logging": LOG_QUERY_TIMING
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    start_time = time.time()
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        response_time = time.time() - start_time
        return {
            "status": "healthy",
            "database": DB_PATH,
            "response_time_ms": round(response_time * 1000, 2)
        }
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Health check failed after {response_time:.3f}s: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")


@app.post("/query")
async def query(request: QueryRequest):
    """
    Execute a SQL SELECT query and return results as CSV or JSON (streaming).
    
    Request Body (JSON):
    - sql: SQL SELECT query (required)
    - delimiter: CSV delimiter (optional, default: comma) - only used for CSV format
    - format: Response format (optional, default: "csv") - "csv" or "json"
    
    Example (CSV):
    {
        "sql": "SELECT * FROM users WHERE name = 'John Doe'",
        "delimiter": ",",
        "format": "csv"
    }
    
    Example (JSON):
    {
        "sql": "SELECT * FROM users WHERE name = 'John Doe'",
        "format": "json"
    }
    """
    query_start_time = time.time()
    logger.info("=" * 80)
    logger.info(f"Query received: {request.sql[:100]}..." if len(request.sql) > 100 else f"Query received: {request.sql}")
    
    # Validate and normalize format
    # request.format has a default value of "csv" in the Pydantic model
    # If user provides "format": "json" in the request, it will override the default
    raw_format = request.format if request.format is not None else "csv"
    provided_format = str(raw_format).strip().lower()
    
    logger.info(f"DEBUG - Raw format from request: '{raw_format}' (type: {type(raw_format)})")
    logger.info(f"DEBUG - Normalized format: '{provided_format}'")
    
    if provided_format not in ["csv", "json"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid format '{request.format}'. Supported formats: 'csv', 'json'"
        )
    
    request_format = provided_format
    logger.info(f"Using format: {request_format}")
    if request_format == "csv":
        logger.info(f"Delimiter: {request.delimiter}")
    
    # Validate that only SELECT queries are allowed
    sql_upper = request.sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        logger.warning(f"Non-SELECT query rejected: {sql_upper[:50]}...")
        raise HTTPException(
            status_code=400,
            detail="Only SELECT queries are allowed for security reasons"
        )
    
    conn = None
    cursor = None
    
    try:
        # Get database connection
        conn_start = time.time()
        conn = get_db_connection()
        conn_time = time.time() - conn_start
        logger.info(f"Connection time: {conn_time:.3f}s")
        
        cursor = conn.cursor()
        
        # Execute query with timeout (on Unix systems)
        exec_start = time.time()
        try:
            if hasattr(signal, 'SIGALRM'):  # Unix systems
                with timeout_handler(QUERY_TIMEOUT):
                    cursor.execute(request.sql)
            else:
                # Windows doesn't support SIGALRM, just execute
                logger.warning("SIGALRM not available (Windows?), timeout not enforced")
                cursor.execute(request.sql)
        except TimeoutError as e:
            exec_time = time.time() - exec_start
            logger.error(f"Query timeout after {exec_time:.3f}s: {str(e)}")
            raise HTTPException(
                status_code=408,
                detail=f"Query execution timeout after {QUERY_TIMEOUT} seconds"
            )
        
        exec_time = time.time() - exec_start
        logger.info(f"Query execution time: {exec_time:.3f}s")
        
        # Get column names
        if cursor.description is None:
            logger.warning("Query returned no results")
            raise HTTPException(status_code=400, detail="Query returned no columns (empty result set)")
        
        column_names = [description[0] for description in cursor.description]
        logger.info(f"Columns: {', '.join(column_names)}")
        
        # Fetch all rows in the main thread (SQLite is not thread-safe)
        # We'll fetch in batches to manage memory
        fetch_start = time.time()
        all_rows = []
        fetch_batch_count = 0
        
        logger.info(f"Fetching all rows (batch size: {BATCH_SIZE})")
        while True:
            rows = cursor.fetchmany(BATCH_SIZE)
            if not rows:
                break
            all_rows.extend(rows)
            fetch_batch_count += 1
            if fetch_batch_count % 10 == 0:
                logger.info(f"Fetched {len(all_rows):,} rows so far...")
        
        fetch_time = time.time() - fetch_start
        total_rows = len(all_rows)
        logger.info(f"Fetched {total_rows:,} total rows in {fetch_time:.3f}s ({fetch_batch_count} batches)")
        
        # Close cursor and connection in the main thread (before streaming)
        cursor.close()
        conn.close()
        logger.info("Database connection closed")
        
        # Stream response based on format (now using pre-fetched data)
        if request_format == "json":
            def generate():
                try:
                    for chunk in stream_json_rows(all_rows, column_names):
                        yield chunk
                except Exception as e:
                    logger.error(f"Error in JSON stream generator: {str(e)}")
                    raise
            
            media_type = "application/json"
            filename = "query_result.json"
        else:  # CSV format
            def generate():
                try:
                    for chunk in stream_csv_rows(all_rows, column_names, request.delimiter):
                        yield chunk
                except Exception as e:
                    logger.error(f"Error in CSV stream generator: {str(e)}")
                    raise
            
            media_type = "text/csv"
            filename = "query_result.csv"
        
        total_time = time.time() - query_start_time
        logger.info(f"Total request processing time: {total_time:.3f}s")
        logger.info("=" * 80)
        
        return StreamingResponse(
            generate(),
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Query-Time": f"{exec_time:.3f}",
                "X-Total-Time": f"{total_time:.3f}",
                "X-Format": request_format
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        if conn:
            conn.close()
        raise
    except sqlite3.Error as e:
        exec_time = time.time() - query_start_time if 'exec_time' not in locals() else exec_time
        logger.error(f"SQLite error after {exec_time:.3f}s: {str(e)}")
        if conn:
            conn.close()
        raise HTTPException(status_code=400, detail=f"SQLite error: {str(e)}")
    except Exception as e:
        total_time = time.time() - query_start_time
        logger.error(f"Unexpected error after {total_time:.3f}s: {str(e)}", exc_info=True)
        if conn:
            conn.close()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    logger.info(f"Database: {DB_PATH}")
    logger.info(f"Query timeout: {QUERY_TIMEOUT}s")
    logger.info(f"Batch size: {BATCH_SIZE}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=None)
