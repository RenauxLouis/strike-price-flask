import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
from constants import CSV_FPATH
from flask import Blueprint, Flask
from yahoo_fin import stock_info

SENDER_EMAIL = os.environ.get("MAIL_USERNAME")
SENDER_PASSWORD = os.environ.get("MAIL_PASSWORD")

app = Flask(__name__)
usersbp = Blueprint("users", __name__)


@usersbp.cli.command("strike_price_compare")
def create():
    compare_current_to_strike_prices()


app.register_blueprint(usersbp)


def create_secure_connection_and_send_mail(ticker, most_recent_price,
                                           strike_price):
    print("In create secure connection")
    port = 465
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        send_mail(ticker, most_recent_price, strike_price, server)


def send_mail(ticker, most_recent_price, strike_price, server):
    print("In send mail")
    receiver_email = "renauxlouis@gmail.com"

    message = MIMEMultipart("alternative")
    message["Subject"] = f"STRIKE PRICE {ticker.upper()}"
    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email

    text = """\
    Hi,
    How are you?
    Real Python has many great tutorials:
    www.realpython.com"""
    html = f"""\
    <html>
    <body>
        <p> Today's closing price on '{ticker}' was ${int(round(most_recent_price, 0))} which is below the strike price you set at ${strike_price}
        </p>
    </body>
    </html>
    """
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)

    server.sendmail(SENDER_EMAIL, receiver_email, message.as_string())


def remove_tickers_db(tickers_to_remove, df):
    len_df_before_removal = len(df)
    df = df.loc[~df["ticker"].isin(tickers_to_remove)]
    assert len(df) + len(tickers_to_remove) == len_df_before_removal

    df.to_csv(CSV_FPATH, index=False)


def compare_current_to_strike_prices():
    df = pd.read_csv(CSV_FPATH)
    tickers_to_remove = []
    for ticker, strike_price in zip(df["ticker"], df["strike_price"]):
        most_recent_price = stock_info.get_live_price(ticker)
        print(ticker, strike_price, most_recent_price)
        if most_recent_price < strike_price:
            create_secure_connection_and_send_mail(
                ticker, most_recent_price, strike_price)
            tickers_to_remove.append(ticker)

    remove_tickers_db(tickers_to_remove, df)
