PUBLIC GRIEVANCE CLASSIFICATION AND MANAGEMENT SYSTEM
======================================================

PROJECT FEATURES
- Citizen registration and login
- Complaint submission
- ML-based complaint category prediction
- Suggested department based on predicted category
- Rule-based priority label (not an ML prediction)
- SQLite complaint storage
- Citizen complaint tracking
- Admin dashboard and status updates

REQUIREMENTS
- Windows 10/11
- Python 3.10 or newer recommended
- VS Code

HOW TO RUN ON WINDOWS
1. Extract the ZIP file.
2. Open the extracted PublicGrievanceSystem folder in VS Code.
3. Open Terminal > New Terminal.
4. Create a virtual environment:
   python -m venv venv
5. Activate it:
   venv\Scripts\activate
6. Install packages:
   pip install -r requirements.txt
7. Start the app:
   python app.py
8. Open this address in your browser:
   http://127.0.0.1:5000

ADMIN LOGIN
Email: admin@grievance.local
Password: Configured locally in the .env file.

CITIZEN TEST
Register a new account, log in, and submit a complaint.

MODEL
The project uses TF-IDF text features and Logistic Regression.
The included CSV is a small demonstration dataset, not a validated
real-world dataset. Do not report its test score as evidence of
real-world performance. For a final academic evaluation, expand and
validate the dataset, use a held-out test set, and report precision,
recall, F1-score and confusion matrix.

PRIORITY
Priority is assigned by transparent keyword rules in this prototype.
It is not predicted by the machine-learning model and should be
reviewed by an administrator.

IMPORTANT
This is an academic prototype, not a live government service.
Change the Flask secret key and admin password before any deployment.
Debug mode is enabled for local development only. Do not deploy it
publicly with debug=True or the demo admin credentials.
