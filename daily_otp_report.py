from pymongo import MongoClient
import os
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv
import sys

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
yesterday = today - timedelta(days=1)
dates = [yesterday.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")]
current_month = today.strftime("%Y-%m")

# ------------ Worksheet Handling ------------ #
try:
    worksheet = sh.worksheet(current_month)
except gspread.exceptions.WorksheetNotFound:
    worksheet = sh.add_worksheet(title=current_month, rows="1000", cols="5")
    worksheet.append_row(["Date", "Verified", "Unverified", "Total", "Unverified %"])


# ------------ MongoDB Aggregation Function ------------ #
def get_data_for_date(date_str):
    pipeline = [
        {
            "$match": {
                "$expr": {
                    "$eq": [
                        {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
                        date_str,
                    ]
                }
            }
        },
        {
            "$group": {
                "_id": None,
                "date": {"$first": date_str},
                "verified": {"$sum": {"$toInt": "$verified"}},
                "unverified": {"$sum": {"$toInt": {"$not": "$verified"}}},
            }
        },
        {
            "$project": {
                "_id": 0,
                "date": 1,
                "verified": 1,
                "unverified": 1,
                "total": {"$add": ["$verified", "$unverified"]},
                "unverified_percentage": {
                    "$cond": {
                        "if": {"$eq": [{"$add": ["$verified", "$unverified"]}, 0]},
                        "then": 0,
                        "else": {
                            "$round": [
                                {
                                    "$multiply": [
                                        {
                                            "$divide": [
                                                "$unverified",
                                                {"$add": ["$verified", "$unverified"]},
                                            ]
                                        },
                                        100,
                                    ]
                                },
                                2,
                            ]
                        },
                    }
                },
            }
        },
    ]
    result = list(collection.aggregate(pipeline))
    return result[0] if result else None


# ------------ Check & Update Data in Google Sheets ------------ #
existing_data = worksheet.get_all_values()
date_column = [row[0] for row in existing_data]

for date in dates:
    data = get_data_for_date(date)
    if data:
        row = [
            str(data["date"]),
            str(data["verified"]),
            str(data["unverified"]),
            str(data["total"]),
            str(data["unverified_percentage"]),
        ]

        if date in date_column:
            row_index = date_column.index(date) + 1
            worksheet.update(range_name=f"A{row_index}:E{row_index}", values=[row])
            print(f"Data updated for {date}: {row}")
        else:
            worksheet.append_row(row)
            print(f"New data added for {date}: {row}")
    else:
        print(f"No data found for {date}")

worksheet.format("A:E", {"horizontalAlignment": "Left"})
