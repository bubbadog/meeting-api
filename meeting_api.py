import os
import json
from flask import Flask, jsonify
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Load API credentials from environment variables
key_json = os.getenv("GOOGLE_CREDENTIALS")
if not key_json:
    raise ValueError("Error: GOOGLE_CREDENTIALS environment variable is missing or empty!")
creds_dict = json.loads(key_json)
creds = Credentials.from_service_account_info(creds_dict)

# Load Sheets & Docs IDs from environment variable
ids_json = os.getenv("GOOGLE_SHEET_DOC_IDS")
if not ids_json:
    raise ValueError("Error: GOOGLE_SHEET_DOC_IDS environment variable is missing!")
ids = json.loads(ids_json)

# Initialize Google APIs
sheets_client = gspread.authorize(creds)
docs_service = build("docs", "v1", credentials=creds)

# Helper Function for Fetching Google Docs Content
def fetch_google_doc(doc_id):
    """Retrieve text from a Google Doc"""
    try:
        doc = docs_service.documents().get(documentId=doc_id).execute()
        content = []
        for elem in doc.get("body", {}).get("content", []):
            if "paragraph" in elem:
                for text_elem in elem["paragraph"]["elements"]:
                    if "textRun" in text_elem:
                        content.append(text_elem["textRun"]["content"])
        return "\n".join(content).strip()

    except Exception as e:
        return f"Error fetching document: {str(e)}"
    
app = Flask(__name__)

@app.route("/get_trivia_data", methods=["GET"])
def get_trivia_data():
    try:
        # Load IDs dynamically from environment variable
        leaderboard_sheet_id = ids["leaderboard_sheet"]
        tickets_sheet_id = ids["tickets_sheet"]
        event_summary_doc_id = ids["event_summary_doc"]
        meeting_notes_doc_id = ids["meeting_notes_doc"]
        planning_doc_id = ids["planning_doc"]

        # Open Sheets
        leaderboard_sheet = sheets_client.open_by_key(leaderboard_sheet_id).sheet1
        tickets_sheet = sheets_client.open_by_key(tickets_sheet_id).sheet1

        # Fetch event summary (Google Sheets)
        days_until_event = leaderboard_sheet.acell("G2").value
        tickets_sold = leaderboard_sheet.acell("C3").value
        sponsor_cash = leaderboard_sheet.acell("D3").value
        donations = leaderboard_sheet.acell("F3").value

        # Fetch leaderboard data (Google Sheets)
        leaderboard_data = leaderboard_sheet.get_all_records(expected_headers=[
            "Name", "Tickets Sold", "Rank (Tickets Sold)", 
            "Sponsor Funds ($)", "Rank (Sponsor Funds)", "Donations"
        ])

        # Fetch event summary document (Google Docs)
        event_summary_text = fetch_google_doc(event_summary_doc_id)
        meeting_notes_text = fetch_google_doc(meeting_notes_doc_id)
        planning_text = fetch_google_doc(planning_doc_id)

        return jsonify({
            "event_summary": {
                "days_until_event": days_until_event,
                "tickets_sold": tickets_sold,
                "sponsor_cash": sponsor_cash,
                "donations": donations
            },
            "leaderboard": leaderboard_data,
            "docs": {
                "event_summary": event_summary_text,
                "meeting_notes": meeting_notes_text,
                "planning": planning_text
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

    
