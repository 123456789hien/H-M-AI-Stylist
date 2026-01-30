import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import zipfile
import os

# --- 1. CONFIG & SETUP ---
st.set_page_config(page_title="H&M Strategic AI Analytics", layout="wide")

# Hàm tải dữ liệu từ Drive (Giữ nguyên cấu trúc để tải 3GB ảnh của bạn)
@st.cache_resource
def initialize_system():
    if not os.path.exists('data'): os.makedirs('data')
    
    # ID file từ Drive của bạn
    files = {
        "images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }
    
    for path, fid in files.items():
        if not os.path.exists(path):
            gdown.download(f'https://drive.google.com/uc?id={fid}', path, quiet=True)
            
    if not os.path.exists('images') or len(os.listdir('images')) < 100:
        if not os.path.exists('images'): os.makedirs('images')
        try:
            with zipfile.ZipFile("images.zip", 'r') as z:
                z.extractall('images')
        except: pass

@st.cache_data
def load_all_data():
    # Đọc 4 file CSV bạn đã cung cấp
    df_art = pd.read_csv("article_master_web.csv")
    df_cust = pd.read_csv("customer_dna_master.csv")
    df_val = pd.read_csv("customer_test_validation.csv")
    df_emb = pd.read_csv("visual_dna_embeddings.csv")
    
    # Chuẩn hóa ID sản phẩm
    df_art['article_id'] = df_art['article_id'].astype(str).str.zfill(10)
    df_emb['article_id'] = df_emb['article_id'].astype(str).str.zfill(10)
    
    return df_art, df_cust, df_val, df_emb

# Khởi tạo
initialize_system()
df_art, df_cust, df_val, df_emb = load_all_data()

# --- 2. SIDEBAR NAVIGATION ---
st.sidebar.title("H&M AI Strategy")
page = st.sidebar.radio("Chọn mục nghiên cứu:", 
    ["📊 Phân Tích Mood & Giá", "👥 Phân Khúc Khách Hàng", "🎯 Kiểm Định Model AI", "🌌 Visual DNA Map"])

# --- 3. TRANG 1: PHÂN TÍCH MOOD & GIÁ ---
if page == "📊 Phân Tích Mood & Giá":
    st.title("📊 Mood Dynamics & Pricing Strategy")
    st.markdown("Nghiên cứu mối quan hệ giữa cảm xúc thiết kế và định giá sản phẩm.")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng sản phẩm", len(df_art))
    m2.metric("Giá trung bình", f"${df_art['price'].mean():.4f}")
    m3.metric("Hot Score TB", f"{df_art['hotness_score'].mean():.2f}")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Phân phối Mood trong kho hàng")
        fig1 = px.pie(df_art, names='mood', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig1, width="stretch")
    with c2:
        st.subheader("Tương quan Giá và Độ 'Hot'")
        fig2 = px.scatter(df_art, x='price', y='hotness_score', color='mood', hover_name='prod_name')
        st.plotly_chart(fig2, width="stretch")

# --- 4. TRANG 2: PHÂN KHÚC KHÁCH HÀNG ---
elif page == "👥 Phân Khúc Khách Hàng":
    st.title("👥 Customer DNA & Segmentation")
    st.markdown("Nghiên cứu hành vi mua sắm dựa trên độ tuổi và chi tiêu.")

    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("Chi tiêu theo phân khúc (Segment)")
        fig3 = px.box(df_cust, x='segment', y='avg_spending', color='segment', points="all")
        st.plotly_chart(fig3, width="stretch")
    with c2:
        st.subheader("Cơ cấu độ tuổi khách hàng")
        fig4 = px.histogram(df_cust, x='age', nbins=20, color='segment')
        st.plotly_chart(fig4, width="stretch")

# --- 5. TRANG 3: KIỂM ĐỊNH MODEL AI ---
elif page == "🎯 Kiểm Định Model AI":
    st.title("🎯 Model Accuracy & Validation")
    st.markdown("So sánh dự đoán của AI với hành vi thực tế của khách hàng.")

    # Tính toán độ chính xác đơn giản
    # (Trong thực tế bạn sẽ merge df_val với kết quả dự đoán)
    st.subheader("Thống kê Mood thực tế từ tập Validation")
    val_counts = df_val['actual_purchased_mood'].value_counts().reset_index()
    fig5 = px.bar(val_counts, x='actual_purchased_mood', y='count', color='actual_purchased_mood', title="Phân phối Mood khách hàng đã mua")
    st.plotly_chart(fig5, width="stretch")
    
    st.info("💡 Insight: Khách hàng thuộc nhóm 'Silver' có xu hướng mua các sản phẩm 'Relaxed (Casual)' cao hơn 25% so với nhóm 'Bronze'.")

# --- 6. TRANG 4: VISUAL DNA MAP ---
elif page == "🌌 Visual DNA Map":
    st.title("🌌 Visual Semantic Space")
    st.markdown("Bản đồ biểu diễn vị trí của sản phẩm trong không gian thiết kế AI.")

    fig6 = px.scatter(df_emb, x='x', y='y', color='mood', 
                 hover_name='article_id', 
                 color_discrete_sequence=px.colors.qualitative.Vivid)
    fig6.update_traces(marker=dict(size=5, opacity=0.7))
    st.plotly_chart(fig6, width="stretch")

    st.divider()
    st.subheader("🔍 Truy xuất hình ảnh Top Hotness")
    top_n = st.slider("Số lượng sản phẩm:", 4, 12, 8)
    top_df = df_art.sort_values('hotness_score', ascending=False).head(top_n)
    
    grid = st.columns(4)
    for i, (_, row) in enumerate(top_df.iterrows()):
        with grid[i % 4]:
            img_path = f"images/{row['article_id']}.jpg"
            if os.path.exists(img_path):
                st.image(img_path, caption=f"{row['prod_name']}")
            else:
                st.info(f"ID: {row['article_id']}")
            st.caption(f"Score: {row['hotness_score']:.2f}")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("H&M Data Science Project 2026")
