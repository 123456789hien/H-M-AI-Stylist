import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown, zipfile, os
from PIL import Image

st.set_page_config(page_title="H&M Enterprise Strategic Dashboard", layout="wide")

# --- DATA LOADING (GIỮ NGUYÊN LOGIC GDOWN CỦA BẠN) ---
@st.cache_resource
def load_all_data():
    # (Đoạn này giữ nguyên các ID file của bạn để tải về)
    # ... code gdown ...
    return pd.read_csv("data/articles.csv"), pd.read_csv("data/customer.csv"), pd.read_csv("data/embeddings.csv"), pd.read_csv("data/validation.csv")

df_articles, df_customer, df_embeddings, df_val = load_all_data()

# --- SIDEBAR: ADVANCED FILTERS (DÀNH CHO QUẢN LÝ) ---
st.sidebar.title("🛠️ Business Filters")
with st.sidebar:
    st.info("Sử dụng các bộ lọc dưới đây để phân tích thị trường.")
    
    # 1. Phân loại theo Giới tính/Khu vực
    sections = st.multiselect("Phân khúc thị trường:", df_articles['section_name'].unique(), default=df_articles['section_name'].unique()[:3])
    
    # 2. Phân loại theo Loại sản phẩm
    groups = st.multiselect("Nhóm sản phẩm:", df_articles['product_group_name'].unique(), default=df_articles['product_group_name'].unique()[:3])
    
    # 3. Lọc theo giá
    price_range = st.slider("Khoảng giá (Normalized):", 
                             float(df_articles['price'].min()), 
                             float(df_articles['price'].max()), 
                             (0.0, 0.1))

# --- DATA PROCESSING CHO FILTERS ---
mask = (df_articles['section_name'].isin(sections)) & \
       (df_articles['product_group_name'].isin(groups)) & \
       (df_articles['price'].between(price_range[0], price_range[1]))
filtered_df = df_articles[mask]

# --- MAIN INTERFACE ---
tabs = st.tabs(["📊 Executive Overview", "🎯 Customer Insights", "📦 Inventory & Showroom"])

# --- TAB 1: EXECUTIVE OVERVIEW (DÀNH CHO GIÁM ĐỐC CHIẾN LƯỢC) ---
with tabs[0]:
    st.header("Thống kê Chiến lược Toàn cầu")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Tổng mã hàng (Sample)", f"{len(df_articles):,}")
    kpi2.metric("Mood phổ biến nhất", df_articles['mood'].mode()[0])
    kpi3.metric("Khách hàng Gold", f"{len(df_customer[df_customer['segment'] == 'Gold']):,}")
    kpi4.metric("Pareto Efficient Items", f"{len(df_articles[df_articles['hotness_score'] > 0.8]):,}")

    c1, c2 = st.columns(2)
    with c1:
        # Biểu đồ tỷ trọng Mood
        fig_mood = px.pie(filtered_df, names='mood', title="Cơ cấu Phong cách (Mood) theo Phân khúc đã chọn", hole=0.4)
        st.plotly_chart(fig_mood, use_container_width=True)
    with c2:
        # Biểu đồ phân bổ giá theo Mood
        fig_price = px.box(filtered_df, x='mood', y='price', color='mood', title="Phân bổ Giá theo Mood")
        st.plotly_chart(fig_price, use_container_width=True)

# --- TAB 2: CUSTOMER INSIGHTS (DÀNH CHO CRM/MARKETING) ---
with tabs[1]:
    st.header("Phân tích Hành vi Khách hàng")
    
    col_table, col_detail = st.columns([1.5, 1])
    
    with col_table:
        st.subheader("Top 100 Khách hàng Tiềm năng")
        # Hiển thị bảng danh sách khách hàng để người dùng chọn thay vì tự gõ ID
        st.dataframe(df_customer[['customer_id', 'segment', 'avg_spending', 'purchase_count']].head(100), use_container_width=True, height=400)
    
    with col_detail:
        customer_id_input = st.text_input("Dán Customer ID vào đây để xem chi tiết Profile:")
        if customer_id_input:
            cust_data = df_customer[df_customer['customer_id'] == customer_id_input]
            if not cust_data.empty:
                st.markdown(f"### Profile: {cust_data['segment'].values[0]}")
                st.write(f"**Tuổi:** {cust_data['age'].values[0]}")
                st.write(f"**Số lần mua hàng:** {cust_data['purchase_count'].values[0]}")
                
                # Validation từ tập Test
                val_data = df_val[df_val['customer_id'] == customer_id_input]
                if not val_data.empty:
                    actual_mood = val_data['actual_purchased_mood'].values[0]
                    st.success(f"Dự đoán phong cách phù hợp nhất: **{actual_mood}**")
                    
                    # Gợi ý sản phẩm dựa trên Mood dự đoán
                    st.write("---")
                    st.write("Sản phẩm gợi ý tối ưu kho (High Pareto Score):")
                    recs = df_articles[(df_articles['mood'] == actual_mood) & (df_articles['hotness_score'] > 0.7)].head(3)
                    r_cols = st.columns(3)
                    for idx, r in enumerate(recs.iterrows()):
                        aid = str(r[1]['article_id']).zfill(10)
                        if os.path.exists(f"images/{aid}.jpg"):
                            r_cols[idx].image(f"images/{aid}.jpg", caption=f"Score: {r[1]['hotness_score']:.2f}")

# --- TAB 3: INVENTORY & SHOWROOM (DÀNH CHO QUẢN LÝ KHO) ---
with tabs[2]:
    st.header("Quản lý Sản phẩm & Showroom")
    
    # Grid hiển thị sản phẩm chuyên nghiệp
    n_cols = 4
    rows = filtered_df.head(24).reset_index()
    
    for i in range(0, len(rows), n_cols):
        cols = st.columns(n_cols)
        for j in range(n_cols):
            if i + j < len(rows):
                item = rows.iloc[i + j]
                aid = str(item['article_id']).zfill(10)
                with cols[j]:
                    if os.path.exists(f"images/{aid}.jpg"):
                        st.image(f"images/{aid}.jpg", use_container_width=True)
                    st.markdown(f"**ID:** `{aid}`")
                    st.markdown(f"**Mood:** {item['mood']}")
                    st.markdown(f"**Giá:** `${item['price']:.4f}`")
                    st.progress(item['hotness_score'], text=f"Hotness: {item['hotness_score']:.2f}")
                    with st.expander("Xem mô tả chi tiết"):
                        st.write(item['detail_desc'])
