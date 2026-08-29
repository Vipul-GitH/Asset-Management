# Dr. Bhasin's Lab Asset Management System

A FastAPI + Jinja V1 for the full operational lifecycle of laboratory, IT, office and furniture assets. The portal is server-hosted with Jinja, plain CSS and lightweight JavaScript, so Node.js is not required.

## Quick start (Windows)

1. Start **MySQL** from the XAMPP Control Panel.
2. Run `py app.py` from the project folder. On the first run it creates `.env` and `.venv`, installs dependencies, and applies database migrations automatically.
3. Open https://labmate.bhasinpathlabs.com:4674. API documentation is at https://labmate.bhasinpathlabs.com:4674/docs.

HTTPS uses `certs/fullchain.pem` and `certs/privkey.pem`. Certificate files are intentionally excluded from Git and must be installed separately on each server.

The application uses its local `asset_management.users` table. Its schema and initial data were copied from `hiccup_ticket.users`; no runtime Hiccup database connection is required. Active users select their name from login suggestions and use their DOB as a `DDMMYYYY` password (for example, `10/04/2003` becomes `10042003`). DOB authentication is temporary and should be replaced before any shared deployment.

The application has four roles only: `Administrator`, `Asset Manager`, `Technician`, and `Employee`. New users default to the Employee role (`role_id = 7`).

## Database and migrations

Database migrations live in `backend/alembic/versions`. The first `py app.py` run applies them with Alembic. The application uses the MySQL/MariaDB connection configured in `.env`.

On application startup, a configured MySQL/MariaDB database is created automatically when it does not exist, followed by any missing tables. The configured database user must have `CREATE DATABASE` permission. Existing databases and data are never dropped.

## Main API groups

`/api/assets`, `/api/tickets`, `/api/pm`, `/api/contracts`, `/api/movements`, `/api/dashboard`, and public `/q/{public_token}`. Public QR data never includes holding class or purchase/contract values. QR tokens are random rather than numerical asset IDs.

## Files, reminders and WhatsApp

Files are placed under `UPLOAD_DIR` (default `uploads/`) and never stored as BLOBs. The notification/WhatsApp integration point is intentionally configured as `WHATSAPP_MODE=mock` for local V1; no messages are sent. PM schedule due dates drive dashboard reminders; a production scheduler/provider can consume this safely without changing workflow records.

## Contract renewal workflow

A renewal request creates an administrator approval. Approval changes the contract to `RENEWAL_APPROVED`; the Contracts page then shows **Complete renewal**. The final form records the new dates, value, reference, optional document and notes, updates the active contract, and preserves the previous values in `contract_renewals` history. Rejected requests restore the appropriate active/expired state, and duplicate open renewal requests are blocked.

## Tests

From `backend`, run `..\.venv\Scripts\python -m pytest -q`. Run `..\.venv\Scripts\alembic.exe upgrade head` and `..\.venv\Scripts\alembic.exe check` to verify the MySQL migration state. Tests cover QR sensitive-field exclusion, ticket restoration/closure and downtime, PM report enforcement, lifecycle approvals, calibration completion, and repeat-breakdown reporting. The application contains transactional transfer, responsibility, issue/return, movement and ticket workflows.

## Backup and troubleshooting

Back up the MySQL database and `backend/uploads` together. If startup reports a database connection error, confirm that XAMPP MySQL is running and that the port and credentials in `.env` match phpMyAdmin.

## Project structure

```text
backend/
  alembic/             Database migrations
  app/
    api/               API routes
    core/              Configuration and security
    db/                Database connection
    models/            SQLAlchemy models
    schemas/           Request/response schemas
    services/          Business workflows
    static/            CSS, JavaScript and logo
    templates/         Jinja pages
  tests/               Backend workflow tests
  uploads/             User-uploaded documents
.vscode/               Project formatter settings
.env                    Local environment settings
app.py                  Single setup and application launcher
```
