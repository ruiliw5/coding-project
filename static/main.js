document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('tax-form');
  
  if (form) {
      form.addEventListener('submit', (e) => {
          let hasError = false;
          
          // Get references to inputs and error spans
          const inputs = {
              filing_status: {
                  field: document.getElementById('filing_status'),
                  error: document.getElementById('filing_status_error')
              },
              gross_income: {
                  field: document.getElementById('gross_income'),
                  error: document.getElementById('gross_income_error')
              }
          };

          // 1. Validate Filing Status
          if (!inputs.filing_status.field.value) {
              inputs.filing_status.error.textContent = "Please select a filing status.";
              inputs.filing_status.field.style.borderColor = "var(--error)";
              hasError = true;
          } else {
              inputs.filing_status.error.textContent = "";
              inputs.filing_status.field.style.borderColor = "var(--border-form)";
          }

          // 2. Validate Gross Income (Required and Numeric)
          const incomeVal = inputs.gross_income.field.value.trim();
          if (!incomeVal || isNaN(incomeVal) || parseFloat(incomeVal) <= 0) {
              inputs.gross_income.error.textContent = "Please enter a valid gross income greater than 0.";
              inputs.gross_income.field.style.borderColor = "var(--error)";
              hasError = true;
          } else if (parseFloat(incomeVal) > 10000000) {
              inputs.gross_income.error.textContent = "Gross income exceeds the prototype limit.";
              inputs.gross_income.field.style.borderColor = "var(--error)";
              hasError = true;
          } else {
              inputs.gross_income.error.textContent = "";
              inputs.gross_income.field.style.borderColor = "var(--border-form)";
          }

          // If there's an error, prevent the form from sending to app.py
          if (hasError) {
              e.preventDefault();
              // Scroll to the first error for better UX
              const firstError = document.querySelector('.field-error:not(:empty)');
              if (firstError) {
                  firstError.parentElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
              }
          }
      });

      // Clear error styling when the user starts typing/correcting
      form.querySelectorAll('input, select').forEach(input => {
          input.addEventListener('input', () => {
              input.style.borderColor = "var(--accent-green-main)";
              const errorSpan = document.getElementById(`${input.id}_error`);
              if (errorSpan) errorSpan.textContent = "";
          });
      });
  }

  // --- AI Agent Auto-Fill Logic ---
  const aiBtn = document.getElementById('ai-parse-btn');
  if (aiBtn) {
      aiBtn.addEventListener('click', async () => {
          const narrative = document.getElementById('narrative-input').value;
          const statusSpan = document.getElementById('ai-status');

          if (!narrative.trim()) {
              statusSpan.textContent = "Please enter a description first.";
              statusSpan.style.color = "var(--error)";
              return;
          }

          statusSpan.textContent = "Thinking...";
          statusSpan.style.color = "var(--text-sub)";
          aiBtn.disabled = true;

          try {
              // Send the data to your Flask backend
              const response = await fetch('/api/parse-narrative', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ narrative })
              });

              let data = {};
              try { data = await response.json(); } catch (_) { data = {}; }

              if (response.ok) {
                  // Populate the form fields with the AI's JSON data
                  if (data.gross_income) document.getElementById('gross_income').value = data.gross_income;
                  if (data.filing_status) document.getElementById('filing_status').value = data.filing_status;
                  if (data.additional_deductions) document.getElementById('additional_deductions').value = data.additional_deductions;
                  if (data.federal_withheld) document.getElementById('federal_withheld').value = data.federal_withheld;

                  statusSpan.textContent = "✨ Form auto-filled successfully!";
                  statusSpan.style.color = "var(--success)";

                  // Clear any previous red error styling
                  document.querySelectorAll('.field-error').forEach(el => el.textContent = "");
                  document.querySelectorAll('input, select').forEach(el => el.style.borderColor = "var(--border-form)");

              } else {
                  statusSpan.textContent = data.error || "Could not parse. Check your description.";
                  statusSpan.style.color = "var(--error)";
              }
          } catch (err) {
              console.error("Fetch error:", err);
              statusSpan.textContent = "Network error. Is the server running?";
              statusSpan.style.color = "var(--error)";
          } finally {
              aiBtn.disabled = false;
          }
      });
  }
});