from dotenv import load_dotenv, find_dotenv
import os
# Charger les variables d'environnement
load_dotenv(find_dotenv())

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import timedelta
from pydantic import BaseModel
from typing import Optional

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
from uuid import UUID, uuid4
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from typing import List, Optional, Generic, TypeVar



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
    "https://mlc-project-h17y.vercel.app",
    "https://mlc-project.vercel.app",
    "http://127.0.0.1:8000",
    "https://mlc.ci/",
    "https://www.mlc.ci",
    "https://mlc.ci"
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

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
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

class ProspectUpdate(BaseModel):
    nom: Optional[str] = None
    contacts: Optional[str] = None
    email: Optional[str] = None

class ProspectInDB(BaseModel):
    id: UUID
    nom: str
    contacts: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True

T = TypeVar('T')

class Pagination(BaseModel, Generic[T]):
    total_count: int
    page: int
    limit: int
    items: List[T]

@app.post("/login", response_model=Token)
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
def submit_form(contact_form: ContactForm, db: Session = Depends(get_db)):
    """
    Endpoint pour recevoir les données du formulaire, les écrire dans Google Sheets,
    et les ajouter à la base de données.
    """
    try:
        # Étape 1 : Écrire les données dans la feuille Google Sheets
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

        # Étape 2 : Ajouter les données à la base de données PostgreSQL
        db_prospect = Prospects(
            nom=contact_form.nom,
            contacts=contact_form.contacts,
            email=contact_form.email,
        )
        db.add(db_prospect)
        db.commit()
        db.refresh(db_prospect)

        return {"message": "Données enregistrées dans Google Sheets et la base de données, e-mail et message WhatsApp envoyés avec succès !"}

    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue: {str(e)}")

@app.post("/prospects/", response_model=ProspectInDB, status_code=status.HTTP_201_CREATED)
def create_prospect(
    prospect: ProspectCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Crée un nouveau prospect et l'ajoute à la base de données ainsi qu'à Google Sheets.
    """
    try:
        # Étape 1 : Ajouter le nouveau prospect à la base de données
        db_prospect = Prospects(
            nom=prospect.nom,
            contacts=prospect.contacts,
            email=prospect.email,
        )
        db.add(db_prospect)
        db.commit()
        db.refresh(db_prospect)

        # Étape 2 : Écrire les données dans la feuille Google Sheets
        # Cette partie est similaire à l'endpoint /api/submit-form
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        sheet_range = "Feuille1!A:C"  # Assurez-vous que le nom de la feuille est correct

        # Préparer les valeurs dans le format requis par la fonction write_to_sheet
        values_to_write = [[prospect.nom, prospect.contacts, prospect.email]]
        
        # Appeler la fonction pour écrire dans le sheets
        write_to_sheet(sheet_id, sheet_range, values_to_write)
        
        return db_prospect

    except Exception as e:
        # En cas d'erreur, annuler la transaction de la base de données
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue lors de la création du prospect: {str(e)}")

@app.get("/prospects/", response_model=Pagination[ProspectInDB])
def get_all_prospects(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Récupère une liste de prospects avec pagination par numéro de page.
    """
    if limit > 100:
        raise HTTPException(status_code=400, detail="La limite ne peut pas dépasser 100.")

    if page < 1:
        raise HTTPException(status_code=400, detail="Le numéro de page doit être supérieur ou égal à 1.")
    
    # Calculer le 'skip' à partir du numéro de page
    skip = (page - 1) * limit

    prospects_query = db.query(Prospects)
    total_count = prospects_query.count()
    
    prospects = prospects_query.offset(skip).limit(limit).all()
    
    # Préparer la réponse paginée
    items = [ProspectInDB.from_orm(p) for p in prospects]
    
    return Pagination[ProspectInDB](
        total_count=total_count,
        page=page,
        limit=limit,
        items=items
    )

def sync_prospect_to_sheets(prospect_data: dict):
    """
    Synchronise les données d'un prospect avec la feuille Google Sheets.
    """
    try:
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        sheet_range = "Feuille1!A:C"
        
        # On prépare la ligne à écrire, en s'assurant que l'ordre des colonnes est correct
        values_to_write = [[prospect_data['nom'], prospect_data['contacts'], prospect_data['email']]]
        
        write_to_sheet(sheet_id, sheet_range, values_to_write)
        print("Données synchronisées avec Google Sheets.")
    except Exception as e:
        print(f"Erreur lors de la synchronisation avec Google Sheets : {e}")


@app.put("/prospects/{prospect_id}", response_model=ProspectInDB)
def update_prospect(
    prospect_id: UUID,
    prospect_data: ProspectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_prospect = db.query(Prospects).filter(Prospects.id == prospect_id).first()
    if not db_prospect:
        raise HTTPException(status_code=404, detail="Prospect non trouvé")

    # Mettre à jour les champs s'ils sont fournis
    if prospect_data.nom is not None:
        db_prospect.nom = prospect_data.nom
    if prospect_data.contacts is not None:
        db_prospect.contacts = prospect_data.contacts
    if prospect_data.email is not None:
        db_prospect.email = prospect_data.email

    db.commit()
    db.refresh(db_prospect)
    return db_prospect

@app.delete("/prospects/{prospect_id}")
def delete_prospect(
    prospect_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_prospect = db.query(Prospects).filter(Prospects.id == prospect_id).first()
    if not db_prospect:
        raise HTTPException(status_code=404, detail="Prospect non trouvé")

    db.delete(db_prospect)
    db.commit()
    return {"message": "Prospect supprimé avec succès"}

@app.post("/prospects/sync-from-sheets")
def sync_prospects_from_sheets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint protégé pour lire tous les prospects de la feuille Google Sheets
    et les ajouter à la base de données sans erreur en cas de doublon.
    """
    try:
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        if not sheet_id:
            raise ValueError("GOOGLE_SHEET_ID non configuré.")

        sheet_data = get_all_sheet_data(sheet_id)
        
        prospects_added_count = 0
        prospects_skipped_count = 0

        # On saute la première ligne qui contient les en-têtes
        for row in sheet_data[1:]:
            if not row or len(row) < 3:
                continue

            nom = row[0]
            contacts = row[1]
            email = row[2]
            
            # Vérifier si un prospect avec cet email existe déjà
            existing_prospect = db.query(Prospects).filter(Prospects.email == email).first()
            if existing_prospect:
                print(f"Prospect avec l'email {email} déjà existant, ignoré.")
                prospects_skipped_count += 1
                continue

            # Créer et ajouter le nouveau prospect
            db_prospect = Prospects(nom=nom, contacts=contacts, email=email)
            db.add(db_prospect)
            db.commit() # On commit à chaque ajout
            prospects_added_count += 1

        return {
            "message": f"{prospects_added_count} prospects ajoutés, {prospects_skipped_count} prospects déjà existants ignorés.",
            "prospects_ajoutes": prospects_added_count,
            "prospects_ignores": prospects_skipped_count
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Une erreur est survenue lors de la synchronisation : {str(e)}")

# Crée les tables si elles n'existent pas (À SUPPRIMER APRÈS LA PREMIÈRE EXÉCUTION !)
# Base.metadata.create_all(bind=engine)