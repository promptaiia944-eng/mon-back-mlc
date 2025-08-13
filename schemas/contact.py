from pydantic import BaseModel, Field, EmailStr

class ContactForm(BaseModel):
    nom: str = Field(..., min_length=2, max_length=100)
    contacts: str = Field(..., min_length=8, max_length=15)
    email: EmailStr