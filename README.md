# UsersOTPs Verifications

## Project Description
This repository manages the `UsersOTPs` collection in MongoDB for the **BotIt** application. It stores all user OTP requests and tracks whether they have been verified. The repository includes three main scripts to handle OTP data reporting and export functionalities.

### Scripts Overview
1. **`daily_otp_report.py`**  
   - Generates a daily report of verified and unverified OTPs.  
   - Adds a row to a sheet (organized by month and year) with the date, count of verified OTPs, and count of unverified OTPs for that day.

2. **`monthly_otp_report.py`**  
   - Generates a report of verified and unverified OTPs for a specified date range (e.g., from `12/12/2025` to `18/03/2025`).  
   - Creates a sheet for each month within the range, listing the date of each day and the count of verified and unverified OTPs.

3. **`export_unverified.py`**  
   - Exports a CSV document containing unverified OTP records for a specific day.  

---

## Installation

1. Set up a virtual environment:
```bash
   python -m venv venv
```


2. Activate the virtual environment:
- On Windows:
```bash
   venv\Scripts\activate
```
- On macOS/Linux:
```bash
   source venv/bin/activate
```


3. Install the required dependencies:
```bash
   pip install -r requirements.txt
```

## Usage
1. daily_otp_report.py
Run the script to generate a daily OTP report:
```bash
   python daily_otp_report.py
```

2. monthly_otp_report.py
Run the script to generate a monthly OTP report for a specific date range:
```bash
   python monthly_otp_report.py
```
Or specify a custom date range:
```bash
   python monthly_otp_report.py <Start_Date (YYYY-MM-DD)> <End_Date (YYYY-MM-DD)>
```

3. export_unverified.py
Run the script to export unverified OTP records for a specific day:

```bash
python export_unverified.py
```
Or specify a custom date:

```bash
python export_unverified.py <Date (YYYY-MM-DD)>
```

## Repository Structure
```bash
UsersOTPs-Verifications/
├── daily_otp_report.py
├── monthly_otp_report.py
├── export_unverified.py
├── requirements.txt
└── README.md
```
