import os
import sys
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get date argument from command-line (optional)
if len(sys.argv) > 1:
    try:
        input_date = datetime.strptime(sys.argv[1], "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Use DD/MM/YYYY.")
        sys.exit(1)
else:
    input_date = datetime.today().strftime("%Y-%m-%d")

# MongoDB Connection
mongo_connection_string = os.getenv("botit_mongo_connection_string")
client = MongoClient(mongo_connection_string)
db = client["botitprod"]
collection = db["UserOTPs"]

# MongoDB Query for Unverified Users
query = {
    "verified": {"$ne": True},
    "$expr": {
        "$eq": [
            {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
            input_date
        ]
    }
}

# Fetch Data (Retrieve all fields)
cursor = collection.find(query)

# Convert to DataFrame and Save as CSV
data = list(cursor)
if data:
    df = pd.DataFrame(data)
    filename = f"unverified_users_{input_date}.csv"
    df.to_csv(filename, index=False)
    print(f"CSV file saved: {filename}")
else:
    print(f"No unverified users found for {input_date}.")
