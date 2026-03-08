#!/usr/bin/env python3
"""
Export all tax results from the database to the terminal.
Run: python export_data.py
Or save to file: python export_data.py > data.txt
"""
import sys
import os

# Add project root so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, TaxResult


def main():
    with app.app_context():
        records = TaxResult.query.order_by(TaxResult.created_at.desc()).all()

        if not records:
            print("No records in the database yet. Run the app and submit a calculation first.")
            return

        print(f"Found {len(records)} record(s)\n")
        print("-" * 80)

        for r in records:
            print(f"ID:           {r.id}")
            print(f"Date:         {r.created_at}")
            print(f"Name:         {r.client_name or '—'}")
            print(f"Email:        {r.client_email or '—'}")
            print(f"Filing:       {r.filing_status}")
            print(f"Gross income: ${float(r.gross_income):,.2f}")
            print(f"Taxable:      ${float(r.taxable_income):,.2f}")
            print(f"Refund/Owed:  ${float(r.refund_or_owed):,.2f} ({'refund' if r.is_refund else 'owed'})")
            print("-" * 80)


if __name__ == "__main__":
    main()
