from twilio.rest import Client
import os

def send_whatsapp_message(to_number: str, body: str):
    """
    Envoie un message WhatsApp via l'API Twilio.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")

    # Lignes de diagnostic à ajouter
    print(f"DEBUG - TWILIO_ACCOUNT_SID lu : {account_sid}")
    print(f"DEBUG - TWILIO_AUTH_TOKEN lu : {auth_token}")
    print(f"DEBUG - TWILIO_WHATSAPP_NUMBER lu : {twilio_whatsapp_number}")

    if not all([account_sid, auth_token, twilio_whatsapp_number]):
        print("Erreur: Les variables d'environnement Twilio ne sont pas configurées.")
        return

    try:
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            from_=twilio_whatsapp_number,
            body=body,
            to=f"whatsapp:{to_number}"
        )
        print(f"Message WhatsApp envoyé avec succès à {to_number}. SID: {message.sid}")
    except Exception as e:
        print(f"Erreur lors de l'envoi du message WhatsApp : {e}")