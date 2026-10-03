import streamlit as st
import sqlite3
import pandas as pd

st.title("Human Detection Dashboard")

conn = sqlite3.connect("data.db")
df = pd.read_sql_query("SELECT * FROM logs", conn)

st.write("Data Logs")
st.dataframe(df)

st.write("Graph")
st.line_chart(df[['in_count','out_count','total']])