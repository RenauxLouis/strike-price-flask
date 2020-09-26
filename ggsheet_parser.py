from __future__ import print_function

import os.path
import pickle
from datetime import date
import pandas as pd
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from constants import CSV_FPATH


SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

SAMPLE_SPREADSHEET_ID = "14UiMpnTg0KwJykPhUMVqLYasi0p81bXLCQDMHwDVouM"
SAMPLE_RANGE_NAME = "Sheet1!B:C"


def get_credentials():
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return creds


def get_ggsheet_as_df():

    creds = get_credentials()
    service = build("sheets", "v4", credentials=creds)

    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    tuples = result["values"]
    assert tuples[0] == ["TICKER", "STRIKE PRICE"]

    df = pd.DataFrame(tuples[1:],
                      columns=["ticker", "strike_price"])
    df["strike_price"] = df["strike_price"].str.replace("$", "").astype(float)

    return df


def get_df_with_dates():
    new_df = get_ggsheet_as_df()

    df_existing = pd.read_csv(CSV_FPATH, index_col=False)
    new_tickers = [
        ticker for ticker in new_df[
            "ticker"].values if ticker not in df_existing["ticker"].values]
    df_new_tickers = new_df.loc[new_df["ticker"].isin(new_tickers)]
    df_new_tickers["strike_price_query_date"] = str(date.today())
    df_updated = df_existing.append(df_new_tickers)
    df_updated.to_csv(CSV_FPATH, index=False)
    print(df_updated)
    return df_updated
