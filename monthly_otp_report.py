from pymongo import MongoClient
import os
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv 

load_dotenv()

# ------------ MongoDB Connection ------------ #
mongo_connection_string = os.getenv("botit_mongo_connection_string")
client = MongoClient(mongo_connection_string)
db = client["botitprod"]
collection = db["UserOTPs"]

# ------------ Google Sheets Authentication ------------ #
SERVICE_ACCOUNT = os.getenv("SERVICE_ACCOUNT")
SHEET_ID = os.getenv("SHEET_ID")
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT, scope)
gc = gspread.authorize(creds)
sh = gc.open_by_key(SHEET_ID)

# ------------ Date Setup ------------ #
start_date = datetime(2024, 12, 1)
end_date = datetime(2025, 3, 31)

while start_date <= end_date:
    current_month = start_date.strftime("%Y-%m")

    # ------------ MongoDB Aggregation (Fetch Entire Month) ------------ #
    pipeline = [
        {
            "$match": {
                "createdAt": {
                    "$gte": start_date,
                    "$lt": start_date.replace(day=28) + timedelta(days=4)  # Ensures full month range
                }
            }
        },
        {
            "$group": {
                "_id": {
                    "date": { "$dateToString": { "format": "%Y-%m-%d", "date": "$createdAt" } }
                },
                "verified": { "$sum": { "$toInt": "$verified" } },
                "unverified": { "$sum": { "$toInt": { "$not": "$verified" } } }
            }
        },
        {
            "$project": {
                "_id": 0,
                "date": "$_id.date",
                "verified": 1,
                "unverified": 1
            }
        },
        { "$sort": { "date": 1 } }
    ]

    result = list(collection.aggregate(pipeline))

    if result:
        df = pd.DataFrame(result)
        
        # ------------ Google Sheets Handling ------------ #
        try:
            worksheet = sh.worksheet(current_month)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = sh.add_worksheet(title=current_month, rows="1000", cols="3")
            worksheet.append_row(["Date", "Verified", "Unverified"])
        
        worksheet.append_rows(df.values.tolist())
        print(f"Data updated for {current_month}")
    else:
        print(f"No data found for {current_month}")

    start_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)