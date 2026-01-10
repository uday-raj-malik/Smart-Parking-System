import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime


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

    def send_capacity_alert(self, current_count, max_capacity, plate_number=None, entry_time=None):
        """
        Sends email alert when parking capacity is exceeded
        
        Args:
            current_count: Current number of vehicles parked
            max_capacity: Maximum parking capacity
            plate_number: Plate number of vehicle that caused capacity exceed (optional)
            entry_time: Entry time of vehicle (optional)
        """
        subject = "🚨 Parking Capacity Exceeded Alert"
        
        # Format entry time if provided
        entry_time_str = entry_time.strftime('%Y-%m-%d %H:%M:%S') if entry_time else "N/A"
        plate_info = plate_number if plate_number else "UNKNOWN"
        
        body = f"""
        ALERT FROM SMART PARKING SYSTEM

        Parking capacity has been exceeded!

        Maximum Capacity : {max_capacity}
        Current Vehicles : {current_count}
        
        Vehicle Details:
        Plate Number : {plate_info}
        Entry Time : {entry_time_str}

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
    
    def send_csv_report(self, csv_file_path: str):
        """
        Sends CSV file as email attachment.
        
        Args:
            csv_file_path: Path to the CSV file to send
        """
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV file not found: {csv_file_path}")
            return False
        
        subject = "📊 Daily Parking Log Report"
        body = f"""
        Smart Parking System - Daily Report
        
        Please find attached the parking log CSV file.
        
        This report contains all vehicle entries and exits for today.
        
        — Smart Parking Enforcement System
        """
        
        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.receiver_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            
            # Attach CSV file
            filename = os.path.basename(csv_file_path)
            with open(csv_file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}',
            )
            
            msg.attach(part)
            
            # Send email
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()
            
            print(f"📧 CSV report sent successfully to {self.receiver_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send CSV report: {e}")
            return False

    def send_illegal_parking_alert(self, plate_number: str, entry_time: datetime = None):
        if entry_time is None:
            entry_time = datetime.now()
        """
        Sends email alert when a vehicle is parked illegally.
        
        Args:
            plate_number: Plate number of vehicle that is parked illegally
            entry_time: Entry time of vehicle that is parked illegally
        """
        subject = "🚨 Illegal Parking Alert"
        body = f"""
        Smart Parking System - Illegal Parking Alert

        A vehicle with plate number {plate_number} has been parked illegally at {entry_time.strftime('%Y-%m-%d %H:%M:%S') if entry_time else 'N/A'}.

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