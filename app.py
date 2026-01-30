import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import zipfile
import os

# --- 1. CẤU HÌNH HỆ THỐNG ---
# Thiết lập trang để triệt tiêu các cảnh báo về giao diện cũ
st.set_page_config(page_title="H&M Emotion Intelligence", layout="wide")

# --- 2. HÀM XỬ LÝ DỮ LIỆU (Tối ưu RAM cho file 3GB) ---
@st.cache_resource
def download_and_unzip():
    """Tải và giải nén: Chỉ thực hiện một lần duy nhất để tránh treo máy"""
    if not os.path.exists('data'): 
        os.makedirs('data')
    
    # Danh sách file từ Google Drive của bạn
    files = {
        "data/article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "data/visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
        "images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }
    
    for path, fid in files.items():
        if not os.path.exists(path):
            with st.spinner(f"Đang tải {path}..."):
                gdown.download(f'https://drive.google.com/uc?id={fid}', path, quiet=True)
            
    # Giải nén ảnh: Kiểm tra nếu chưa có thư mục images hoặc thư mục rỗng mới giải nén
    if not os.path.exists('images') or len(os.listdir('images')) < 100:
        if not os.path.exists('images'): 
            os.makedirs('images')
        with st.spinner("Đang giải nén kho ảnh 3GB... (Vui lòng đợi 1-2 phút)"):
            try:
                with zipfile.ZipFile("images.zip", 'r') as z:
                    z.extractall('images')
            except Exception as e:
                st.error(f"Lỗi khi giải nén: {e}")

@st.cache_data
def load_processed_data():
    """Đọc dữ liệu và chuẩn hóa ID sản phẩm"""
    df_a = pd.read_csv("data/article_master_web.csv")
    df_e = pd.read_csv("data/visual_dna_embeddings.csv")
    
    # Đảm bảo article_id luôn có 10 chữ số (thêm số 0 ở đầu nếu thiếu)
    df_a['article_id'] = df_a['article_id'].astype(str).str.zfill(10)
    df_e['article_id'] = df_e['article_id'].astype(str).str.zfill(10)
    
    return df_a, df_e

# Thực thi nạp dữ liệu
with st.spinner("🚀 Hệ thống đang khởi động dữ liệu chiến lược..."):
    download_and_unzip()
    df_art, df_emb = load_processed_data()

# --- 3. GIAO DIỆN CHÍNH (Sử dụng chuẩn hiển thị mới nhất 2026) ---
st.title("🏛 H&M Emotion Strategic Hub")

# Menu điều hướng bằng Tabs
tab1, tab2, tab3 = st.tabs(["📊 BI Dashboard", "🔥 Top Performance", "🌌 AI Visual Map"])

# --- TAB 1: DASHBOARD TỔNG QUAN ---
with tab1:
    m1, m2, m3 = st.columns(3)
    m1.metric("Tổng số mặt hàng", f"{len(df_art):,}")
    m2.metric("Mood chủ đạo", df_art['mood'].mode()[0])
    m3.metric("Giá trung bình", f"${df_art['price'].mean():.4f}")
    
    st.divider()
    
    col_a, col_b = st.columns([2, 3])
    with col_a:
        st.subheader("🎯 Brand DNA Alignment")
        target = {'Confidence': 0.35, 'Relaxed': 0.25, 'Energetic': 0.15, 'Affectionate': 0.15, 'Introspective': 0.10}
        actual = df_art['mood'].value_counts(normalize=True).to_dict()
        categories = list(target.keys())
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=[target.get(c,0) for c in categories], theta=categories, fill='toself', name='Mục tiêu'))
        fig_radar.add_trace(go.Scatterpolar(r=[actual.get(c,0) for c in categories], theta=categories, fill='toself', name='Thực tế'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 0.5])), height=400)
        st.plotly_chart(fig_radar, use_container_width=True)

    with col_b:
        st.subheader("💰 Pricing Distribution per Mood")
        fig_box = px.box(df_art, x="mood", y="price", color="mood", points="outliers")
        st.plotly_chart(fig_box, use_container_width=True)

# --- TAB 2: TOP PERFORMANCE (Hiển thị ảnh an toàn) ---
with tab2:
    st.subheader("Top 12 Sản phẩm Hot nhất (Phân tích Pareto)")
    
    # Lọc và lấy top 12 để tránh quá tải trình duyệt
    top_df = df_art.sort_values('hotness_score', ascending=False).head(12)
    
    grid = st.columns(4)
    for idx, (_, row) in enumerate(top_df.iterrows()):
        with grid[idx % 4]:
            img_file = f"images/{row['article_id']}.jpg"
            if os.path.exists(img_file):
                # use_container_width=True là chuẩn mới nhất để không bị lỗi Logs
                st.image(img_file, caption=row['prod_name'], use_container_width=True)
            else:
                st.warning(f"Thiếu ảnh: {row['article_id']}")
            
            st.caption(f"Mood: {row['mood']} | Score: {row['hotness_score']:.2f}")

# --- TAB 3: VISUAL DNA CLUSTERS ---
with tab3:
    st.subheader("🌌 Không gian Visual DNA (t-SNE)")
    st.info("Các điểm gần nhau đại diện cho các sản phẩm có thiết kế tương đồng.")
    
    fig_map = px.scatter(
        df_emb, x='x', y='y', color='mood',
        hover_name='article_id',
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    st.plotly_chart(fig_map, use_container_width=True)

# Sidebar bổ sung
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=80)
st.sidebar.markdown("---")
st.sidebar.success("Dữ liệu đã sẵn sàng!")
st.sidebar.caption("Phiên bản BI 2.6.1 | Đã tối ưu RAM")
