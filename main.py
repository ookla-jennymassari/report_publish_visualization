import argparse
import json
import os
import pandas as pd
import smtplib

from datetime import date, datetime
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from utils import make_image_market_test

load_dotenv()


# Market information needed
period = "2025-1H"

# Filepaths for storing the markets
ALL_MARKETS_FILE = "all_markets.json"
REMAINING_MARKETS_FILE = "remaining_markets.json"


def save_json(data, filepath):
    """
    Save data to a JSON file.
    """
    try:
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)
        print(f"Data saved to {filepath}")
    except Exception as e:
        print(f"Failed to save data to {filepath}: {e}")

def load_json(filepath):
    """
    Load data from a JSON file.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print(f"Warning: {filepath} is empty or invalid. Initializing an empty dictionary.")
            return {}
        except Exception as e:
            print(f"Failed to load data from {filepath}: {e}")
            return {}
    else:
        return {}


def run_sql_query(sql_query):
    return pd.read_sql_query(sql_query, con=os.getenv('RSR_SVC_CONN')) 

def get_market_status(csid=None, 
                        period=None, 
                        lma_status=None, 
                        collection_set=None,
                        collection_is_reportable=None, 
                        collection_area=None, 
                        country_id=None,
                        collection_type_id=None,
                        collection_set_status_id=None,
                        product_period_id=None):
    market_status = f'''
    SELECT
        collection_set_id,
        collection_set,
        collection_is_reportable,
        product_period,
        product_period_id,
        collection_area,
        collection_set_status_id,
        collection_type_id,
        country_id,
        lma_status,
        last_status_time
    FROM auto.vi_collection_status_reporting
    WHERE 1=1
    '''

    if csid is not None:
        market_status += f" AND collection_set_id = {csid}"
    if period is not None:
        market_status += f" AND product_period = '{period}'"
    if lma_status is not None:
        market_status += f" AND lma_status = '{lma_status}'"
    if collection_set is not None:
        market_status += f" AND collection_set = '{collection_set}'"
    if collection_area is not None:
        market_status += f" AND collection_area = '{collection_area}'"
    if country_id is not None:
        market_status += f" AND country_id = {country_id}"
    if collection_type_id is not None:
        market_status += f" AND collection_type_id = {collection_type_id}"
    if collection_set_status_id is not None:
        market_status += f" AND collection_set_status_id = {collection_set_status_id}"
    if product_period_id is not None:
        market_status += f" AND product_period_id = {product_period_id}"
    # if collection_is_reportable is True:
    #     market_status += f" AND collection_is_reportable = True"
    # elif collection_is_reportable is False:
    #     market_status += " AND collection_is_reportable = '{}'"
    
    

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None) 

    df_market_status = pd.read_sql_query(market_status, con=os.getenv('RSR_SVC_CONN'))
    print("Running SQL query:")
    print(df_market_status)

    if csid or collection_set:
        df_transposed_status = df_market_status.T.reset_index()
        print(df_transposed_status)
    else:
        print(df_market_status)

    print(f"Query returned {len(df_market_status)} rows.")
    return df_market_status



# def get_market_status():
#     market_status = f'''
#     SELECT *
#     FROM auto.vi_collection_status_reporting
#     WHERE collection_set_status_id = 20
#     AND product_period = '{period}'
#     AND collection_is_reportable = True
#     AND collection_type_id = 1;
#     '''
#     df_market_status = run_sql_query(market_status)
#     return df_market_status

# df_market_status = get_market_status()

def initialize_all_markets(df_market_status):
    """
    Create the initial JSON file with all markets if it doesn't exist.
    """
    if not os.path.exists(ALL_MARKETS_FILE):
        all_markets = {str(row['collection_set_id']): row['collection_area'] for _, row in df_market_status.iterrows()}
        save_json(all_markets, ALL_MARKETS_FILE)

    if not os.path.exists(REMAINING_MARKETS_FILE):
        remaining_markets = load_json(ALL_MARKETS_FILE)  
        save_json(remaining_markets, REMAINING_MARKETS_FILE)


def process_sent_emails(df_market_status, csid=None):
    """
    Process the DataFrame to send emails and update the remaining markets JSON file.
    """

    remaining_markets = load_json(REMAINING_MARKETS_FILE)
    present = datetime.combine(date.today(), datetime.min.time())
    email_counter = 0
    max_emails_to_send = 2
    
    for index, row in df_market_status.iterrows():
        if email_counter >= max_emails_to_send:
            print("Maximum number of emails sent.")
            break

        csid = str(row['collection_set_id'])
        collection_set_name = row['collection_area']
        url_market_name = collection_set_name.replace(",", "-").replace(" ", "").lower()
        image_test = make_image_market_test()

        print(f"Processing market: CSID: {csid}, Collection Set Name: {collection_set_name}")

        if csid in remaining_markets:  
            if present >= row['last_status_time']:
                send_email(csid, collection_set_name, url_market_name, image_test)
                del remaining_markets[csid]  
                save_json(remaining_markets, REMAINING_MARKETS_FILE)  
                email_counter += 1

        else:
            print(f"Email already sent for CSID: {csid}, Collection Set Name: {collection_set_name}.")


def send_email(csid, collection_set_name, url_market_name, image_test):
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
            <br>
            <p> You can check an image test bellow: </p>
            <img src="{{image_test}}" alt="Market Test Image" style="width:600px;height:auto;"><br>
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
        image_test=image_test
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
    
    parser = argparse.ArgumentParser(description="Process market emails.")
    parser.add_argument("--csid", type=int, help="The collection set ID to process.")
    parser.add_argument("--period", type=str, default="2025-1H", help="The period for which to process markets.")
    parser.add_argument("-r", "--reportable",action="store_true", help="Check if market is reportable.")
    parser.add_argument("-status", "--lma_status", type=str, help="Market status to process" )
    parser.add_argument("--collection_set", type=str, help="Collection set to process")
    parser.add_argument("--collection_area", type=str, help="Collection area to process")
    parser.add_argument("--country_id", type=int, help="Country ID to filter markets")
    parser.add_argument("--collection_type_id", default= 1, type=int, help="Collection type ID to filter markets")
    parser.add_argument("--collection_set_status_id", default= 20, type=int, help="Collection set status ID to filter markets")
    parser.add_argument("--product_period_id", type=int, help="Product period ID to filter markets")

    args = parser.parse_args()

    csid = args.csid
    period = args.period
    lma_status = args.lma_status
    collection_set = args.collection_set
    collection_area = args.collection_area
    country_id = args.country_id
    collection_type_id = args.collection_type_id
    collection_set_status_id = args.collection_set_status_id
    product_period_id = args.product_period_id
    reportable = args.reportable
 


    df_market_status = get_market_status(csid=csid, 
                                             period=period, 
                                             lma_status=lma_status, 
                                             collection_set=collection_set, 
                                             collection_area=collection_area,
                                             country_id=country_id,
                                             collection_type_id=collection_type_id,
                                             collection_set_status_id=collection_set_status_id,
                                             product_period_id=product_period_id,
                                             collection_is_reportable=reportable)


    initialize_all_markets(df_market_status)
    process_sent_emails(df_market_status, csid=csid)

    print("All markets processed.")



