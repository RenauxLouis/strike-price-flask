from __future__ import print_function

from datetime import date
import pandas as pd
import gspread

from constants import CSV_FPATH

from re import sub
from decimal import Decimal
import numpy as np


ALL_TICKERS_CSV_FPATH = "all_tickers.csv"


def connect_to_worksheet():
    gc = gspread.service_account()
    wks = gc.open("strike_price_test").sheet1
    return wks


def get_ggsheet_as_df():

    wks = connect_to_worksheet()
    df = pd.DataFrame(wks.get_all_records())
    if not df.empty:
        df = df.rename(columns={"TICKER": "ticker",
                                "STRIKE PRICE": "strike_price"})
        df["ticker"].replace("", np.nan, inplace=True)
        df["strike_price"].replace("", np.nan, inplace=True)
        df = df.dropna()

        all_tickers = pd.read_csv(
            ALL_TICKERS_CSV_FPATH, index_col=False)["ticker"]
        df = df.loc[df["ticker"].isin(all_tickers)]
        df["strike_price"] = df["strike_price"].apply(
            lambda x: Decimal(sub(r"[^\d.]", "", x)))
        df = df.set_index("")

    return df


def get_df_with_dates():
    new_df = get_ggsheet_as_df()
    df_existing = pd.read_csv(CSV_FPATH, index_col=False)

    if new_df.empty:
        df_updated = df_existing
    else:
        new_tickers = [
            ticker for ticker in new_df[
                "ticker"].values if ticker not in df_existing["ticker"].values]

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
