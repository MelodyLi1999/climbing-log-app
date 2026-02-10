import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import re

# ========= 主题切换 =========
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"

def toggle_theme():
    st.session_state.theme_mode = "light" if st.session_state.theme_mode == "dark" else "dark"

st.sidebar.button("🌙 / 🌞 切换模式", on_click=toggle_theme)

if st.session_state.theme_mode == "dark":
    plt.style.use("dark_background")
    LINE_COLOR = "#4CAF50"
    BAR_COLOR = "#81C784"
    HEATMAP_CMAP = plt.cm.YlGn
    HEATMAP_BG = "#0E1117"
else:
    plt.style.use("seaborn-v0_8-whitegrid")
    LINE_COLOR = "#2E7D32"
    BAR_COLOR = "#66BB6A"
    HEATMAP_CMAP = plt.cm.Greens
    HEATMAP_BG = "white"

# ========= Supabase =========
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

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

# ========= 记录 =========
if menu == "记录攀岩":
    st.header("新增攀岩记录")
    user = st.selectbox("你的名字", ["十三","小浪","辣辣","听雨","ZC","颜"])
    date = st.date_input("日期", datetime.date.today())
    country = st.text_input("国家")
    city = st.text_input("城市")
    gym = st.text_input("岩馆")
    climb_type = st.selectbox("攀岩类型", ["室内抱石", "高墙顶绳", "高墙先锋", "野攀"])
    route_count = st.number_input("完成路线数", min_value=0, step=1)
    max_grade = st.text_input("最高等级（V5 或 5.11c）")

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
        st.success("记录已保存！")

# ========= 个人统计 =========
if menu == "个人统计":
    st.header("📊 我的攀岩统计")

    df = pd.DataFrame(supabase.table("climb_records").select("*").execute().data)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["grade_num"] = df["max_grade"].apply(grade_to_number)

        user = st.selectbox("选择用户", df["user_name"].unique())
        df = df[df["user_name"] == user]

        start_date = st.date_input("开始日期", df["date"].min())
        end_date = st.date_input("结束日期", df["date"].max())
        df = df[(df["date"] >= pd.to_datetime(start_date)) & (df["date"] <= pd.to_datetime(end_date))]

        st.subheader("训练概览")
        col1, col2, col3 = st.columns(3)
        col1.metric("攀爬天数", df["date"].nunique())
        col2.metric("完成总路线", int(df["route_count"].sum()))
        col3.metric("去过岩馆数", df["gym"].nunique())

        # 岩馆统计
        st.subheader("🧗 常去岩馆")
        gym_counts = df["gym"].value_counts()
        fig, ax = plt.subplots()
        ax.bar(gym_counts.index, gym_counts.values, color=BAR_COLOR)
        ax.set_title("Most Visited Gyms")
        st.pyplot(fig)

        # 趋势图
        st.subheader("Training Frequency Trend")
        monthly = df.groupby(df["date"].dt.to_period("M")).size()
        monthly.index = monthly.index.astype(str)
        fig, ax = plt.subplots()
        ax.plot(monthly.index, monthly.values, marker="o", color=LINE_COLOR)
        st.pyplot(fig)

        # 热力图
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

        fig, ax = plt.subplots(figsize=(14,3))
        cmap = HEATMAP_CMAP
        cmap.set_bad(color=HEATMAP_BG)
        ax.imshow(heatmap, aspect='auto', cmap=cmap, vmin=0, vmax=1)
        ax.set_yticks(range(7))
        ax.set_yticklabels(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
        st.pyplot(fig)

        # Streak
        st.subheader("🔥 连续训练记录")
        dates = sorted(trained_days)
        longest = current = 0
        prev_day = None
        for d in dates:
            if prev_day and (d - prev_day).days == 1:
                current += 1
            else:
                current = 1
            longest = max(longest, current)
            prev_day = d

        today = datetime.date.today()
        streak = 0
        temp = today
        while temp in trained_days:
            streak += 1
            temp -= datetime.timedelta(days=1)

        col1, col2 = st.columns(2)
        col1.metric("当前连续训练天数", streak)
        col2.metric("历史最长连续训练", longest)

# ========= 多人对比 =========
if menu == "多人对比":
    st.header("👥 多人对比")

    df = pd.DataFrame(supabase.table("climb_records").select("*").execute().data)
    if not df.empty:
        df["grade_num"] = df["max_grade"].apply(grade_to_number)
        users = st.multiselect("选择对比用户", df["user_name"].unique())

        if users:
            comp = df[df["user_name"].isin(users)]
            days = comp.groupby("user_name")["date"].nunique()
            grades = comp.groupby("user_name")["grade_num"].max()

            fig1, ax1 = plt.subplots()
            ax1.bar(days.index, days.values, color=BAR_COLOR)
            ax1.set_title("Climbing Days")
            st.pyplot(fig1)

            fig2, ax2 = plt.subplots()
            ax2.bar(grades.index, grades.values, color=LINE_COLOR)
            ax2.set_title("Highest Grade")
            st.pyplot(fig2)

