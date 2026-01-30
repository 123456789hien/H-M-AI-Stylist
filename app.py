import streamlit as st
import pandas as pd
import plotly.express as px
import gdown
import zipfile
import os
from PIL import Image

st.set_page_config(page_title="H&M AI Stylist Universe", layout="wide")

# --- CẤU HÌNH ID FILE TỪ GOOGLE DRIVE ---
FILES = {
    "articles": "1LBli1p1ee714ndmRC716SGWKBZkiiyzj",
    "customer": "1bLxYRUweEX4EJjfz3LFQqR5gVB4gtz9h",
    "validation": "11C9ZGG17VkVR9J5qr34WANEdHB8-MM9C",
    "embeddings": "1bs2LUhcdjeMAOlVYiuYHXL38H2r3XnDz",
    "images_zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
}

@st.cache_resource
def load_data_and_images():
    # Tạo thư mục data và images nếu chưa có
    if not os.path.exists('data'): os.makedirs('data')
    
    # Tải các file CSV
    for name, file_id in FILES.items():
        if name != "images_zip":
            path = f"data/{name}.csv"
            if not os.path.exists(path):
                gdown.download(f'https://drive.google.com/uc?id={file_id}', path, quiet=True)
    
    # Tải và giải nén ảnh (3GB - Quá trình này có thể mất vài phút lần đầu)
    if not os.path.exists('images'):
        st.info("📦 Đang tải kho ảnh 3GB từ Google Drive... Vui lòng đợi trong giây lát.")
        zip_path = "images.zip"
        gdown.download(f'https://drive.google.com/uc?id={FILES["images_zip"]}', zip_path, quiet=False)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall('images')
        os.remove(zip_path)
    
    return (pd.read_csv("data/articles.csv"), 
            pd.read_csv("data/customer.csv"), 
            pd.read_csv("data/embeddings.csv"),
            pd.read_csv("data/validation.csv"))

# Load dữ liệu
try:
    df_articles, df_customer, df_embeddings, df_val = load_data_and_images()
except Exception as e:
    st.error(f"Lỗi tải dữ liệu: {e}")
    st.stop()

# --- GIAO DIỆN ---
st.title("👗 H&M AI Stylist: The Emotion Universe")
st.markdown("---")

# Sidebar: Bộ lọc
st.sidebar.header("🔍 Bộ lọc Showroom")
selected_mood = st.sidebar.multiselect("Chọn phong cách (Mood):", df_articles['mood'].unique(), default=df_articles['mood'].unique()[:2])
min_hotness = st.sidebar.slider("Độ Hot tối thiểu (Pareto Score):", 0.0, 1.0, 0.5)

# Layout chính
tab1, tab2, tab3 = st.tabs(["🌌 Vũ trụ cảm xúc", "👤 Khách hàng & Gợi ý", "🛍️ Showroom"])

with tab1:
    st.subheader("Bản đồ định vị phong cách (t-SNE)")
    fig = px.scatter(df_embeddings, x='x', y='y', color='mood', 
                     hover_data=['article_id'],
                     title="Di chuột để xem ID sản phẩm",
                     color_discrete_sequence=px.colors.qualitative.Safe)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col_input, col_res = st.columns([1, 2])
    with col_input:
        c_id = st.text_input("Nhập Customer ID:")
        if c_id:
            # Tra cứu thông tin khách hàng
            c_info = df_customer[df_customer['customer_id'] == c_id]
            if not c_info.empty:
                st.success(f"Phân khúc: {c_info['segment'].values[0]}")
                st.write(f"Độ tuổi: {c_info['age'].values[0]}")
                
                # Kiểm chứng từ tập Test (Section 10)
                c_val = df_val[df_val['customer_id'] == c_id]
                if not c_val.empty:
                    st.warning(f"Gu thực tế (Test Set): {c_val['actual_purchased_mood'].values[0]}")
            else:
                st.error("Không tìm thấy ID khách hàng này.")

    with col_res:
        if c_id and not c_info.empty:
            st.subheader("Gợi ý từ AI Stylist")
            mood_pref = c_val['actual_purchased_mood'].values[0] if not c_val.empty else "Relaxed"
            recs = df_articles[(df_articles['mood'] == mood_pref) & (df_articles['hotness_score'] >= 0.7)].head(4)
            
            cols = st.columns(4)
            for i, (idx, row) in enumerate(recs.iterrows()):
                aid = str(row['article_id']).zfill(10)
                img_path = f"images/{aid}.jpg"
                if os.path.exists(img_path):
                    cols[i].image(Image.open(img_path), caption=f"Hotness: {row['hotness_score']:.2f}")

with tab3:
    st.subheader("Khám phá bộ sưu tập")
    display_items = df_articles[(df_articles['mood'].isin(selected_mood)) & (df_articles['hotness_score'] >= min_hotness)].head(20)
    
    grid = st.columns(5)
    for i, (idx, row) in enumerate(display_items.iterrows()):
        aid = str(row['article_id']).zfill(10)
        img_path = f"images/{aid}.jpg"
        if os.path.exists(img_path):
            grid[i % 5].image(Image.open(img_path), use_column_width=True)
            grid[i % 5].caption(f"ID: {aid} | {row['mood']}")
