# AI Tax Agent

A Flask web app for simplified federal income tax calculations (Form 1040-style). Enter your information, get an instant estimate, and optionally use the AI assistant to auto-fill the form from natural language. 

Sample deployment at AWS: http://18.116.242.216:8000

## Features

- **Tax calculator** — Enter gross income, filing status, deductions; get refund/amount owed
- **AI Auto-Fill** — Describe your situation; Gemini fills the form for you
- **Form 1040 view** — Printable/saveable tax return-style output
- **Firm portal** — Tax preparers can log in and view client calculation history
- **2025 brackets** — Uses current-year standard deductions and tax brackets (single, married filing jointly, head of household)

---

## Project structure

```
tax_ai_agent/
├── app.py              # Flask app, routes, validation, DB, AI
├── tax_engine.py       # Tax calculation logic (2025 brackets)
├── requirements.txt
├── .env                # API keys (create this, do not commit)
├── .gitignore
├── static/
│   ├── style.css
│   └── main.js
├── templates/
│   ├── base.html
│   ├── index.html      # Main form
│   ├── results.html
│   ├── tax_form.html   # Form output
│   ├── firm_login.html
│   └── history.html
├── instance/           # SQLite DB (created on first run)
│   └── tax_data.db
└── export_data.py      # CLI to export DB records
```

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | For AI | Google AI API key for Auto-Fill (`GOOGLE_API_KEY` also supported) |
| `DATABASE_URL` | Optional | MySQL/PostgreSQL connection string; defaults to SQLite |

---

## Database

- **Default:** SQLite at `instance/tax_data.db` (created automatically)
- **Reset:** Delete `instance/tax_data.db` to start fresh
- **MySQL/Postgres:** Set `DATABASE_URL` in `.env`

---

## Firm portal (sample login)

For testing the preparer view:

- URL: `/firm/login`
- Credentials: `emp001` / `tax2025` or `admin` / `admin123`

**Note:** Replace with real authentication before any production use.

---

## Disclaimer

This is a **prototype** for demonstration only. Do not use it for actual tax filing. Consult a tax professional for real returns.
