import streamlit as st
from supabase import create_client
import pandas as pd
import datetime

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
    max_grade = st.text_input("最高等级")

    if st.button("保存记录"):
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

    response = supabase.table("climb_records").select("*").execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        st.info("还没有记录")
    else:
        df["date"] = pd.to_datetime(df["date"])

        # 选择用户
        user = st.selectbox("选择用户", df["user_name"].unique())
        df = df[df["user_name"] == user]

        # 时间范围筛选
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
        type_sum = df.groupby("climb_type")["route_count"].sum()
        st.bar_chart(type_sum)

        st.subheader("最常去的岩馆")
        gym_count = df["gym"].value_counts()
        st.bar_chart(gym_count)

        st.subheader("训练频率趋势")
        monthly = df.groupby(df["date"].dt.to_period("M")).size()
        monthly.index = monthly.index.astype(str)
        st.line_chart(monthly)

