import sqlite3
import os

DB_PATH = "test.db"

def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY,
            name TEXT,
            location TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE employees (
            id INTEGER PRIMARY KEY,
            name TEXT,
            salary INTEGER,
            department_id INTEGER,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    ''')
    
    cursor.executemany("INSERT INTO departments (id, name, location) VALUES (?, ?, ?)", [
        (1, "Engineering", "New York"),
        (2, "Sales", "London"),
        (3, "HR", "Paris")
    ])
    
    cursor.executemany("INSERT INTO employees (id, name, salary, department_id) VALUES (?, ?, ?, ?)", [
        (1, "Alice", 75000, 1),
        (2, "Bob", 60000, 1),
        (3, "Charlie", 45000, 2),
        (4, "David", 80000, 1),
        (5, "Eve", 50000, 3),
        (6, "Frank", 55000, 2),
        (7, "Grace", 90000, 1),
        (8, "Heidi", 40000, 3),
        (9, "Ivan", 70000, 2),
        (10, "Judy", 65000, 1)
    ])
    
    conn.commit()
    conn.close()

def get_schema():
    return {
        "employees": ["id", "name", "salary", "department_id"],
        "departments": ["id", "name", "location"]
    }

def get_schema_with_types():
    return {
        "employees": {"id": "INTEGER", "name": "TEXT", "salary": "INTEGER", "department_id": "INTEGER"},
        "departments": {"id": "INTEGER", "name": "TEXT", "location": "TEXT"}
    }

def execute_query(sql):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        
        if sql.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            columns = rows[0].keys() if rows else []
            return {
                "columns": list(columns),
                "rows": [list(row) for row in rows]
            }
        else:
            conn.commit()
            return {"columns": [], "rows": []}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if 'conn' in locals():
            conn.close()
