from fastapi import FastAPI
from app.database import get_connection
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Flight Scanner")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-test")
def db_test():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM routes;")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return {"routes": rows}
