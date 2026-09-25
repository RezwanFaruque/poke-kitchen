# ChefsTable

A simple Django project for managing kitchen records.

## Project structure

- `chefsTable/` - Django project settings and configuration
- `kitchines/` - application logic, models, views, templates, and URLs
- `env/` - Python virtual environment

## Requirements

- Python 3.10+
- Django 5.2+

## Setup

1. Clone the project:

   ```bash
   git clone <your-repository-url>
   cd chefsTable
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv env
   ```

   On Windows:

   ```bash
   env\Scripts\activate
   ```

   On macOS/Linux:

   ```bash
   source env/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install django
   ```

4. Apply migrations:

   ```bash
   python manage.py migrate
   ```

5. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```

## Run the project

```bash
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

## App overview

This project includes a `Kitchen` model with fields such as:

- `name`
- `member`

The app currently renders data through the `member.html` template.

## Useful commands

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py shell
python manage.py test
```

## Notes

If you are using GitHub, this README gives a basic setup guide for contributors and collaborators.
