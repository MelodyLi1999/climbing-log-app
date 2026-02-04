import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import re

# ========= 主题切换 =========
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"

def set_theme(mode):
    st.session_state.theme_mode = mode

col_theme1, col_theme2 = st.columns([8,1])
with col_theme2:
    if st.session_state.theme_mode == "dark":
        if st.button("🌞"):
            set_theme("light")
    else:
        if st.button("🌙"):
            set_theme("dark")

# ========= 图表风格 =========
if st.session_state.theme_mode == "dark":
    plt.style.use("dark_background")
    LINE_COLOR = "#4CAF50"
    BAR_COLOR = "#81C784"
else:
    plt.style.use("seaborn-v0_8-whitegrid")
    LINE_COLOR = "#2E7D32"
    BAR_COLOR = "#66BB6A"

# ========= Supabase =========
SUPABASE_URL = "https://mdgeybilesogysrsqqrb.supabase.co"
SUPABASE_KEY = "sb_publishable_CZ6WGBuNw499wR1oez3bAA_wJ0nKDQR"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.set_page_config(page_title="攀岩日志", layout="wide")
st.title("🏔️ 攀岩日志系统")

menu = st.sidebar.selectbox("菜单", ["记录攀岩", "个人统计", "多人对比"])

# ========= 等级转换 =========
def grade_to_number(grade):
    if not grade:
        return None
    grade = grade.strip().lower()
    if grade.startswith("v"):
        return int(grade.replace("v", ""))
    match = re.match(r"5\.(\d+)([abcd]?)", grade)
    if match:
        base = int(match.group(1))
        offset = {"":0, "a":0.1, "b":0.2, "c":0.3, "d":0.4}
        return base + offset.get(match.group(2), 0)
    return None

# ========= 记录页面 =========
if menu == "记录攀岩":
    st.header("新增攀岩记录")

    user = st.selectbox("你的名字", ["十三","小浪","辣辣","听雨","ZC","颜"])
    date = st.date_input("日期", datetime.date.today())
    country = st.text_input("国家")
    city = st.text_input("城市")
    gym = st.text_input("岩馆")
    climb_type = st.selectbox("攀岩类型", ["室内抱石", "高墙顶绳", "高墙先锋", "野攀"])
    route_count = st.number_input("完成路线数", min_value=0, step=1)
    max_grade = st.text_input("最高等级（如 V5 或 5.11c）")

    if st.button("保存记录"):
        data = {
            "user_name": user.strip(),
            "date": str(date),
            "country": country,
            "city": city,
            "gym": gym,
            "climb_type": climb_type,
            "route_count": int(route_count),
            "max_grade": max_grade.strip()
        }
        supabase.table("climb_records").insert(data, returning="minimal").execute()
        st.success("记录已保存到云端数据库！")

# ========= 个人统计 =========
if menu == "个人统计":
    st.header("📊 我的攀岩统计")
    df = pd.DataFrame(supabase.table("climb_records").select("*").execute().data)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        user = st.selectbox("选择用户", df["user_name"].unique())
        df = df[df["user_name"] == user]

        st.metric("攀爬天数", df["date"].nunique())

# ========= 多人对比 =========
if menu == "多人对比":
    st.header("👥 多人训练对比")

    df = pd.DataFrame(supabase.table("climb_records").select("*").execute().data)

    if df.empty:
        st.info("暂无数据")
    else:
        df["date"] = pd.to_datetime(df["date"])
        df["grade_num"] = df["max_grade"].apply(grade_to_number)

        users = st.multiselect("选择对比用户", df["user_name"].unique())

        if users:
            compare = df[df["user_name"].isin(users)]

            # ===== 攀爬天数对比 =====
            days = compare.groupby("user_name")["date"].nunique()

            fig1, ax1 = plt.subplots()
            ax1.bar(days.index, days.values, color=BAR_COLOR)
            ax1.set_title("Climbing Days Comparison")
            ax1.set_ylabel("Days")
            st.pyplot(fig1)

            # ===== 最高等级对比 =====
            max_grade = compare.groupby("user_name")["grade_num"].max()

            fig2, ax2 = plt.subplots()
            ax2.bar(max_grade.index, max_grade.values, color=LINE_COLOR)
            ax2.set_title("Highest Grade Achieved")
            ax2.set_ylabel("Grade (Numeric)")
            st.pyplot(fig2)

