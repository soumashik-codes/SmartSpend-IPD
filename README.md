# SmartSpend – Predictive Personal Finance Tracker (IPD Prototype)

This repository contains the **Interim Progress Demonstration (IPD)** prototype for the
Final Year Project **SmartSpend – Predictive Personal Finance Tracker**.

The IPD prototype demonstrates the core functionality, system architecture, and early
analytics capabilities of the proposed personal finance tracking system, including
transaction analysis, spending insights, and predictive features.

---
## Live Prototype (Streamlit Cloud)

👉 **Live App:**
https://smartspend-ipd-n7yubpb9ceuyeizxcpwiyi.streamlit.app

⚠️ **Important Notice**
The hosted Streamlit Cloud deployment may be **temporarily unavailable** or fail to load due to:

- Streamlit Cloud environment limitations  
- Dependency and runtime constraints  
- Server overload or cold-start issues  

These issues are **deployment-related** and **not caused by application logic or implementation errors**.
For full and reliable evaluation of the system, **running the application locally is strongly recommended**.

---

## Running the Application Locally (Recommended)

1) Download or clone the repository
Option A – Download ZIP

- Click **Code → Download ZIP** on this repository
- Extract the ZIP file to a local directory

Option B – Clone using Git

```bash
git clone https://github.com/soumashik-codes/SmartSpend-IPD.git
```

cd SmartSpend-IPD

2) Create a virtual environment (Windows),
Go to bash/Powershell
python -m venv .venv
.venv\Scripts\activate

3) Install dependencies
pip install -r requirements.txt

4) Run the application
streamlit run app.py

The application will open automatically in your default web browser.

---

## Login & Usage

Create a user account using the Create Account tab
Log in to access the dashboard and available IPD-stage features
All authentication and data persistence are handled locally

---

## Receipt OCR (Partial – IPD Stage)

Receipt extraction uses Tesseract OCR

**Tesseract must be installed locally for receipt scanning to function correctly**

OCR functionality is partial at IPD stage and is included to demonstrate feasibility

## Tesseract Setup Notes

- After installation, verify Tesseract by running:
  ```bash
  tesseract --version
On Windows systems, Tesseract may need to be added to the system PATH

If Tesseract is not detected automatically, its executable path may need to be specified in the code

---
## Alternative: Running via GitHub Codespaces
The application can also be executed using GitHub Codespaces:

Open this repository on GitHub

Click Code → Codespaces → Create codespace on main

Install dependencies inside the Codespace terminal

Run the application:

streamlit run app.py


This option allows the project to be evaluated without requiring local environment setup.

If Tesseract is not installed, all other application features continue to work normally.

---

## Notes (IPD Stage)

All data is stored locally using SQLite (db/smartspend.db)

No external banking APIs are used (privacy-preserving design)

Predictive analytics are demonstrated using sample datasets

The prototype focuses on feasibility, system architecture, and core logic

---

## Project Status

This repository represents the IPD prototype and not a final production system.

Further development in the final phase will focus on:

Improved UI/UX

A Decoupled Backend Frontend Structure is planned replacing Streamlit.

Enhanced predictive accuracy

Scalability and robustness

Production-ready architecture
