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
@app.route("/get_meeting_data", methods=["GET"])
def get_meeting_data():
    try:
        SHEET_ID = "1w_2js9ct36PBR3jyCZyE5cXI0Rlzsjt2MPRbEJpFMh4"  # Update with your actual Google Sheet ID
        sheet = sheets_client.open_by_key(SHEET_ID).sheet1
        data = sheet.get_all_records()  # Fetch all rows as dict

        return jsonify({"meeting_data": data})

    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
