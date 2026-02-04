import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import re

# ✅ 中文字体修复
matplotlib.rcParams['font.family'] = 'Noto Sans CJK JP'
matplotlib.rcParams['axes.unicode_minus'] = False

# ========= 图表全局风格 =========
plt.style.use("seaborn-v0_8-whitegrid")
matplotlib.rcParams.update({
    "axes.titlesize": 14,
    "axes.labelsize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "axes.edgecolor": "#dddddd",
    "axes.linewidth": 0.8,
    "grid.color": "#eeeeee",
    "grid.linestyle": "-",
    "grid.linewidth": 0.6,
    "axes.unicode_minus": False,
})

# ========= Supabase 连接 =========
SUPABASE_URL = "https://mdgeybilesogysrsqqrb.supabase.co"
SUPABASE_KEY = "sb_publishable_CZ6WGBuNw499wR1oez3bAA_wJ0nKDQR"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

st.set_page_config(page_title="攀岩日志", layout="wide")
st.title("🏔️ 攀岩日志系统")

menu = st.sidebar.selectbox("菜单", ["记录攀岩", "个人统计"])

# ========= 等级转换 =========
def grade_to_number(grade, climb_type):
    if not grade:
        return None
    grade = grade.strip().lower()
    if "抱石" in climb_type and grade.startswith("v"):
        try:
            return int(grade.replace("v", ""))
        except:
            return None
    match = re.match(r"5\.(\d+)([abcd]?)", grade)
    if match:
        base = int(match.group(1))
        offset = {"":0, "a":0.1, "b":0.2, "c":0.3, "d":0.4}
        return base + offset.get(match.group(2), 0)
    return None

# ========= 记录功能 =========
if menu == "记录攀岩":
    st.header("新增攀岩记录")

    user = st.selectbox("你的名字", ["十三","小浪","辣辣","听雨","ZC","颜"])
    date = st.date_input("日期", datetime.date.today())
    country = st.text_input("国家")
    city = st.text_input("城市")
    gym = st.text_input("岩馆")
    climb_type = st.selectbox("攀岩类型", ["室内抱石", "高墙顶绳", "高墙先锋", "野攀"])
    route_count = st.number_input("完成路线数", min_value=0, step=1)

    # ===== 等级输入增强 =====
    boulder_grades = [f"V{i}" for i in range(13)]
    rope_grades = ["5.9","5.10a","5.10b","5.10c","5.10d",
                   "5.11a","5.11b","5.11c","5.11d",
                   "5.12a","5.12b","5.12c","5.12d",
                   "5.13a","5.13b","5.13c","5.13d"]

    st.markdown("**最高等级**")
    col1, col2 = st.columns([2,1])

    with col1:
        max_grade_input = st.text_input("手动输入等级（可选）")

    with col2:
        max_grade_select = st.selectbox(
            "常见等级选择",
            [""] + (boulder_grades if "抱石" in climb_type else rope_grades)
        )

    max_grade_raw = max_grade_select if max_grade_select else max_grade_input

    def normalize_grade(g):
        if not g:
            return ""
        g = g.strip()
        if g.lower().startswith("v"):
            return "V" + g[1:]
        return g.lower()

    max_grade = normalize_grade(max_grade_raw)

    valid = True
    if max_grade:
        if "抱石" in climb_type and not re.match(r"^V\d+$", max_grade):
            valid = False
        if "抱石" not in climb_type and not re.match(r"^5\.\d{1,2}[abcd]?$", max_grade):
            valid = False

    if not valid:
        st.warning("等级格式不正确，请使用 V5 或 5.11c")
    else:
        st.caption("等级填写规范：抱石 V5；绳索 5.11c")

    if st.button("保存记录") and valid:
        data = {
            "user_name": user.strip(),
            "date": str(date),
            "country": country,
            "city": city,
            "gym": gym,
            "climb_type": climb_type,
            "route_count": int(route_count),
            "max_grade": max_grade,
        }
        supabase.table("climb_records").insert(data, returning="minimal").execute()
        st.success("记录已保存到云端数据库！")

# ========= 统计功能 =========
if menu == "个人统计":
    st.header("📊 我的攀岩统计")

    df = pd.DataFrame(supabase.table("climb_records").select("*").execute().data)

    if df.empty:
        st.info("还没有记录")
    else:
        df["date"] = pd.to_datetime(df["date"])
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

        st.divider()

        st.subheader("各类型完成路线数")
        st.bar_chart(df.groupby("climb_type")["route_count"].sum())

        st.subheader("最常去的岩馆")
        st.bar_chart(df["gym"].value_counts())

        st.subheader("训练频率趋势")
        monthly = df.groupby(df["date"].dt.to_period("M")).size()
        monthly.index = monthly.index.astype(str)
        fig, ax = plt.subplots()
        ax.plot(monthly.index, monthly.values, marker="o", linewidth=2)
        ax.set_title("每月训练次数趋势")
        ax.set_xlabel("月份")
        ax.set_ylabel("训练次数")
        st.pyplot(fig)

        # ===== 打卡热力图 =====
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
        cmap = plt.cm.Greens
        cmap.set_bad(color="white")
        ax.imshow(heatmap, aspect='auto', cmap=cmap, vmin=0, vmax=1)
        ax.set_yticks(range(7))
        ax.set_yticklabels(["周一","周二","周三","周四","周五","周六","周日"])
        ax.set_title(f"{year} 年训练打卡图")
        ax.set_xticks([])
        ax.spines[:].set_visible(False)
        st.pyplot(fig)

        # ===== 连续训练 Streak =====
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
        while today in trained_days:
            streak += 1
            today -= datetime.timedelta(days=1)

        col1, col2 = st.columns(2)
        col1.metric("当前连续训练天数", streak)
        col2.metric("历史最长连续训练", longest)

