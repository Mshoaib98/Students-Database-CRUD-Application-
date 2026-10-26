# Students Database CRUD API

A beginner-friendly backend internship project using Python, FastAPI, and SQLite.

## Features

- Create a student
- List all students
- Filter students by name, course, or date of birth
- Retrieve a student by ID
- Partially update a student
- Delete a student
- Validate request data
- Return helpful errors for missing students and duplicate emails
- Persist data in a local SQLite database

## Requirements

- Python 3.10 or newer
- Internet connection for installing Python packages (first setup only)

## Setup on Windows PowerShell

```powershell
cd path\to\students_crud_project
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

If PowerShell blocks activation, you can skip activation and run:

```powershell
py -m pip install -r requirements.txt
py -m uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs to test the API interactively.

## Example: create a student

Choose `POST /students`, click **Try it out**, and send:

```json
{
  "name": "Ayesha Khan",
  "date_of_birth": "2005-04-12",
  "email": "ayesha@example.com",
  "phone": "9876543210",
  "course": "BTech AIML",
  "address": "New Delhi",
  "enrollment_date": "2026-08-01"
}
```

At least one of `email` or `phone` is required. Dates must use `YYYY-MM-DD`.

## Endpoint summary

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Check that the API is running |
| POST | `/students` | Create a student |
| GET | `/students` | List students |
| GET | `/students?name=Ayesha` | Filter by name |
| GET | `/students?course=BTech%20AIML` | Filter by course |
| GET | `/students?born_after=2005-01-01` | Filter by birth date |
| GET | `/students/1` | Retrieve student ID 1 |
| PATCH | `/students/1` | Update selected fields |
| DELETE | `/students/1` | Delete student ID 1 |

## Example update

```json
{
  "course": "Computer Science",
  "phone": "9999999999"
}
```

## Important behavior

- Student IDs are generated automatically.
- The SQLite database file `students.db` is created automatically beside `main.py`.
- A missing student returns HTTP `404`.
- Invalid request data returns HTTP `422`.
- A duplicate email returns HTTP `409`.
- A request with no update fields returns HTTP `400`.
- This is a learning project, not a production-ready system with authentication, authorization, backups, or deployment hardening.

