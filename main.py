from dotenv import load_dotenv, find_dotenv
import os
# Charger les variables d'environnement
load_dotenv(find_dotenv())

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from pydantic import BaseModel

from schemas.contact import ContactForm
from google_sheets import write_to_sheet, get_all_sheet_data
from email_sender import send_confirmation_email
from whatsapp_sender import send_whatsapp_message
from auth import verify_password, create_access_token, get_current_user, oauth2_scheme

from fastapi.security import OAuth2PasswordRequestForm



app = FastAPI()

# Configuration de CORS
origins = [
    "http://localhost:5173",  # L'URL par défaut de ton application React
    # Tu peux ajouter d'autres URL ici si besoin
    #"https://mlc-project-h17y.vercel.app",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model pour l'endpoint de login
class Token(BaseModel):
    access_token: str
    token_type: str

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/admin/login", response_model=Token)
def login_for_access_token(user_data: UserLogin): # On attend un JSON
    username = os.getenv("DASHBOARD_USERNAME")
    password_hashed = os.getenv("DASHBOARD_PASSWORD_HASHED")

    # On vérifie les identifiants en utilisant les données du JSON
    if user_data.username != username or not verify_password(user_data.password, password_hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(
        data={"sub": user_data.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/admin", dependencies=[Depends(oauth2_scheme)])
def get_admin_data(current_user: str = Depends(get_current_user)):
    """
    Endpoint protégé pour récupérer toutes les données de la feuille Google Sheets.
    Nécessite un JWT valide.
    """
    try:
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        if not sheet_id:
            raise ValueError("GOOGLE_SHEET_ID non configuré.")

        data = get_all_sheet_data(sheet_id)

        headers = ["Nom", "Contacts", "Email"]
        formatted_data = [dict(zip(headers, row)) for row in data]

        return {"message": "Données du dashboard récupérées avec succès", "data": formatted_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue: {str(e)}")


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
        whatsapp_message_body = f"""
        Salut {contact_form.nom} ! 👋✨

    Tu veux en savoir plus sur notre programme MLC et découvrir comment il peut transformer ta vie ? 🌟
    Voici les étapes à suivre :

    ETAPE 1 : Inscris-toi sur la plateforme officielle MLC ici 👇
    https://mlc.health/fr/fsd865

    ETAPE 2 : Rejoins le groupe WhatsApp ici 👇
    https://chat.whatsapp.com/CuYWhHMHkin9PjwO4t2JMM?mode=ac_t

    Avec MLC, c’est une transformation garantie et un accompagnement sur mesure ❤️
    """
        send_whatsapp_message(contact_form.contacts, whatsapp_message_body)

        return {"message": "Données enregistrées, e-mail et message WhatsApp envoyés avec succès !"}

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue: {str(e)}")