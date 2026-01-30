import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import zipfile
import os

# --- 1. CẤU HÌNH HỆ THỐNG (Cập nhật chuẩn 2026) ---
st.set_page_config(page_title="H&M Emotion Intelligence", layout="wide")

# --- 2. HÀM XỬ LÝ DỮ LIỆU ---
@st.cache_resource
def download_and_unzip():
    if not os.path.exists('data'): os.makedirs('data')
    
    files = {
        "data/article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "data/visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
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
        except Exception as e:
            st.error(f"Lỗi giải nén: {e}")

@st.cache_data
def load_processed_data():
    df_a = pd.read_csv("data/article_master_web.csv")
    df_e = pd.read_csv("data/visual_dna_embeddings.csv")
    
    # Chuẩn hóa ID
    df_a['article_id'] = df_a['article_id'].astype(str).str.zfill(10)
    df_e['article_id'] = df_e['article_id'].astype(str).str.zfill(10)
    
    # SỬA LỖI: Kiểm tra cột 'price'. Nếu không có, gán giá trị mặc định để tránh lỗi ValueError
    if 'price' not in df_a.columns:
        # Giả định giá bằng 0.01 (hoặc bạn thay bằng tên cột giá đúng trong file của bạn)
        df_a['price'] = 0.0100 
        
    return df_a, df_e

# Khởi chạy nạp dữ liệu
with st.spinner("🚀 Đang khởi động hệ thống..."):
    download_and_unzip()
    df_art, df_emb = load_processed_data()

# --- 3. GIAO DIỆN CHÍNH ---
st.title("🏛 H&M Strategic AI Dashboard")

tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "🔥 Top Items", "🌌 Visual DNA"])

# --- TAB 1: DASHBOARD ---
with tab1:
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng sản phẩm", f"{len(df_art):,}")
    m2.metric("Mood phổ biến", df_art['mood'].mode()[0])
    m3.metric("Giá TB", f"${df_art['price'].mean():.4f}")
    
    st.divider()
    
    c1, c2 = st.columns([2, 3])
    with c1:
        st.subheader("🎯 DNA Alignment")
        target = {'Confidence': 0.35, 'Relaxed': 0.25, 'Energetic': 0.15, 'Affectionate': 0.15, 'Introspective': 0.10}
        actual = df_art['mood'].value_counts(normalize=True).to_dict()
        cats = list(target.keys())
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=[target.get(c,0) for c in cats], theta=cats, fill='toself', name='Target'))
        fig_radar.add_trace(go.Scatterpolar(r=[actual.get(c,0) for c in cats], theta=cats, fill='toself', name='Actual'))
        fig_radar.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_radar, width="stretch")

    with c2:
        st.subheader("💰 Price Analysis")
        # Vẽ biểu đồ với cột price đã được kiểm tra an toàn
        fig_box = px.box(df_art, x="mood", y="price", color="mood")
        st.plotly_chart(fig_box, width="stretch")

# --- TAB 2: TOP PERFORMANCE ---
with tab2:
    st.subheader("🔥 Top Hotness Score (Pareto)")
    # Sử dụng cột 'hotness_score' chính xác từ lỗi của bạn
    top_items = df_art.sort_values('hotness_score', ascending=False).head(12)
    
    cols = st.columns(4)
    for idx, (_, row) in enumerate(top_items.iterrows()):
        with cols[idx % 4]:
            path = f"images/{row['article_id']}.jpg"
            if os.path.exists(path):
                st.image(path, use_container_width=True)
            else:
                st.info(f"ID: {row['article_id']}")
            st.caption(f"{row['prod_name'][:20]}... | Score: {row['hotness_score']:.2f}")

# --- TAB 3: VISUAL DNA ---
with tab3:
    st.subheader("🌌 Semantic Space Visualization")
    fig_map = px.scatter(
        df_emb, x='x', y='y', color='mood',
        hover_name='article_id',
        template="plotly_dark"
    )
    st.plotly_chart(fig_map, width="stretch")

st.sidebar.caption("Version 2.6.2 | Fix ValueError & Width")
