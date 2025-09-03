import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from string import Template

# -----------------------------
# TEMPLATES DÉTERMINISTES
# -----------------------------
HTML_EMAIL_TEMPLATE = Template(r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Bienvenue chez MLC</title>
<style>
  @media only screen and (max-width:600px) {
    .container { width:100% !important; }
    .stack-column, .stack-cell { display:block !important; width:100% !important; max-width:100% !important; }
    .greeting { font-size:1.25rem !important; }
    .logo-img { height:44px !important; }
    .feature-img { width:40px !important; height:auto !important; }
    .cta-button { padding:12px 20px !important; font-size:16px !important; }
  }
</style>
</head>
<body style="margin:0;padding:0;background-color:#f8f9fa;font-family:Arial, Helvetica, sans-serif;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f8f9fa;">
  <tr>
    <td align="center" style="padding:20px;">
      <table role="presentation" class="container" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.06);">
        <tr>
          <td style="background:linear-gradient(135deg,#2563eb 0%,#1d4ed8 100%);padding:22px 20px;text-align:left;">
            <table role="presentation" width="100%">
              <tr>
                <td>
                  <a href="https://mlc.health" target="_blank" style="text-decoration:none;display:inline-block;">
                    <img src="https://mlc.health/img/logo.png" alt="MLC" class="logo-img" width="60" height="60" style="display:block;max-width:100%;width:60px;height:60px;border-radius:50%;background-color:#ffffff;padding:6px;box-shadow:0 0 5px rgba(0,0,0,0.1);border:0;outline:0;">
                  </a>
                </td>
                <td style="text-align:right;color:#e8f0ff;font-size:14px;">
                  <div style="font-weight:600">Programme de Santé Globale</div>
                </td>
              </tr>
            </table>
          </td>
        </tr>

        <tr>
          <td style="padding:34px 30px 20px 30px;">
            <div class="greeting" style="font-size:1.6rem;color:#1f2937;font-weight:600;margin-bottom:14px;">
              Bonjour <span style="color:#2563eb;font-weight:700;">$nom</span> !
            </div>

            <div style="font-size:1.02rem;color:#4b5563;line-height:1.6;margin-bottom:16px;">
              Bienvenue dans l'aventure <span style="color:#2563eb;font-weight:600;">MLC</span> ! Nous sommes ravis de vous accueillir dans notre programme innovant de santé globale qui aide déjà de nombreuses personnes à transformer leur quotidien.
            </div>

            <div style="font-size:1.02rem;color:#4b5563;line-height:1.6;margin-bottom:22px;">
              Cette <span style="color:#2563eb;font-weight:600;">opportunité unique</span> dans le domaine de la santé et du bien-être va vous permettre d'améliorer durablement votre énergie, votre forme physique et votre équilibre de vie.
            </div>

            <table role="presentation" width="100%" style="margin-bottom:18px;">
              <tr>
                <td class="stack-cell" valign="top" align="center" style="padding:8px;">
                  <table role="presentation" style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:18px;width:100%;">
                    <tr><td align="center" style="padding-bottom:8px;">
                      <img src="https://cdn-icons-png.flaticon.com/512/1828/1828884.png" alt="Innovation" class="feature-img" width="45" style="display:block;width:45px;height:auto;border:0;outline:0;">
                    </td></tr>
                    <tr><td align="center" style="font-size:0.95rem;font-weight:600;color:#374151;">Innovation</td></tr>
                    <tr><td align="center" style="font-size:0.85rem;color:#6b7280;">Programme révolutionnaire</td></tr>
                  </table>
                </td>
                <td class="stack-cell" valign="top" align="center" style="padding:8px;">
                  <table role="presentation" style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:18px;width:100%;">
                    <tr><td align="center" style="padding-bottom:8px;">
                      <img src="https://cdn-icons-png.flaticon.com/512/869/869869.png" alt="Bien-être" class="feature-img" width="45">
                    </td></tr>
                    <tr><td align="center" style="font-size:0.95rem;font-weight:600;color:#374151;">Bien-être</td></tr>
                    <tr><td align="center" style="font-size:0.85rem;color:#6b7280;">Transformation durable</td></tr>
                  </table>
                </td>
                <td class="stack-cell" valign="top" align="center" style="padding:8px;">
                  <table role="presentation" style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:10px;padding:18px;width:100%;">
                    <tr><td align="center" style="padding-bottom:8px;">
                      <img src="https://cdn-icons-png.flaticon.com/512/1256/1256650.png" alt="Communauté" class="feature-img" width="45">
                    </td></tr>
                    <tr><td align="center" style="font-size:0.95rem;font-weight:600;color:#374151;">Communauté</td></tr>
                    <tr><td align="center" style="font-size:0.85rem;color:#6b7280;">Accompagnement expert</td></tr>
                  </table>
                </td>
              </tr>
            </table>

            <div style="background:#f0f9ff;border-left:4px solid #2563eb;padding:14px 18px;margin-bottom:22px;font-size:1rem;color:#374151;line-height:1.6;">
              <strong>Voici les étapes à suivre :</strong><br>
              <strong>ÉTAPE 1 :</strong> Inscrivez-vous sur la plateforme officielle MLC en cliquant 👉 <a href="https://mlc.health/fr/fsd865" target="_blank" style="color:#2563eb;font-weight:600;">ici</a><br>
              <strong>ÉTAPE 2 :</strong> Rejoignez le groupe WhatsApp en cliquant 👉 <a href="https://chat.whatsapp.com/CuYWhHMHkin9PjwO4t2JMM?mode=ac_t" target="_blank" style="color:#2563eb;font-weight:600;">ici</a>
            </div>
          </td>
        </tr>

        <tr>
          <td style="background-color:#f8fafc;padding:18px 24px 24px 24px;text-align:center;border-top:1px solid #e5e7eb;color:#6b7280;font-size:0.95rem;">
            <div style="font-weight:700;color:#374151;margin-bottom:6px;">Votre parcours vers un mieux-être optimal commence ici !</div>
            <div style="font-size:0.85rem;color:#9ca3af;">MLC Health</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>
</table>
</body>
</html>
""")

def send_confirmation_email(recipient_email: str, recipient_name: str):
    """
    Envoie un e-mail de confirmation HTML à un utilisateur en utilisant un template.
    """
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("EMAIL_SMTP_SERVER")
    smtp_port = os.getenv("EMAIL_SMTP_PORT")

    if not all([sender_email, sender_password, smtp_server, smtp_port]):
        print("Erreur: Les variables d'environnement pour l'email ne sont pas configurées.")
        return

    # Création du message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'Bienvenue chez MLC - Confirmation de votre inscription'
    msg['From'] = sender_email
    msg['To'] = recipient_email

    # Remplacer la variable $nom dans le template
    html_content = HTML_EMAIL_TEMPLATE.safe_substitute(nom=recipient_name)
    
    # Attacher la partie HTML
    part1 = MIMEText(html_content, 'html')
    msg.attach(part1)

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        print(f"E-mail HTML de confirmation envoyé à {recipient_email}")
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'e-mail : {e}")