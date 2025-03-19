import os
import json
from flask import Flask, jsonify
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.metadata.readonly"
]

# Load API credentials from environment variables
key_json = os.getenv("GOOGLE_CREDENTIALS")
if not key_json:
    raise ValueError("Error: GOOGLE_CREDENTIALS environment variable is missing or empty!")
creds_dict = json.loads(key_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)


# Load Sheets & Docs IDs from environment variable
ids_json = os.getenv("GOOGLE_SHEET_DOC_IDS")
if not ids_json:
    raise ValueError("Error: GOOGLE_SHEET_DOC_IDS environment variable is missing!")
ids = json.loads(ids_json)

# Initialize Google APIs
sheets_client = gspread.authorize(creds)
docs_service = build("docs", "v1", credentials=creds)

# Helper function to fetch Google Docs content
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

# Initialize Flask App
app = Flask(__name__)

@app.route("/get_trivia_data", methods=["GET"])
def get_trivia_data():
    try:
        # Load IDs dynamically from environment variable
        leaderboard_sheet_id = ids["leaderboard_sheet"]
        meeting_summary_doc_id = ids["meeting_summary_doc"]
        committees_planning_sheet_id = ids["committees_planning_sheet"]

        # Open Sheets
        leaderboard_sheet = sheets_client.open_by_key(leaderboard_sheet_id).sheet1
        committees_planning_sheet = sheets_client.open_by_key(committees_planning_sheet_id).sheet1

        # Fetch leaderboard data (Google Sheets)
        leaderboard_data = leaderboard_sheet.get_all_records(expected_headers=[
            "Name", "Tickets Sold", "Rank (Tickets Sold)", 
            "Sponsor Funds ($)", "Rank (Sponsor Funds)", "Donations"
        ])

        # Fetch committees planning data (Google Sheets)
        committees_planning_data = committees_planning_sheet.get_all_records()

        # Fetch meeting summary document (Google Docs)
        meeting_summary_text = fetch_google_doc(meeting_summary_doc_id)

        return jsonify({
            "leaderboard": leaderboard_data,
            "committees_planning": committees_planning_data,
            "meeting_summary": meeting_summary_text
        })

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


    
