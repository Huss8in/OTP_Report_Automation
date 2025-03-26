import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

load_dotenv()

# ------------ Load Environment Variables ------------ #
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT")
SHEET_ID = os.getenv("SHEET_ID")

print("Loaded environment variables successfully.")
print(f"Email Sender: {EMAIL_USER}, Recipient: {RECIPIENT_EMAIL}")
print(f"SMTP Server: {SMTP_SERVER}, Port: {SMTP_PORT}")

# ------------ Google Sheets Authentication ------------ #
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT, scope)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SHEET_ID)

print(f"Connected to Google Sheet with ID: {SHEET_ID}")

# ------------ Date Setup ------------ #
today = datetime.today().strftime("%Y-%m-%d")
yesterday = (datetime.today() - timedelta(days=1)).strftime("%Y-%m-%d")
current_month = datetime.today().strftime("%Y-%m")

print(f"Checking Unverified % for dates: {today} and {yesterday}")

try:
    worksheet = sh.worksheet(current_month)
    data = worksheet.get_all_values()
    print(f"Worksheet '{current_month}' found and loaded successfully.")
except gspread.exceptions.WorksheetNotFound:
    print(f"Worksheet for the current month '{current_month}' not found.")
    exit()

# ------------ Check Unverified % ------------ #
header = data[0]
date_idx = header.index("Date")
unverified_idx = header.index("Unverified %")

alert_rows = []
for row in data[1:]:  # Skip header
    if row[date_idx] in [today, yesterday]:
        try:
            unverified_percent = float(row[unverified_idx])
            print(f"Date: {row[date_idx]}, Unverified %: {unverified_percent}%")
            if unverified_percent > 5:
                alert_rows.append(row)
        except ValueError:
            print(f"Skipping invalid row: {row}")
            continue  # Skip if conversion fails

# ------------ Send Alert Email if Needed ------------ #
SHEET_LINK = os.getenv("SHEET_LINK")

if alert_rows:
    email_subject = "🚨 Alert: High Unverified Percentage in OTP Verification Logs"
    email_body = (
        "<p>Dear Team,</p>"
        "<p>This is an <b>automated alert</b> regarding high unverified percentages in OTP verification logs.</p>"
        "<p>The following records have exceeded the acceptable threshold:</p>"
        "<ul>"
    )

    for row in alert_rows:
        email_body += f"<li><b>Date:</b> {row[date_idx]}, <b>Unverified %:</b> {row[unverified_idx]}%</li>"

    email_body += (
        "</ul>"
        "<p>Please investigate the issue and take necessary actions.</p>"
        f"<p>You can review the details in the <b><a href='{SHEET_LINK}'>Google Sheet</a></b>.</p>"
        "<p>Best regards,<br>Automated Monitoring System</p>"
        "<p style='color: red;'><b> Please do not reply to this email. This is an automated notification.</b></p>"
    )

    print(f"Preparing to send alert email with subject: {email_subject}")
    # print(f"Email Body: \n{email_body}")

    def send_email(subject, body, to_email):
        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_USER
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))  # Send as HTML for formatting

            print(f"Sending email from {EMAIL_USER} to {to_email} via {SMTP_SERVER}:{SMTP_PORT}")

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_USER, to_email, msg.as_string())

            print("Alert email sent successfully!")
        except Exception as e:
            print(f"Error sending email: {e}")

    send_email(
        subject=email_subject,
        body=email_body,
        to_email=RECIPIENT_EMAIL
    )
else:
    print("No alert needed. Unverified % is within limits.")
