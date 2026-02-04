import streamlit as st
from supabase import create_client, Client
import datetime
import pandas as pd

# ========= 连接 Supabase =========
SUPABASE_URL = "https://mdgeybilesogysrsqqrb.supabase.co"
SUPABASE_KEY = "sb_publishable_CZ6WGBuNw499wR1oez3bAA_wJ0nKDQR"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("🏔️ 攀岩日志 APP（云端版）")

menu = st.sidebar.selectbox("菜单", ["记录攀岩", "查看统计"])

# ================= 记录功能 =================
if menu == "记录攀岩":
    st.header("新增攀岩记录")

    user = st.text_input("你的名字")
    date = st.date_input("日期", datetime.date.today())
    country = st.text_input("国家")
    city = st.text_input("城市")
    gym = st.text_input("岩馆")

    climb_type = st.selectbox("攀岩类型", ["室内抱石", "高墙顶绳", "高墙先锋", "野攀"])
    route_count = st.number_input("完成路线数", min_value=0, step=1)
    max_grade = st.text_input("最高等级")

    if st.button("保存记录"):
        data = {
            "date": str(date),
            "user_name": user,
            "country": country,
            "city": city,
            "gym": gym,
            "climb_type": climb_type,
            "route_count": int(route_count),
            "max_grade": max_grade,
        }

        supabase.table("climb_records").insert(data).execute()
        st.success("记录已保存到云端数据库！")

# ================= 统计功能 =================
if menu == "查看统计":
    st.header("数据统计")

    response = supabase.table("climb_records").select("*").execute()
    df = pd.DataFrame(response.data)

    if df.empty:
        st.info("还没有数据")
    else:
        st.dataframe(df)

        st.subheader("各类型完成路线数")
        type_sum = df.groupby("climb_type")["route_count"].sum()
        st.bar_chart(type_sum)

        st.subheader("各岩馆攀爬天数")
        gym_count = df["gym"].value_counts()
        st.bar_chart(gym_count)

