# AGENT.md

This file provides guidance when working with code in this repository.

## Project Overview

This is "Sorting and Scrap Data Management" - a Polish data management application for tracking 100% sorting/control results and internal defects. The application runs as a **Flask web application** with **SQLAlchemy ORM**, **Jinja2 templates**, and **Tailwind CSS** for modern responsive styling.

## Development Commands

### Running the Application
```bash
python run.py
```
- Launches the Flask development server on port 5001
- Creates a local web server accessible at http://localhost:5001
- Debug mode is enabled by default

### Installing Dependencies
```bash
pip install -r requirements.txt
```
- Installs Flask, Flask-SQLAlchemy, and other required packages

### Database Setup
The database is automatically created when the application starts. The SQLite database file `scrap_data.db` is located in the project root.

## Application Architecture

### Main Structure
```
ScrapsDataManagement/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── models.py        # SQLAlchemy models
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── main.py          # Dashboard routes
│   │   ├── reports.py       # Report CRUD routes
│   │   ├── operators.py     # Operator management routes
│   │   └── categories.py    # Category management routes
│   └── templates/
│       ├── base.html        # Base layout with Tailwind CSS
│       ├── components/      # Reusable UI components
│       │   ├── sidebar.html
│       │   └── flash_messages.html
│       ├── dashboard/
│       │   └── index.html   # Reports table view
│       ├── reports/
│       │   ├── create.html  # Add report form
│       │   └── edit.html    # Edit report form
│       ├── operators/
│       │   └── index.html   # Operators management
│       └── categories/
│           └── index.html   # Categories management
├── run.py                   # Application entry point
├── requirements.txt         # Python dependencies
└── scrap_data.db            # SQLite database
```

### Navigation System
The app uses a sidebar navigation with 4 main views:
1. **Dashboard** (`/`) - Main overview with reports table
2. **Dodaj Raport** (`/reports/create`) - Form for entering sorting/control data
3. **Operatorzy** (`/operators`) - Operator management (CRUD)
4. **Kategorie** (`/categories`) - Category/department management (CRUD)

### Database Schema

#### dane_z_raportow (DaneRaportu)
Main report data for sorting/control results. Fields:
- `id` (Integer, primary key)
- `nr_raportu`, `nr_niezgodnosci`, `nr_instrukcji` (String - report identifiers)
- `operator_id` (FK -> operatorzy)
- `selekcja_na_biezaco` (Boolean)
- `ilosc_detali_sprawdzonych` (Integer)
- `zalecana_wydajnosc`, `czas_pracy` (Float)
- `uwagi`, `uwagi_do_wydajnosci` (String)
- `data_selekcji` (Date)
- `braki_defekty` (relationship -> BrakiDefektyRaportu, one-to-many with cascade delete)

#### operatorzy (Operator)
Operator information. Fields:
- `id` (Integer, primary key)
- `nr_operatora` (Integer, unique)
- `imie_nazwisko` (String)
- `dzial_id` (FK -> dzialy)

#### dzialy (KategoriaZrodlaDanych)
Department/category data. Fields:
- `id` (Integer, primary key)
- `opis_kategorii` (String, unique)

#### braki_defekty_raportow (BrakiDefektyRaportu)
Defects/issues related to reports. Multiple defects can be associated with a single report.
Fields:
- `id` (Integer, primary key)
- `raport_id` (FK -> dane_z_raportow)
- `defekt` (String) - name/type of the defect
- `ilosc` (Integer) - quantity of parts with this defect

### Flask Development Patterns

#### Adding Routes
Routes are organized in blueprints located in `app/routes/`. Each blueprint handles a specific feature area.

```python
from flask import Blueprint, render_template
from app import db
from app.models import YourModel

bp = Blueprint('your_feature', __name__)

@bp.route('/')
def index():
    items = YourModel.query.all()
    return render_template('your_feature/index.html', items=items)
```

#### Database Operations
```python
from app import db
from app.models import DaneRaportu, Operator

# Query all
reports = DaneRaportu.query.all()

# Query with filter
report = DaneRaportu.query.get(id)
operators = Operator.query.filter_by(dzial_id=1).all()

# Add new record
new_report = DaneRaportu(nr_raportu="1", ...)
db.session.add(new_report)
db.session.commit()

# Update record
report.uwagi = "Updated notes"
db.session.commit()

# Delete record
db.session.delete(report)
db.session.commit()
```

#### Templates
Templates use Jinja2 syntax and extend `base.html`:

```html
{% extends 'base.html' %}

{% block title %}Page Title{% endblock %}
{% block page_title %}Header Title{% endblock %}

{% block content %}
<!-- Your page content here -->
{% endblock %}
```

## Code Conventions
- Polish language used in UI text and database column names
- Comments and variable names mix Polish and English
- Tailwind CSS classes used for styling (via CDN)
- Flask blueprints for route organization
- Database models use Polish table and column names reflecting business domain

## Styling with Tailwind CSS
The application uses Tailwind CSS via CDN with a custom color palette defined in `base.html`:
- **Primary colors**: Blue gradient (`primary-500` to `primary-700`)
- **Accent colors**: Emerald/green for success states
- **Design system**: Card-based layouts, rounded corners, subtle shadows, gradient backgrounds
