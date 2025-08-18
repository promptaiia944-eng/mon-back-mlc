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
from auth import verify_password, create_access_token, get_current_user, get_password_hash, oauth2_scheme

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime



app = FastAPI()

# URL de la base de données
DATABASE_URL = os.getenv("DATABASE_URL")

# Création du moteur de base de données
engine = create_engine(DATABASE_URL)

# Création d'une classe de session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Création de la classe de base pour les modeles de données
Base = declarative_base()

# Dépendance pour la base de données
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hashed = Column(String)

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

class UserCreate(BaseModel):
    username: str
    password: str


# Modèle pour la base de données (table "prospects")
class Prospects(Base):
    __tablename__ = "prospects"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    contacts = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Schémas Pydantic pour la validation des données
class ProspectBase(BaseModel):
    nom: str
    contacts: str
    email: str

class ProspectCreate(ProspectBase):
    pass

class ProspectUpdate(ProspectBase):
    pass

class ProspectInDB(ProspectBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

@app.post("/admin/login", response_model=Token)
def login_for_access_token(user_data: UserLogin, db: Session = Depends(get_db)):
    # Recherche l'utilisateur dans la base de données
    user = db.query(User).filter(User.username == user_data.username).first()

    # Si l'utilisateur n'existe pas ou que le mot de passe est incorrect
    if not user or not verify_password(user_data.password, user.password_hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
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

@app.post("/prospects/", response_model=ProspectInDB)
def create_prospect(prospect: ProspectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_prospect = Prospects(
        nom=prospect.nom,
        contacts=prospect.contacts,
        email=prospect.email,
    )
    db.add(db_prospect)
    db.commit()
    db.refresh(db_prospect)
    return db_prospect

@app.get("/prospects/", response_model=list[ProspectInDB])
def get_all_prospects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    prospects = db.query(Prospects).all()
    return prospects

@app.put("/prospects/{prospect_id}", response_model=ProspectInDB)
def update_prospect(
    prospect_id: int,
    prospect_data: ProspectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_prospect = db.query(Prospects).filter(Prospects.id == prospect_id).first()
    if not db_prospect:
        raise HTTPException(status_code=404, detail="Prospect non trouvé")
    
    db_prospect.nom = prospect_data.nom
    db_prospect.contacts = prospect_data.contacts
    db_prospect.email = prospect_data.email
    
    db.commit()
    db.refresh(db_prospect)
    return db_prospect

@app.delete("/prospects/{prospect_id}")
def delete_prospect(
    prospect_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_prospect = db.query(Prospects).filter(Prospects.id == prospect_id).first()
    if not db_prospect:
        raise HTTPException(status_code=404, detail="Prospect non trouvé")
    
    db.delete(db_prospect)
    db.commit()
    return {"message": "Prospect supprimé avec succès"}

# Crée les tables si elles n'existent pas (À SUPPRIMER APRÈS LA PREMIÈRE EXÉCUTION !)
# Base.metadata.create_all(bind=engine)