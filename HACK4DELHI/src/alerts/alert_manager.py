import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class AlertManager:
    def __init__(self, sender_email, sender_password, receiver_email):
        """
        sender_email: Email from which alert is sent
        sender_password: App password (NOT normal email password)
        receiver_email: MCD / authority email
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.receiver_email = receiver_email

    def send_capacity_alert(self, current_count, max_capacity):
        """
        Sends email alert when parking capacity is exceeded
        """
        subject = "🚨 Parking Capacity Exceeded Alert"
        body = f"""
        ALERT FROM SMART PARKING SYSTEM

        Parking capacity has been exceeded.

        Maximum Capacity : {max_capacity}
        Current Vehicles : {current_count}

        Immediate action required.

        — Smart Parking Enforcement System
        """

        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.receiver_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()

            print("📧 Email alert sent successfully to MCD")

        except Exception as e:
            print("❌ Failed to send email alert:", e)
