from flask import Flask, jsonify
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive"
]

# Load credentials
import os
import json

# Load credentials from environment variable
key_json = os.getenv("GOOGLE_CREDENTIALS")  # Retrieve JSON key from environment
creds_dict = json.loads(key_json)  # Convert JSON string to dictionary
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)


# Initialize Google Sheets client
sheets_client = gspread.authorize(creds)

# Initialize Google Docs API client
docs_service = build("docs", "v1", credentials=creds)

app = Flask(__name__)

# 📌 API Endpoint: Fetch meeting notes from Google Docs
@app.route("/get_meeting_notes", methods=["GET"])
def get_meeting_notes():
    try:
        DOCUMENT_ID = "1ow0HJ-jpqpBOlMBro2O3Q3c7CMrCBRG1u_RWb9_edsA"  # Update with your actual Google Doc ID
        doc = docs_service.documents().get(documentId=DOCUMENT_ID).execute()

        content = []
        for elem in doc.get("body", {}).get("content", []):
            if "paragraph" in elem:
                for text_elem in elem["paragraph"]["elements"]:
                    content.append(text_elem.get("textRun", {}).get("content", ""))

        return jsonify({"meeting_notes": "\n".join(content)})

    except Exception as e:
        return jsonify({"error": str(e)})

# 📌 API Endpoint: Fetch meeting data from Google Sheets
@app.route("/get_trivia_data", methods=["GET"])
def get_trivia_data():
    try:
        SHEET_ID = "your-google-sheet-id"  # Update with your actual Google Sheet ID
        sheet = sheets_client.open_by_key(SHEET_ID).sheet1

        # Fetch event-level summary data (Top section)
        days_until_event = sheet.acell("G2").value
        tickets_sold = sheet.acell("C3").value
        sponsor_cash = sheet.acell("D3").value
        donations = sheet.acell("F3").value

        # Fetch leaderboard data (Rows 5 and below)
        data = sheet.get_all_records(expected_headers=[
            "Name", "Tickets Sold", "Rank (Tickets Sold)", 
            "Sponsor Funds ($)", "Rank (Sponsor Funds)", "Donations"
        ])

        return jsonify({
            "event_summary": {
                "days_until_event": days_until_event,
                "tickets_sold": tickets_sold,
                "sponsor_cash": sponsor_cash,
                "donations": donations
            },
            "leaderboard": data
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
