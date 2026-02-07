"""
Real-Time Restaurant Ordering System - Flask Backend
Complete with SQLite database, QR codes, real order management
Multi-tenant with 24-hour automated reports and data security
Version: 2.1.0 - Railway deployment ready
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from datetime import datetime, timedelta
import sqlite3
import os
import json
import secrets
import string
from functools import wraps
from io import BytesIO
import qrcode
from PIL import Image, ImageDraw, ImageFont
from werkzeug.security import generate_password_hash, check_password_hash
import random
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from threading import Thread
import time
import requests

# Database configuration - supports both SQLite (local) and PostgreSQL (Cloud Run)
USE_POSTGRES = os.environ.get('DB_HOST') is not None

if USE_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST'),
        'database': os.environ.get('DB_NAME', 'restaurant_db'),
        'user': os.environ.get('DB_USER'),
        'password': os.environ.get('DB_PASSWORD'),
        'port': os.environ.get('DB_PORT', '5432')
    }

# Configure Flask with explicit paths for templates and static files
# This ensures they work correctly in cloud deployments like Railway
app_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(app_dir, 'templates')
static_dir = os.path.join(app_dir, 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.environ.get('SECRET_KEY', 'restaurant_system_secret_2026')

# Email Configuration for sending reports
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', '').strip()
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', '').strip()

# Validate email credentials
EMAIL_CONFIGURED = SENDER_EMAIL and SENDER_PASSWORD and not SENDER_EMAIL.startswith('your-')
if not EMAIL_CONFIGURED:
    print("[WARNING] Email not configured!")
    print("  - Set SENDER_EMAIL environment variable")
    print("  - Set SENDER_PASSWORD environment variable (use Gmail App Password)")
    print("  - OTP emails will not be sent until configured")
else:
    print(f"[OK] Email configured: {SENDER_EMAIL}")

# Razorpay Configuration
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_YOUR_KEY')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'YOUR_SECRET')

# Subscription Plans (in INR)
SUBSCRIPTION_PLANS = {
    'basic': {'name': 'Basic', 'price': 2499, 'period_days': 30, 'features': ['Up to 10 tables', 'Basic analytics', 'Email support']},
    'pro': {'name': 'Pro', 'price': 5999, 'period_days': 30, 'features': ['Up to 50 tables', 'Advanced analytics', 'Priority support', 'Kitchen display']},
    'enterprise': {'name': 'Enterprise', 'price': 15999, 'period_days': 30, 'features': ['Unlimited tables', 'Full analytics', '24/7 support', 'Kitchen display', 'API access']},
}

# Trial Configuration
TRIAL_DAYS = 7
FREE_TRIAL_PERIOD = timedelta(days=TRIAL_DAYS)
INACTIVITY_WARNING_DAYS = 30
ACCOUNT_DELETE_DAYS = 31

def send_otp_email(recipient_email, otp_code):
    """Send OTP to email with comprehensive error handling"""
    import sys
    
    # Check if email is configured
    if not EMAIL_CONFIGURED:
        print(f"[WARNING] Email not configured - OTP not sent to {recipient_email}", flush=True)
        print(f"[INFO] OTP for testing: {otp_code}", flush=True)
        sys.stderr.flush()
        return False
    
    try:
        # Validate email format
        if '@' not in recipient_email:
            print(f"[ERROR] Invalid recipient email: {recipient_email}", flush=True)
            return False
        
        print(f"[DEBUG] Preparing OTP email for {recipient_email}", flush=True)
        
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = f"Your OTP Code: {otp_code}"
        
        # HTML email template
        html_body = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                    .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 40px; border-radius: 8px; }}
                    .header {{ color: #667eea; font-size: 24px; margin-bottom: 20px; text-align: center; }}
                    .otp-box {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0; }}
                    .otp-code {{ font-size: 32px; font-weight: bold; color: #667eea; letter-spacing: 2px; }}
                    .warning {{ color: #ff6b6b; font-size: 12px; margin-top: 15px; text-align: center; }}
                    .footer {{ color: #999; font-size: 12px; margin-top: 20px; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">Your OTP Code</div>
                    
                    <p>Hello,</p>
                    <p>You requested a password reset or email verification. Use the OTP code below:</p>
                    
                    <div class="otp-box">
                        <div class="otp-code">{otp_code}</div>
                    </div>
                    
                    <p><strong>This OTP will expire in 10 minutes.</strong></p>
                    
                    <p>If you did not request this code, please ignore this email and do not share this code with anyone.</p>
                    
                    <div class="warning">
                        Never share this OTP with anyone. Our team will never ask for your OTP.
                    </div>
                    
                    <div class="footer">
                        <p>Best regards,<br/>Hotel Management System Team</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
Your OTP Code: {otp_code}

This OTP will expire in 10 minutes.

If you did not request this code, please ignore this email.

Do not share this OTP with anyone.

Best regards,
Hotel Management System Team
        """
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email via SMTP with error handling
        try:
            print(f"[DEBUG] Connecting to {SMTP_SERVER}:{SMTP_PORT}", flush=True)
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10)
            print("[DEBUG] Connected to SMTP server", flush=True)
            
            print("[DEBUG] Starting TLS", flush=True)
            server.starttls()
            print("[DEBUG] TLS started", flush=True)
            
            print(f"[DEBUG] Logging in as {SENDER_EMAIL}", flush=True)
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("[DEBUG] Login successful", flush=True)
            
            print(f"[DEBUG] Sending message to {recipient_email}", flush=True)
            server.send_message(msg)
            print("[DEBUG] Message sent", flush=True)
            
            server.quit()
            print("[DEBUG] Connection closed", flush=True)
            
            print(f"[OK] OTP email sent successfully to {recipient_email}", flush=True)
            sys.stderr.flush()
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"[ERROR] SMTP Authentication failed - check SENDER_EMAIL and SENDER_PASSWORD", flush=True)
            print(f"[ERROR] Exception: {str(e)}", flush=True)
            print(f"[ERROR] SENDER_EMAIL: {SENDER_EMAIL}", flush=True)
            print(f"[ERROR] SENDER_PASSWORD length: {len(SENDER_PASSWORD)}", flush=True)
            sys.stderr.flush()
            return False
        except smtplib.SMTPException as e:
            print(f"[ERROR] SMTP error sending email: {str(e)}", flush=True)
            sys.stderr.flush()
            return False
        except socket.timeout as e:
            print(f"[ERROR] SMTP connection timeout: {str(e)}", flush=True)
            sys.stderr.flush()
            return False
        except Exception as e:
            print(f"[ERROR] Connection error: {str(e)}", flush=True)
            print(f"[ERROR] Error type: {type(e).__name__}", flush=True)
            sys.stderr.flush()
            return False
        
    except Exception as e:
        print(f"[ERROR] Failed to create email for {recipient_email}: {str(e)}", flush=True)
        sys.stderr.flush()
        return False

def generate_otp():
    """Generate 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def save_otp(email, otp_code, retries=3):
    """Save OTP to database with retry logic for locked database"""
    for attempt in range(retries):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            c = conn.cursor()
            expires_at = datetime.now() + timedelta(minutes=10)
            
            c.execute('DELETE FROM otp_tokens WHERE owner_email = ?', (email,))
            c.execute('''INSERT INTO otp_tokens (owner_email, otp_code, expires_at) 
                         VALUES (?, ?, ?)''', (email, otp_code, expires_at))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < retries - 1:
                print(f"[WARNING] Database locked on OTP save, retrying ({attempt + 1}/{retries})...")
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            else:
                print(f"[ERROR] Failed to save OTP after {retries} attempts: {e}")
                return False
        except Exception as e:
            print(f"[ERROR] Error saving OTP: {e}")
            return False

def check_otp(email, otp_code, retries=3):
    """Verify OTP with retry logic"""
    for attempt in range(retries):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            c = conn.cursor()
            
            c.execute('''SELECT * FROM otp_tokens 
                         WHERE owner_email = ? AND otp_code = ? AND is_used = 0 
                         AND expires_at > datetime('now')''', (email, otp_code))
            
            result = c.fetchone()
            conn.close()
            
            return result is not None
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < retries - 1:
                print(f"[WARNING] Database locked on OTP check, retrying ({attempt + 1}/{retries})...")
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                print(f"[ERROR] Failed to check OTP after {retries} attempts: {e}")
                return False

def mark_otp_used(email, retries=3):
    """Mark OTP as used with retry logic"""
    for attempt in range(retries):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            c = conn.cursor()
            
            c.execute('UPDATE otp_tokens SET is_used = 1 WHERE owner_email = ? AND is_used = 0',
                      (email,))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < retries - 1:
                print(f"[WARNING] Database locked on OTP mark, retrying ({attempt + 1}/{retries})...")
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                print(f"[ERROR] Failed to mark OTP as used after {retries} attempts: {e}")
                return False

def mark_email_verified(email, retries=3):
    """Mark email as verified in settings with retry logic"""
    for attempt in range(retries):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            c = conn.cursor()
            
            c.execute('UPDATE settings SET owner_verified = 1 WHERE owner_email = ?', (email,))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < retries - 1:
                print(f"[WARNING] Database locked on email verification, retrying ({attempt + 1}/{retries})...")
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                print(f"[ERROR] Failed to mark email verified after {retries} attempts: {e}")
                return False


def generate_daily_report_pdf(hotel_id, hotel_name, owner_email):
    """Generate 24-hour report PDF for a hotel - ONLY this hotel's data"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        c = conn.cursor()
        
        # ============================================================================
        # CRITICAL: ALL queries below filter by hotel_id to ensure data isolation
        # Each report contains ONLY this hotel's data, NO other hotels' data
        # ============================================================================
        
        # Get 24-hour data
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        # Get orders from last 24 hours - FILTERED by hotel_id
        c.execute('''SELECT COUNT(*) as count, SUM(total) as revenue 
                     FROM orders WHERE hotel_id = ? AND created_at >= ?''',
                 (hotel_id, yesterday))
        order_stats = c.fetchone()
        
        # Get menu items sold - FILTERED by hotel_id
        c.execute('''SELECT * FROM menu_items WHERE hotel_id = ? AND is_available = 1 LIMIT 20''',
                 (hotel_id,))
        menu_items = c.fetchall()
        
        # Get all orders for details - FILTERED by hotel_id and time
        c.execute('''SELECT * FROM orders WHERE hotel_id = ? AND created_at >= ? ORDER BY created_at DESC''',
                 (hotel_id, yesterday))
        orders = c.fetchall()
        
        conn.close()
        
        # Verify data isolation - ensure all orders belong to this hotel
        for order in orders:
            if order['hotel_id'] != hotel_id:
                raise Exception(f"DATA ISOLATION ERROR: Order {order['id']} has wrong hotel_id!")
        
        # Create PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Add security header to PDF
        security_text = f"Confidential - {hotel_name} Only | Report Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        story.append(Paragraph(security_text, styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=1
        )
        story.append(Paragraph(f"24-Hour Report: {hotel_name}", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Report period
        period_text = f"Report Period: {yesterday.strftime('%Y-%m-%d %H:%M')} to {now.strftime('%Y-%m-%d %H:%M')}"
        story.append(Paragraph(period_text, styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Summary section
        story.append(Paragraph("SUMMARY", styles['Heading2']))
        total_orders = order_stats['count'] or 0
        total_revenue = order_stats['revenue'] or 0
        
        summary_data = [
            ['Total Orders (24h)', str(total_orders)],
            ['Total Revenue (24h)', f'₹{total_revenue:.2f}'],
            ['Average Order Value', f'₹{(total_revenue/total_orders if total_orders > 0 else 0):.2f}']
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Recent orders
        if orders:
            story.append(Paragraph("RECENT ORDERS", styles['Heading2']))
            orders_data = [['Order ID', 'Table', 'Amount', 'Status', 'Time']]
            for order in orders[:10]:  # Last 10 orders
                order_time = order['created_at'].split('.')[0] if order['created_at'] else 'N/A'
                orders_data.append([
                    str(order['id']),
                    str(order['table_number']),
                    f"₹{order['total']:.2f}",
                    order['status'],
                    order_time
                ])
            
            orders_table = Table(orders_data, colWidths=[0.8*inch, 0.8*inch, 1*inch, 1*inch, 1.5*inch])
            orders_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(orders_table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None


def send_report_email(hotel_id, hotel_name, owner_email):
    """Send 24-hour report to hotel owner via email"""
    try:
        # Generate PDF
        pdf_buffer = generate_daily_report_pdf(hotel_id, hotel_name, owner_email)
        
        if not pdf_buffer:
            print(f"Failed to generate PDF for {hotel_name}")
            return False
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = owner_email
        msg['Subject'] = f"24-Hour Report - {hotel_name} ({datetime.now().strftime('%Y-%m-%d')})"
        
        # Email body
        body = f"""
        Dear Hotel Owner,
        
        Please find attached the 24-hour performance report for {hotel_name}.
        
        This report includes:
        - Total orders and revenue
        - Average order value
        - Recent orders summary
        - Period: Last 24 hours
        
        Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        
        Best regards,
        Hotel Management System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_buffer.getvalue())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= "Report_{hotel_name}_{datetime.now().strftime("%Y%m%d")}.pdf"')
        msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"[OK] Report sent to {owner_email} for {hotel_name}")
        return True
        
    except Exception as e:
        print(f"Error sending email to {owner_email}: {e}")
        return False


def send_daily_reports():
    """Send 24-hour reports to all hotels"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get all hotels with owner email
        c.execute('SELECT id, hotel_name, owner_email FROM settings WHERE owner_email IS NOT NULL AND owner_email != ""')
        hotels = c.fetchall()
        conn.close()
        
        for hotel in hotels:
            hotel_id = hotel['id']
            hotel_name = hotel['hotel_name']
            owner_email = hotel['owner_email']
            
            if owner_email:
                send_report_email(hotel_id, hotel_name, owner_email)
        
        return True
    except Exception as e:
        print(f"Error in daily report generation: {e}")
        return False


def start_daily_report_scheduler():
    """Start background scheduler for daily reports (runs once per day)"""
    def scheduler():
        while True:
            try:
                now = datetime.now()
                # Run at 11:59 PM every day
                target_time = now.replace(hour=23, minute=59, second=0, microsecond=0)
                
                # If time has passed today, schedule for tomorrow
                if now > target_time:
                    target_time = target_time + timedelta(days=1)
                
                # Calculate wait time
                wait_seconds = (target_time - now).total_seconds()
                
                # Sleep until target time
                time.sleep(wait_seconds)
                
                # Send reports
                send_daily_reports()
                
            except Exception as e:
                print(f"Scheduler error: {e}")
                time.sleep(3600)  # Sleep 1 hour on error
    
    # Start scheduler in background thread
    scheduler_thread = Thread(target=scheduler, daemon=True)
    scheduler_thread.start()


# ============================================================================
# SUBSCRIPTION & PAYMENT MANAGEMENT FUNCTIONS
# ============================================================================

def get_subscription_status(hotel_id):
    """Get hotel's subscription status"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''SELECT subscription_status, trial_ends_at, subscription_end_date, 
                        is_active, last_payment_date, subscription_plan
                 FROM settings WHERE id = ?''', (hotel_id,))
    
    result = c.fetchone()
    conn.close()
    
    if not result:
        return None
    
    return {
        'status': result['subscription_status'],
        'trial_ends_at': result['trial_ends_at'],
        'subscription_end_date': result['subscription_end_date'],
        'is_active': result['is_active'],
        'last_payment_date': result['last_payment_date'],
        'plan': result['subscription_plan']
    }

def is_subscription_active(hotel_id):
    """Check if hotel's subscription is active"""
    status = get_subscription_status(hotel_id)
    if not status:
        return False
    
    # Check if account is active
    if status['is_active'] == 0:
        return False
    
    # Check if in trial period
    if status['status'] == 'trial':
        trial_ends = datetime.fromisoformat(status['trial_ends_at'])
        if datetime.now() < trial_ends:
            return True
        return False
    
    # Check if paid subscription is active
    if status['status'] == 'active':
        if status['subscription_end_date']:
            sub_ends = datetime.fromisoformat(status['subscription_end_date'])
            if datetime.now() < sub_ends:
                return True
        return False
    
    return False

def create_razorpay_order(hotel_id, hotel_name, plan):
    """Create Razorpay order for subscription"""
    if plan not in SUBSCRIPTION_PLANS:
        return None, "Invalid plan"
    
    plan_details = SUBSCRIPTION_PLANS[plan]
    amount_in_paise = int(plan_details['price'] * 100)  # Razorpay expects paise
    
    try:
        url = "https://api.razorpay.com/v1/orders"
        auth = (RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
        
        payload = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": f"hotel_{hotel_id}_{int(datetime.now().timestamp())}",
            "notes": {
                "hotel_id": str(hotel_id),
                "hotel_name": hotel_name,
                "plan": plan
            }
        }
        
        response = requests.post(url, data=payload, auth=auth, timeout=5)
        
        if response.status_code == 200:
            order_data = response.json()
            return order_data, None
        else:
            return None, f"Razorpay error: {response.status_code}"
    
    except Exception as e:
        return None, str(e)

def verify_razorpay_payment(order_id, payment_id, signature, hotel_id):
    """Verify Razorpay payment signature and log payment"""
    try:
        import hashlib
        import hmac
        
        # Create verification string
        verify_string = f"{order_id}|{payment_id}"
        
        # Create signature
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            verify_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        if generated_signature == signature:
            # Log successful verification
            conn = sqlite3.connect(DB_PATH, timeout=30)
            c = conn.cursor()
            c.execute('''INSERT INTO payments (order_id, payment_id, amount, status, created_at)
                         VALUES (?, ?, 0, "verified", datetime("now"))''',
                     (order_id, payment_id))
            conn.commit()
            conn.close()
            return True, "Payment verified successfully"
        else:
            print(f"[ERROR] Payment signature mismatch for order {order_id}")
            return False, "Payment signature mismatch"
    
    except Exception as e:
        print(f"[ERROR] Payment verification error: {str(e)}")
        return False, str(e)

def check_existing_subscription(hotel_id):
    """Check if hotel already has an active/paid subscription"""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''SELECT subscription_status, subscription_plan, subscription_end_date, is_active
                 FROM settings WHERE id = ? AND subscription_status = "active"''', (hotel_id,))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        # Check if subscription end date has passed
        if result['subscription_end_date']:
            sub_ends = datetime.fromisoformat(result['subscription_end_date'])
            if datetime.now() < sub_ends:
                return True, result['subscription_plan']  # Active subscription exists
    
    return False, None

def activate_subscription(hotel_id, plan, payment_id=None):
    """Activate subscription for hotel after payment"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        now = datetime.now()
        end_date = now + timedelta(days=SUBSCRIPTION_PLANS[plan]['period_days'])
        
        c.execute('''UPDATE settings 
                     SET subscription_status = "active",
                         subscription_plan = ?,
                         subscription_start_date = ?,
                         subscription_end_date = ?,
                         payment_status = "completed",
                         razorpay_payment_id = ?,
                         last_payment_date = ?,
                         is_active = 1
                     WHERE id = ?''',
                 (plan, now, end_date, payment_id, now, hotel_id))
        
        # Log the subscription activation
        c.execute('''INSERT INTO subscription_logs 
                     (hotel_id, hotel_name, event_type, event_description, new_status)
                     SELECT id, hotel_name, "subscription_activated", ?, "active"
                     FROM settings WHERE id = ?''',
                 (f"Activated {plan} plan via Razorpay", hotel_id))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        conn.close()
        return False

def deactivate_account(hotel_id, reason="Subscription expired"):
    """Deactivate account when subscription expires"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''UPDATE settings SET is_active = 0 WHERE id = ?''', (hotel_id,))
        
        c.execute('''INSERT INTO subscription_logs 
                     (hotel_id, hotel_name, event_type, event_description, old_status, new_status)
                     SELECT id, hotel_name, "account_deactivated", ?, "active", "inactive"
                     FROM settings WHERE id = ?''',
                 (reason, hotel_id))
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        conn.close()
        return False

def check_subscription_expiry():
    """Check and deactivate expired subscriptions (background task)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    now = datetime.now()
    
    # Find subscriptions that have expired
    c.execute('''SELECT id, hotel_name, subscription_end_date 
                 FROM settings 
                 WHERE subscription_status = "active" 
                 AND subscription_end_date IS NOT NULL 
                 AND subscription_end_date < ?''',
             (now,))
    
    expired = c.fetchall()
    
    for hotel in expired:
        deactivate_account(hotel['id'], f"Subscription expired on {hotel['subscription_end_date']}")
    
    conn.close()
    return len(expired)

def check_trial_expiry():
    """Check and deactivate expired trials"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    now = datetime.now()
    
    # Find trials that have expired
    c.execute('''SELECT id, hotel_name, trial_ends_at 
                 FROM settings 
                 WHERE subscription_status = "trial" 
                 AND trial_ends_at IS NOT NULL 
                 AND trial_ends_at < ?''',
             (now,))
    
    expired = c.fetchall()
    
    for hotel in expired:
        # Update status to "trial_expired" but keep account active for viewing
        c.execute('''UPDATE settings 
                     SET subscription_status = "trial_expired", is_active = 0 
                     WHERE id = ?''', (hotel['id'],))
        
        c.execute('''INSERT INTO subscription_logs 
                     (hotel_id, hotel_name, event_type, event_description, old_status, new_status)
                     SELECT id, hotel_name, "trial_expired", ?, "trial", "trial_expired"
                     FROM settings WHERE id = ?''',
                 ('Free trial period ended', hotel['id']))
    
    conn.commit()
    conn.close()
    return len(expired)

def check_account_inactivity():
    """Check for inactive accounts and delete after 31 days
    CRITICAL SAFETY: Only deletes explicitly trial-expired accounts, NOT new trial accounts
    REQUIRES: subscription_status='trial_expired' AND no previous payments AND 31+ days old"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        now = datetime.now()
        delete_threshold = now - timedelta(days=ACCOUNT_DELETE_DAYS)
        
        # SAFETY-FIRST QUERIES: Multiple conditions to protect against accidental deletion
        # 1. subscription_status MUST be 'trial_expired' (not just 'trial')
        # 2. MUST have NO previous payments (last_payment_date IS NULL)
        # 3. MUST be older than ACCOUNT_DELETE_DAYS (31 days by default)
        # 4. is_active MUST be 0 (account was explicitly deactivated)
        
        c.execute('''SELECT id, hotel_name, subscription_end_date, last_payment_date, created_at, subscription_status
                     FROM settings 
                     WHERE subscription_status = "trial_expired"
                     AND last_payment_date IS NULL
                     AND created_at < ?
                     AND is_active = 0''',
                 (delete_threshold,))
        
        inactive = c.fetchall()
        
        if inactive:
            print(f"\n[CLEANUP] ========== ACCOUNT INACTIVITY CHECK ==========")
            print(f"[CLEANUP] Found {len(inactive)} expired trial accounts eligible for deletion")
            print(f"[CLEANUP] Criteria: status='trial_expired' + no payments + 31+ days old + is_active=0")
        
        deleted_count = 0
        for hotel in inactive:
            try:
                # Final confirmation: re-check ALL conditions before deletion
                c.execute('''SELECT id FROM settings 
                            WHERE id = ? 
                            AND subscription_status = "trial_expired"
                            AND last_payment_date IS NULL
                            AND created_at < ?
                            AND is_active = 0''',
                         (hotel['id'], delete_threshold))
                
                if c.fetchone():
                    print(f"[CLEANUP] Deleting expired trial: {hotel['hotel_name']} (ID: {hotel['id']}) - Status verified")
                    c.execute('DELETE FROM settings WHERE id = ?', (hotel['id'],))
                    c.execute('DELETE FROM orders WHERE hotel_id = ?', (hotel['id'],))
                    c.execute('DELETE FROM menu_items WHERE hotel_id = ?', (hotel['id'],))
                    c.execute('DELETE FROM restaurant_tables WHERE hotel_id = ?', (hotel['id'],))
                    deleted_count += 1
                else:
                    print(f"[WARNING] Hotel {hotel['id']} no longer meets deletion criteria - SKIPPED")
            except Exception as e:
                print(f"[ERROR] Failed to delete hotel {hotel['id']}: {e}")
        
        if deleted_count > 0:
            conn.commit()
            print(f"[CLEANUP] Successfully deleted {deleted_count} accounts")
            print(f"[CLEANUP] ========== END INACTIVITY CHECK ==========\n")
        
        conn.close()
        return deleted_count
    except Exception as e:
        print(f"[ERROR] Error checking account inactivity: {e}")
        return 0

# ============================================================================
# 90-DAY DATA RETENTION & AUTOMATIC DELETION SYSTEM
# ============================================================================

def delete_old_orders(days_to_retain=90):
    """
    Delete orders and associated data older than specified days.
    Called daily to maintain 90-day rolling window of data.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Calculate date threshold (90 days ago)
        cutoff_date = datetime.now() - timedelta(days=days_to_retain)
        cutoff_iso = cutoff_date.isoformat()
        
        # Count records before deletion
        c.execute('SELECT COUNT(*) FROM orders WHERE created_at < ?', (cutoff_iso,))
        orders_to_delete = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM payments WHERE created_at < ?', (cutoff_iso,))
        payments_to_delete = c.fetchone()[0]
        
        # Delete old orders
        c.execute('DELETE FROM orders WHERE created_at < ?', (cutoff_iso,))
        
        # Delete old payments
        c.execute('DELETE FROM payments WHERE created_at < ?', (cutoff_iso,))
        
        # Delete old subscription logs
        c.execute('DELETE FROM subscription_logs WHERE created_at < ?', (cutoff_iso,))
        
        # Vacuum database to reclaim space
        c.execute('VACUUM')
        
        conn.commit()
        conn.close()
        
        # Log deletion activity
        log_data_deletion(orders_to_delete, payments_to_delete, days_to_retain)
        
        print(f"[OK] Data retention cleanup completed:")
        print(f"  ├─ Orders deleted: {orders_to_delete}")
        print(f"  ├─ Payments deleted: {payments_to_delete}")
        print(f"  ├─ Cutoff date: {cutoff_iso}")
        print(f"  └─ Database optimized (VACUUM)")
        
        return {
            'success': True,
            'orders_deleted': orders_to_delete,
            'payments_deleted': payments_to_delete,
            'cutoff_date': cutoff_iso
        }
        
    except Exception as e:
        print(f"[ERROR] Error during data retention cleanup: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def log_data_deletion(orders_count, payments_count, days_retained):
    """Log data deletion activity for audit trail"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Create deletion log table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS data_deletion_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        deletion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        orders_deleted INTEGER,
                        payments_deleted INTEGER,
                        days_retained INTEGER,
                        database_size TEXT
                    )''')
        
        # Insert deletion record
        c.execute('''INSERT INTO data_deletion_logs 
                     (orders_deleted, payments_deleted, days_retained)
                     VALUES (?, ?, ?)''', 
                  (orders_count, payments_count, days_retained))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Could not log deletion: {str(e)}")

def schedule_daily_deletion():
    """
    Schedule automatic daily deletion at 2:00 AM.
    Runs in background thread.
    """
    def daily_cleanup():
        while True:
            try:
                # Calculate time until 2:00 AM
                now = datetime.now()
                tomorrow_2am = (now + timedelta(days=1)).replace(hour=2, minute=0, second=0, microsecond=0)
                seconds_until_2am = (tomorrow_2am - now).total_seconds()
                
                # Sleep until 2:00 AM
                time.sleep(seconds_until_2am)
                
                # Run deletion
                delete_old_orders(days_to_retain=90)
                
            except Exception as e:
                print(f"Error in daily deletion scheduler: {str(e)}")
                time.sleep(3600)  # Retry in 1 hour if error
    
    # Start scheduler in background thread (only once)
    if not hasattr(app, 'deletion_scheduler_started'):
        deletion_thread = Thread(target=daily_cleanup, daemon=True)
        deletion_thread.start()
        app.deletion_scheduler_started = True
        print("[OK] Daily data deletion scheduler started (runs at 2:00 AM daily)")

def get_database_stats():
    """Get current database size and retention statistics"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Count current records
        c.execute('SELECT COUNT(*) FROM orders')
        orders_count = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM payments')
        payments_count = c.fetchone()[0]
        
        # Get date range of data
        c.execute('SELECT MIN(created_at), MAX(created_at) FROM orders')
        date_range = c.fetchone()
        oldest_order = date_range[0] if date_range[0] else 'N/A'
        newest_order = date_range[1] if date_range[1] else 'N/A'
        
        # Get database file size
        db_size = os.path.getsize(DB_PATH)
        db_size_mb = db_size / (1024 * 1024)
        
        conn.close()
        
        return {
            'orders_count': orders_count,
            'payments_count': payments_count,
            'oldest_order': oldest_order,
            'newest_order': newest_order,
            'database_size_bytes': db_size,
            'database_size_mb': round(db_size_mb, 2),
            'retention_days': 90,
            'status': 'Active'
        }
    except Exception as e:
        return {
            'error': str(e),
            'status': 'Error'
        }

def subscription_required(f):
    """Decorator to check if subscription is active for QR code access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        table_id = request.args.get('id')
        if table_id:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute('SELECT hotel_id FROM restaurant_tables WHERE id = ?', (table_id,))
            table = c.fetchone()
            conn.close()
            
            if table and not is_subscription_active(table['hotel_id']):
                return render_template('subscription_expired.html'), 403
        
        return f(*args, **kwargs)
    
    return decorated_function

def validate_hotel_slug(slug):

    """Validate hotel slug (Instagram-style: alphanumeric, hyphens, underscores only)"""
    import re
    # Must be 3-30 chars, start with letter or number, only alphanumeric/hyphen/underscore
    if not slug:
        return False, "Hotel ID is required"
    
    # Convert to lowercase for processing
    slug_lower = slug.lower()
    
    if len(slug_lower) < 3 or len(slug_lower) > 30:
        return False, "Hotel ID must be 3-30 characters"
    
    # Lowercase only, can contain letters, numbers, hyphens, underscores
    # Must match the pattern: start and end with alphanumeric, any middle chars valid
    if not re.match(r'^[a-z0-9][a-z0-9_-]*[a-z0-9]$|^[a-z0-9]$', slug_lower):
        return False, "Hotel ID can only contain lowercase letters, numbers, hyphens, and underscores. Must start and end with alphanumeric character."
    
    return True, "Valid"


def generate_hotel_slug(hotel_name):
    """Generate unique hotel slug from hotel name"""
    import re
    # Convert to lowercase, replace spaces and special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', hotel_name.lower())
    slug = slug.strip('-')[:30]  # Max 30 chars
    return slug


def is_hotel_slug_available(slug, retries=3):
    """Check if hotel slug is already taken - with retry logic for database locks"""
    for attempt in range(retries):
        try:
            conn = sqlite3.connect(DB_PATH, timeout=30)
            c = conn.cursor()
            c.execute('SELECT id FROM settings WHERE hotel_slug = ?', (slug.lower(),))
            result = c.fetchone()
            conn.close()
            return result is None  # True if available (no result found)
        except sqlite3.OperationalError as e:
            if 'database is locked' in str(e) and attempt < retries - 1:
                print(f"[WARNING] Database locked checking slug, retrying ({attempt + 1}/{retries})...")
                time.sleep(0.5 * (attempt + 1))
                continue
            else:
                # On error, return False (assume taken) to be safe rather than creating duplicates
                print(f"[ERROR] Could not check hotel slug availability: {e}")
                return False
        except Exception as e:
            print(f"[ERROR] Error checking hotel slug availability: {e}")
            return False


# Custom Jinja2 filter for JSON parsing
def from_json(value):
    """Parse JSON string to Python object"""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except:
            return []
    return value

app.jinja_env.filters['from_json'] = from_json

# ============================================================================
# DATABASE SETUP - PERSISTENT STORAGE FOR RAILWAY DEPLOYMENT
# ============================================================================
# IMPORTANT: On Railway, the app directory is ephemeral and gets wiped on redeploy.
# To keep your data (menus, orders, QR codes, admin data) persistent:
# 
# 1. Go to your Railway project dashboard
# 2. Click on your hotel-app service  
# 3. Go to "Storage" tab (or "Volumes" in newer Railway UI)
# 4. Click "Create New"
# 5. Set Mount Path to: /data
# 6. Leave size as default (10GB)
# 7. Deploy - app will now use /data for persistent storage
#
# The app automatically detects /data directory if it exists and uses it.
# Otherwise, it falls back to storing in the app directory (local development).
# ============================================================================

# Database setup - use persistent storage if available (Railway Disk)
# CRITICAL: For Railway deployment, persistent storage MUST be configured
# Without it, all data will be lost on redeploy!
# See: RAILWAY_DEPLOYMENT.md for setup instructions

def get_db_path():
    """Get database path - prioritize persistent storage"""
    # Check if /data directory exists (Railway persistent volume)
    if os.path.exists('/data'):
        return '/data/restaurant.db'
    elif os.path.exists('/persistent'):
        return '/persistent/restaurant.db'
    else:
        # Fallback to app directory (local development only)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'restaurant.db')

DB_PATH = get_db_path()

# Log database location for debugging
print(f"[DATABASE] Using database at: {DB_PATH}")
print(f"[DATABASE] Persistent storage exists: {os.path.exists('/data') or os.path.exists('/persistent')}")

def init_db():
    """Initialize database - with full error tolerance"""
    try:
        conn = sqlite3.connect(DB_PATH, timeout=30)
        # Enable WAL mode and concurrency settings
        c = conn.cursor()
        c.execute('PRAGMA journal_mode=WAL')
        c.execute('PRAGMA busy_timeout=30000')
        c.execute('PRAGMA synchronous=NORMAL')
        conn.commit()
        c.close()
        conn = sqlite3.connect(DB_PATH, timeout=30)
        c = conn.cursor()
        
        # Admin users table
        c.execute('''CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Tables QR codes
        c.execute('''CREATE TABLE IF NOT EXISTS restaurant_tables (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER,
            table_number INTEGER UNIQUE,
            qr_code TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Menu items
        c.execute('''CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER,
            name TEXT,
            category TEXT,
            price REAL,
            description TEXT,
            image_path TEXT,
            is_available INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Settings table
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            hotel_name TEXT DEFAULT 'Royal Restaurant',
            hotel_slug TEXT UNIQUE,
            hotel_address TEXT,
            hotel_gstn TEXT,
            hotel_food_license TEXT,
            hotel_logo TEXT,
            owner_email TEXT,
            owner_password TEXT,
            owner_verified INTEGER DEFAULT 0,
            auto_accept_orders INTEGER DEFAULT 0,
            print_name INTEGER DEFAULT 1,
            print_address INTEGER DEFAULT 1,
            print_gstn INTEGER DEFAULT 1,
            print_license INTEGER DEFAULT 1,
            subscription_status TEXT DEFAULT 'trial',
            trial_ends_at TIMESTAMP,
            subscription_end_date TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            last_payment_date TIMESTAMP,
            subscription_plan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Orders table
        c.execute('''CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER,
            table_id INTEGER,
            table_number INTEGER,
            items TEXT,
            subtotal REAL,
            tax REAL,
            service_charge REAL,
            total REAL,
            status TEXT DEFAULT 'pending',
            assigned_to INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Sub-admins table
        c.execute('''CREATE TABLE IF NOT EXISTS sub_admins (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            name TEXT,
            assigned_tables TEXT,
            assigned_categories TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Payments table
        c.execute('''CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER,
            order_id INTEGER,
            payment_id TEXT,
            order_id_razorpay TEXT,
            amount REAL,
            currency TEXT,
            status TEXT DEFAULT 'pending',
            plan TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # OTP tokens table
        c.execute('''CREATE TABLE IF NOT EXISTS otp_tokens (
            id INTEGER PRIMARY KEY,
            owner_email TEXT,
            otp_code TEXT,
            is_used INTEGER DEFAULT 0,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Subscription logs table
        c.execute('''CREATE TABLE IF NOT EXISTS subscription_logs (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER,
            hotel_name TEXT,
            event_type TEXT,
            event_description TEXT,
            new_status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Store profiles (extended information about each restaurant)
        c.execute('''CREATE TABLE IF NOT EXISTS store_profiles (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER UNIQUE,
            phone_number TEXT,
            store_email TEXT,
            street_address TEXT,
            city TEXT,
            state TEXT,
            postal_code TEXT,
            country TEXT,
            latitude REAL,
            longitude REAL,
            open_time TEXT,
            close_time TEXT,
            working_days TEXT,
            holiday_dates TEXT,
            store_description TEXT,
            cuisine_type TEXT,
            average_rating REAL DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            logo_url TEXT,
            banner_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Photo gallery for each store
        c.execute('''CREATE TABLE IF NOT EXISTS store_gallery (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER,
            photo_url TEXT,
            photo_title TEXT,
            photo_description TEXT,
            display_order INTEGER DEFAULT 0,
            is_featured INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Store website templates and customization
        c.execute('''CREATE TABLE IF NOT EXISTS store_websites (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER UNIQUE,
            website_theme TEXT DEFAULT 'default',
            website_title TEXT,
            website_description TEXT,
            website_color TEXT,
            enable_online_ordering INTEGER DEFAULT 1,
            enable_reservations INTEGER DEFAULT 0,
            enable_delivery INTEGER DEFAULT 0,
            header_text TEXT,
            footer_text TEXT,
            custom_css TEXT,
            is_published INTEGER DEFAULT 0,
            published_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Enhanced table management with more details
        c.execute('''CREATE TABLE IF NOT EXISTS table_details (
            id INTEGER PRIMARY KEY,
            hotel_id INTEGER,
            table_number INTEGER,
            table_section TEXT,
            capacity INTEGER DEFAULT 4,
            is_active INTEGER DEFAULT 1,
            qr_code_url TEXT,
            table_status TEXT DEFAULT 'available',
            assigned_waiter TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        conn.commit()
        
        # Superadmin users table
        c.execute('''CREATE TABLE IF NOT EXISTS superadmins (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Add columns if they don't exist
        try:
            c.execute('ALTER TABLE settings ADD COLUMN approval_status TEXT DEFAULT "pending"')
            conn.commit()
        except:
            pass
        
        try:
            c.execute('ALTER TABLE settings ADD COLUMN contact_email TEXT')
            conn.commit()
        except:
            pass
        
        try:
            c.execute('ALTER TABLE settings ADD COLUMN contact_phone TEXT')
            conn.commit()
        except:
            pass
        
        try:
            c.execute('ALTER TABLE settings ADD COLUMN service_online_ordering INTEGER DEFAULT 0')
            conn.commit()
        except:
            pass
        
        try:
            c.execute('ALTER TABLE settings ADD COLUMN service_table_management INTEGER DEFAULT 0')
            conn.commit()
        except:
            pass
        
        try:
            c.execute('ALTER TABLE settings ADD COLUMN service_analytics INTEGER DEFAULT 0')
            conn.commit()
        except:
            pass
        
        try:
            c.execute('ALTER TABLE settings ADD COLUMN service_payments INTEGER DEFAULT 0')
            conn.commit()
        except:
            pass
        
        try:
            c.execute('ALTER TABLE settings ADD COLUMN owner_password TEXT')
            conn.commit()
        except:
            pass
        
        try:
            c.execute('ALTER TABLE settings ADD COLUMN owner_verified INTEGER DEFAULT 0')
            conn.commit()
        except:
            pass
        
        # Insert default data if tables are empty
        try:
            c.execute('SELECT COUNT(*) FROM settings')
            if c.fetchone()[0] == 0:
                c.execute('INSERT INTO settings (hotel_name, hotel_slug, approval_status) VALUES (?, ?, ?)', 
                         ('Royal Restaurant', 'royal-restaurant', 'pending'))
                conn.commit()
        except:
            pass
        
        try:
            c.execute('SELECT COUNT(*) FROM admin_users')
            if c.fetchone()[0] == 0:
                c.execute('INSERT INTO admin_users (username, password) VALUES (?, ?)', 
                         ('admin', 'admin123'))
                conn.commit()
        except:
            pass
        
        # Create default superadmin if not exists
        try:
            c.execute('SELECT COUNT(*) FROM superadmins')
            if c.fetchone()[0] == 0:
                # Create owner account - username: owner, password: owner123
                from werkzeug.security import generate_password_hash
                hashed_pw = generate_password_hash('owner123')
                c.execute('INSERT INTO superadmins (username, password) VALUES (?, ?)', 
                         ('owner', hashed_pw))
                conn.commit()
        except:
            pass
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"[WARNING] Database init error: {e}")
        return False

# Initialize DB on startup (non-blocking)
try:
    print("[*] Initializing database...")
    if init_db():
        print("[OK] Database initialized")
    else:
        print("[!] Database init had errors, will retry on first request")
except Exception as e:
    print(f"[!] Database startup error (non-fatal): {e}")

# Background tasks - run less frequently to improve performance
background_tasks_last_run = {'check_inactivity': datetime.now()}
BACKGROUND_TASK_INTERVAL = 3600  # Run every 1 hour instead of on every request

def should_run_background_tasks():
    """Check if background tasks should run (every 1 hour)"""
    now = datetime.now()
    if (now - background_tasks_last_run.get('check_inactivity', now)).total_seconds() > BACKGROUND_TASK_INTERVAL:
        background_tasks_last_run['check_inactivity'] = now
        return True
    return False


def get_db():
    """Get database connection with timeout to prevent 'database is locked' errors"""
    if USE_POSTGRES:
        conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
        return conn
    else:
        # Set timeout to 30 seconds to handle concurrent access
        conn = sqlite3.connect(DB_PATH, timeout=30)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency (only once)
        try:
            conn.execute('PRAGMA journal_mode=WAL')
            # Set busy timeout in milliseconds (30 seconds)
            conn.execute('PRAGMA busy_timeout=30000')
            # Allow concurrent reads during writes
            conn.execute('PRAGMA synchronous=NORMAL')
            # Reduce overhead by using shared cache
            conn.execute('PRAGMA query_only=FALSE')
        except:
            pass
        return conn

def get_current_hotel_id():
    """Get the current user's hotel ID (settings.id)"""
    if 'admin_email' in session:
        # Email-based login (new users)
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id FROM settings WHERE owner_email = ?', (session['admin_email'],))
        result = c.fetchone()
        conn.close()
        if result:
            return result[0]
    elif 'admin_id' in session:
        # Legacy login - admin_id is the settings.id
        return session.get('admin_id', 1)
    return 1  # Default to first hotel

def login_required(f):
    """Admin login required decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session and 'subadmin_id' not in session and 'admin_email' not in session:
            # For API requests (JSON), return JSON error
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Not authenticated'}), 401
            # For page requests, redirect to login
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_only(f):
    """Only main admin allowed"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            # For API requests (JSON), return JSON error
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Admin access required'}), 403
            # For page requests, redirect to login
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================================================
# ADMIN ROUTES
# ============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login - supports both email and username login"""
    try:
        if request.method == 'POST':
            email_or_username = request.form.get('email_or_username', '').strip()
            password = request.form.get('password', '').strip()
            login_type = request.form.get('login_type', 'email')  # 'email' or 'username'
            
            if not email_or_username or not password:
                return render_template('admin/login.html', error='invalid_credentials')
            
            conn = get_db()
            c = conn.cursor()
            
            # Try email-based login first (new system)
            if login_type == 'email' or '@' in email_or_username:
                # Find all hotels owned by this email
                c.execute('SELECT id, hotel_name, hotel_slug FROM settings WHERE owner_email = ? AND owner_password IS NOT NULL', (email_or_username,))
                hotels = c.fetchall()
                
                if hotels:
                    # Verify password matches any of the hotels (all should have same password)
                    c.execute('SELECT owner_password FROM settings WHERE owner_email = ? LIMIT 1', (email_or_username,))
                    owner = c.fetchone()
                    
                    if owner and check_password_hash(owner['owner_password'], password):
                        # If user owns multiple hotels, show selection page
                        if len(hotels) > 1:
                            session['admin_email'] = email_or_username
                            session['temp_hotels'] = [(h['id'], h['hotel_name'], h['hotel_slug']) for h in hotels]
                            conn.close()
                            return redirect(url_for('select_hotel'))
                        else:
                            # Single hotel - proceed to dashboard
                            hotel = hotels[0]
                            session['admin_id'] = hotel['id']
                            session['admin_email'] = email_or_username
                            session['hotel_name'] = hotel['hotel_name']
                            session['hotel_slug'] = hotel['hotel_slug']
                            session['is_main_admin'] = True
                            session['auth_type'] = 'email'
                            conn.close()
                            return redirect(url_for('admin_dashboard'))
            
            # Fallback to legacy username login
            c.execute('SELECT * FROM admin_users WHERE username = ? AND password = ?', (email_or_username, password))
            admin = c.fetchone()
            
            if admin:
                session['admin_id'] = admin['id']
                session['admin_username'] = admin['username']
                session['is_main_admin'] = True
                session['auth_type'] = 'legacy'
                conn.close()
                return redirect(url_for('admin_dashboard'))
            
            # Check sub-admin
            c.execute('SELECT * FROM sub_admins WHERE username = ? AND password = ? AND is_active = 1', (email_or_username, password))
            subadmin = c.fetchone()
            
            if subadmin:
                conn.close()
                session['subadmin_id'] = subadmin['id']
                session['subadmin_username'] = subadmin['username']
                session['subadmin_name'] = subadmin['name']
                session['is_main_admin'] = False
                session['auth_type'] = 'subadmin'
                return redirect(url_for('subadmin_dashboard'))
            
            # Check if account doesn't exist - look for any matching email in settings
            c.execute('SELECT owner_email FROM settings WHERE owner_email = ? LIMIT 1', (email_or_username,))
            account_exists = c.fetchone() is not None
            conn.close()
            
            if not account_exists and '@' in email_or_username:
                return render_template('admin/login.html', error='account_not_found', input_email=email_or_username)
            
            return render_template('admin/login.html', error='invalid_credentials')
        
        return render_template('admin/login.html')
    except Exception as e:
        print(f"Error in admin_login: {str(e)}")
        return render_template('admin/login.html', error='system_error'), 500

@app.route('/admin/select-hotel', methods=['GET', 'POST'])
def select_hotel():
    """Select which hotel to access (when user owns multiple hotels)"""
    if 'admin_email' not in session or 'temp_hotels' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        selected_hotel_id = request.form.get('hotel_id')
        
        # Find and verify the selected hotel
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT id, hotel_name, hotel_slug FROM settings WHERE id = ? AND owner_email = ?', 
                 (selected_hotel_id, session['admin_email']))
        hotel = c.fetchone()
        conn.close()
        
        if hotel:
            # Set session variables for selected hotel
            session['admin_id'] = hotel['id']
            session['hotel_name'] = hotel['hotel_name']
            session['hotel_slug'] = hotel['hotel_slug']
            session['is_main_admin'] = True
            # Clear temp data
            session.pop('temp_hotels', None)
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin/select_hotel.html', 
                                 hotels=session['temp_hotels'],
                                 error='Invalid hotel selection')
    
    return render_template('admin/select_hotel.html', hotels=session['temp_hotels'])

@app.route('/auth/signup', methods=['GET', 'POST'])
def signup():
    """Owner signup with email and password"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        hotel_name = request.form.get('hotel_name', '').strip()
        hotel_slug = request.form.get('hotel_slug', '').strip().lower()
        
        # Validation
        if not email or not password or not hotel_name or not hotel_slug:
            return render_template('auth/signup.html', error='All fields are required')
        
        # Validate hotel slug format
        is_valid, message = validate_hotel_slug(hotel_slug)
        if not is_valid:
            return render_template('auth/signup.html', error=f'Hotel ID: {message}', 
                                 email=email, hotel_name=hotel_name, hotel_slug=hotel_slug)
        
        if password != confirm_password:
            return render_template('auth/signup.html', error='Passwords do not match',
                                 email=email, hotel_name=hotel_name, hotel_slug=hotel_slug)
        
        if len(password) < 6:
            return render_template('auth/signup.html', error='Password must be at least 6 characters',
                                 email=email, hotel_name=hotel_name, hotel_slug=hotel_slug)
        
        # Check if hotel slug is available
        if not is_hotel_slug_available(hotel_slug):
            return render_template('auth/signup.html', error='This Hotel ID is already taken. Choose another.',
                                 email=email, hotel_name=hotel_name, hotel_slug=hotel_slug)
        
        conn = get_db()
        c = conn.cursor()
        
        # Note: Removed email uniqueness check to allow one email to manage multiple hotels
        # Email can now create multiple hotel accounts
        
        # Create new hotel record with initial status
        hashed_password = generate_password_hash(password)
        try:
            # Set trial end date to 7 days from now
            trial_end = datetime.now() + timedelta(days=7)
            c.execute('''INSERT INTO settings (hotel_name, hotel_slug, owner_email, owner_password, owner_verified, subscription_status, trial_ends_at, is_active)
                         VALUES (?, ?, ?, ?, 0, ?, ?, 1)''',
                      (hotel_name, hotel_slug, email, hashed_password, 'trial', trial_end))
            conn.commit()
            conn.close()
            
            # Generate and send verification OTP
            otp_code = generate_otp()
            save_otp(email, otp_code)
            
            # Send verification email with OTP
            email_sent = send_otp_email(email, otp_code)
            
            if email_sent:
                return render_template('auth/signup_success.html', 
                                     email=email, 
                                     hotel_slug=hotel_slug,
                                     message='Account created successfully! Verification email has been sent.',
                                     verify_url=url_for('verify_otp', email=email))
            else:
                return render_template('auth/signup_success.html', 
                                     email=email, 
                                     hotel_slug=hotel_slug,
                                     message='Account created! We were unable to send verification email. You can try password reset to verify later.')
        except Exception as e:
            conn.close()
            return render_template('auth/signup.html', error=f'Signup failed: {str(e)}',
                                 email=email, hotel_name=hotel_name, hotel_slug=hotel_slug)
    
    return render_template('auth/signup.html')

@app.route('/auth/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM settings WHERE owner_email = ?', (email,))
        user = c.fetchone()
        conn.close()
        
        if not user:
            # Don't reveal if email exists (security best practice)
            return render_template('auth/forgot_password.html', 
                                 message='If the email exists, you will receive an OTP shortly')
        
        # Generate and save OTP
        otp_code = generate_otp()
        save_otp(email, otp_code)
        
        # Send OTP via email
        email_sent = send_otp_email(email, otp_code)
        
        if email_sent:
            return render_template('auth/forgot_password.html', 
                                 message=f'✅ OTP sent to {email}. Check your email for the verification code.',
                                 redirect_url=url_for('verify_otp', email=email))
        else:
            return render_template('auth/forgot_password.html', 
                                 message='Failed to send OTP. Please check your email configuration and try again.',
                                 error=True)
    
    return render_template('auth/forgot_password.html')

@app.route('/auth/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify OTP for email verification and password reset"""
    email = request.args.get('email') or request.form.get('email')
    
    if request.method == 'POST':
        otp_code = request.form.get('otp', '').strip()
        
        if check_otp(email, otp_code):
            mark_otp_used(email)
            # Mark email as verified
            mark_email_verified(email)
            # Check if this is a password reset or signup verification
            # If password reset, go to reset password page
            # If signup verification, show success message
            conn = get_db()
            c = conn.cursor()
            c.execute('SELECT id FROM settings WHERE owner_email = ?', (email,))
            account = c.fetchone()
            conn.close()
            
            if account:
                return redirect(url_for('reset_password', email=email))
            else:
                return render_template('auth/verify_otp.html', email=email, 
                                     success='Email verified successfully! You can now login.',
                                     redirect_url=url_for('admin_login'))
        else:
            return render_template('auth/verify_otp.html', email=email, 
                                 error='Invalid or expired OTP')
    
    return render_template('auth/verify_otp.html', email=email)

@app.route('/auth/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Set new password after OTP verification"""
    email = request.args.get('email') or request.form.get('email')
    
    if request.method == 'POST':
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not password or password != confirm_password:
            return render_template('auth/reset_password.html', email=email,
                                 error='Passwords do not match or empty')
        
        if len(password) < 6:
            return render_template('auth/reset_password.html', email=email,
                                 error='Password must be at least 6 characters')
        
        conn = get_db()
        c = conn.cursor()
        
        hashed_password = generate_password_hash(password)
        c.execute('UPDATE settings SET owner_password = ? WHERE owner_email = ?',
                  (hashed_password, email))
        conn.commit()
        conn.close()
        
        return render_template('auth/reset_success.html', email=email)
    
    return render_template('auth/reset_password.html', email=email)

@app.route('/admin/logout')
def logout():
    """Logout user"""
    session.clear()
    return redirect(url_for('admin_login'))


@app.route('/health/email-config')
def email_config_status():
    """Check email configuration status (for diagnostics)"""
    return jsonify({
        'email_configured': EMAIL_CONFIGURED,
        'sender_email_set': bool(SENDER_EMAIL),
        'sender_password_set': bool(SENDER_PASSWORD),
        'sender_email_masked': f"{SENDER_EMAIL[:3]}***@{SENDER_EMAIL.split('@')[1]}" if SENDER_EMAIL and '@' in SENDER_EMAIL else 'Not set',
        'smtpserver': SMTP_SERVER,
        'smtp_port': SMTP_PORT,
        'message': 'Email is configured and ready' if EMAIL_CONFIGURED else 'Email is NOT configured - OTP emails will not be sent.'
    })


@app.route('/admin/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    """Admin dashboard"""
    conn = get_db()
    c = conn.cursor()
    hotel_id = get_current_hotel_id()
    
    # Get orders for this hotel only
    c.execute('SELECT * FROM orders WHERE hotel_id = ? ORDER BY created_at DESC LIMIT 50', (hotel_id,))
    orders_raw = c.fetchall()
    
    # Parse JSON items for each order
    orders = []
    for order in orders_raw:
        order_dict = dict(order)
        try:
            order_dict['parsed_items'] = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
        except:
            order_dict['parsed_items'] = []
        orders.append(order_dict)
    
    # Get stats for this hotel
    c.execute('SELECT COUNT(*) as total FROM orders WHERE hotel_id = ?', (hotel_id,))
    total = c.fetchone()['total']
    
    c.execute('SELECT COUNT(*) as pending FROM orders WHERE hotel_id = ? AND status = ?', (hotel_id, 'pending'))
    pending = c.fetchone()['pending']
    
    c.execute('SELECT COUNT(*) as confirmed FROM orders WHERE hotel_id = ? AND status = ?', (hotel_id, 'confirmed'))
    confirmed = c.fetchone()['confirmed']
    
    c.execute('SELECT SUM(total) as revenue FROM orders WHERE hotel_id = ? AND status IN (?, ?)', (hotel_id, 'completed', 'confirmed'))
    revenue = c.fetchone()['revenue'] or 0
    
    # Get this hotel's settings
    c.execute('SELECT hotel_name FROM settings WHERE id = ?', (hotel_id,))
    settings = c.fetchone()
    hotel_name = settings['hotel_name'] if settings else 'My Hotel'
    
    stats = {
        'total': total,
        'pending': pending,
        'confirmed': confirmed,
        'revenue': revenue
    }
    
    conn.close()
    
    return render_template('admin/dashboard.html', 
                         orders=orders,
                         stats=stats,
                         hotel_name=hotel_name)

@app.route('/admin/profile', methods=['GET'])
@admin_only
def admin_profile():
    """Admin profile management page"""
    conn = get_db()
    c = conn.cursor()
    
    # Get current hotel_id
    current_hotel_id = get_current_hotel_id()
    
    # Get hotel settings for CURRENT HOTEL ONLY
    c.execute('SELECT * FROM settings WHERE id = ?', (current_hotel_id,))
    settings = c.fetchone()
    
    # Get admin info
    c.execute('SELECT username FROM admin_users WHERE id = ?', (session.get('admin_id'),))
    admin = c.fetchone()
    
    conn.close()
    
    profile = {
        'hotel_name': settings['hotel_name'] if settings else 'Royal Restaurant',
        'hotel_address': settings['hotel_address'] if settings else '',
        'hotel_gstn': settings['hotel_gstn'] if settings else '',
        'hotel_food_license': settings['hotel_food_license'] if settings else '',
        'owner_email': settings['owner_email'] if settings else '',
        'print_name': settings['print_name'] if settings and settings['print_name'] is not None else 1,
        'print_address': settings['print_address'] if settings and settings['print_address'] is not None else 1,
        'print_gstn': settings['print_gstn'] if settings and settings['print_gstn'] is not None else 1,
        'print_license': settings['print_license'] if settings and settings['print_license'] is not None else 1
    }
    
    admin_username = admin['username'] if admin else 'Admin'
    
    return render_template('admin/profile.html', profile=profile, admin_username=admin_username)

@app.route('/api/dashboard/custom-summary', methods=['GET'])
@login_required
def dashboard_custom_summary():
    """Get business summary for custom number of days"""
    from datetime import datetime, timedelta
    
    days = request.args.get('days', type=int)
    
    if not days or days < 1 or days > 90:
        return jsonify({'success': False, 'message': 'Days must be between 1 and 90'})
    
    conn = get_db()
    c = conn.cursor()
    
    # Calculate date from days ago
    start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Get comprehensive summary
    c.execute('''SELECT 
                    COUNT(*) as total_orders,
                    SUM(total) as total_revenue,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_orders,
                    SUM(CASE WHEN status = 'declined' THEN 1 ELSE 0 END) as declined_orders,
                    SUM(CASE WHEN status = 'confirmed' THEN 1 ELSE 0 END) as confirmed_orders
                 FROM orders WHERE DATE(created_at) >= ?''', (start_date,))
    result = c.fetchone()
    
    # Auto-delete orders older than 90 days
    cutoff_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    c.execute('DELETE FROM orders WHERE DATE(created_at) < ?', (cutoff_date,))
    conn.commit()
    
    conn.close()
    
    return jsonify({
        'success': True,
        'summary': {
            'total_orders': result['total_orders'] or 0,
            'total_revenue': result['total_revenue'] or 0,
            'completed_orders': result['completed_orders'] or 0,
            'pending_orders': result['pending_orders'] or 0,
            'declined_orders': result['declined_orders'] or 0,
            'confirmed_orders': result['confirmed_orders'] or 0
        }
    })

@app.route('/admin/tables', methods=['GET', 'POST'])
@login_required
def admin_tables():
    """Redirect old tables route to new table management page"""
    return redirect(url_for('table_management_page'))

@app.route('/qr/download/<int:table_id>')
@login_required
def download_qr(table_id):
    """Download QR code for a table"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT qr_code FROM restaurant_tables WHERE id = ?', (table_id,))
    result = c.fetchone()
    conn.close()
    
    if not result or not result['qr_code']:
        return "QR code not found", 404
    
    qr_filename = result['qr_code']
    qr_path = os.path.join('static', 'qr_codes', qr_filename)
    
    if not os.path.exists(qr_path):
        return "QR code file not found", 404
    
    return send_file(qr_path, mimetype='image/png', as_attachment=True, 
                    download_name=f'table_{table_id}_qr.png')

@app.route('/admin/table/<int:table_id>/delete', methods=['POST'])
@login_required
def delete_table(table_id):
    """Delete table"""
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM restaurant_tables WHERE id = ?', (table_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Table deleted'})

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_only
def admin_settings():
    """Manage hotel settings"""
    # Get current hotel_id
    current_hotel_id = get_current_hotel_id()
    
    if request.method == 'POST':
        hotel_name = request.form.get('hotel_name', 'Royal Restaurant')
        
        conn = get_db()
        c = conn.cursor()
        # Update ONLY current hotel's settings
        c.execute('UPDATE settings SET hotel_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (hotel_name, current_hotel_id))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin_settings'))
    
    conn = get_db()
    c = conn.cursor()
    # Get ONLY current hotel's settings
    c.execute('SELECT * FROM settings WHERE id = ?', (current_hotel_id,))
    settings = c.fetchone()
    conn.close()
    
    return render_template('admin/settings.html', settings=settings)

@app.route('/api/settings/hotel-name', methods=['GET'])
def get_hotel_name():
    """Get hotel name for display"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT hotel_name FROM settings LIMIT 1')
    result = c.fetchone()
    conn.close()
    
    hotel_name = result['hotel_name'] if result else 'Royal Restaurant'
    return jsonify({'success': True, 'hotel_name': hotel_name})

@app.route('/api/settings/auto-accept', methods=['GET', 'POST'])
def auto_accept_setting():
    """Get or set auto-accept orders setting"""
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute('SELECT auto_accept_orders FROM settings LIMIT 1')
        result = c.fetchone()
        conn.close()
        auto_accept = result['auto_accept_orders'] if result else 0
        return jsonify({'success': True, 'auto_accept': auto_accept})
    
    elif request.method == 'POST':
        data = request.get_json()
        auto_accept = data.get('auto_accept', 0)
        c.execute('UPDATE settings SET auto_accept_orders = ?, updated_at = CURRENT_TIMESTAMP', (auto_accept,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'auto_accept': auto_accept})

@app.route('/api/settings/profile', methods=['GET', 'POST'])
@admin_only
def profile_setting():
    """Get or update restaurant profile"""
    conn = get_db()
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute('SELECT * FROM settings LIMIT 1')
        result = c.fetchone()
        conn.close()
        
        if result:
            return jsonify({
                'success': True,
                'profile': {
                    'hotel_name': result['hotel_name'] or 'Royal Restaurant',
                    'hotel_address': result['hotel_address'] or '',
                    'hotel_email': result['owner_email'] or '',
                    'hotel_gstn': result['hotel_gstn'] or '',
                    'hotel_food_license': result['hotel_food_license'] or '',
                    'print_name': result['print_name'] if result['print_name'] is not None else 1,
                    'print_address': result['print_address'] if result['print_address'] is not None else 1,
                    'print_gstn': result['print_gstn'] if result['print_gstn'] is not None else 1,
                    'print_license': result['print_license'] if result['print_license'] is not None else 1
                }
            })
        return jsonify({'success': False, 'message': 'Profile not found'})
    
    elif request.method == 'POST':
        data = request.get_json()
        c.execute('''UPDATE settings SET 
                     hotel_name = ?,
                     hotel_address = ?,
                     owner_email = ?,
                     hotel_gstn = ?,
                     hotel_food_license = ?,
                     print_name = ?,
                     print_address = ?,
                     print_gstn = ?,
                     print_license = ?,
                     updated_at = CURRENT_TIMESTAMP''',
                 (data.get('hotel_name', 'Royal Restaurant'),
                  data.get('hotel_address', ''),
                  data.get('hotel_email', ''),
                  data.get('hotel_gstn', ''),
                  data.get('hotel_food_license', ''),
                  int(data.get('print_name', 1)),
                  int(data.get('print_address', 1)),
                  int(data.get('print_gstn', 1)),
                  int(data.get('print_license', 1))))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Profile updated successfully'})

@app.route('/admin/menu', methods=['GET', 'POST'])
@login_required
def admin_menu():
    """Manage menu items"""
    hotel_id = get_current_hotel_id()
    
    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        price = request.form.get('price', type=float)
        description = request.form.get('description', '')
        image_path = None
        
        # Handle image upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                # Create static/menu_images directory if it doesn't exist
                os.makedirs('static/menu_images', exist_ok=True)
                filename = f"item_{int(datetime.now().timestamp())}_{file.filename}"
                file.save(os.path.join('static/menu_images', filename))
                image_path = f"/static/menu_images/{filename}"
        
        conn = get_db()
        c = conn.cursor()
        c.execute('INSERT INTO menu_items (hotel_id, name, category, price, description, image_path) VALUES (?, ?, ?, ?, ?, ?)',
                 (hotel_id, name, category, price, description, image_path))
        conn.commit()
        conn.close()
        
        return redirect(url_for('admin_menu'))
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM menu_items WHERE hotel_id = ? ORDER BY category, name', (hotel_id,))
    menu_items = c.fetchall()
    
    # Get this hotel's settings
    c.execute('SELECT hotel_name FROM settings WHERE id = ?', (hotel_id,))
    settings = c.fetchone()
    hotel_name = settings['hotel_name'] if settings else 'My Hotel'
    conn.close()
    
    return render_template('admin/menu.html', menu_items=menu_items, hotel_name=hotel_name)

@app.route('/admin/menu/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_menu_item(item_id):
    """Delete menu item"""
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM menu_items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_menu'))

@app.route('/admin/orders', methods=['GET'])
@login_required
def admin_orders():
    """View all orders"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM orders ORDER BY created_at DESC')
    orders_raw = c.fetchall()
    
    # Get sub-admins for assignment dropdown
    c.execute('SELECT id, name, username FROM sub_admins WHERE is_active = 1')
    subadmins = [dict(sa) for sa in c.fetchall()]
    
    conn.close()
    
    # Parse JSON items for each order
    orders = []
    for order in orders_raw:
        order_dict = dict(order)
        try:
            order_dict['parsed_items'] = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
        except:
            order_dict['parsed_items'] = []
        orders.append(order_dict)
    
    return render_template('admin/orders.html', orders=orders, subadmins=subadmins)

@app.route('/admin/order/<int:order_id>/view', methods=['GET'])
@login_required
def view_order(order_id):
    """View order details"""
    conn = get_db()
    c = conn.cursor()
    
    # Get order
    c.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
    order = c.fetchone()
    
    # Get restaurant profile settings
    c.execute('SELECT * FROM settings LIMIT 1')
    settings = c.fetchone()
    
    conn.close()
    
    if not order:
        return "Order not found", 404
    
    order_dict = dict(order)
    try:
        order_dict['parsed_items'] = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
    except:
        order_dict['parsed_items'] = []
    
    # Build profile dict with settings
    profile = {}
    if settings:
        profile = {
            'hotel_name': settings['hotel_name'] or 'Royal Restaurant',
            'hotel_address': settings['hotel_address'] or '',
            'hotel_email': settings['owner_email'] or '',
            'hotel_gstn': settings['hotel_gstn'] or '',
            'hotel_food_license': settings['hotel_food_license'] or '',
            'print_name': settings['print_name'] if settings['print_name'] is not None else 1,
            'print_address': settings['print_address'] if settings['print_address'] is not None else 1,
            'print_gstn': settings['print_gstn'] if settings['print_gstn'] is not None else 1,
            'print_license': settings['print_license'] if settings['print_license'] is not None else 1
        }
    
    return render_template('admin/order_details.html', order=order_dict, profile=profile)

@app.route('/admin/order/<int:order_id>/accept', methods=['POST'])
@login_required
def accept_order(order_id):
    """Accept order"""
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE orders SET status = ? WHERE id = ?', ('confirmed', order_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Order accepted'})

@app.route('/admin/order/<int:order_id>/decline', methods=['POST'])
@login_required
def decline_order(order_id):
    """Decline order"""
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE orders SET status = ? WHERE id = ?', ('declined', order_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Order declined'})

@app.route('/admin/order/<int:order_id>/complete', methods=['POST'])
@login_required
def complete_order(order_id):
    """Mark order as completed"""
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE orders SET status = ? WHERE id = ?', ('completed', order_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Order completed'})

@app.route('/kitchen/order/<int:order_id>/ready', methods=['POST'])
@login_required
def mark_order_ready(order_id):
    """Mark order as ready (kitchen finished cooking)"""
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE orders SET status = ? WHERE id = ?', ('ready', order_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Order marked as ready'})

@app.route('/admin/logout')
def admin_logout():
    """Logout"""
    session.clear()
    return redirect(url_for('admin_login'))


@app.route('/kitchen')
@login_required
def kitchen_main():
    """Main Kitchen Display System - shows all confirmed orders"""
    return render_template('admin/kitchen_main.html')

# ============================================================================
# SUB-ADMIN MANAGEMENT ROUTES (Admin Only)
# ============================================================================

@app.route('/admin/subadmins', methods=['GET', 'POST'])
@admin_only
def manage_subadmins():
    """Manage sub-admins"""
    conn = get_db()
    c = conn.cursor()
    error_message = None
    success_message = None
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        name = request.form.get('name', '').strip()
        assigned_tables = request.form.getlist('tables')
        assigned_categories = request.form.getlist('categories')
        
        # Validate form fields
        if not username or not password or not name:
            error_message = "All fields (username, password, name) are required"
        else:
            try:
                c.execute('INSERT INTO sub_admins (username, password, name, assigned_tables, assigned_categories) VALUES (?, ?, ?, ?, ?)',
                         (username, password, name, json.dumps(assigned_tables), json.dumps(assigned_categories)))
                conn.commit()
                conn.close()
                # Redirect to clear the form and show success message
                session['success_message'] = f"Sub-admin '{name}' created successfully!"
                return redirect(url_for('manage_subadmins'))
            except sqlite3.IntegrityError as e:
                error_message = f"Username '{username}' already exists"
    
    # Get all sub-admins
    c.execute('SELECT * FROM sub_admins ORDER BY created_at DESC')
    subadmins = []
    for sa in c.fetchall():
        sa_dict = dict(sa)
        try:
            sa_dict['tables_list'] = json.loads(sa_dict.get('assigned_tables', '[]')) or []
        except:
            sa_dict['tables_list'] = []
        try:
            sa_dict['categories_list'] = json.loads(sa_dict.get('assigned_categories', '[]')) or []
        except:
            sa_dict['categories_list'] = []
        subadmins.append(sa_dict)
    
    # Get tables and categories for assignment
    c.execute('SELECT * FROM restaurant_tables ORDER BY table_number')
    tables = [dict(t) for t in c.fetchall()]
    
    c.execute('SELECT DISTINCT category FROM menu_items')
    categories = [row['category'] for row in c.fetchall()]
    
    conn.close()
    
    # Check if there's a success message in session
    if 'success_message' in session:
        success_message = session.pop('success_message')
    
    return render_template('admin/subadmins.html', subadmins=subadmins, tables=tables, categories=categories, 
                         error_message=error_message, success_message=success_message)

@app.route('/admin/subadmin/<int:subadmin_id>/delete', methods=['POST'])
@admin_only
def delete_subadmin(subadmin_id):
    """Delete sub-admin"""
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM sub_admins WHERE id = ?', (subadmin_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Sub-admin deleted'})

@app.route('/admin/subadmin/<int:subadmin_id>/toggle', methods=['POST'])
@admin_only
def toggle_subadmin(subadmin_id):
    """Toggle sub-admin active status"""
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE sub_admins SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?', (subadmin_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Status updated'})

@app.route('/admin/order/<int:order_id>/assign', methods=['POST'])
@admin_only
def assign_order(order_id):
    """Assign order to sub-admin"""
    data = request.get_json()
    subadmin_id = data.get('subadmin_id')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('UPDATE orders SET assigned_to = ? WHERE id = ?', (subadmin_id, order_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Order assigned'})

# ============================================================================
# SUB-ADMIN DASHBOARD ROUTES
# ============================================================================

@app.route('/subadmin/dashboard')
@login_required
def subadmin_dashboard():
    """Sub-admin dashboard - shows only assigned orders"""
    if 'subadmin_id' not in session:
        return redirect(url_for('admin_login'))
    
    subadmin_id = session['subadmin_id']
    
    conn = get_db()
    c = conn.cursor()
    
    # Get sub-admin info
    c.execute('SELECT * FROM sub_admins WHERE id = ?', (subadmin_id,))
    subadmin = c.fetchone()
    
    if not subadmin:
        session.clear()
        return redirect(url_for('admin_login'))
    
    # Parse assigned tables and categories
    try:
        assigned_tables = json.loads(subadmin['assigned_tables'] or '[]')
    except:
        assigned_tables = []
    
    try:
        assigned_categories = json.loads(subadmin['assigned_categories'] or '[]')
    except:
        assigned_categories = []
    
    # Get orders - either assigned directly OR matching table/category
    orders = []
    
    # First get directly assigned orders
    c.execute('SELECT * FROM orders WHERE assigned_to = ? ORDER BY created_at DESC', (subadmin_id,))
    for order in c.fetchall():
        order_dict = dict(order)
        order_dict['assigned_by_admin'] = True  # Mark as directly assigned
        try:
            order_dict['parsed_items'] = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
        except:
            order_dict['parsed_items'] = []
        orders.append(order_dict)
    
    # Also get orders from assigned tables (not already assigned to someone else)
    if assigned_tables:
        table_ids = [int(t) for t in assigned_tables if str(t).isdigit()]
        if table_ids:
            placeholders = ','.join(['?' for _ in table_ids])
            c.execute(f'SELECT * FROM orders WHERE table_id IN ({placeholders}) AND assigned_to IS NULL ORDER BY created_at DESC', 
                     tuple(table_ids))
            for order in c.fetchall():
                if order['id'] not in [o['id'] for o in orders]:
                    order_dict = dict(order)
                    order_dict['assigned_by_admin'] = False  # From assigned table
                    try:
                        order_dict['parsed_items'] = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
                    except:
                        order_dict['parsed_items'] = []
                    orders.append(order_dict)
    
    # Stats
    total_orders = len(orders)
    pending = len([o for o in orders if o['status'] == 'pending'])
    confirmed = len([o for o in orders if o['status'] == 'confirmed'])
    completed = len([o for o in orders if o['status'] == 'completed'])
    
    conn.close()
    
    return render_template('admin/subadmin_dashboard.html', 
                          orders=orders, 
                          subadmin=dict(subadmin),
                          stats={'total': total_orders, 'pending': pending, 'confirmed': confirmed, 'completed': completed})

@app.route('/subadmin/orders')
@login_required
def subadmin_orders():
    """Sub-admin orders page"""
    if 'subadmin_id' not in session:
        return redirect(url_for('admin_login'))
    
    subadmin_id = session['subadmin_id']
    
    conn = get_db()
    c = conn.cursor()
    
    # Get sub-admin info
    c.execute('SELECT * FROM sub_admins WHERE id = ?', (subadmin_id,))
    subadmin = c.fetchone()
    
    if not subadmin:
        session.clear()
        return redirect(url_for('admin_login'))
    
    # Parse assigned tables
    try:
        assigned_tables = json.loads(subadmin['assigned_tables'] or '[]')
    except:
        assigned_tables = []
    
    # Get orders
    orders = []
    
    # Get directly assigned orders by admin
    c.execute('SELECT * FROM orders WHERE assigned_to = ? ORDER BY created_at DESC', (subadmin_id,))
    for order in c.fetchall():
        order_dict = dict(order)
        order_dict['assigned_by_admin'] = True
        try:
            order_dict['parsed_items'] = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
        except:
            order_dict['parsed_items'] = []
        orders.append(order_dict)
    
    # Get orders from assigned tables (not assigned to others)
    if assigned_tables:
        table_ids = [int(t) for t in assigned_tables if str(t).isdigit()]
        if table_ids:
            placeholders = ','.join(['?' for _ in table_ids])
            c.execute(f'SELECT * FROM orders WHERE table_id IN ({placeholders}) AND assigned_to IS NULL ORDER BY created_at DESC', 
                     tuple(table_ids))
            for order in c.fetchall():
                if order['id'] not in [o['id'] for o in orders]:
                    order_dict = dict(order)
                    order_dict['assigned_by_admin'] = False
                    try:
                        order_dict['parsed_items'] = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
                    except:
                        order_dict['parsed_items'] = []
                    orders.append(order_dict)
    
    conn.close()
    
    return render_template('admin/subadmin_orders.html', orders=orders)

@app.route('/subadmin/kitchen')
@login_required
def kitchen_display():
    """Kitchen Display System for sub-admin"""
    if 'subadmin_id' not in session:
        return redirect(url_for('admin_login'))
    
    return render_template('admin/kitchen_display.html')

# ============================================================================
# CUSTOMER ROUTES
# ============================================================================

@app.route('/health')
def health_check():
    """Health check endpoint for Railway deployment"""
    return jsonify({'status': 'healthy', 'message': 'Hotel app is running'}), 200

@app.route('/')
def index():
    """Home page"""
    return redirect(url_for('admin_login'))

@app.route('/qr/<qr_code>')
def scan_qr(qr_code):
    """Scan QR code - redirect to order page"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM restaurant_tables WHERE qr_code = ?', (qr_code,))
    table = c.fetchone()
    conn.close()
    
    if table:
        return redirect(url_for('order_page', table_id=table['id']))
    else:
        return "Invalid QR Code", 404

@app.route('/order/<int:table_id>')
def order_page(table_id):
    """Customer ordering page"""
    conn = get_db()
    c = conn.cursor()
    
    # Get table info
    c.execute('SELECT * FROM restaurant_tables WHERE id = ?', (table_id,))
    table = c.fetchone()
    
    if not table:
        return "Table not found", 404
    
    # Get hotel_id from table
    hotel_id = table['hotel_id'] if table else 1
    
    # Get menu items for THIS HOTEL ONLY
    c.execute('SELECT * FROM menu_items WHERE hotel_id = ? AND is_available = 1 ORDER BY category, name', (hotel_id,))
    menu_items = c.fetchall()
    
    # Get hotel settings for THIS HOTEL
    c.execute('SELECT hotel_name FROM settings WHERE id = ?', (hotel_id,))
    settings = c.fetchone()
    hotel_name = settings['hotel_name'] if settings else 'Royal Restaurant'
    
    conn.close()
    
    return render_template('customer/order.html', table_id=table_id, menu_items=menu_items, hotel_name=hotel_name)

# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/api/menu', methods=['GET'])
def api_get_menu():
    """Get menu items for the hotel"""
    table_id = request.args.get('table_id', type=int)
    
    conn = get_db()
    c = conn.cursor()
    
    # Get hotel_id from table
    c.execute('SELECT hotel_id FROM restaurant_tables WHERE id = ?', (table_id,))
    table_row = c.fetchone()
    hotel_id = table_row['hotel_id'] if table_row else 1
    
    # Get menu items for this hotel only
    c.execute('SELECT * FROM menu_items WHERE hotel_id = ? AND is_available = 1 ORDER BY category, name', (hotel_id,))
    items = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify({'success': True, 'items': items})

@app.route('/api/get-menu', methods=['GET'])
def api_get_menu_by_hotel():
    """Get menu items by hotel slug or table number"""
    hotel_slug = request.args.get('hotel')
    table_number = request.args.get('table', type=int)
    
    conn = get_db()
    c = conn.cursor()
    
    hotel_id = None
    
    # Try to get hotel_id from slug first
    if hotel_slug:
        c.execute('SELECT id FROM settings WHERE hotel_slug = ?', (hotel_slug,))
        result = c.fetchone()
        if result:
            hotel_id = result['id']
    
    # If no hotel found by slug, try to get from table
    if not hotel_id and table_number:
        c.execute('SELECT hotel_id FROM restaurant_tables WHERE table_number = ?', (table_number,))
        result = c.fetchone()
        if result:
            hotel_id = result['hotel_id']
    
    # If still no hotel_id, try to get the first hotel
    if not hotel_id:
        c.execute('SELECT id FROM settings LIMIT 1')
        result = c.fetchone()
        if result:
            hotel_id = result['id']
    
    if not hotel_id:
        conn.close()
        return jsonify({'success': False, 'error': 'No store found', 'menu': []})
    
    # Get menu items for this hotel
    c.execute('SELECT * FROM menu_items WHERE hotel_id = ? ORDER BY category, name', (hotel_id,))
    items = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify({'success': True, 'menu': items, 'hotel_id': hotel_id})

@app.route('/api/order/place', methods=['POST'])
def place_order():
    """Place order"""
    data = request.get_json()
    table_id = data.get('table_id')
    items = data.get('items', [])
    subtotal = data.get('subtotal', 0)
    
    # Get table and hotel information
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT table_number, hotel_id FROM restaurant_tables WHERE id = ?', (table_id,))
    table_row = c.fetchone()
    table_number = table_row['table_number'] if table_row else 'Unknown'
    hotel_id = table_row['hotel_id'] if table_row else 1
    
    # Calculate
    gst_rate = 18
    tax = (subtotal * gst_rate) / 100
    service_charge = (subtotal * 5) / 100
    total = subtotal + tax + service_charge
    
    # Check if table is assigned to any sub-admin
    assigned_subadmin_id = None
    c.execute('SELECT id, assigned_tables FROM sub_admins WHERE is_active = 1')
    for subadmin in c.fetchall():
        try:
            assigned_tables = json.loads(subadmin['assigned_tables'] or '[]')
            if str(table_id) in assigned_tables or table_id in assigned_tables:
                assigned_subadmin_id = subadmin['id']
                break
        except:
            pass
    
    # Check auto-accept setting for this hotel
    c.execute('SELECT auto_accept_orders FROM settings WHERE id = ?', (hotel_id,))
    settings = c.fetchone()
    auto_accept = int(settings['auto_accept_orders']) if settings and settings['auto_accept_orders'] else 0
    
    # Set order status based on auto-accept setting
    order_status = 'confirmed' if (auto_accept == 1) else 'pending'
    
    # Insert order with hotel_id
    c.execute('INSERT INTO orders (hotel_id, table_id, table_number, items, subtotal, tax, service_charge, total, status, assigned_to) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
             (hotel_id, table_id, table_number, json.dumps(items), subtotal, tax, service_charge, total, order_status, assigned_subadmin_id))
    conn.commit()
    order_id = c.lastrowid
    conn.close()
    
    return jsonify({
        'success': True,
        'order_id': order_id,
        'message': 'Order placed successfully',
        'bill': {
            'subtotal': round(subtotal, 2),
            'tax': round(tax, 2),
            'service_charge': round(service_charge, 2),
            'total': round(total, 2)
        }
    })

@app.route('/api/order/<int:order_id>/update', methods=['POST'])
def update_order(order_id):
    """Update existing order items and total"""
    data = request.get_json()
    items = data.get('items', [])
    subtotal = data.get('subtotal', 0)
    tax = data.get('tax', 0)
    service_charge = data.get('service_charge', 0)
    total = data.get('total', 0)
    
    conn = get_db()
    c = conn.cursor()
    
    # Get current user's hotel_id
    current_hotel_id = get_current_hotel_id()
    
    # Check if order exists, is pending, AND belongs to current hotel
    c.execute('SELECT status, hotel_id FROM orders WHERE id = ?', (order_id,))
    order = c.fetchone()
    
    if not order:
        conn.close()
        return jsonify({'success': False, 'message': 'Order not found'}), 404
    
    # Verify order belongs to current hotel
    if order['hotel_id'] != current_hotel_id:
        conn.close()
        return jsonify({'success': False, 'message': 'Unauthorized - order belongs to different hotel'}), 403
    
    if order['status'] != 'pending':
        conn.close()
        return jsonify({'success': False, 'message': 'Order cannot be updated - already processed'}), 400
    
    # Update order
    c.execute('UPDATE orders SET items = ?, subtotal = ?, tax = ?, service_charge = ?, total = ? WHERE id = ? AND hotel_id = ?',
             (json.dumps(items), subtotal, tax, service_charge, total, order_id, current_hotel_id))
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': 'Order updated successfully',
        'order_id': order_id
    })

@app.route('/api/orders/<int:table_id>', methods=['GET'])
def get_table_orders(table_id):
    """Get orders for table"""
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE table_id = ? ORDER BY created_at DESC', (table_id,))
    orders = [dict(row) for row in c.fetchall()]
    conn.close()
    
    return jsonify({'success': True, 'orders': orders})

@app.route('/api/subadmin/orders', methods=['GET'])
@login_required
def api_subadmin_orders():
    """Get orders for sub-admin (for KDS)"""
    if 'subadmin_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    subadmin_id = session['subadmin_id']
    
    conn = get_db()
    c = conn.cursor()
    
    # Get sub-admin info
    c.execute('SELECT * FROM sub_admins WHERE id = ?', (subadmin_id,))
    subadmin = c.fetchone()
    
    if not subadmin:
        return jsonify({'success': False, 'message': 'Sub-admin not found'}), 404
    
    # Parse assigned tables
    try:
        assigned_tables = json.loads(subadmin['assigned_tables'] or '[]')
    except:
        assigned_tables = []
    
    orders = []
    
    # Get directly assigned orders
    c.execute('SELECT * FROM orders WHERE assigned_to = ? ORDER BY status, created_at DESC', (subadmin_id,))
    for order in c.fetchall():
        order_dict = dict(order)
        try:
            order_dict['parsed_items'] = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
        except:
            order_dict['parsed_items'] = []
        orders.append(order_dict)
    
    # Get orders from assigned tables (not assigned to others)
    if assigned_tables:
        table_ids = [int(t) for t in assigned_tables if str(t).isdigit()]
        if table_ids:
            placeholders = ','.join(['?' for _ in table_ids])
            c.execute(f'SELECT * FROM orders WHERE table_id IN ({placeholders}) AND assigned_to IS NULL ORDER BY status, created_at DESC', 
                     tuple(table_ids))
            for order in c.fetchall():
                if order['id'] not in [o['id'] for o in orders]:
                    order_dict = dict(order)
                    try:
                        order_dict['parsed_items'] = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
                    except:
                        order_dict['parsed_items'] = []
                    orders.append(order_dict)
    
    conn.close()
    
    return jsonify({'success': True, 'orders': orders})

@app.route('/api/orders/all', methods=['GET'])
@admin_only
def api_all_orders():
    """Get all orders for admin dashboard (for auto-refresh)"""
    conn = get_db()
    c = conn.cursor()
    hotel_id = get_current_hotel_id()
    
    # Get orders for this hotel only
    c.execute('''SELECT o.*, rt.table_number 
                 FROM orders o 
                 LEFT JOIN restaurant_tables rt ON o.table_id = rt.id 
                 WHERE o.hotel_id = ?
                 ORDER BY o.created_at DESC''', (hotel_id,))
    
    orders = []
    for row in c.fetchall():
        order_dict = dict(row)
        
        # Parse items and format for display
        try:
            items = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
            items_display = '<br>'.join([f"{item.get('name', 'Unknown')} x{item.get('quantity', 1)}" for item in items])
        except:
            items_display = 'Items error'
        
        order_dict['items_display'] = items_display
        order_dict['table_number'] = order_dict.get('table_number') or order_dict.get('table_id', '?')
        orders.append(order_dict)
    
    conn.close()
    
    return jsonify({'success': True, 'orders': orders})

@app.route('/api/kitchen/orders', methods=['GET'])
@admin_only
def api_kitchen_orders():
    """Get all confirmed orders for main kitchen display"""
    conn = get_db()
    c = conn.cursor()
    hotel_id = get_current_hotel_id()
    
    # Get confirmed, ready, and completed orders for this hotel only
    c.execute('''SELECT o.*, rt.table_number FROM orders o
                 LEFT JOIN restaurant_tables rt ON o.table_id = rt.id
                 WHERE o.hotel_id = ? AND o.status IN ('confirmed', 'ready', 'completed')
                 ORDER BY CASE WHEN o.status = 'confirmed' THEN 0 WHEN o.status = 'ready' THEN 1 ELSE 2 END, o.created_at DESC''', (hotel_id,))
    
    orders = []
    for order in c.fetchall():
        order_dict = dict(order)
        try:
            order_dict['parsed_items'] = json.loads(order_dict.get('items', '[]')) if order_dict.get('items') else []
        except:
            order_dict['parsed_items'] = []
        orders.append(order_dict)
    
    conn.close()
    
    return jsonify({'success': True, 'orders': orders})

# ============================================================================
# SUBSCRIPTION & INFORMATION PAGES ROUTES
# ============================================================================

@app.route('/subscription')
def subscription():
    """Subscription plans page"""
    hotel_id = session.get('hotel_id')
    subscription_status = None
    has_active_subscription = False
    
    if hotel_id:
        subscription_status = get_subscription_status(hotel_id)
        has_active_subscription = is_subscription_active(hotel_id)
        
        print(f"[DEBUG] Hotel {hotel_id} subscription status: {subscription_status}")
        print(f"[DEBUG] Active: {has_active_subscription}")
    
    return render_template('admin/subscription.html', 
                         current_status=subscription_status,
                         has_active_subscription=has_active_subscription,
                         plans=SUBSCRIPTION_PLANS,
                         razorpay_key_id=RAZORPAY_KEY_ID)

@app.route('/about')
def about():
    """About Us page"""
    return render_template('about.html')

@app.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')

@app.route('/disclaimer')
def disclaimer():
    """Disclaimer page"""
    return render_template('disclaimer.html')

@app.route('/data-handling')
def data_handling():
    """Data Handling Policy page"""
    return render_template('data_handling.html')

@app.route('/faq')
def faq():
    """FAQs page"""
    return render_template('faq.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact Us page and form handler"""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically save to database or send email
        # For now, we'll just return success
        return jsonify({'success': True, 'message': 'Message received! We will contact you soon.'})
    
    return render_template('contact.html')

@app.route('/api/create-order', methods=['POST'])
def api_create_order():
    """Create Razorpay order for subscription"""
    if 'hotel_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    hotel_id = session['hotel_id']
    plan = request.json.get('plan')
    
    if plan not in SUBSCRIPTION_PLANS:
        return jsonify({'success': False, 'message': 'Invalid plan'}), 400
    
    try:
        # Check if hotel already has an active subscription
        has_active_sub, existing_plan = check_existing_subscription(hotel_id)
        if has_active_sub:
            print(f"[WARNING] Hotel {hotel_id} already has active {existing_plan} subscription")
            return jsonify({
                'success': False, 
                'message': f'Your hotel already has an active {existing_plan} subscription (Expires {datetime.now().strftime("%Y-%m-%d")}). You cannot subscribe again until it expires. If you want to upgrade, please contact support.',
                'existing_subscription': True,
                'existing_plan': existing_plan
            }), 400
        
        print(f"[OK] Creating Razorpay order for hotel {hotel_id} - {plan} plan")
        order_response, error = create_razorpay_order(hotel_id, session.get('hotel_name', 'Hotel'), plan)
        
        if order_response and order_response.get('id'):
            print(f"[OK] Order created: {order_response.get('id')}")
            return jsonify({
                'success': True,
                'order_id': order_response.get('id'),
                'amount': order_response.get('amount'),
                'currency': order_response.get('currency'),
                'key_id': RAZORPAY_KEY_ID
            }), 200
        else:
            print(f"[ERROR] Failed to create order: {error}")
            return jsonify({'success': False, 'message': f'Failed to create order: {error}'}), 500
    
    except Exception as e:
        print(f"[ERROR] Error creating order: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error creating order: {str(e)}'}), 500

@app.route('/api/verify-payment', methods=['POST'])
def api_verify_payment():
    """Verify Razorpay payment and activate subscription"""
    if 'hotel_id' not in session:
        print("[ERROR] No hotel_id in session for payment verification")
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    hotel_id = session['hotel_id']
    
    try:
        data = request.json
        order_id = data.get('order_id')
        payment_id = data.get('payment_id')
        signature = data.get('signature')
        plan = data.get('plan')
        
        # Validate inputs
        if not all([order_id, payment_id, signature, plan]):
            print(f"[ERROR] Missing payment data for hotel {hotel_id}")
            return jsonify({'success': False, 'message': 'Missing payment information'}), 400
        
        if plan not in SUBSCRIPTION_PLANS:
            print(f"[ERROR] Invalid plan '{plan}' requested by hotel {hotel_id}")
            return jsonify({'success': False, 'message': 'Invalid subscription plan'}), 400
        
        # Check if hotel already has an active subscription
        has_active_sub, existing_plan = check_existing_subscription(hotel_id)
        if has_active_sub:
            print(f"[WARNING] Hotel {hotel_id} already has active {existing_plan} subscription")
            return jsonify({
                'success': False, 
                'message': f'Your hotel already has an active {existing_plan} subscription. Please wait for it to expire or contact support to upgrade.',
                'existing_plan': existing_plan
            }), 400
        
        # Verify payment with Razorpay
        is_verified, verification_message = verify_razorpay_payment(order_id, payment_id, signature, hotel_id)
        
        if is_verified:
            print(f"[OK] Payment verified for hotel {hotel_id} - activating {plan} subscription")
            
            # Activate subscription
            success = activate_subscription(hotel_id, plan, payment_id)
            
            if success:
                print(f"[OK] Subscription activated for hotel {hotel_id}")
                return jsonify({
                    'success': True,
                    'message': f'Payment successful! Your {plan.capitalize()} subscription is now active! 🎉',
                    'plan': plan,
                    'order_id': order_id,
                    'payment_id': payment_id
                }), 200
            else:
                print(f"[ERROR] Failed to activate subscription for hotel {hotel_id}")
                return jsonify({
                    'success': False, 
                    'message': 'Payment verified but failed to activate subscription. Please contact support.',
                    'order_id': order_id,
                    'payment_id': payment_id
                }), 500
        else:
            print(f"[ERROR] Payment verification failed for hotel {hotel_id}: {verification_message}")
            return jsonify({
                'success': False,
                'message': f'Payment verification failed: {verification_message}',
                'order_id': order_id
            }), 400
    
    except Exception as e:
        print(f"[ERROR] Error verifying payment: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error processing payment: {str(e)}'}), 500

@app.route('/api/subscription-status', methods=['GET'])
def api_subscription_status():
    """Get current subscription status for the hotel"""
    if 'hotel_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    try:
        hotel_id = session['hotel_id']
        status = get_subscription_status(hotel_id)
        is_active = is_subscription_active(hotel_id)
        
        if not status:
            return jsonify({
                'success': True,
                'has_subscription': False,
                'message': 'No subscription found'
            }), 200
        
        response_data = {
            'success': True,
            'has_subscription': True,
            'is_active': is_active,
            'current_status': status['status'],
            'plan': status['plan'],
            'last_payment_date': status['last_payment_date'],
            'active_until': status['subscription_end_date'] if status['status'] == 'active' else status['trial_ends_at']
        }
        
        # Add days remaining
        if status['subscription_end_date']:
            end_date = datetime.fromisoformat(status['subscription_end_date'])
            days_remaining = (end_date - datetime.now()).days
            response_data['days_remaining'] = max(0, days_remaining)
        
        return jsonify(response_data), 200
    
    except Exception as e:
        print(f"[ERROR] Error getting subscription status: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

# ============================================================================
# DATA RETENTION & MANAGEMENT ROUTES
# ============================================================================

@app.route('/admin/database-stats', methods=['GET'])
@admin_only
def database_stats():
    """Admin page to view database statistics and data retention info"""
    stats = get_database_stats()
    return render_template('admin/database_stats.html', stats=stats)

@app.route('/api/database-stats', methods=['GET'])
@admin_only
def api_database_stats():
    """API endpoint to get database statistics"""
    stats = get_database_stats()
    return jsonify(stats)

@app.route('/api/cleanup-old-data', methods=['POST'])
@admin_only
def api_cleanup_old_data():
    """
    Manual trigger to delete data older than 90 days.
    Normally runs automatically at 2:00 AM daily.
    """
    try:
        # Optional: allow custom retention period from request
        data = request.get_json() or {}
        days = data.get('days', 90)
        
        # Validate input
        if not isinstance(days, int) or days < 7 or days > 365:
            return jsonify({
                'success': False,
                'message': 'Days must be between 7 and 365'
            }), 400
        
        result = delete_old_orders(days_to_retain=days)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'message': f"Data older than {days} days deleted successfully",
                'details': result
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Cleanup failed',
                'error': result.get('error')
            }), 500
            
    except Exception as e:
        print(f"[ERROR] Error in manual cleanup: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error during cleanup',
            'error': str(e)
        }), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors - return JSON for API requests, HTML for pages"""
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors gracefully"""
    import traceback
    tb = traceback.format_exc()
    print(f"[ERROR 500] Internal Server Error: {str(error)}")
    print(f"[TRACEBACK]\n{tb}")
    
    # For API requests, return JSON error
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal Server Error', 'message': str(error)}), 500
    
    # For page requests, return JSON (since we don't have error template)
    return jsonify({'error': 'Internal Server Error', 'message': str(error), 'details': tb}), 500

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("REAL-TIME RESTAURANT ORDERING SYSTEM")
    print("="*70)
    print("\nFeatures:")
    print("   [+] Admin Login & Dashboard")
    print("   [+] Table & QR Management")
    print("   [+] Menu Management (Add/Delete items)")
    print("   [+] Real-time Order Processing")
    print("   [+] Order Accept/Decline/Complete")
    print("   [+] QR Code Scanning")
    print("   [+] SQLite Database (persistent)")
    print("   [+] Multi-tenant Data Isolation")
    print("   [+] 24-Hour Automated Reports")
    print("\nAccess Points:")
    print("   Admin Panel:  http://localhost:5000/admin/login")
    print("   Order Page:   http://localhost:5000/order/1  (Table 1)")
    print("\nAdmin Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\nSteps:")
    print("   1. Login as admin: http://localhost:5000/admin/login")
    print("   2. Create tables and add QR codes")
    print("   3. Add menu items")
    print("   4. Scan QR from table and order")
    print("   5. Admin approves/manages orders")
    print("\nServer running on http://localhost:5000")
    print("="*70 + "\n")
    
    # Start 24-hour report scheduler
    try:
        start_daily_report_scheduler()
        print("[OK] Daily report scheduler started (runs every 24 hours)")
    except Exception as e:
        print(f"[WARNING] Failed to start daily report scheduler: {e}")
    
    # Start daily data deletion scheduler (90-day retention)
    try:
        schedule_daily_deletion()
        print("[OK] 90-day data retention scheduler started")
    except Exception as e:
        print(f"[WARNING] Failed to start daily deletion scheduler: {e}")
    
    # Add diagnostic endpoint
    @app.route('/api/system-diagnostics', methods=['GET'])
    def system_diagnostics():
        """
        Diagnostic endpoint to check database persistence status.
        Accessible via: /api/system-diagnostics
        
        Returns:
        - database_path: Where the database file is stored
        - persistent_storage: Whether /data volume is detected
        - database_exists: Whether database.db file exists
        - database_size_kb: Size of database file
        - writable: Whether we can write to database
        - is_production: Whether running on Railway
        """
        try:
            db_exists = os.path.exists(DB_PATH)
            writable = verify_db_writable() if db_exists else False
            
            db_size = 0
            if db_exists:
                db_size = os.path.getsize(DB_PATH) / 1024
            
            env = os.environ.get('PORT')  # If PORT is set, likely on Railway
            
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'database_path': DB_PATH,
                'database_exists': db_exists,
                'database_size_kb': round(db_size, 2),
                'persistent_storage_enabled': USING_PERSISTENT_STORAGE,
                'writable': writable,
                'is_production': env is not None,
                'app_directory': os.path.dirname(os.path.abspath(__file__)),
                'data_volume_exists': os.path.exists('/data'),
                'message': 'YES - Data persists' if USING_PERSISTENT_STORAGE else 'NO - Data will be lost on redeploy (add /data volume)'
            })
        except Exception as e:
            return jsonify({
                'error': str(e),
                'message': 'Diagnostics check failed'
            }), 500
    
# ============================================================================
# STORE MANAGEMENT API ROUTES
# ============================================================================

@app.route('/store-profile')
@login_required
def store_profile_page():
    """Display store profile management page"""
    return render_template('admin/store_profile.html')

@app.route('/table-management')
@login_required
def table_management_page():
    """Display table management page"""
    hotel_id = get_current_hotel_id()
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT hotel_slug FROM settings WHERE id = ?', (hotel_id,))
    result = c.fetchone()
    hotel_slug = result['hotel_slug'] if result else 'default'
    conn.close()
    return render_template('admin/table_management.html', hotel_slug=hotel_slug)

@app.route('/api/get-tables')
@login_required
def api_get_tables():
    """Get all tables for current hotel"""
    try:
        hotel_id = get_current_hotel_id()
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        conn = get_db()
        c = conn.cursor()
        
        # Get tables from restaurant_tables
        c.execute('SELECT id, hotel_id, table_number, is_active FROM restaurant_tables WHERE hotel_id = ? ORDER BY table_number', 
                 (hotel_id,))
        tables = c.fetchall()
        conn.close()
        
        # Convert to dict format
        tables_list = []
        for table in tables:
            tables_list.append({
                'id': table['id'],
                'table_number': table['table_number'],
                'table_section': 'Main',
                'capacity': 4,
                'table_status': 'available' if table['is_active'] else 'closed',
                'assigned_waiter': '',
                'notes': ''
            })
        
        return jsonify({'success': True, 'tables': tables_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-table', methods=['POST'])
@login_required
def api_save_table():
    """Save or create a table"""
    try:
        hotel_id = get_current_hotel_id()
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        table_number = data.get('table_number', type=int)
        table_id = data.get('id')
        
        if not table_number:
            return jsonify({'success': False, 'error': 'Table number is required'})
        
        conn = get_db()
        c = conn.cursor()
        
        try:
            if table_id:
                # Update existing table
                c.execute('UPDATE restaurant_tables SET table_number = ? WHERE id = ? AND hotel_id = ?',
                         (table_number, table_id, hotel_id))
            else:
                # Create new table
                c.execute('INSERT INTO restaurant_tables (hotel_id, table_number, is_active) VALUES (?, ?, ?)',
                         (hotel_id, table_number, 1))
            
            conn.commit()
            conn.close()
            
            return jsonify({'success': True, 'message': 'Table saved successfully'})
        except sqlite3.IntegrityError:
            conn.close()
            return jsonify({'success': False, 'error': 'Table number already exists'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/delete-table/<int:table_id>', methods=['DELETE'])
@login_required
def api_delete_table(table_id):
    """Delete a table"""
    try:
        hotel_id = get_current_hotel_id()
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        conn = get_db()
        c = conn.cursor()
        
        # Verify table belongs to this hotel
        c.execute('SELECT hotel_id FROM restaurant_tables WHERE id = ?', (table_id,))
        table = c.fetchone()
        
        if not table or table['hotel_id'] != hotel_id:
            conn.close()
            return jsonify({'success': False, 'error': 'Table not found'}), 404
        
        # Delete the table
        c.execute('DELETE FROM restaurant_tables WHERE id = ?', (table_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Table deleted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/create-tables-bulk', methods=['POST'])
@login_required
def api_create_tables_bulk():
    """Create multiple tables at once from start number to end number"""
    try:
        hotel_id = get_current_hotel_id()
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        start_number = int(data.get('start_number', 1))
        end_number = int(data.get('end_number', 12))
        table_section = data.get('table_section', 'Main Hall')
        capacity = int(data.get('capacity', 4))
        
        if start_number < 1 or end_number < 1 or start_number > end_number:
            return jsonify({'success': False, 'error': 'Invalid table range'})
        
        if end_number - start_number + 1 > 100:
            return jsonify({'success': False, 'error': 'Cannot create more than 100 tables at once'})
        
        conn = get_db()
        c = conn.cursor()
        
        created = 0
        failed = 0
        existing = 0
        
        for table_num in range(start_number, end_number + 1):
            try:
                c.execute('INSERT INTO restaurant_tables (hotel_id, table_number, table_section, capacity, is_active) VALUES (?, ?, ?, ?, ?)',
                         (hotel_id, table_num, table_section, capacity, 1))
                created += 1
            except sqlite3.IntegrityError:
                existing += 1
            except Exception as e:
                failed += 1
        
        conn.commit()
        conn.close()
        
        message = f'Created {created} tables'
        if existing > 0:
            message += f', {existing} already existed'
        if failed > 0:
            message += f', {failed} failed'
        
        return jsonify({
            'success': True, 
            'message': message,
            'created': created,
            'existing': existing,
            'failed': failed
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update-store-profile', methods=['POST'])
@login_required
def update_store_profile():
    """Update store profile information"""
    try:
        hotel_id = get_current_hotel_id()
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        section = request.form.get('section')
        conn = get_db()
        c = conn.cursor()
        
        if section == 'basic':
            # Update hotel settings
            c.execute('''UPDATE settings 
                        SET hotel_name = ?, hotel_address = ?, 
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?''',
                     (request.form.get('store_name'), 
                      request.form.get('street_address'),
                      hotel_id))
            
            # Update or insert store profile
            c.execute('''INSERT OR REPLACE INTO store_profiles 
                        (hotel_id, phone_number, store_email, street_address, city, 
                         state, postal_code, cuisine_type, store_description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (hotel_id,
                      request.form.get('phone_number'),
                      request.form.get('store_email'),
                      request.form.get('street_address'),
                      request.form.get('city'),
                      request.form.get('state'),
                      request.form.get('postal_code'),
                      request.form.get('cuisine_type'),
                      request.form.get('store_description')))
        
        elif section == 'hours':
            c.execute('''UPDATE store_profiles 
                        SET open_time = ?, close_time = ?, 
                            working_days = ?, holiday_dates = ?
                        WHERE hotel_id = ?''',
                     (request.form.get('open_time'),
                      request.form.get('close_time'),
                      request.form.get('working_days'),
                      request.form.get('holiday_dates'),
                      hotel_id))
        
        elif section == 'appearance':
            c.execute('''INSERT OR REPLACE INTO store_websites 
                        (hotel_id, website_theme, website_color, 
                         website_title, website_description)
                        VALUES (?, ?, ?, ?, ?)''',
                     (hotel_id,
                      request.form.get('website_theme'),
                      request.form.get('website_color'),
                      request.form.get('website_title'),
                      request.form.get('website_description')))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/upload-store-photos', methods=['POST'])
@login_required
def upload_store_photos():
    """Upload photos to store gallery"""
    try:
        hotel_id = get_current_hotel_id()
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        conn = get_db()
        c = conn.cursor()
        
        if 'photos' not in request.files:
            return jsonify({'success': False, 'error': 'No photos provided'})
        
        files = request.files.getlist('photos')
        uploaded = []
        
        for file in files:
            if file and file.filename != '':
                # Save file
                filename = f"store_{hotel_id}_{int(time.time())}_{file.filename}"
                filepath = os.path.join('static/store_photos', filename)
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                file.save(filepath)
                
                # Add to gallery
                c.execute('''INSERT INTO store_gallery 
                            (hotel_id, photo_url, photo_title)
                            VALUES (?, ?, ?)''',
                         (hotel_id, f'/{filepath}', file.filename))
                uploaded.append(file.filename)
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'uploaded': len(uploaded)})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get-store-photos')
@login_required
def get_store_photos():
    """Get store photo gallery"""
    try:
        hotel_id = get_current_hotel_id()
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM store_gallery WHERE hotel_id = ? ORDER BY display_order DESC',
                 (hotel_id,))
        
        photos = []
        for row in c.fetchall():
            photos.append({
                'id': row['id'],
                'photo_url': row['photo_url'],
                'photo_title': row['photo_title'],
                'is_featured': row['is_featured']
            })
        
        conn.close()
        return jsonify({'success': True, 'photos': photos})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/get-tables')
@login_required
def get_tables():
    """Get all tables for current hotel"""
    try:
        hotel_id = get_current_hotel_id()
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT * FROM table_details WHERE hotel_id = ? 
                    ORDER BY table_number''', (hotel_id,))
        
        tables = []
        for row in c.fetchall():
            tables.append({
                'id': row['id'],
                'table_number': row['table_number'],
                'table_section': row['table_section'],
                'capacity': row['capacity'],
                'table_status': row['table_status'],
                'assigned_waiter': row['assigned_waiter'],
                'notes': row['notes']
            })
        
        conn.close()
        return jsonify({'success': True, 'tables': tables})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/save-table', methods=['POST'])
@login_required
def save_table():
    """Save or update a table"""
    try:
        hotel_id = get_current_hotel_id()
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        conn = get_db()
        c = conn.cursor()
        
        if data.get('id'):
            # Update existing table
            c.execute('''UPDATE table_details 
                        SET table_section = ?, capacity = ?, 
                            table_status = ?, assigned_waiter = ?, notes = ?
                        WHERE id = ? AND hotel_id = ?''',
                     (data.get('table_section'), data.get('capacity'),
                      data.get('table_status'), data.get('assigned_waiter'),
                      data.get('notes'), data.get('id'), hotel_id))
        else:
            # Insert new table
            c.execute('''INSERT INTO table_details 
                        (hotel_id, table_number, table_section, capacity, 
                         table_status, assigned_waiter, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (hotel_id, data.get('table_number'), 
                      data.get('table_section'), data.get('capacity'),
                      data.get('table_status'), data.get('assigned_waiter'),
                      data.get('notes')))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/order')
def customer_order_page():
    """Customer order page (what they see after scanning QR)"""
    return render_template('customer_order.html')

@app.route('/api/get-store-info')
def get_store_info():
    """Get store information for customer order page"""
    try:
        hotel_slug = request.args.get('hotel', 'default')
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''SELECT s.*, sp.phone_number, sp.store_email, 
                            sp.street_address
                    FROM settings s
                    LEFT JOIN store_profiles sp ON s.id = sp.hotel_id
                    WHERE s.hotel_slug = ?''', (hotel_slug,))
        
        store = c.fetchone()
        conn.close()
        
        if not store:
            return jsonify({'success': False, 'error': 'Store not found'})
        
        return jsonify({'success': True, 'store': {
            'id': store['id'],
            'hotel_name': store['hotel_name'],
            'address': store['street_address'],
            'phone': store['phone_number'],
            'logo': store['hotel_logo']
        }})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/place-order', methods=['POST'])
def place_order_api():
    """Place a new order from customer"""
    try:
        data = request.get_json()
        
        conn = get_db()
        c = conn.cursor()
        
        # Get hotel ID from slug
        c.execute('SELECT id FROM settings WHERE hotel_slug = ?', 
                 (data.get('hotel_slug'),))
        hotel = c.fetchone()
        
        if not hotel:
            return jsonify({'success': False, 'error': 'Hotel not found'})
        
        # Create order
        c.execute('''INSERT INTO orders 
                    (hotel_id, table_number, items, subtotal, tax, total, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'pending')''',
                 (hotel['id'], data.get('table_number'),
                  data.get('items'), data.get('subtotal'),
                  data.get('tax'), data.get('total')))
        
        conn.commit()
        order_id = c.lastrowid
        conn.close()
        
        return jsonify({'success': True, 'order_id': order_id})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/store/<hotel_slug>')
def public_store_website(hotel_slug):
    """Public store website - accessible to customers"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Get store profile
        c.execute('''SELECT s.*, sp.* FROM settings s
                    LEFT JOIN store_profiles sp ON s.id = sp.hotel_id
                    WHERE s.hotel_slug = ?''', (hotel_slug,))
        store = c.fetchone()
        
        if not store:
            conn.close()
            return render_template('404.html'), 404
        
        # Get website settings
        c.execute('SELECT * FROM store_websites WHERE hotel_id = ?', (store['id'],))
        website = c.fetchone()
        
        if not website:
            # Create default website settings
            c.execute('''INSERT INTO store_websites (hotel_id, website_title, website_theme, website_color)
                        VALUES (?, ?, ?, ?)''',
                     (store['id'], store['hotel_name'], 'default', '#4CAF50'))
            conn.commit()
            # Query again to get the newly inserted website
            c.execute('SELECT * FROM store_websites WHERE hotel_id = ?', (store['id'],))
            website = c.fetchone()
        
        # Get store photos/gallery
        c.execute('''SELECT * FROM store_gallery WHERE hotel_id = ? 
                    ORDER BY display_order DESC LIMIT 12''', (store['id'],))
        photos = c.fetchall()
        
        conn.close()
        
        # Generate order link
        order_link = url_for('customer_order_page', hotel=hotel_slug, _external=True)
        
        return render_template('public_store_website.html',
                             store=store,
                             website=website,
                             photos=photos,
                             order_link=order_link)
    
    except Exception as e:
        print(f"[ERROR] Error loading store website: {e}")
        import traceback
        traceback.print_exc()
        return render_template('404.html'), 404

@app.route('/api/get-store-website-url')
@login_required
def get_store_website_url():
    """Get the public website URL for current store"""
    try:
        hotel_id = get_current_hotel_id()
        if not hotel_id:
            return jsonify({'success': False, 'error': 'Not authenticated'}), 401
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT hotel_slug FROM settings WHERE id = ?', (hotel_id,))
        result = c.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'error': 'Hotel not found'}), 404
        
        website_url = url_for('public_store_website', hotel_slug=result['hotel_slug'], _external=True)
        return jsonify({
            'success': True,
            'website_url': website_url,
            'share_url': website_url,
            'slug': result['hotel_slug']
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================================================
# SUPERADMIN ROUTES (Software Owner)
# ============================================================================

@app.route('/superadmin/login', methods=['GET', 'POST'])
def superadmin_login():
    """Superadmin login page"""
    if request.method == 'GET':
        return render_template('superadmin_login.html')
    
    # POST request - handle login
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM superadmins WHERE username = ?', (username,))
        superadmin = c.fetchone()
        conn.close()
        
        if not superadmin or not check_password_hash(superadmin['password'], password):
            return jsonify({'success': False, 'error': 'Invalid credentials'})
        
        session['superadmin_id'] = superadmin['id']
        session['is_superadmin'] = True
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/superadmin/dashboard')
def superadmin_dashboard():
    """Superadmin dashboard"""
    if not session.get('is_superadmin'):
        return redirect(url_for('superadmin_login'))
    
    return render_template('superadmin_dashboard.html')

@app.route('/superadmin/logout', methods=['POST'])
def superadmin_logout():
    """Logout superadmin"""
    session.clear()
    return jsonify({'success': True})

@app.route('/superadmin/api/stores')
def api_get_stores():
    """Get all stores for superadmin"""
    if not session.get('is_superadmin'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM settings ORDER BY created_at DESC')
        stores = [dict(row) for row in c.fetchall()]
        conn.close()
        return jsonify({'success': True, 'stores': stores})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/superadmin/api/approve-store/<int:store_id>', methods=['POST'])
def api_approve_store(store_id):
    """Approve a store and enable all services"""
    if not session.get('is_superadmin'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''UPDATE settings 
                    SET approval_status = ?, 
                        service_online_ordering = 1,
                        service_table_management = 1,
                        service_analytics = 1,
                        service_payments = 1
                    WHERE id = ?''',
                 ('approved', store_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/superadmin/api/reject-store/<int:store_id>', methods=['POST'])
def api_reject_store(store_id):
    """Reject a store request"""
    if not session.get('is_superadmin'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        reason = data.get('reason', 'No reason provided')
        
        conn = get_db()
        c = conn.cursor()
        c.execute('''UPDATE settings 
                    SET approval_status = ?
                    WHERE id = ?''',
                 ('rejected', store_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/superadmin/api/disable-store/<int:store_id>', methods=['POST'])
def api_disable_store(store_id):
    """Suspend/disable a store"""
    if not session.get('is_superadmin'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db()
        c = conn.cursor()
        c.execute('''UPDATE settings 
                    SET approval_status = ?
                    WHERE id = ?''',
                 ('suspended', store_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/superadmin/api/toggle-service/<int:store_id>', methods=['POST'])
def api_toggle_service(store_id):
    """Toggle a service for a store"""
    if not session.get('is_superadmin'):
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        service = data.get('service')
        enabled = data.get('enabled', True)
        
        service_map = {
            'online_ordering': 'service_online_ordering',
            'table_management': 'service_table_management',
            'analytics': 'service_analytics',
            'payments': 'service_payments'
        }
        
        if service not in service_map:
            return jsonify({'success': False, 'error': 'Invalid service'})
        
        column = service_map[service]
        conn = get_db()
        c = conn.cursor()
        c.execute(f'UPDATE settings SET {column} = ? WHERE id = ?',
                 (1 if enabled else 0, store_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    try:
        app.run(debug=False, port=port, host='0.0.0.0', threaded=True)
    except Exception as e:
        print(f"[ERROR] Server crashed: {e}")
        import traceback
        traceback.print_exc()
    print("[INFO] Server stopped.")
