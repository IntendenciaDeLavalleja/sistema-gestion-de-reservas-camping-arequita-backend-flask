from flask_mail import Message
from flask import current_app, render_template
from app.extensions import mail
from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Error al enviar correo electrónico: {e}")

def send_email(subject, recipients, text_body, html_body, attachments=None):
    msg = Message(subject, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    
    if attachments:
        for att in attachments:
            msg.attach(
                att['filename'],
                att['content_type'],
                att['data']
            )
    
    # Send asynchronously to not block the server
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def send_2fa_email(to_email, code):
    subject = "[Sistema de Reservas Camping Arequita] Código de Verificación"
    
    html_body = render_template(
        'emails/2fa_code.html',
        code=code
    )
    
    send_email(
        subject=subject,
        recipients=[to_email],
        text_body=f"Tu código de verificación es: {code}. Expira en 10 minutos.",
        html_body=html_body
    )


def send_camping_pre_reservation_email(pre_reservation):
    subject = f"[Camping Arequita] Pre-reserva recibida - {pre_reservation.code}"

    html_body = render_template(
        'emails/camping_pre_reservation.html',
        pre_reservation=pre_reservation,
        payment_phone='4440 2503',
    )

    service_name = pre_reservation.service.localized_name(pre_reservation.lang) if pre_reservation.service else 'Servicio'
    text_body = (
        f"Tu pre-reserva {pre_reservation.code} para {service_name} fue recibida. "
        f"Debes formalizarla llamando al 4440 2503 para completar el pago."
    )

    send_email(
        subject=subject,
        recipients=[pre_reservation.email],
        text_body=text_body,
        html_body=html_body,
    )
