# ============================================================
# 📈 Universal Stock Strategy App (Colab + Streamlit + yfinance)
# ============================================================

!pip install streamlit yfinance pandas numpy openpyxl matplotlib pyngrok --quiet

import nest_asyncio
import threading
from pyngrok import ngrok
import streamlit.web.cli as stcli

import pandas as pd
import numpy as np
import yfinance as yf
import datetime as dt
import matplotlib.pyplot as plt

# ============================================================
# 🔹 Strategy Logic
# ============================================================

def backtest_stock(symbol, buy_drop=3, sell_profit=5, start_date='2024-01-01'):
    try:
        df = yf.download(symbol, start=start_date)
        if df.empty:
            return None

        df['Buy_Price'] = np.nan
        df['Sell_Price'] = np.nan
        df['Status'] = ''
        df['Target_Achieved'] = ''

        position = None
        buy_price = 0

        for i in range(1, len(df)):
            change_pct = (df['Close'][i] - df['Close'][i-1]) / df['Close'][i-1] * 100

            # 📉 Buy condition: price dropped by X%
            if position is None and change_pct <= -buy_drop:
                position = 'Bought'
                buy_price = df['Close'][i]
                df.loc[df.index[i], 'Buy_Price'] = buy_price
                df.loc[df.index[i], 'Status'] = 'Bought'

            # 📈 Sell condition: price up by Y% from buy
            elif position == 'Bought':
                gain_pct = (df['Close'][i] - buy_price) / buy_price * 100
                if gain_pct >= sell_profit:
                    df.loc[df.index[i], 'Sell_Price'] = df['Close'][i]
                    df.loc[df.index[i], 'Status'] = 'Sold'
                    df.loc[df.index[i], 'Target_Achieved'] = 'Yes'
                    position = None

        # 📊 Summary
        total_trades = len(df[df['Status'] == 'Sold'])
        total_buys = len(df[df['Status'] == 'Bought'])
        profit_trades = len(df[df['Target_Achieved'] == 'Yes'])
        summary = {
            'Symbol': symbol,
            'Total_Trades': total_trades,
            'Open_Positions': total_buys,
            'Successful_Trades': profit_trades
        }

        return {'data': df, 'summary': summary}

    except Exception as e:
        print(f"Error in {symbol}: {e}")
        return None


# ============================================================
# 🔹 Excel Report Creator
# ============================================================

def create_excel_report(results):
    summary_data = [r['summary'] for r in results if r is not None]
    if not summary_data:
        return None

    df_summary = pd.DataFrame(summary_data)
    success_rate = (df_summary['Successful_Trades'].sum() / df_summary['Total_Trades'].sum() * 100) if df_summary['Total_Trades'].sum() > 0 else 0

    with pd.ExcelWriter("Stock_Backtest_Report.xlsx") as writer:
        df_summary.to_excel(writer, index=False, sheet_name='Summary')

        for r in results:
            if r is not None:
                r['data'].to_excel(writer, sheet_name=r['summary']['Symbol'][:30])

    return f"✅ Report generated with {len(df_summary)} stocks\nSuccess Rate: {success_rate:.2f}%"


# ============================================================
# 🔹 Streamlit App
# ============================================================

def run_streamlit():
    import stream
