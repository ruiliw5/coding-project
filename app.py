"""
AI Tax Agent Prototype - Flask Application

Handles form submission, validation, tax calculation, and rendering
of the input form, results page, and simplified tax return form.
Stores calculation results in SQLite (or MySQL via DATABASE_URL).
"""

import os
import re
import json
from datetime import datetime

from flask import jsonify
from google import genai
from google.genai import types
from dotenv import load_dotenv
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from werkzeug.datastructures import ImmutableMultiDict

from tax_engine import run_tax_calculation, get_marginal_bracket

app = Flask(__name__)
app.secret_key = "prototype-secret-change-in-production"

load_dotenv()

# Database: use absolute path for SQLite (relative paths fail when CWD differs)
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_DB_DIR = os.path.join(_BASE_DIR, "instance")
_DB_PATH = os.path.join(_DB_DIR, "tax_data.db")
os.makedirs(_DB_DIR, exist_ok=True)

# AI: use GEMINI_API_KEY or GOOGLE_API_KEY from .env
api_key = os.getenv("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None
if not client:
    print("Warning: GEMINI_API_KEY or GOOGLE_API_KEY not found. AI Auto-Fill will be offline.")

# Use DATABASE_URL only for MySQL/Postgres; for SQLite always use absolute path
_env_db = os.environ.get("DATABASE_URL", "").strip()
if _env_db and (_env_db.startswith("mysql") or _env_db.startswith("postgresql")):
    app.config["SQLALCHEMY_DATABASE_URI"] = _env_db
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + _DB_PATH
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class TaxResult(db.Model):
    """Stored tax calculation for persistence."""
    __tablename__ = "tax_results"

    id = db.Column(db.Integer, primary_key=True)
    client_name = db.Column(db.String(200), nullable=True)
    client_email = db.Column(db.String(200), nullable=True)
    filing_status = db.Column(db.String(50), nullable=False)
    gross_income = db.Column(db.Numeric(12, 2), nullable=False)
    standard_deduction = db.Column(db.Numeric(12, 2))
    additional_deductions = db.Column(db.Numeric(12, 2), default=0)
    total_deductions = db.Column(db.Numeric(12, 2))
    taxable_income = db.Column(db.Numeric(12, 2))
    tax_before_credits = db.Column(db.Numeric(12, 2))
    tax_owed = db.Column(db.Numeric(12, 2))
    federal_withheld = db.Column(db.Numeric(12, 2))
    refund_or_owed = db.Column(db.Numeric(12, 2))
    is_refund = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_result_dict(self):
        """Convert to dict matching _session_to_result format for templates."""
        bracket = get_marginal_bracket(Decimal(str(self.taxable_income)), self.filing_status)
        return {
            "client_name": self.client_name,
            "client_email": self.client_email,
            "filing_status": self.filing_status,
            "marginal_bracket": {
                "rate_pct": bracket["rate_pct"],
                "bracket_label": bracket["bracket_label"],
                "bracket_range": bracket.get("bracket_range", ""),
            },
            "gross_income": Decimal(str(self.gross_income)),
            "standard_deduction": Decimal(str(self.standard_deduction)),
            "additional_deductions": Decimal(str(self.additional_deductions)),
            "total_deductions": Decimal(str(self.total_deductions)),
            "taxable_income": Decimal(str(self.taxable_income)),
            "tax_before_credits": Decimal(str(self.tax_before_credits)),
            "tax_owed": Decimal(str(self.tax_owed)),
            "federal_withheld": Decimal(str(self.federal_withheld)),
            "refund_or_owed": Decimal(str(self.refund_or_owed)),
            "is_refund": self.is_refund,
        }

ALLOWED_FILING_STATUSES = {"single", "married_joint", "head_of_household"}
MAX_INCOME = Decimal("10000000")
MAX_DEDUCTION = Decimal("10000000")
MAX_WITHHELD = Decimal("10000000")


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def sanitize_decimal(value: str, default: Decimal = Decimal("0")) -> Decimal:
    """Parse and sanitize a string to a non-negative Decimal."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return default
    value = str(value).strip()
    if not re.match(r"^\d+(\.\d{1,2})?$", value):
        return default
    try:
        d = Decimal(value)
        return max(Decimal("0"), d) if d >= 0 else default
    except (InvalidOperation, ValueError):
        return default


def validate_and_parse_form(form: ImmutableMultiDict) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    """Validate form data and return (parsed_data, errors)."""
    errors = []

    client_name = (form.get("client_name") or "").strip() or None
    client_email = (form.get("client_email") or "").strip() or None
    if client_email and not EMAIL_RE.match(client_email):
        errors.append("Please enter a valid email address.")

    filing_status = (form.get("filing_status") or "").strip().lower()
    if filing_status not in ALLOWED_FILING_STATUSES:
        errors.append("Please select a valid filing status.")

    gross_income = sanitize_decimal(form.get("gross_income"))
    if gross_income <= 0:
        errors.append("Gross income must be greater than zero.")
    if gross_income > MAX_INCOME:
        errors.append("Gross income exceeds maximum allowed value.")

    additional_deductions = sanitize_decimal(form.get("additional_deductions"))
    if additional_deductions > MAX_DEDUCTION:
        errors.append("Additional deductions exceed maximum allowed value.")

    federal_withheld = sanitize_decimal(form.get("federal_withheld"))
    if federal_withheld > MAX_WITHHELD:
        errors.append("Federal tax withheld exceeds maximum allowed value.")

    if errors:
        return None, errors

    return {
        "client_name": client_name,
        "client_email": client_email,
        "gross_income": gross_income,
        "filing_status": filing_status,
        "additional_deductions": additional_deductions,
        "federal_withheld": federal_withheld,
        "use_standard_deduction": True,
    }, []


@app.route("/")
def index():
    """Serve the main input form."""
    return render_template("index.html", ai_available=client is not None)


@app.route("/calculate", methods=["POST"])
def calculate():
    """Process form submission, run tax calculation, redirect to results."""
    parsed, errors = validate_and_parse_form(request.form)
    if errors:
        for err in errors:
            flash(err, "error")
        return redirect(url_for("index"))

    result = run_tax_calculation(
        gross_income=parsed["gross_income"],
        filing_status=parsed["filing_status"],
        additional_deductions=parsed["additional_deductions"],
        federal_withheld=parsed["federal_withheld"],
        use_standard_deduction=parsed["use_standard_deduction"],
    )

    # Save to database
    tax_record = TaxResult(
        client_name=parsed["client_name"],
        client_email=parsed["client_email"],
        filing_status=parsed["filing_status"],
        gross_income=float(result["gross_income"]),
        standard_deduction=float(result["standard_deduction"]),
        additional_deductions=float(result["additional_deductions"]),
        total_deductions=float(result["total_deductions"]),
        taxable_income=float(result["taxable_income"]),
        tax_before_credits=float(result["tax_before_credits"]),
        tax_owed=float(result["tax_owed"]),
        federal_withheld=float(result["federal_withheld"]),
        refund_or_owed=float(result["refund_or_owed"]),
        is_refund=result["is_refund"],
    )
    db.session.add(tax_record)
    db.session.commit()

    session["tax_result"] = {k: str(v) for k, v in result.items() if k != "marginal_bracket"}
    session["tax_result"]["marginal_bracket"] = {
        "rate_pct": result["marginal_bracket"]["rate_pct"],
        "bracket_label": result["marginal_bracket"]["bracket_label"],
        "bracket_range": result["marginal_bracket"].get("bracket_range", ""),
    }
    session["tax_result"]["client_name"] = parsed["client_name"] or ""
    session["tax_result"]["client_email"] = parsed["client_email"] or ""
    session["tax_result"]["filing_status"] = parsed["filing_status"]
    session["tax_result_id"] = tax_record.id
    return redirect(url_for("results")) 

def _session_to_result(data: dict) -> dict:
    """Convert session-stored strings back to Decimal/bool for templates."""
    result = {}
    skip_keys = {"is_refund", "client_name", "client_email", "filing_status"}
    for k, v in data.items():
        if k == "is_refund":
            result[k] = v == "True"
        elif k == "marginal_bracket":
            result[k] = v if isinstance(v, dict) else {}
        elif k in skip_keys:
            result[k] = v or None
        else:
            result[k] = Decimal(v)
    return result


@app.route("/results")
def results():
    """Display tax calculation results."""
    # Prefer loading from DB if we have an ID (e.g. after page refresh)
    tax_id = session.get("tax_result_id")
    if tax_id:
        record = TaxResult.query.get(tax_id)
        if record:
            return render_template("results.html", result=record.to_result_dict())

    data = session.get("tax_result")
    if not data:
        flash("No tax data found. Please submit the form first.", "error")
        return redirect(url_for("index"))
    result = _session_to_result(data)
    return render_template("results.html", result=result)


# Sample firm login (prototype only — replace with real auth)
FIRM_EMPLOYEES = {"emp001": "tax2025", "admin": "admin123"}


def _firm_logged_in():
    return session.get("firm_employee_id") is not None


@app.route("/history")
def history():
    """Redirect to firm portal (keeps old URLs working)."""
    return redirect(url_for("firm_login"))


@app.route("/firm/login", methods=["GET", "POST"])
def firm_login():
    """Firm login page. Sample: emp001 / tax2025 or admin / admin123"""
    if _firm_logged_in():
        return redirect(url_for("firm_history"))

    if request.method == "POST":
        employee_id = (request.form.get("employee_id") or "").strip()
        password = request.form.get("password") or ""

        if employee_id in FIRM_EMPLOYEES and FIRM_EMPLOYEES[employee_id] == password:
            session["firm_employee_id"] = employee_id
            flash("Logged in successfully.", "success")
            return redirect(url_for("firm_history"))

        flash("Invalid employee ID or password.", "error")

    return render_template("firm_login.html")


@app.route("/firm/logout")
def firm_logout():
    session.pop("firm_employee_id", None)
    flash("Logged out.", "success")
    return redirect(url_for("index"))


@app.route("/firm")
def firm_history():
    """Firm-only view: list all client calculations. Requires login."""
    if not _firm_logged_in():
        return redirect(url_for("firm_login"))

    records = TaxResult.query.order_by(TaxResult.created_at.desc()).limit(50).all()
    return render_template("history.html", records=records, firm_view=True)


@app.route("/results/<int:id>")
def results_by_id(id):
    """Display a specific tax calculation from the database."""
    record = TaxResult.query.get_or_404(id)
    return render_template("results.html", result=record.to_result_dict())


@app.route("/tax-form")
def tax_form():
    """Display simplified 1040-style tax return form with calculated values."""
    tax_id = session.get("tax_result_id")
    if tax_id:
        record = TaxResult.query.get(tax_id)
        if record:
            return render_template("tax_form.html", result=record.to_result_dict())

    data = session.get("tax_result")
    if not data:
        flash("No tax data found. Please submit the form first.", "error")
        return redirect(url_for("index"))
    result = _session_to_result(data)
    return render_template("tax_form.html", result=result)

@app.route("/api/parse-narrative", methods=["POST"])
def parse_narrative():
    data = request.get_json() or {}
    narrative = (data.get("narrative") or "").strip()

    if not narrative:
        return jsonify({"error": "No narrative provided"}), 400

    if not client:
        return jsonify({
            "error": "AI Agent offline. Add GEMINI_API_KEY or GOOGLE_API_KEY to your .env file. Get a key at https://aistudio.google.com/apikey"
        }), 503

    prompt = f"Extract tax data from this narrative. Return JSON with keys: gross_income (number), filing_status (exactly one of: single, married_joint, head_of_household), additional_deductions (number), federal_withheld (number). Narrative: {narrative}"

    # Try models in order; gemini-1.5-flash is widely available
    models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-flash-8b"]
    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction="You extract tax data. Return only valid JSON with keys: gross_income, filing_status, additional_deductions, federal_withheld. Use numbers for amounts. filing_status must be exactly: single, married_joint, or head_of_household.",
                ),
                contents=prompt,
            )

            # Extract text: SDK may use .text or candidates[0].content.parts[0].text
            raw_text = getattr(response, "text", None)
            if not raw_text and hasattr(response, "candidates") and response.candidates:
                c = response.candidates[0]
                if hasattr(c, "content") and c.content and hasattr(c.content, "parts") and c.content.parts:
                    raw_text = getattr(c.content.parts[0], "text", None)
            raw_text = raw_text or ""

            if not raw_text.strip():
                continue

            # Parse JSON; handle markdown code blocks
            text = raw_text.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
                text = text.strip()
            parsed = json.loads(text)
            return jsonify(parsed)

        except json.JSONDecodeError as e:
            last_error = f"AI returned invalid JSON: {e}"
            continue
        except Exception as e:
            last_error = str(e)
            print(f"AI Error ({model_name}): {e}")
            continue

    err_msg = last_error or "AI could not process the request."
    return jsonify({"error": err_msg}), 500
    

def _migrate_add_client_columns():
    """Add client_name, client_email to existing DBs."""
    for col in ("client_name", "client_email"):
        try:
            with db.engine.connect() as conn:
                conn.execute(text(f"ALTER TABLE tax_results ADD COLUMN {col} VARCHAR(200)"))
                conn.commit()
        except Exception:
            pass  # Column exists or table missing


if __name__ == "__main__":
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        db.create_all()
        _migrate_add_client_columns()
    app.run(debug=True, port=5000)
