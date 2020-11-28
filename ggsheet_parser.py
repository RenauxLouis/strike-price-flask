from __future__ import print_function

import os
from datetime import date
from decimal import Decimal
from re import sub

import gspread
import numpy as np
import pandas as pd

from constants import CSV_FPATH

ALL_TICKERS_CSV_FPATH = "all_tickers.csv"


def connect_to_worksheet():
    gc = gspread.service_account()
    wks = gc.open("strike_price_test").sheet1
    return wks


def get_ggsheet_as_df():

    wks = connect_to_worksheet()
    df = pd.DataFrame(wks.get_all_records())
    local_df_columns = ["ticker", "strike_price"]
    if not df.empty:
        clean_columns_rename = {col: col.replace(" ", "") for col in
                                df.columns}
        df = df.rename(columns=clean_columns_rename)
        df = df.rename(columns={
            "TICKER": "ticker", "STRIKEPRICE": "strike_price"})
        df["ticker"].replace("", np.nan, inplace=True)
        df["strike_price"].replace("", np.nan, inplace=True)
        df = df.dropna()

        df = df[local_df_columns]

        all_tickers = pd.read_csv(
            ALL_TICKERS_CSV_FPATH, index_col=False)["ticker"]
        df = df.loc[df["ticker"].isin(all_tickers)]
        df["strike_price"] = df["strike_price"].apply(
            lambda x: float(sub(r"[^\d.]", "", x)))

    return df


def get_new_tickers_and_prices(new_df, df_existing):

    existing_tickers_prices = zip(df_existing.ticker, df_existing.strike_price)
    new_tickers_prices = zip(new_df.ticker, new_df.strike_price)

    not_preexisting_tuples = [
        ticker_price for ticker_price in new_tickers_prices if (
            ticker_price not in existing_tickers_prices)]

    new_tickers = [ticker for ticker, _ in not_preexisting_tuples]

    return new_tickers


def get_df_with_dates():
    new_df = get_ggsheet_as_df()
    if os.path.exists(CSV_FPATH):
        df_existing = pd.read_csv(CSV_FPATH, index_col=False)
    else:
        df_existing = pd.DataFrame(columns=new_df.columns)

    if new_df.empty:
        df_updated = df_existing
    else:
        new_tickers = get_new_tickers_and_prices(new_df, df_existing)
        df_new_tickers = new_df.loc[new_df["ticker"].isin(new_tickers)].copy()
        df_new_tickers["strike_price_query_date"] = str(date.today())
        df_updated = df_existing.append(df_new_tickers)
        df_updated.to_csv(CSV_FPATH, index=False)

    return df_updated


def remove_tickers_ggsheet(tickers_to_remove):

    wks = connect_to_worksheet()
    for ticker in tickers_to_remove:
        cell_list = wks.findall(ticker)
        if cell_list == []:
            print(f"Ticker {ticker} not in the ggsheet")
        else:
            assert len(cell_list) == 1
            ticker_row = cell_list[0].row
            wks.delete_rows(ticker_row)
