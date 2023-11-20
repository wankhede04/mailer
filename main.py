import time
import requests
import smtplib
from email.message import EmailMessage
from email_template import get_html_body
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

### EMAIL CONFIG ###
SENDER_EMAIL = os.getenv("GMAIL_EMAIL")
SENDER_PASSWORD = os.getenv("GMAIL_PASSWORD")  # gmail app password
RECIPIENTS = [
    "shivansh0507@audacelabs.com",
    "wankhede.tech@gmail.com",
    'sachin@audacelabs.com',
    'sujith@unore.io'
]

### CONTRACT CONFIG ###
CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # USDT CONTRACT ADDRESS

### ACCOUNTS TO WATCH ###
ACCOUNTS_TO_WATCH = [
    "TJZDAAP4QMrtzsPw8R8mRq1feqBUYS6MdH",
    "TRNXU4XDvBhBgrUsVVQLoj9E3f3vPxuMZZ",
    "TA586MH4FcQtN349SCdp5J932TcRedw1Wf",
    "TAAUt8MPHX7qUzowM97Lc7DXAsiLhcMk2r",
]

### POLLING CONFIG ###
POLL_INTERVAL = 0.1  # 5 minutes

seen_transactions = set()


def send_email(subject, body):
    msg = EmailMessage()
    msg.set_content(body, subtype="html")
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = ", ".join(RECIPIENTS)
    smtp_server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    smtp_server.login(SENDER_EMAIL, SENDER_PASSWORD)
    smtp_server.sendmail(SENDER_EMAIL, RECIPIENTS, msg.as_string())
    smtp_server.quit()


def get_usdt_transactions(account):
    transactions_url = f"https://api.trongrid.io/v1/accounts/{account}/transactions/trc20?&contract_address={CONTRACT}"
    response = requests.get(transactions_url)
    return response.json()


def get_usdt_balance(account):
    account_url = (
        f"https://apilist.tronscan.org/api/account?address={account}&includeToken=true"
    )
    response = requests.get(account_url)
    data = response.json()
    for token in data["trc20token_balances"]:
        if token["tokenName"] == "Tether USD":
            usdt_balance = round(
                float(token["balance"]) * pow(10, -token["tokenDecimal"]), 6
            )
            return usdt_balance


def create_send_email(tx):
    timestamp = tx["block_timestamp"]
    id = tx["transaction_id"]
    datetime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp / 1000))
    is_deposit = tx["to"] in ACCOUNTS_TO_WATCH
    amount = round(float(tx["value"]) * pow(10, -tx["token_info"]["decimals"]), 6)
    action = "Deposit" if is_deposit else "Withdrawal"
    other_account = tx["from"] if is_deposit else tx["to"]
    from_account=tx["from"] 
    to_account=tx["to"] 
    subject = (
         f'DEMO - [{action}] confirmation of USDT on {other_account}'
    )
    link = f"https://tronscan.org/#/transaction/{id}"
    other_key = "From" if is_deposit else "To"
    body = get_html_body(
        from_account,
        id,
        action,
        amount,
        datetime,
        link,
        other_key,
        to_account,
    )
    send_email(subject, body)


def handle_usdt_transactions(start_timestamp, accounts_to_watch):
    while True:
        for account in accounts_to_watch:
            transactions = get_usdt_transactions(account)["data"]
            current_time = time.time() * 1000
            for tx in transactions:
                tx_timestamp = tx["block_timestamp"]
                id = tx["transaction_id"]
                if id not in seen_transactions:
                    seen_transactions.add(id)
                    if tx_timestamp >= start_timestamp:
                        print(f"New transaction for account {account}")
                        create_send_email(tx)
        print("Will sleep for:", POLL_INTERVAL, "minutes")
        time.sleep(POLL_INTERVAL * 60)


def main():
    print("Job Started ...")
    timestamp = time.time() * 1000
    handle_usdt_transactions(timestamp, ACCOUNTS_TO_WATCH)


main()
