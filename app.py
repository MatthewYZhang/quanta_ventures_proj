import streamlit as st
import pandas as pd
import datetime
import yfinance as yf

st.title("Stock Trading Logic Tester")

stock_ticker = st.text_input("Stock Ticker", "AAPL")
start_date = st.date_input("Start Date", datetime.date(2012, 1, 1))
end_date = st.date_input("End Date", datetime.date(2022, 12, 31))
threshold_1 = st.number_input("Percent Volume Breakout Threshold (%)", value=200.0, step=1.0)
threshold_2 = st.number_input("Daily Change Threshold (%)", value=2.0, step=0.1)
holding_period = st.number_input("Holding Period (days)", min_value=1, value=10, step=1)

generate_report = st.button("Generate Report")

def get_historical_price(stock_ticker, start_date, end_date):
    data = yf.download(stock_ticker, start=start_date, end=end_date)
    if len(data) == 0:
        st.error(f"Error: no ticker called {stock_ticker}")
        return pd.DataFrame()
    df = data.stack(level=-1).reset_index()
    df = df.rename(columns={"level_1": "Ticker"}).set_index("Date")

    df.index = pd.to_datetime(df.index)
    return df

def generate_trading_report(stock_ticker, start_date, end_date, threshold_1, threshold_2, holding_period):
    historical_data = get_historical_price(stock_ticker, start_date, end_date)

    if historical_data is None or historical_data.empty:
        st.error("No data retrieved for the specified stock and date range.")
        return pd.DataFrame()

    historical_data["20D_Avg_Volume"] = historical_data["Volume"].shift(1).rolling(window=20).mean()
    historical_data[f"Future_Return_{holding_period}_days"] = historical_data["Close"].shift(-holding_period) / historical_data["Close"] - 1

    historical_data["Breakout"] = (
        (historical_data["Volume"] - (threshold_1 / 100) * historical_data["20D_Avg_Volume"] > 0) &
        ((historical_data["Close"] / historical_data["Close"].shift(1) - 1 - threshold_2 / 100) > 0)
    )

    breakout_days = historical_data[historical_data["Breakout"]].copy()

    report = breakout_days[["Volume", "Close", f"Future_Return_{holding_period}_days"]]
    report.rename(columns={"Volume": "Volume on Breakout", "Close": "Close Price on Breakout", f"Future_Return_{holding_period}_days": "Return"}, inplace=True)
    report.reset_index(inplace=True)

    return report

def validate_inputs(start_date, end_date):
    if start_date > end_date:
        st.error("Error: Start date must be before end date.")
        return False
    return True

def generate_summary(df):
    trading_days = len(df)
    average_profit = df.Return.mean()
    return f"During selected days, we have {trading_days} trading days with average profit {average_profit}"


if generate_report:
    if validate_inputs(start_date, end_date):
        report = generate_trading_report(stock_ticker, start_date, end_date, threshold_1, threshold_2, holding_period)
        summary = generate_summary(report)
        st.text(summary)
        csv = report.to_csv(index=False)
        st.download_button(
            label="Download Report as CSV",
            data=csv,
            file_name=f"{stock_ticker}_trading_report_{start_date}_{end_date}_{holding_period}days_holding.csv",
            mime="text/csv",
        )

        st.success("Report generated and ready for download!")
