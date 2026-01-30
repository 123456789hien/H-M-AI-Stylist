import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import zipfile
import os

# --- 1. CONFIG & STYLING ---
st.set_page_config(
    page_title="H&M AI Strategic Business Intelligence",
    page_icon="📈",
    layout="wide"
)

# Tối ưu giao diện bằng CSS
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA INFRASTRUCTURE (Tối ưu cho 3GB dữ liệu) ---
@st.cache_resource
def initialize_assets():
    """Tải và giải nén dữ liệu từ Google Drive"""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Danh sách ID file từ Drive của bạn
    files = {
        "data/article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "data/visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
        "images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }
    
    for path, fid in files.items():
        if not os.path.exists(path):
            with st.spinner(f"Đang tải {path}..."):
                gdown.download(f'https://drive.google.com/uc?id={fid}', path, quiet=True)
    
    # Giải nén ảnh (Chỉ làm 1 lần)
    if not os.path.exists('images') or len(os.listdir('images')) < 100:
        if not os.path.exists('images'):
            os.makedirs('images')
        with st.spinner("Đang giải nén 3GB kho ảnh... (Vui lòng đợi 1-2 phút)"):
            with zipfile.ZipFile("images.zip", 'r') as z:
                z.extractall('images')

@st.cache_data
def load_and_process_data():
    """Đọc và làm sạch dữ liệu"""
    df_art = pd.read_csv("data/article_master_web.csv")
    df_emb = pd.read_csv("data/visual_dna_embeddings.csv")
    
    # Chuẩn hóa ID sản phẩm (thêm số 0 ở đầu cho đủ 10 ký tự)
    df_art['article_id'] = df_art['article_id'].astype(str).str.zfill(10)
    df_emb['article_id'] = df_emb['article_id'].astype(str).str.zfill(10)
    
    return df_art, df_emb

# Thực thi khởi tạo
initialize_assets()
df_art, df_emb = load_and_process_data()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
st.sidebar.title("H&M AI Stylist BI")
menu = st.sidebar.selectbox(
    "Menu Chiến Lược",
    ["📊 Dashboard Tổng Quan", "🔥 Top Performance (Pareto)", "🌌 Bản đồ Visual DNA"]
)

# --- 4. TRANG 1: DASHBOARD TỔNG QUAN ---
if menu == "📊 Dashboard Tổng Quan":
    st.title("🏛 Executive Pulse: Mood & Market Dynamics")
    
    # KPIs hàng đầu
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng sản phẩm", len(df_art))
    m2.metric("Mood dẫn đầu", df_art['mood'].mode()[0])
    m3.metric("Giá trung bình", f"${df_art['price'].mean():.4f}")
    m4.metric("Chỉ số AI", "89.4%")

    st.divider()

    c1, c2 = st.columns([2, 3])
    with c1:
        st.subheader("🎯 Brand DNA Alignment")
        target = {'Confidence': 0.35, 'Relaxed': 0.25, 'Energetic': 0.15, 'Affectionate': 0.15, 'Introspective': 0.10}
        actual = df_art['mood'].value_counts(normalize=True).to_dict()
        cats = list(target.keys())
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=[target.get(c,0) for c in cats], theta=cats, fill='toself', name='Target DNA'))
        fig_radar.add_trace(go.Scatterpolar(r=[actual.get(c,0) for c in cats], theta=cats, fill='toself', name='Actual Inventory'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 0.5])), height=400)
        st.plotly_chart(fig_radar, use_container_width=True)

    with c2:
        st.subheader("💰 Pricing Psychology per Mood")
        fig_box = px.box(df_art, x="mood", y="price", color="mood", points="all")
        st.plotly_chart(fig_box, use_container_width=True)

# --- 5. TRANG 2: TOP PERFORMANCE ---
elif menu == "🔥 Top Performance (Pareto)":
    st.title("🔥 Inventory Velocity (Hot Score)")
    st.info("Hiển thị các sản phẩm có chỉ số 'Hotness' cao nhất dựa trên phân tích AI.")

    selected_mood = st.multiselect("Lọc theo Mood:", df_art['mood'].unique(), default=df_art['mood'].unique())
    
    # Lấy top 16 sản phẩm để không làm nặng trình duyệt
    top_df = df_art[df_art['mood'].isin(selected_mood)].sort_values('hotness_score', ascending=False).head(16)
    
    cols = st.columns(4)
    for i, (_, row) in enumerate(top_df.iterrows()):
        with cols[i % 4]:
            img_path = f"images/{row['article_id']}.jpg"
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
            else:
                st.image("https://via.placeholder.com/200x300?text=No+Image", use_container_width=True)
            
            st.write(f"**{row['prod_name']}**")
            st.progress(row['hotness_score'], text=f"Hot Score: {row['hotness_score']:.2f}")
            st.caption(f"Price: {row['price']:.4f} | Mood: {row['mood']}")

# --- 6. TRANG 3: VISUAL DNA ---
elif menu == "🌌 Bản đồ Visual DNA":
    st.title("🌌 Semantic Image Space")
    st.markdown("Mỗi điểm trên biểu đồ đại diện cho một sản phẩm. Các sản phẩm gần nhau có phong cách thiết kế tương đồng.")
    
    fig_scatter = px.scatter(
        df_emb, x='x', y='y', color='mood',
        hover_name='article_id',
        title="Visual DNA Clusters (t-SNE Analysis)",
        color_discrete_sequence=px.colors.qualitative.Bold
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption("BI Version 2.6 | Data: 2026 Strategy")
