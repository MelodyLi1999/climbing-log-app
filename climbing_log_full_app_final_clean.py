# climbing_log_full_app_final_clean_chinese.py
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import logging

# --------------------------
# 屏蔽 Streamlit 警告
# --------------------------
logging.getLogger("streamlit").setLevel(logging.ERROR)

# --------------------------
# 支持中文显示
# --------------------------
plt.rcParams['font.sans-serif'] = ['SimHei']   # Windows 中文字体黑体
plt.rcParams['axes.unicode_minus'] = False     # 负号正常显示

# ---------- 文件路径 ----------
RECORDS_FILE = "records_final.csv"
TYPES_FILE = "types_final.csv"

# ---------- 初始化数据 ----------
if not os.path.exists(RECORDS_FILE):
    pd.DataFrame(columns=["RecordID","日期","国家","城市","场馆","笔记"]).to_csv(RECORDS_FILE, index=False)
if not os.path.exists(TYPES_FILE):
    pd.DataFrame(columns=["RecordID","攀岩类型","完成路线数","最高等级"]).to_csv(TYPES_FILE, index=False)

records_df = pd.read_csv(RECORDS_FILE)
types_df = pd.read_csv(TYPES_FILE)

# ---------- 工具函数 ----------
def fig_to_bytes(fig):
    import io
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight')
    buf.seek(0)
    return buf.read()

# ---------- APP 界面 ----------
st.set_page_config(page_title="攀岩日志 APP", layout="wide")
st.title("🏔️ 攀岩日志 APP - 中文支持版")

menu = st.sidebar.selectbox("选择功能", ["记录日志", "查看统计", "导出数据"])

# ---------- 记录日志 ----------
if menu == "记录日志":
    st.header("📋 新增攀岩记录")
    
    date = st.date_input("日期", datetime.today())
    
    existing_countries = records_df["国家"].dropna().unique().tolist()
    country = st.selectbox("国家", options=existing_countries + ["新增..."])
    if country == "新增...":
        country = st.text_input("请输入新国家")
    
    city = st.text_input("城市")
    
    existing_gyms = records_df["场馆"].dropna().unique().tolist()
    gym = st.selectbox("场馆", options=existing_gyms + ["新增..."])
    if gym == "新增...":
        gym = st.text_input("请输入新场馆")
    
    note = st.text_area("笔记（可选）")
    
    st.subheader("攀岩类型明细")
    types_options = ["室内抱石", "高墙-顶绳", "高墙-先锋", "野外攀岩"]
    selected_types = st.multiselect("选择攀岩类型", types_options)
    
    type_details = []
    for t in selected_types:
        st.markdown(f"**{t}**")
        num_routes = st.number_input(f"{t} 完成路线数（可选）", min_value=0, step=1, key=f"{t}_num")
        grade = st.text_input(f"{t} 最高等级（可选）", key=f"{t}_grade")
        type_details.append({"攀岩类型": t, "完成路线数": num_routes, "最高等级": grade})
    
    if st.button("保存记录"):
        new_id = 1 if records_df.empty else records_df["RecordID"].max()+1
        new_record = pd.DataFrame([{
            "RecordID": new_id,
            "日期": date.strftime("%Y-%m-%d"),
            "国家": country,
            "城市": city,
            "场馆": gym,
            "笔记": note
        }])
        records_df = pd.concat([records_df, new_record], ignore_index=True)
        records_df.to_csv(RECORDS_FILE, index=False)
        
        new_types = pd.DataFrame([{"RecordID": new_id, **td} for td in type_details])
        types_df = pd.concat([types_df, new_types], ignore_index=True)
        types_df.to_csv(TYPES_FILE, index=False)
        
        st.success("✅ 记录保存成功！")

# ---------- 查看统计 ----------
elif menu == "查看统计":
    st.header("📊 统计图表")
    
    if not records_df.empty:
        records_df["日期"] = pd.to_datetime(records_df["日期"])
        records_df["Year"] = records_df["日期"].dt.year
        records_df["Month"] = records_df["日期"].dt.month
        records_df["Quarter"] = records_df["日期"].dt.quarter
        
        st.subheader("📅 时间范围选择")
        min_date = records_df["日期"].min()
        max_date = records_df["日期"].max()
        start_date, end_date = st.date_input("选择时间范围", [min_date, max_date])
        
        filtered = records_df[(records_df["日期"] >= pd.to_datetime(start_date)) &
                              (records_df["日期"] <= pd.to_datetime(end_date))]
        
        st.write(f"显示 {start_date} 到 {end_date} 的统计")
        
        range_stats = filtered.agg({
            "国家": pd.Series.nunique,
            "城市": pd.Series.nunique,
            "场馆": pd.Series.nunique,
            "RecordID": "count"
        }).rename({
            "国家":"国家数",
            "城市":"城市数",
            "场馆":"岩馆数",
            "RecordID":"攀爬天数"
        })
        st.write("📊 时间范围统计")
        st.dataframe(range_stats.to_frame().T)
        
        st.subheader("📈 图表面板")
        
        if not types_df.empty:
            types_filtered = types_df[types_df["RecordID"].isin(filtered["RecordID"])]
            
            # 类型完成路线数
            type_sum = types_filtered.groupby("攀岩类型")["完成路线数"].sum()
            fig, ax = plt.subplots()
            type_sum.plot(kind="bar", ax=ax, title="攀岩类型完成路线数")
            ax.set_ylabel("完成路线数")
            st.pyplot(fig)
            st.download_button("下载类型图表 PNG", fig_to_bytes(fig), "type_chart.png")
            
            # 岩馆攀爬天数
            gym_count = filtered.groupby(["场馆","国家"])["RecordID"].count()
            gym_count.index = [f"{g} ({c})" for g, c in gym_count.index]
            fig2, ax2 = plt.subplots(figsize=(8,4))
            gym_count.plot(kind="bar", ax=ax2, title="岩馆攀爬天数（按国家/城市）")
            ax2.set_ylabel("天数")
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig2)
            st.download_button("下载岩馆图表 PNG", fig_to_bytes(fig2), "gym_chart.png")
            
            # 季度趋势
            quarter_trend = filtered.groupby(["Year","Quarter"])["RecordID"].count()
            fig3, ax3 = plt.subplots()
            quarter_trend.plot(kind="line", marker="o", ax=ax3, title="季度攀爬天数趋势")
            ax3.set_ylabel("天数")
            st.pyplot(fig3)
            st.download_button("下载季度趋势 PNG", fig_to_bytes(fig3), "quarter_trend.png")
            
            # 年度累计
            year_trend = filtered.groupby("Year")["RecordID"].count()
            fig4, ax4 = plt.subplots()
            year_trend.plot(kind="bar", ax=ax4, title="年度累计攀爬天数")
            ax4.set_ylabel("天数")
            st.pyplot(fig4)
            st.download_button("下载年度累计 PNG", fig_to_bytes(fig4), "year_chart.png")
            
            # 最高等级统计图
            st.subheader("🏅 最高等级分布（按攀岩类型）")
            types_filtered_grade = types_filtered[types_filtered["最高等级"].notna() & (types_filtered["最高等级"]!="")]
            
            if not types_filtered_grade.empty:
                fig5, ax5 = plt.subplots(figsize=(8,4))
                sns.countplot(data=types_filtered_grade, x="最高等级", hue="攀岩类型", ax=ax5)
                ax5.set_title("最高等级分布（按攀岩类型）")
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig5)
                st.download_button("下载最高等级统计 PNG", fig_to_bytes(fig5), "grade_distribution.png")
            else:
                st.info("暂无最高等级数据可统计")
    else:
        st.info("暂无记录，先添加日志吧！")

# ---------- 导出数据 ----------
elif menu == "导出数据":
    st.header("💾 导出 CSV")
    st.download_button("下载记录表 CSV", records_df.to_csv(index=False).encode("utf-8"), "records.csv")
    st.download_button("下载类型明细 CSV", types_df.to_csv(index=False).encode("utf-8"), "types.csv")
