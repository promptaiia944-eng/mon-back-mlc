from google.oauth2 import service_account
from googleapiclient.discovery import build
import os

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def get_google_sheet_service():
    creds_file_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
    if not creds_file_path or not os.path.exists(creds_file_path):
        raise FileNotFoundError(f"Fichier de credentials Google Sheets non trouvé à: {creds_file_path}")

    creds = service_account.Credentials.from_service_account_file(
        creds_file_path,
        scopes=SCOPES
    )
    return build('sheets', 'v4', credentials=creds)

def write_to_sheet(sheet_id: str, range_name: str, values: list[list[str]]):
    service = get_google_sheet_service()
    body = {
        'values': values
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption='RAW',
        insertDataOption='INSERT_ROWS',
        body=body
    ).execute()
    return result

def get_all_sheet_data(sheet_id: str, range_name: str = "Feuille1!A:C"):
    """
    Récupère toutes les données de la feuille Google Sheets.
    """
    try:
        service = get_google_sheet_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        values = result.get('values', [])
        return values
    except Exception as e:
        raise Exception(f"Erreur lors de la lecture des données de la feuille : {str(e)}")