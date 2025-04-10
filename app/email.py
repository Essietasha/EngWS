# app/email.py
from flask_mail import Message
from app import mail
from flask import current_app
from datetime import datetime, timezone

def send_confirmation_email(to_email, name, lastname, date, time, phone, created_at):

    created_date = created_at.strftime('%B %d, %Y, %I:%M %p')

    msg = Message('Your Trial Lesson is Booked!',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[to_email] )
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

For more enquiries: essietasharae@gmail.com

Warm regards,  
Essie
"""
    mail.send(msg)


    admin_msg = Message(
    subject='📥 New Trial Booking',
    sender=current_app.config['MAIL_USERNAME'],
    recipients=['essietasharae@gmail.com'],
    body=f"""
A New Trial Lesson has been booked:

DETAILS:

Name: {name}

Last Name: {lastname}

Email: {to_email}

Date: {date}

Time: {time}

Phone Number: {phone}

Booking Confirmation Date: {created_date}
"""
)
    mail.send(admin_msg)



