from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # Importation du module
from dotenv import load_dotenv
import os

from schemas.contact import ContactForm
from google_sheets import write_to_sheet
from email_sender import send_confirmation_email
from whatsapp_sender import send_whatsapp_message



# Charger les variables d'environnement
load_dotenv()

app = FastAPI()

# Configuration de CORS
origins = [
    "http://localhost:5173",  # L'URL par défaut de ton application React
    # Tu peux ajouter d'autres URL ici si besoin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... (endpoint read_root) ...

@app.post("/api/submit-form")
def submit_form(contact_form: ContactForm):
    """
    Endpoint pour recevoir les données du formulaire, les écrire dans Google Sheets,
    envoyer un e-mail et un message WhatsApp de confirmation.
    """
    try:
        # Écrire les données dans la feuille Google Sheets
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        sheet_range = "Feuille1!A:C"
        values_to_write = [[contact_form.nom, contact_form.contacts, contact_form.email]]
        write_to_sheet(sheet_id, sheet_range, values_to_write)
        
        # Envoi de l'e-mail de confirmation
        send_confirmation_email(contact_form.email, contact_form.nom)

        # Envoi du message WhatsApp de confirmation
        whatsapp_message_body = f"""Salut {contact_form.nom} ! :salut_main::scintillements:
            Tu veux en savoir plus sur notre programme MLC et découvrir comment il peut transformer ta vie ? :étoile2:
            Voici les étapes à suivre :
            ETAPE 1 : Inscris-toi sur la plateforme officielle MLC ici :index_vers_la_droite: https://mlc.health/fr/fsd865
            ETAPE 2 : Rejoins le groupe WhatsApp ici :index_vers_la_droite: https://chat.whatsapp.com/CuYWhHMHkin9PjwO4t2JMM?mode=ac_t
            Avec MLC, c’est une transformation garantie et un accompagnement sur mesure :cœur:
            WhatsApp.comWhatsApp.com
            MLC Africa 6"""
        send_whatsapp_message(contact_form.contacts, whatsapp_message_body)

        return {"message": "Données enregistrées, e-mail et message WhatsApp envoyés avec succès !"}

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue: {str(e)}")