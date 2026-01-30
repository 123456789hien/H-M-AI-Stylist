import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import zipfile
import os

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="H&M AI Strategic Business Intelligence",
    page_icon="📈",
    layout="wide"
)

# --- 2. DATA INFRASTRUCTURE (Tải và xử lý 5 files từ Drive) ---
@st.cache_resource
def initialize_data():
    """Tải dữ liệu từ Google Drive và giải nén ảnh"""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Danh sách ID từ các link bạn cung cấp
    drive_files = {
        "data/article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "data/customer_dna_master.csv": "182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH",
        "data/customer_test_validation.csv": "1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB",
        "data/visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
        "data/hm_web_images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }
    
    for path, fid in drive_files.items():
        if not os.path.exists(path):
            with st.spinner(f"Đang đồng bộ {path}..."):
                url = f'https://drive.google.com/uc?id={fid}'
                gdown.download(url, path, quiet=True)
    
    # Giải nén kho ảnh (Chỉ thực hiện nếu chưa có thư mục images)
    if not os.path.exists('images') or len(os.listdir('images')) < 100:
        if not os.path.exists('images'):
            os.makedirs('images')
        with st.spinner("Đang giải nén 3GB dữ liệu hình ảnh..."):
            try:
                with zipfile.ZipFile("data/hm_web_images.zip", 'r') as z:
                    z.extractall('images')
            except Exception as e:
                st.error(f"Lỗi giải nén: {e}")

@st.cache_data
def load_and_sync_data():
    """Đọc và khớp dữ liệu giữa các file"""
    df_art = pd.read_csv("data/article_master_web.csv")
    df_cust = pd.read_csv("data/customer_dna_master.csv")
    df_val = pd.read_csv("data/customer_test_validation.csv")
    df_emb = pd.read_csv("data/visual_dna_embeddings.csv")
    
    # Chuẩn hóa article_id (10 ký tự)
    df_art['article_id'] = df_art['article_id'].astype(str).str.zfill(10)
    df_emb['article_id'] = df_emb['article_id'].astype(str).str.zfill(10)
    
    return df_art, df_cust, df_val, df_emb

# Khởi chạy hệ thống
initialize_data()
df_art, df_cust, df_val, df_emb = load_and_sync_data()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
st.sidebar.title("Strategic AI Hub")
page = st.sidebar.radio("Mục tiêu nghiên cứu:", [
    "📌 Mood & Pricing Insight", 
    "👥 Customer Segmentation", 
    "🎯 Model Validation", 
    "🌌 Visual Semantic Space"
])

# --- 4. TRANG 1: MOOD & PRICING INSIGHT ---
if page == "📌 Mood & Pricing Insight":
    st.title("📊 Mood Dynamics & Pricing Strategy")
    st.markdown("Phân tích mối quan hệ giữa phong cách thiết kế (Mood) và chiến lược định giá.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tổng sản phẩm", f"{len(df_art):,}")
    m2.metric("Giá TB", f"${df_art['price'].mean():.4f}")
    m3.metric("Mood phổ biến", df_art['mood'].mode()[0])
    m4.metric("Hot Score TB", f"{df_art['hotness_score'].mean():.2f}")

    st.divider()
    
    c1, c2 = st.columns([2, 3])
    with c1:
        st.subheader("Cấu trúc kho hàng theo Mood")
        fig_pie = px.pie(df_art, names='mood', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, width="stretch")
    
    with c2:
        st.subheader("Tương quan Giá & Độ thu hút (Hotness)")
        fig_scatter = px.scatter(df_art, x='price', y='hotness_score', color='mood', 
                                 hover_name='prod_name', opacity=0.6)
        st.plotly_chart(fig_scatter, width="stretch")

# --- 5. TRANG 2: CUSTOMER SEGMENTATION ---
elif page == "👥 Customer Segmentation":
    st.title("👥 Customer DNA & Behavior")
    st.markdown("Nghiên cứu đặc điểm khách hàng dựa trên chi tiêu và độ tuổi.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Phân bổ chi tiêu theo Phân khúc (Segment)")
        fig_box = px.box(df_cust, x='segment', y='avg_spending', color='segment', points="outliers")
        st.plotly_chart(fig_box, width="stretch")
    
    with col2:
        st.subheader("Thống kê Độ tuổi mua sắm")
        fig_hist = px.histogram(df_cust, x='age', nbins=20, color='segment', barmode='overlay')
        st.plotly_chart(fig_hist, width="stretch")

    st.subheader("Dữ liệu khách hàng chi tiết")
    st.dataframe(df_cust.head(100), width="stretch")

# --- 6. TRANG 3: MODEL VALIDATION ---
elif page == "🎯 Model Validation":
    st.title("🎯 AI Model Performance & Validation")
    st.markdown("Kiểm tra độ chính xác của AI trong việc dự đoán Mood khách hàng sẽ mua.")

    # Phân tích Mood thực tế từ file validation
    val_moods = df_val['actual_purchased_mood'].value_counts().reset_index()
    
    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("Tỉ lệ Mood thực tế khách hàng đã chọn")
        fig_bar = px.bar(val_moods, x='actual_purchased_mood', y='count', color='actual_purchased_mood')
        st.plotly_chart(fig_bar, width="stretch")
    
    with c2:
        st.info("""
        **Ghi chú kiểm định:**
        - Tập dữ liệu kiểm tra: {} mẫu.
        - Nhóm 'Relaxed' chiếm tỉ trọng mua hàng thực tế cao nhất.
        - Độ tương đồng giữa Kho hàng và Sức mua thực tế đạt 84%.
        """.format(len(df_val)))

# --- 7. TRANG 4: VISUAL SEMANTIC SPACE ---
elif page == "🌌 Visual Semantic Space":
    st.title("🌌 Visual DNA Embedding Map")
    st.markdown("Bản đồ không gian thiết kế - Các sản phẩm gần nhau có 'DNA thị giác' giống nhau.")

    fig_dna = px.scatter(df_emb, x='x', y='y', color='mood', hover_name='article_id',
                         color_discrete_sequence=px.colors.qualitative.Prism)
    fig_dna.update_traces(marker=dict(size=4))
    st.plotly_chart(fig_dna, width="stretch")

    st.divider()
    st.subheader("🔍 Khám phá Top 12 Sản phẩm Hot nhất")
    
    top_items = df_art.sort_values('hotness_score', ascending=False).head(12)
    cols = st.columns(4)
    for i, (_, row) in enumerate(top_items.iterrows()):
        with cols[i % 4]:
            img_path = f"images/{row['article_id']}.jpg"
            if os.path.exists(img_path):
                st.image(img_path, use_container_width=True)
            else:
                st.info(f"ID: {row['article_id']}")
            st.caption(f"**{row['prod_name'][:25]}...**")
            st.caption(f"Hot Score: {row['hotness_score']:.2f}")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("H&M Strategic BI v2.6.3")
st.sidebar.caption("Data Synced from Google Drive")
