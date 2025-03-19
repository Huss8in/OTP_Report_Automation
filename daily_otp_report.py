from pymongo import MongoClient
import os
import pandas as pd
from datetime import datetime
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
today = datetime.today()
current_month = today.strftime("%Y-%m")
current_date = today.strftime("%Y-%m-%d")

# ------------ Worksheet Handling ------------ #
try:
    worksheet = sh.worksheet(current_month)
except gspread.exceptions.WorksheetNotFound:
    try:
        worksheet = sh.add_worksheet(title=current_month, rows="1000", cols="3")
        worksheet.append_row(["Date", "Verified", "Unverified"])
    except Exception as e:
        print(f"Error creating worksheet: {e}")
        exit()

# ------------ MongoDB Aggregation ------------ #
pipeline = [
    {
        "$match": {
            "$expr": {
                "$eq": [
                    { "$dateToString": { "format": "%Y-%m-%d", "date": "$createdAt" } },
                    current_date
                ]
            }
        }
    },
    {
        "$group": {
            "_id": None,
            "date": { "$first": current_date },
            "verified": { "$sum": { "$toInt": "$verified" } },
            "unverified": { "$sum": { "$toInt": { "$not": "$verified" } } }
        }
    },
    {
        "$project": {
            "_id": 0,
            "date": 1,
            "verified": 1,
            "unverified": 1
        }
    }
]

# ------------ Append Data to Google Sheets ------------ #
result = list(collection.aggregate(pipeline))

if result:
    df = pd.DataFrame(result)
    row = [str(df.iloc[0]["date"]), str(df.iloc[0]["verified"]), str(df.iloc[0]["unverified"])]
    worksheet.append_row(row)
    print(f"Data updated for {current_date}")
else:
    print(f"No data found for {current_date}")
