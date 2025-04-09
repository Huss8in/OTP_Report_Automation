import os
import sys
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Parse command-line arguments
args = sys.argv[1:]

if len(args) == 0:
    start_date = end_date = datetime.today().strftime("%Y-%m-%d")
elif len(args) == 1:
    try:
        start_date = end_date = datetime.strptime(args[0], "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Use DD-MM-YYYY.")
        sys.exit(1)
elif len(args) == 2:
    try:
        start_date = datetime.strptime(args[0], "%d-%m-%Y").strftime("%Y-%m-%d")
        end_date = datetime.strptime(args[1], "%d-%m-%Y").strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Use DD-MM-YYYY.")
        sys.exit(1)
else:
    print("Usage: python export_unverified.py [DD-MM-YYYY] [DD-MM-YYYY]")
    sys.exit(1)

# MongoDB Connection
mongo_connection_string = os.getenv("botit_mongo_connection_string")
client = MongoClient(mongo_connection_string)
db = client["botitprod"]
collection = db["UserOTPs"]

# MongoDB Query for Unverified Users
query = {
    "verified": {"$ne": True},
    "$expr": {
        "$and": [
            {"$gte": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}}, start_date]},
            {"$lte": [{"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}}, end_date]}
        ]
    }
}

# Fetch Data
cursor = collection.find(query)

# Convert to DataFrame and Save as CSV
data = list(cursor)
if data:
    df = pd.DataFrame(data)
    df["repeated_request"] = df["count"] > 1
    filename = f"unverified_users_{start_date}_to_{end_date}.csv" if start_date != end_date else f"unverified_users_{start_date}.csv"
    df.to_csv(filename, index=False)
    print(f"CSV file saved: {filename}")
else:
    print(f"No unverified users found for the period {start_date} to {end_date}.")
