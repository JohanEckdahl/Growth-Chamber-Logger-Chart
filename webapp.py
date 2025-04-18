import pandas as pd
import requests
from io import StringIO
import plotly.express as px
import streamlit as st
from datetime import datetime, timedelta

st.set_page_config(layout='wide')

# 1. Download and read CSV
file_id = "10Hzs1GFe8XqxzmItJ84S780Md3a48fIh"
download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
response = requests.get(download_url)

if response.status_code != 200:
    st.error("Failed to download file.")
    st.stop()

content = StringIO(response.text)
df = pd.read_csv(content, skiprows=1).iloc[2:]
df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'])

# Convert all other columns to float
for col in df.columns:
    if col != 'TIMESTAMP':
        df[col] = df[col].astype(float)

# 2. Calibration
def ToppEq(x):
    return 4.3e-6 * x**3 - 5.5e-4 * x**2 + 2.92e-2 * x - 5.3e-2

cal = {"DateTime" : df["TIMESTAMP"],
    # TEMPS
    "HiC HiM 1 Upper Temp": df["T(1)"],
    "HiC HiM 1 Lower Temp": df["T(2)"],
    "HiC HiM 2 Upper Temp": df["T(3)"],
    "HiC HiM 2 Lower Temp": df["T(4)"],
    "HiC HiM 3 Upper Temp": df["T(5)"],
    "HiC HiM 3 Lower Temp": df["T(6)"],
    "HiC LoM 1 Upper Temp": df["T(7)"],
    "HiC LoM 1 Lower Temp": df["T(8)"],
    "HiC LoM 2 Upper Temp": df["T(9)"],
    "HiC LoM 2 Lower Temp": df["T(10)"],
    "HiC LoM 3 Upper Temp": df["T(11)"],
    "HiC LoM 3 Lower Temp": df["T(12)"],
    "LoC HiM 1 Upper Temp": df["T_2(1)"],
    "LoC HiM 1 Lower Temp": df["T_2(2)"],
    "LoC HiM 2 Upper Temp": df["T_2(3)"],
    "LoC HiM 2 Lower Temp": df["T_2(4)"],
    "LoC HiM 3 Upper Temp": df["T_2(5)"],
    "LoC HiM 3 Lower Temp": df["T_2(6)"],
    "LoC LoM 1 Upper Temp": df["T_2(7)"],
    "LoC LoM 1 Lower Temp": df["T_2(8)"],
    "LoC LoM 2 Upper Temp": df["T_2(9)"],
    "LoC LoM 2 Lower Temp": df["T_2(10)"],
    "LoC LoM 3 Upper Temp": df["T_2(11)"],
    "LoC LoM 3 Lower Temp": df["T_2(12)"],

    # VWCs
    "HiC HiM 1 Upper VWC": ToppEq(df["e(1)"]),
    "HiC HiM 1 Lower VWC": ToppEq(df["e(2)"]),
    "HiC HiM 2 Upper VWC": ToppEq(df["e(3)"]),
    "HiC HiM 2 Lower VWC": ToppEq(df["e(4)"]),
    "HiC HiM 3 Upper VWC": ToppEq(df["e(5)"]),
    "HiC HiM 3 Lower VWC": ToppEq(df["e(6)"]),
    "HiC LoM 1 Upper VWC": ToppEq(df["e(7)"]),
    "HiC LoM 1 Lower VWC": ToppEq(df["e(8)"]),
    "HiC LoM 2 Upper VWC": ToppEq(df["e(9)"]),
    "HiC LoM 2 Lower VWC": ToppEq(df["e(10)"]),
    "HiC LoM 3 Upper VWC": ToppEq(df["e(11)"]),
    "HiC LoM 3 Lower VWC": ToppEq(df["e(12)"]),
    "LoC HiM 1 Upper VWC": ToppEq(df["e_2(1)"]),
    "LoC HiM 1 Lower VWC": ToppEq(df["e_2(2)"]),
    "LoC HiM 2 Upper VWC": ToppEq(df["e_2(3)"]),
    "LoC HiM 2 Lower VWC": ToppEq(df["e_2(4)"]),
    "LoC HiM 3 Upper VWC": ToppEq(df["e_2(5)"]),
    "LoC HiM 3 Lower VWC": ToppEq(df["e_2(6)"]),
    "LoC LoM 1 Upper VWC": ToppEq(df["e_2(7)"]),
    "LoC LoM 1 Lower VWC": ToppEq(df["e_2(8)"]),
    "LoC LoM 2 Upper VWC": ToppEq(df["e_2(9)"]),
    "LoC LoM 2 Lower VWC": ToppEq(df["e_2(10)"]),
    "LoC LoM 3 Upper VWC": ToppEq(df["e_2(11)"]),
    "LoC LoM 3 Lower VWC": ToppEq(df["e_2(12)"]),
}

df2 = df.assign(**cal)[list(cal.keys())]

# ——— Plot Section ———

# MELT for long-form plotting
temp_cols = [c for c in df2.columns if "Temp" in c]
vwc_cols = [c for c in df2.columns if "VWC" in c]

df_temp = df2.melt(id_vars=["DateTime"],
                   value_vars=temp_cols,
                   var_name="Sensor",
                   value_name="Temperature")

df_vwc = df2.melt(id_vars=["DateTime"],
                  value_vars=vwc_cols,
                  var_name="Sensor",
                  value_name="VWC")

# ——— Temperature Chart ———
fig_temp = px.line(df_temp, x="DateTime", y="Temperature", color="Sensor", title="Temperature Sensors")
fig_temp.update_layout(xaxis_title="Time", yaxis_title="Temperature (°C)", height=600)

# ——— VWC Chart ———
fig_vwc = px.line(df_vwc, x="DateTime", y="VWC", color="Sensor", title="Soil Moisture Sensors")
fig_vwc.update_layout(xaxis_title="Time", yaxis_title="Volumetric Water Content (%)", height=600)

# 3. Error Log Section

def error_log(df, time_col='TIMESTAMP', threshold_min=40):
    df = df.copy()
    df[time_col] = pd.to_datetime(df[time_col])
    
    # Find most recent timestamp
    recent_ts = df[time_col].max()
    now = datetime.now() - timedelta(hours=7) 
    delta = now - recent_ts
    
    # Display status (green if recent)
    warning = delta > timedelta(minutes=threshold_min)
    msg = (f"Last data point @ {recent_ts} — "
           f"{int(delta.total_seconds()//60)} min {int(delta.total_seconds()%60)} s ago")
    
    if warning:
        return f"**<span style='color:red'>⚠️  STALE DATA: {msg}</span>**", warning
    else:
        return f"**<span style='color:green'>✅ Recent data: {msg}</span>**", warning

# Error message and download button
error_msg, warning = error_log(df, time_col='TIMESTAMP', threshold_min=40)

# Display the error message and CSV download button at the top
col1, col2 = st.columns([4, 1])

with col1:
    st.markdown(error_msg, unsafe_allow_html=True)

with col2:
    # 4. Download CSV Button
    def convert_df(df):
        return df.to_csv(index=False).encode('utf-8')

    csv = convert_df(df2)

    st.download_button(
        label="Download CSV",
        data=csv,
        file_name='sensor_data.csv',
        mime='text/csv',
    )

# ——— Display the Graphs After the Error and Download Sections ———
st.plotly_chart(fig_temp, use_container_width=True)
st.plotly_chart(fig_vwc, use_container_width=True)

# 4. Error List Section (Columns with NaN or 0 Values)
def find_errors(df):
    errors = []
    for col in df.columns:
        if df[col].isna().any() or (df[col] == 0).any():
            # Find rows where NaN or 0 values exist
            error_rows = df[df[col].isna() | (df[col] == 0)]
            for _, row in error_rows.iterrows():
                errors.append({'column': col, 'timestamp': row['TIMESTAMP']})
    return errors

errors = find_errors(df)

if errors:
    # Sort errors by timestamp (latest first)
    error_df = pd.DataFrame(errors)
    error_df = error_df.sort_values(by='timestamp', ascending=False)
    
    st.write("### Columns with NaN or 0 Values:")
    st.dataframe(error_df)  # Display the errors in a dataframe
else:
    st.write("### No NaN or Zero Values detected.")
