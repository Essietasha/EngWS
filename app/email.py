# app/email.py
from flask_mail import Message
from app import mail
from flask import current_app

def send_confirmation_email(to_email, date, time, name):
    msg = Message('Your Trial Lesson is Booked!',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[to_email],
                  cc=['essietasharae@gmail.com'] )
    msg.body = f"""
Hi {name}!

Your trial lesson has been booked for:
📅 Date: {date}
⏰ Time: {time}

Please join using the Zoom link at the scheduled time:
🔗 Zoom Link: https://us05web.zoom.us/j/84731778227?pwd=wxUdG2qIEmcLcgEvhtXdLFNzpKFEer.1
Meeting ID: 847 3177 8227
Passcode: 125
Looking forward to meeting you!

For more enquiries:
Email: essietasharae@gmail.com
WhatsApp: +2347018454916

Warm regards,  
Essie
"""
    mail.send(msg)
