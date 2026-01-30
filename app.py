import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import zipfile
import os
from PIL import Image

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="H&M Emotion-Driven Strategic Dashboard", layout="wide", page_icon="📈")

# --- QUẢN LÝ DỮ LIỆU TỪ GOOGLE DRIVE ---
FILES = {
    "articles": "1LBli1p1ee714ndmRC716SGWKBZkiiyzj",
    "customer": "1bLxYRUweEX4EJjfz3LFQqR5gVB4gtz9h",
    "validation": "11C9ZGG17VkVR9J5qr34WANEdHB8-MM9C",
    "embeddings": "1bs2LUhcdjeMAOlVYiuYHXL38H2r3XnDz",
    "images_zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
}

@st.cache_resource
def load_and_verify_data():
    if not os.path.exists('data'): os.makedirs('data')
    for name, f_id in FILES.items():
        path = f"data/{name}.csv" if name != "images_zip" else "images.zip"
        if not os.path.exists(path if name != "images_zip" else "images"):
            gdown.download(f'https://drive.google.com/uc?id={f_id}', path, quiet=True)
            if name == "images_zip":
                with zipfile.ZipFile(path, 'r') as z: z.extractall('images')
                os.remove(path)
    
    # Đọc dữ liệu
    df_art = pd.read_csv("data/articles.csv")
    df_cust = pd.read_csv("data/customer.csv")
    df_emb = pd.read_csv("data/embeddings.csv")
    df_val = pd.read_csv("data/validation.csv")
    
    # Kiểm tra các cột bắt buộc cho BI
    required_cols = ['price', 'hotness_score', 'mood', 'prod_name', 'section_name', 'product_group_name']
    missing = [c for c in required_cols if c not in df_art.columns]
    if missing:
        st.error(f"❌ File articles.csv thiếu các cột chiến lược: {missing}. Hãy kiểm tra lại Section 6 trên Kaggle!")
        st.stop()
        
    return df_art, df_cust, df_emb, df_val

df_art, df_cust, df_emb, df_val = load_and_verify_data()

# --- SIDEBAR: ĐIỀU HÀNH CHIẾN LƯỢC ---
st.sidebar.title("🏢 Management Panel")
menu = st.sidebar.selectbox("Chọn tầng phân tích:", 
    ["1. Emotion Strategy (Dashboard)", "2. Customer DNA Analytics", "3. Visual Inventory Explorer"])

# --- PHẦN 1: CHIẾN LƯỢC CẢM XÚC (EMOTION STRATEGY) ---
if menu == "1. Emotion Strategy (Dashboard)":
    st.title("📊 H&M Global Emotion Strategy Dashboard")
    st.markdown("Dashboard này phân tích mối quan hệ giữa **Cảm xúc khách hàng** và **Hiệu quả kinh doanh**.")

    # KPI Metrics
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Tổng mã hàng", f"{len(df_art):,}")
    kpi2.metric("Mood Chủ đạo", df_art['mood'].mode()[0])
    kpi3.metric("Giá TB ($)", f"{df_art['price'].mean():.4f}")
    kpi4.metric("Độ Hot TB", f"{df_art['hotness_score'].mean():.2f}")

    st.divider()

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("🌋 Bản đồ Mật độ Cảm xúc theo Ngành hàng")
        # Phân tích xem Emotions phân bổ thế nào trong các Section (Nam, Nữ, Trẻ em...)
        fig_sun = px.sunburst(df_art, path=['section_name', 'mood'], values='hotness_score',
                              color='hotness_score', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_sun, use_container_width=True)

    with col_b:
        st.subheader("💰 Tương quan Giá & Cảm xúc")
        # Doanh nghiệp cần biết Mood nào mang lại giá trị cao nhất
        fig_box = px.box(df_art, x="mood", y="price", color="mood", title="Biên độ giá theo từng Cung bậc Cảm xúc")
        st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("🚀 Pareto Analysis: Hotness vs. Price")
    fig_scatter = px.scatter(df_art, x="price", y="hotness_score", color="mood",
                             size="hotness_score", hover_name="prod_name",
                             template="plotly_white")
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- PHẦN 2: PHÂN TÍCH KHÁCH HÀNG (CUSTOMER DNA) ---
elif menu == "2. Customer DNA Analytics":
    st.title("🎯 Customer Psychographic DNA")
    
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.subheader("Phân khúc Khách hàng")
        fig_pie = px.pie(df_cust, names='segment', hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_r:
        st.subheader("Tra cứu DNA Khách hàng")
        selected_id = st.selectbox("Chọn ID Khách hàng (Top 500):", df_cust['customer_id'].head(500))
        
        c_data = df_cust[df_cust['customer_id'] == selected_id].iloc[0]
        v_data = df_val[df_val['customer_id'] == selected_id]
        
        c_col1, c_col2 = st.columns(2)
        c_col1.write(f"**Hạng:** {c_data['segment']}")
        c_col1.write(f"**Số đơn:** {c_data['purchase_count']}")
        
        if not v_data.empty:
            actual_mood = v_data['actual_purchased_mood'].values[0]
            c_col2.success(f"**Mood yêu thích:** {actual_mood}")
            
            # Gợi ý sản phẩm
            st.write("---")
            st.write("🎁 **Gợi ý tối ưu dựa trên DNA:**")
            recs = df_art[df_art['mood'] == actual_mood].sort_values('hotness_score', ascending=False).head(4)
            r_cols = st.columns(4)
            for i, r in enumerate(recs.iterrows()):
                aid = str(r[1]['article_id']).zfill(10)
                if os.path.exists(f"images/{aid}.jpg"):
                    r_cols[i].image(f"images/{aid}.jpg", caption=f"Hotness: {r[1]['hotness_score']:.2f}")

# --- PHẦN 3: QUẢN LÝ KHO (INVENTORY EXPLORER) ---
elif menu == "3. Visual Inventory Explorer":
    st.title("🏬 Visual Merchandising & Inventory")
    
    # Filters
    f_sec = st.multiselect("Lọc theo Section:", df_art['section_name'].unique())
    f_mood = st.multiselect("Lọc theo Mood:", df_art['mood'].unique())
    
    query = df_art.copy()
    if f_sec: query = query[query['section_name'].isin(f_sec)]
    if f_mood: query = query[query['mood'].isin(f_mood)]
    
    st.write(f"Tìm thấy **{len(query)}** sản phẩm.")
    
    # Grid hiển thị
    rows = st.columns(4)
    for i, r in enumerate(query.head(20).iterrows()):
        with rows[i % 4]:
            aid = str(r[1]['article_id']).zfill(10)
            if os.path.exists(f"images/{aid}.jpg"):
                st.image(f"images/{aid}.jpg", use_container_width=True)
            st.caption(f"**{r[1]['prod_name']}**")
            st.write(f"Price: `{r[1]['price']:.4f}` | Mood: {r[1]['mood']}")
            st.progress(r[1]['hotness_score'])
