import json
import os
import pandas as pd
import smtplib

from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template

load_dotenv()

# Market information needed
period = "2025-1H"

# Filepath for storing the dictionary
SENT_EMAILS_LOG_FILE = "sent_emails_log.json"

# Initialize the sent_emails_log dictionary
if os.path.exists(SENT_EMAILS_LOG_FILE):
    try:
        with open(SENT_EMAILS_LOG_FILE, "r") as file:
            sent_emails_log = json.load(file)
        print(f"Loaded sent emails log from {SENT_EMAILS_LOG_FILE}")
    except json.JSONDecodeError:
        print(f"Warning: {SENT_EMAILS_LOG_FILE} is empty or invalid. Initializing an empty log.")
        sent_emails_log = {}
    except Exception as e:
        print(f"Failed to load sent emails log: {e}")
        sent_emails_log = {}
else:
    print(f"No existing log file found at {SENT_EMAILS_LOG_FILE}. Starting with an empty log.")
    sent_emails_log = {}


def save_log_to_json():
    try:
        with open(SENT_EMAILS_LOG_FILE, "w") as file:
            json.dump(sent_emails_log, file, indent=4)
        print(f"Log saved to {SENT_EMAILS_LOG_FILE}")
    except Exception as e:
        print(f"Failed to save log: {e}")

def run_sql_query(sql_query):
    return pd.read_sql_query(sql_query, con=os.getenv('RSR_SVC_CONN')) 

def get_market_status():
    market_status = f'''
    SELECT *
    FROM analytic.vi_dqa_assignment_list 
    WHERE additional_status = 'Report Publish'
    AND product_period_name = '{period}'
    AND collection_type_name = 'RSR US Metro';
    '''
    df_market_status = run_sql_query(market_status)
    return df_market_status

df_market_status = get_market_status()

def process_sent_emails(df_market_status):
    global sent_emails_log
    for index, row in df_market_status.iterrows():
        csid = str(row['collection_set_id'])  
        collection_set_name = row['collection_area_name']
        url_market_name = collection_set_name.replace(",", "-").replace(" ", "").lower()

        print(f"Processing market: CSID: {csid}, Collection Set Name: {collection_set_name}")

        if csid not in sent_emails_log:  
            send_email(csid, collection_set_name, url_market_name)
            sent_emails_log[csid] = collection_set_name  
            save_log_to_json()  
        else:
            print(f"Email already sent for CSID: {csid}, Collection Set Name: {collection_set_name}.")

def send_email(csid, collection_set_name, url_market_name):
    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Report Publish Summary</title>
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    <style>
        p {
            line-height: 1.8; 
            margin-bottom: 20px; 
        }
    </style>
    </head>
    <body>
        <p> 
            Verizon Wireless Clients,<br> 
            The latest results for {{collection_set_name}} Metro are now available on RootInsights.<br>
            Final detail and test summary files can be downloaded from the RootInsights API.<br>
            Click here to review market-level details: 
            <a href="https://rootinsights.rootmetrics.com/unitedstates/rsrmetro/market/20251h/{{url_market_name}}/rsr/">Market Details</a><br>
            <br>
            Best Regards,<br>
            Jenny Massari | RootMetrics Intern<br>
            206.376.0884 | D 000.000.0000<br>
            jenny.massari@ookla.com<br>
            <a href="https://www.rootmetrics.com">www.rootmetrics.com</a>
        </p>
    </body>
    </html>
    """

    template = Template(html_template)
    rendered_html = template.render(
        collection_set_name=collection_set_name,
        url_market_name=url_market_name,
    )

    # Reload the .env file
    load_dotenv(override=True)

    # Email credentials and SMTP configuration
    email_user = os.getenv("SES_USER")  
    email_password = os.getenv("SES_PWD")  
    smtp_endpoint = "email-smtp.us-west-2.amazonaws.com"

    send_from = "jenny.massari@ookla.com"
    send_to = ["jenny.massari@ookla.com"]

    # Create the email message
    msg = MIMEMultipart("mixed")
    msg['From'] = send_from
    msg['To'] = ", ".join(send_to)
    msg['Subject'] = f"Automated Email Test - RootScore Final Deliverables Ready for Download - {collection_set_name}" 

    # Create the alternative part for plain text and HTML
    msg_alternative = MIMEMultipart("alternative")
    msg.attach(msg_alternative)

    msg.attach(MIMEText(rendered_html, 'html'))

    try:
        # Connect to the SMTP server
        with smtplib.SMTP(smtp_endpoint, 587) as s:
            s.starttls()  
            s.login(email_user, email_password)  
            s.sendmail(send_from, send_to, msg.as_string())  
            print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

if __name__ == "__main__":
    process_sent_emails(df_market_status)