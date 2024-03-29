import math
import os
import smtplib
import ssl
import tempfile
from datetime import date, datetime, timedelta
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from matplotlib import rc
from PIL import Image
from yahoo_fin import stock_info

from constants import CSV_FPATH
from ggsheet_parser import get_df_with_dates, remove_tickers_ggsheet


def compress_image(fpath_image):

    img = Image.open(fpath_image)
    img = img.convert("RGB")
    assert os.path.splitext(fpath_image)[1] == ".png"
    fpath_image_compressed = fpath_image.replace(".png", ".jpg")
    img.save(fpath_image_compressed, optimize=True, quality=95)

    return fpath_image_compressed


def get_closing_price_past_year_min(ticker, strike_price_query_date):

    strike_price_query_datetime = datetime.strptime(
        strike_price_query_date, "%Y-%m-%d")
    today = date.today()
    a_year_ago = date.today() - timedelta(days=365)
    start_date = min(strike_price_query_datetime.date(), a_year_ago)
    df = yf.download(ticker, start=start_date, end=today)
    return df["Close"]


def plot_price_history(ticker, closing_prices, strike_price, tmpdirpath,
                       strike_price_query_date):

    font = {"weight": "bold",
            "size": 22}
    rc("font", **font)

    fig, ax = plt.subplots(figsize=(16, 9))
    ax.plot(closing_prices.index, closing_prices,
            label=ticker, color="#000000")

    strike_price_query_datetime = datetime.strptime(
        strike_price_query_date, "%Y-%m-%d")
    strike_price_query_date_slice = strike_price_query_datetime - \
        timedelta(days=100)
    today = date.today()
    strike_price_x_axis = pd.date_range(start=strike_price_query_date_slice,
                                        end=today)
    ax.plot(strike_price_x_axis,
            [strike_price]*len(strike_price_x_axis),
            color="#CC3333", label="STRIKE PRICE", ls="--", lw=2)

    ax.set_ylabel("PRICE - $", font=font)

    n_ticks = 10
    max_val = closing_prices.max()
    min_val = closing_prices.min()
    start_yticks = int(math.floor(min_val / 10.0)) * 10
    end_yticks = int(math.ceil(max_val / 10.0)) * 10
    range_ticks = end_yticks - start_yticks
    step = range_ticks/n_ticks
    yticks = np.arange(start_yticks, end_yticks+step, step)
    plt.yticks(yticks)

    ax.legend()
    plt.grid(alpha=0.25)
    fig.tight_layout()

    fpath_image = os.path.join(tmpdirpath, "plot.png")
    fig.savefig(fpath_image)
    plt.close()

    return fpath_image


def create_secure_connection_and_send_mail(ticker, most_recent_price,
                                           strike_price, sender_email,
                                           sender_password, fpath_image):

    port = 465
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender_email, sender_password)
        send_mail(ticker, most_recent_price, strike_price,
                  server, sender_email, fpath_image)


def send_mail(ticker, most_recent_price, strike_price, server, sender_email,
              fpath_image):

    title = f"{ticker} STRIKE PRICE REACHED"
    subtitle = f"{ticker} just reached ${round(most_recent_price, 2)} which is below the strike price you set at ${strike_price}"

    receiver_email = "renauxlouis@gmail.com"
    assert receiver_email.split("@")[1] == "gmail.com"

    msg_root = MIMEMultipart("alternative")
    msg_root["Subject"] = title
    msg_root["From"] = sender_email
    msg_root["To"] = receiver_email
    msg_root.preamble = title

    msg_alternative = MIMEMultipart("alternative")
    msg_root.attach(msg_alternative)

    msg_text = MIMEText(subtitle, "plain")
    msg_alternative.attach(msg_text)

    with open("mail_format.html") as fi:
        html = fi.read()
    formated_html = html.format(title=title, subtitle=subtitle)

    msg_text = MIMEText(formated_html, "html")
    msg_alternative.attach(msg_text)

    with open(fpath_image, "rb") as img_data:
        msg_image = MIMEImage(img_data.read())
    msg_image.add_header("Content-ID", "<image1>")
    msg_root.attach(msg_image)

    server.sendmail(sender_email, receiver_email, msg_root.as_string())


def remove_tickers_local_csv(tickers_to_remove, df):
    df = df.loc[~df["ticker"].isin(tickers_to_remove)]
    df.to_csv(CSV_FPATH, index=False)


def create_mail_and_send(ticker, strike_price, most_recent_price, tmpdirpath,
                         sender_email, sender_password,
                         strike_price_query_date):
    closing_prices = get_closing_price_past_year_min(
        ticker, strike_price_query_date)
    fpath_image = plot_price_history(
        ticker, closing_prices, strike_price, tmpdirpath,
        strike_price_query_date)
    fpath_image_compressed = compress_image(fpath_image)
    create_secure_connection_and_send_mail(
        ticker, most_recent_price, strike_price, sender_email,
        sender_password, fpath_image_compressed)


def compare_current_to_strike_prices(sender_email, sender_password):

    df = get_df_with_dates()
    tickers_to_remove = []

    with tempfile.TemporaryDirectory() as tmpdirpath:
        for ticker, strike_price, strike_price_query_date in zip(
                df["ticker"], df["strike_price"],
                df["strike_price_query_date"]):
            most_recent_price = stock_info.get_live_price(ticker)
            if most_recent_price <= strike_price:
                create_mail_and_send(
                    ticker, strike_price, most_recent_price, tmpdirpath,
                    sender_email, sender_password, strike_price_query_date)
                tickers_to_remove.append(ticker)

    remove_tickers_local_csv(tickers_to_remove, df)
    remove_tickers_ggsheet(tickers_to_remove)
