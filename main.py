"""
Students Database CRUD API
Stack: Python + FastAPI + SQLite

Run:
    python -m pip install -r requirements.txt
    uvicorn main:app --reload

Open interactive API docs at:
    http://127.0.0.1:8000/docs
"""

from contextlib import contextmanager
from datetime import date
from pathlib import Path
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

# Store the database beside this Python file.
DATABASE_PATH = Path(__file__).with_name("students.db")

app = FastAPI(
    title="Students Database CRUD API",
    description="Create, read, update, and delete student records.",
    version="1.0.0",
)


@contextmanager
def get_connection():
    """Open a database connection and always close it afterward."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    """Create the students table if it does not already exist."""
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                course TEXT,
                address TEXT,
                enrollment_date TEXT
            )
            """
        )


# Initialize the table when this module is loaded.
initialize_database()


class StudentCreate(BaseModel):
    """Fields required/accepted when creating a student."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    date_of_birth: date
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    course: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=250)
    enrollment_date: Optional[date] = None

    @model_validator(mode="after")
    def require_contact_method(self):
        if not self.email and not self.phone:
            raise ValueError("Provide at least an email address or phone number.")
        return self


class StudentUpdate(BaseModel):
    """All fields are optional so the client can update only what changed."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    date_of_birth: Optional[date] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=30)
    course: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=250)
    enrollment_date: Optional[date] = None


def row_to_student(row: sqlite3.Row) -> dict:
    """Convert a SQLite row into a normal dictionary for JSON output."""
    student = dict(row)
    return student


@app.get("/")
def home():
    """A simple health/info endpoint."""
    return {
        "message": "Students Database CRUD API is running",
        "docs": "/docs",
    }


@app.post("/students", status_code=201)
def create_student(student: StudentCreate):
    """Create and return a student record."""
    values = student.model_dump(mode="json")
    columns = ", ".join(values.keys())
    placeholders = ", ".join("?" for _ in values)
    sql = f"INSERT INTO students ({columns}) VALUES ({placeholders})"

    try:
        with get_connection() as connection:
            cursor = connection.execute(sql, tuple(values.values()))
            new_id = cursor.lastrowid
            row = connection.execute(
                "SELECT * FROM students WHERE student_id = ?", (new_id,)
            ).fetchone()
            return row_to_student(row)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="A student with this email address already exists.",
        ) from exc


@app.get("/students")
def list_students(
    name: Optional[str] = Query(default=None, description="Filter by part of a name"),
    course: Optional[str] = Query(default=None, description="Filter by course"),
    born_after: Optional[date] = Query(
        default=None, description="Only students born after this date"
    ),
):
    """List students, optionally filtering by name, course, or date of birth."""
    sql = "SELECT * FROM students WHERE 1 = 1"
    parameters = []

    if name:
        sql += " AND name LIKE ?"
        parameters.append(f"%{name}%")

    if course:
        sql += " AND course LIKE ?"
        parameters.append(f"%{course}%")

    if born_after:
        sql += " AND date_of_birth > ?"
        parameters.append(born_after.isoformat())

    sql += " ORDER BY student_id"

    with get_connection() as connection:
        rows = connection.execute(sql, parameters).fetchall()
        return [row_to_student(row) for row in rows]


@app.get("/students/{student_id}")
def get_student(student_id: int):
    """Return one student, or a 404 error if the ID does not exist."""
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Student not found.")

    return row_to_student(row)


@app.patch("/students/{student_id}")
def update_student(student_id: int, changes: StudentUpdate):
    """Update only fields supplied by the client."""
    updates = changes.model_dump(mode="json", exclude_unset=True)

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one field to update.",
        )

    # Do not let a request containing only null values erase every contact method.
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()

        if existing is None:
            raise HTTPException(status_code=404, detail="Student not found.")

        resulting_email = updates.get("email", existing["email"])
        resulting_phone = updates.get("phone", existing["phone"])
        if not resulting_email and not resulting_phone:
            raise HTTPException(
                status_code=422,
                detail="A student must have an email address or phone number.",
            )

        assignments = ", ".join(f"{column} = ?" for column in updates)
        values = list(updates.values())
        values.append(student_id)

        try:
            connection.execute(
                f"UPDATE students SET {assignments} WHERE student_id = ?", values
            )
        except sqlite3.IntegrityError as exc:
            raise HTTPException(
                status_code=409,
                detail="A student with this email address already exists.",
            ) from exc

        row = connection.execute(
            "SELECT * FROM students WHERE student_id = ?", (student_id,)
        ).fetchone()
        return row_to_student(row)


@app.delete("/students/{student_id}")
def delete_student(student_id: int):
    """Delete one student and confirm the deletion."""
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM students WHERE student_id = ?", (student_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Student not found.")

    return {"message": "Student deleted successfully.", "student_id": student_id}
