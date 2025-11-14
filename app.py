from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Optional
import sqlite3
import csv
import io
import os

app = FastAPI(title="SQLite HTTP CSV API", description="Expose SQLite database via HTTP REST API with CSV responses")

# SQLite database path - can be overridden via environment variable
DB_PATH = os.getenv("SQLITE_DB_PATH", "/data/database.db")


class QueryRequest(BaseModel):
    sql: str
    delimiter: Optional[str] = ","


def get_db_connection():
    """Create and return a SQLite database connection."""
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=404, detail=f"Database file not found: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # This allows column access by name
    return conn


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "SQLite HTTP CSV API",
        "version": "1.0.0",
        "endpoints": {
            "/query": "Query the database using POST with JSON body",
            "/health": "Health check endpoint"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "database": DB_PATH}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")


@app.post("/query")
async def query(request: QueryRequest):
    """
    Execute a SQL SELECT query and return results as CSV.
    
    Request Body (JSON):
    - sql: SQL SELECT query (required)
    - delimiter: CSV delimiter (optional, default: comma)
    
    Example:
    {
        "sql": "SELECT * FROM users WHERE name = 'John Doe'",
        "delimiter": ","
    }
    """
    # Validate that only SELECT queries are allowed
    sql_upper = request.sql.strip().upper()
    if not sql_upper.startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT queries are allowed for security reasons"
        )
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Execute the query
        cursor.execute(request.sql)
        
        # Fetch column names
        column_names = [description[0] for description in cursor.description]
        
        # Fetch all rows
        rows = cursor.fetchall()
        
        conn.close()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output, delimiter=request.delimiter)
        
        # Write header
        writer.writerow(column_names)
        
        # Write data rows
        for row in rows:
            writer.writerow(row)
        
        # Prepare CSV response
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="query_result.csv"'
            }
        )
        
    except sqlite3.Error as e:
        raise HTTPException(status_code=400, detail=f"SQLite error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

