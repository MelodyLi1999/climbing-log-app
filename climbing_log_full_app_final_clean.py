import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

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

# ========= 图表风格随主题变化 =========
if st.session_state.theme_mode == "dark":
    plt.style.use("dark_background")
    matplotlib.rcParams.update({
        "axes.edgecolor": "#444",
        "grid.color": "#333",
        "text.color": "#E6EDF3",
        "axes.labelcolor": "#E6EDF3",
        "xtick.color": "#AAB2BF",
        "ytick.color": "#AAB2BF",
    })
    LINE_COLOR = "#4CAF50"
    HEATMAP_CMAP = plt.cm.YlGn
    HEATMAP_BG = "#0E1117"
else:
    plt.style.use("seaborn-v0_8-whitegrid")
    matplotlib.rcParams.update({
        "axes.edgecolor": "#dddddd",
        "grid.color": "#eeeeee",
        "text.color": "#333333",
        "axes.labelcolor": "#333333",
        "xtick.color": "#555555",
        "ytick.color": "#555555",
    })
    LINE_COLOR = "#2E7D32"
    HEATMAP_CMAP = plt.cm.Greens
    HEATMAP_BG = "white"

# ========= Supabase =========
SUPABASE_URL = "你的SUPABASE_URL"
SUPABASE_KEY = "你的SUPABASE_KEY"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.set_page_config(page_title="攀岩日志", layout="wide")
st.title("🏔️ 攀岩日志系统")

menu = st.sidebar.selectbox("菜单", ["记录攀岩", "个人统计"])

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

# ========= 统计页面 =========
if menu == "个人统计":
    st.header("📊 我的攀岩统计")

    df = pd.DataFrame(supabase.table("climb_records").select("*").execute().data)

    if df.empty:
        st.info("还没有记录")
    else:
        df["date"] = pd.to_datetime(df["date"])
        user = st.selectbox("选择用户", df["user_name"].unique())
        df = df[df["user_name"] == user]

        st.subheader("训练概览")
        col1, col2, col3 = st.columns(3)
        col1.metric("攀爬天数", df["date"].nunique())
        col2.metric("完成总路线", int(df["route_count"].sum()))
        col3.metric("去过岩馆数", df["gym"].nunique())

        # ===== 趋势图 =====
        st.subheader("Training Frequency Trend")
        monthly = df.groupby(df["date"].dt.to_period("M")).size()
        monthly.index = monthly.index.astype(str)

        fig, ax = plt.subplots()
        ax.plot(monthly.index, monthly.values, marker="o", linewidth=2, color=LINE_COLOR)
        ax.set_title("Monthly Training Frequency")
        ax.set_xlabel("Month")
        ax.set_ylabel("Sessions")
        st.pyplot(fig)

        # ===== 热力图 =====
        st.subheader("📅 年度训练打卡图")
        year = st.selectbox("选择年份", sorted(df["date"].dt.year.unique(), reverse=True))
        df_year = df[df["date"].dt.year == year]
        trained_days = set(df_year["date"].dt.date)

        start = datetime.date(year, 1, 1)
        end = datetime.date(year, 12, 31)
        all_days = pd.date_range(start, end)

        heatmap = np.full((7, len(all_days)//7 + 2), np.nan)

        for day in all_days:
            week = day.isocalendar().week - 1
            weekday = day.weekday()
            if day.date() in trained_days:
                heatmap[weekday, week] = 1

        fig, ax = plt.subplots(figsize=(14, 3))
        cmap = HEATMAP_CMAP
        cmap.set_bad(color=HEATMAP_BG)

        ax.imshow(heatmap, aspect='auto', cmap=cmap, vmin=0, vmax=1)
        ax.set_yticks(range(7))
        ax.set_yticklabels(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
        ax.set_title(f"{year} Training Heatmap")
        ax.set_xticks([])
        ax.spines[:].set_visible(False)
        st.pyplot(fig)
