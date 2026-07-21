import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Quản Lý Thiết Bị & File Video",
    page_icon="🎥",
    layout="wide",
)

st.title("🎥 Hệ Thống Quản Lý Thiết Bị & File Video")

tab1, tab2 = st.tabs(["📦 Quản lý Thiết bị quay", "📁 Quản lý File Video"])

with tab1:
    st.header("Danh sách thiết bị")
    if os.path.exists("thiet_bi.csv"):
        df_thiet_bi = pd.read_csv("thiet_bi.csv")
        st.dataframe(df_thiet_bi, use_container_width=True)
    else:
        st.info("Chưa tìm thấy dữ liệu thiết bị.")

with tab2:
    st.header("Danh sách File Video")
    if os.path.exists("danh_sach_file.csv"):
        df_file = pd.read_csv("danh_sach_file.csv")
        st.dataframe(df_file, use_container_width=True)
    else:
        st.info("Chưa tìm thấy dữ liệu file video.")
