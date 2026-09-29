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
   pip install -r requirements.txt
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

## Order suggestions

Order suggestions retrieve up to five recent orders from the signed-in user and selected kitchen directly from Django's database, then use a LangChain Groq chain to draft a suggestion. No vector database, embedding model, or sync command is needed. Groq requires an API key and applies account-specific rate limits; check its current plan and model availability before use. Only item names, quantities, and notes are sent to Groq; customer names are not included. Avoid putting sensitive information in order notes.

1. Create a Groq account and an API key in its developer console.

2. Enter the key securely in PowerShell before starting Django (keep it private and do not commit it):

   ```powershell
   $secure = Read-Host 'Enter your Groq API key' -AsSecureString
   $env:GROQ_API_KEY = [System.Net.NetworkCredential]::new('', $secure).Password
   ```

3. Install the project requirements and start Django in that same PowerShell window. The default model is `openai/gpt-oss-20b`; set `GROQ_MODEL` to another model available to your account if needed.

Orders are available to suggestions immediately after they are saved. If the API key is missing, the hosted service is unavailable, or there is no matching history, order creation and saving continue normally.

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

## GRK API KEY

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 [made it public intensionally]
