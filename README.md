# 🚀 NL to SQL Compiler

<p align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite)
![Google Gemini](https://img.shields.io/badge/Google-Gemini_AI-4285F4?style=for-the-badge&logo=google)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

</p>

---

## 📖 Overview

The **NL to SQL Compiler** is an AI-powered web application that converts **Natural Language queries** into executable **SQL statements**. It combines **Google Gemini AI** with **compiler design concepts** such as lexical analysis, parsing, semantic validation, and query optimization to generate accurate SQL queries.

The generated SQL is executed on a **SQLite database**, and the results are displayed through an interactive web interface.

---

# ✨ Features

- 🤖 Natural Language to SQL conversion using Google Gemini AI
- ⚙️ Compiler-inspired architecture
- 🔍 SQL syntax validation
- 🧠 Semantic error detection
- ⚡ Query optimization
- 🗄️ SQLite database execution
- 🌐 Interactive web interface
- 📊 Query result visualization
- 📝 Clean and modular backend architecture

---

# 🏗️ System Architecture


<p align="center">

<img src="assets/architecture.png" width="850">

</p>

---

# 📸 Application Screenshots

## 🏠 Home Page

<p align="center">

<img src="assets/home.png" width="900">

</p>

---

## 💬 Natural Language Input

<p align="center">

<img src="assets/input.png" width="900">

</p>

---

## 🧠 Generated SQL

<p align="center">

<img src="assets/sql_output.png" width="900">

</p>

---

## 📊 Execution Result

<p align="center">

<img src="assets/execution.png" width="900">

</p>

---

## ❌ Error Detection

<p align="center">

<img src="assets/error.png" width="900">

</p>

---

# 🎥 Demo

<p align="center">

<img src="assets/demo.gif">

</p>

---

# ⚙️ Technology Stack

## Frontend

- HTML5
- CSS3
- JavaScript

## Backend

- Python
- FastAPI
- Pydantic

## Database

- SQLite

## AI

- Google Gemini API

## Compiler Components

- Lexer
- Parser
- Semantic Analyzer
- SQL Optimizer

---

# 📂 Project Structure

```text
AI-NL2SQL-Compiler/
│
├── backend/
│   ├── compiler/
│   │   ├── lexer.py
│   │   ├── parser.py
│   │   ├── semantic.py
│   │   ├── optimizer.py
│   │   ├── codegen.py
│   │   ├── diagnostics.py
│   │   └── ir.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   └── schema.py
│   │
│   ├── main.py
│   └── test.db
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── assets/
│   ├── home.png
│   ├── input.png
│   ├── sql_output.png
│   ├── execution.png
│   ├── error.png
│   ├── architecture.png
│   └── demo.gif
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

# 🚀 Installation

## Clone the repository

```bash
git clone https://github.com/sreejamukkara/AI-NL2SQL-Compiler.git
```

## Go to the project folder

```bash
cd AI-NL2SQL-Compiler
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Start the backend

```bash
cd backend
uvicorn main:app --reload
```

The backend will start at

```
http://127.0.0.1:8000
```

Open `frontend/index.html` in your browser to use the application.

---

# 💡 Example

### Natural Language Query

```text
Show all employees whose salary is greater than 50000.
```

### Generated SQL

```sql
SELECT *
FROM employees
WHERE salary > 50000;
```

---

# 🎯 Future Enhancements

- Support for MySQL and PostgreSQL
- User authentication
- Query history
- Export results to CSV/PDF
- Voice-based SQL generation
- Explain generated SQL
- Dashboard with analytics
- Dark mode
- Multi-database support

---

# 👩‍💻 Author

**Mukkara Sreeja**

B.Tech Computer Science Engineering

Interested in:
- Artificial Intelligence
- Compiler Design
- Database Systems
- Full Stack Development

GitHub:
https://github.com/sreejamukkara

---

# 📄 License

This project is licensed under the MIT License.

---

⭐ **If you found this project useful, consider giving it a star on GitHub!**
