import smtplib
from email.message import EmailMessage


def email_alert(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['subject'] = subject
    msg['to'] = to

    user = "shaalaloka@gmail.com"
    msg['from'] = user
    password = "tfgkdqhihsasqhyn"

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(user, password)
    server.send_message(msg)

    server.quit()

# email_id = "anaghakswamy14@gmail.com"
# if __name__ == '__main__':
#     email_alert("Profile Authentication", "Your Organization have successfully authenticated your account. You can "
#                                           "Login from now onwards.", email_id)
