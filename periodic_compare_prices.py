import os
import smtplib
import ssl
import tempfile
from datetime import date, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from yahoo_fin import stock_info

from constants import CSV_FPATH


def get_closing_price_past_year(ticker):

    today = date.today()
    a_year_ago = date.today() - timedelta(days=365)
    df = yf.download(ticker, start=a_year_ago, end=today)
    return = df["Close"]


def plot_price_history(ticker, closing_prices, tmpdirpath):

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.plot(closing_prices.index, closing_prices, label=ticker)
    ax.set_xlabel("Date")
    ax.set_ylabel("Closing price ($)")
    ax.legend()

    fpath_image = os.path.join(tmpdirpath, "plot.png")
    fig.savefig(fpath_image)
    plt.close()

    return fpath_image


def create_secure_connection_and_send_mail(ticker, most_recent_price,
                                           strike_price, sender_email,
                                           sender_password, fpath_image):
    print("In create secure connection")
    port = 465
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender_email, sender_password)
        send_mail(ticker, most_recent_price, strike_price,
                  server, sender_email, fpath_image)


def send_mail(ticker, most_recent_price, strike_price, server, sender_email,
              fpath_image):
    print("In send mail")
    receiver_email = "renauxlouis@gmail.com"

    msgRoot = MIMEMultipart("alternative")
    msgRoot["Subject"] = f"STRIKE PRICE {ticker.upper()}"
    msgRoot["From"] = sender_email
    msgRoot["To"] = receiver_email
    msgRoot.preamble = "This is a multi-part message in MIME format."

    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    text = "Alternative text if no html"

    msgText = MIMEText(text, "plain")
    msgAlternative.attach(msgText)

    with open("mail_format.html") as fi:
        html = fi.read()
    # html = f"""\
    # <html>
    # <body>
    #     <p> Today's closing price on '{ticker}' was ${int(round(most_recent_price, 2))} which is below the strike price you set at ${strike_price}
    #     </p>
    # </body>
    # </html>
    # """
    msgText = MIMEText(html, "html")
    msgAlternative.attach(msgText)

    # part1 = MIMEText(text, "plain")
    # part2 = MIMEText(html, "html")
    # message.attach(part1)
    # message.attach(part2)

    # Adds the image
    with open(fpath_image, "rb") as img_data:
        msgImage = MIMEImage(img_data.read())

    # Define the image's ID as referenced above
    msgImage.add_header('Content-ID', '<image1>')
    msgRoot.attach(msgImage)

    server.sendmail(sender_email, receiver_email, msgRoot.as_string())


def remove_tickers_db(tickers_to_remove, df):
    len_df_before_removal = len(df)
    df = df.loc[~df["ticker"].isin(tickers_to_remove)]
    assert len(df) + len(tickers_to_remove) == len_df_before_removal

    df.to_csv(CSV_FPATH, index=False)


def compare_current_to_strike_prices(sender_email, sender_password):
    df = pd.read_csv(CSV_FPATH)
    tickers_to_remove = []

    with tempfile.TemporaryDirectory() as tmpdirpath:
        for ticker, strike_price in zip(df["ticker"], df["strike_price"]):
            most_recent_price = stock_info.get_live_price(ticker)
            print(ticker, strike_price, most_recent_price)
            if most_recent_price < strike_price:
                closing_prices = get_closing_price_past_year(ticker)
                fpath_image = plot_price_history(
                    ticker, closing_prices, tmpdirpath)
                create_secure_connection_and_send_mail(
                    ticker, most_recent_price, strike_price, sender_email,
                    sender_password, fpath_image)
                tickers_to_remove.append(ticker)

    # remove_tickers_db(tickers_to_remove, df)
