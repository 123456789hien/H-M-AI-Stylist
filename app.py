import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gdown
import os
import zipfile
import warnings

warnings.filterwarnings('ignore')

# ============================================================================
# 1. PAGE CONFIGURATION (Giữ nguyên thiết kế chuyên nghiệp)
# ============================================================================
st.set_page_config(
    page_title="Fashion Emotion BI Dashboard",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (Giữ nguyên bố cục gốc của bạn)
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .header-title { font-size: 2.5rem; font-weight: 700; color: #E50019; margin-bottom: 0.5rem; }
    .metric-box { background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%); padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 10px; }
    .insight-box { background: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #E50019; margin-bottom: 1rem; }
    .product-card { border: 1px solid #eee; border-radius: 10px; padding: 10px; transition: 0.3s; background: white; }
    .product-card:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.1); transform: translateY(-5px); }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. DATA LOADING & AUTOMATIC DOWNLOAD (Fix lỗi thiếu file)
# ============================================================================
@st.cache_resource
def load_all_data():
    # IDs lấy từ link bạn đã cung cấp
    file_ids = {
        "article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "customer_dna_master.csv": "182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH",
        "customer_test_validation.csv": "1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB",
        "visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
        "hm_web_images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }

    # Download files nếu chưa tồn tại
    for filename, fid in file_ids.items():
        if not os.path.exists(filename):
            try:
                url = f'https://drive.google.com/uc?id={fid}'
                gdown.download(url, filename, quiet=False)
            except Exception as e:
                st.error(f"Lỗi tải file {filename}: {e}")

    # Giải nén ảnh nếu có file zip
    if os.path.exists("hm_web_images.zip") and not os.path.exists("images"):
        with zipfile.ZipFile("hm_web_images.zip", 'r') as zip_ref:
            zip_ref.extractall("images")

    try:
        # Đọc dữ liệu
        df_art = pd.read_csv("article_master_web.csv")
        df_cust = pd.read_csv("customer_dna_master.csv")
        df_val = pd.read_csv("customer_test_validation.csv")
        
        # Tiền xử lý ID
        df_art['article_id'] = df_art['article_id'].astype(str).str.zfill(10)
        df_art['revenue'] = df_art['hotness_score'] * df_art['price'] * 1000
        
        return df_art, df_cust, df_val
    except Exception as e:
        st.error(f"Lỗi xử lý dữ liệu: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_articles, df_customers, df_validation = load_all_data()

# Dừng app nếu dữ liệu không load được để tránh lỗi Traceback
if df_articles.empty:
    st.error("Không thể tải dữ liệu từ Google Drive. Vui lòng kiểm tra quyền chia sẻ link (Anyonewith the link).")
    st.stop()

# ============================================================================
# 3. SIDEBAR (Giữ nguyên cấu trúc Filter)
# ============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
    st.markdown("---")
    page = st.radio("NAVIGATION", [
        "📊 Executive Dashboard", "🔍 Product Intelligence", 
        "👤 Customer Intelligence", "😊 Emotion Analytics", 
        "🤖 Recommendation Engine", "📈 Model Performance"
    ])
    
    st.markdown("---")
    st.markdown("### FILTERS")
    
    # Sửa lỗi: Đảm bảo lấy đúng cột có trong file csv của bạn
    section_col = 'section_name' if 'section_name' in df_articles.columns else 'index'
    sections = ["All"] + sorted(df_articles[section_col].unique().tolist())
    selected_section = st.selectbox("Select Gender/Section", sections)
    
    cat_col = 'product_group_name'
    categories = ["All"] + sorted(df_articles[cat_col].unique().tolist())
    selected_cat = st.selectbox("Select Category", categories)
    
    moods = ["All"] + sorted(df_articles['mood'].unique().tolist())
    selected_mood = st.selectbox("Select Mood", moods)

# Logic lọc dữ liệu
df_filtered = df_articles.copy()
if selected_section != "All":
    df_filtered = df_filtered[df_filtered[section_col] == selected_section]
if selected_cat != "All":
    df_filtered = df_filtered[df_filtered[cat_col] == selected_cat]
if selected_mood != "All":
    df_filtered = df_filtered[df_filtered['mood'] == selected_mood]

# ============================================================================
# 4. TRANG 1: EXECUTIVE DASHBOARD
# ============================================================================
if page == "📊 Executive Dashboard":
    st.markdown('<h1 class="header-title">Executive Dashboard</h1>', unsafe_allow_html=True)
    
    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Products", f"{len(df_filtered):,}")
    with c2: st.metric("Avg Hotness", f"{df_filtered['hotness_score'].mean():.2f}")
    with c3: st.metric("Avg Price", f"${df_filtered['price'].mean():.4f}")
    with c4: st.metric("Revenue Potential", f"${df_filtered['revenue'].sum():,.0f}")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("💰 Revenue by Category")
        rev_data = df_filtered.groupby(cat_col)['revenue'].sum().sort_values(ascending=True).reset_index()
        # FIX: Sửa lỗi barh bằng orientation='h'
        fig = px.bar(rev_data, x='revenue', y=cat_col, orientation='h', color='revenue', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("🎭 Emotion Distribution")
        fig_pie = px.pie(df_filtered, names='mood', values='revenue', hole=0.4, color_discrete_sequence=px.colors.sequential.Reds_r)
        st.plotly_chart(fig_pie, use_container_width=True)

# ============================================================================
# 5. TRANG 3: CUSTOMER INTELLIGENCE
# ============================================================================
elif page == "👤 Customer Intelligence":
    st.markdown('<h1 class="header-title">Customer Intelligence</h1>', unsafe_allow_html=True)
    
    col_a, col_b = st.columns([1, 2])
    with col_a:
        st.markdown('<div class="insight-box"><h3>Loyalty Segments</h3></div>', unsafe_allow_html=True)
        seg_data = df_customers['segment'].value_counts().reset_index()
        fig_seg = px.pie(seg_data, names='segment', values='count', color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(fig_seg, use_container_width=True)
    with col_b:
        st.markdown('<div class="insight-box"><h3>Spending vs Age</h3></div>', unsafe_allow_html=True)
        # Sample dữ liệu để biểu đồ chạy nhanh hơn
        sample_size = min(1000, len(df_customers))
        fig_scatter = px.scatter(df_customers.sample(sample_size), x='age', y='avg_spending', color='segment', size='purchase_count')
        st.plotly_chart(fig_scatter, use_container_width=True)

# ============================================================================
# 6. TRANG 5: RECOMMENDATION ENGINE (Fix logic cập nhật động)
# ============================================================================
elif page == "🤖 Recommendation Engine":
    st.markdown('<h1 class="header-title">Emotion-Based Recommendations</h1>', unsafe_allow_html=True)
    
    avail_prods = df_filtered['prod_name'].unique()
    if len(avail_prods) > 0:
        target_name = st.selectbox("Pick a product reference:", avail_prods)
        target_info = df_articles[df_articles['prod_name'] == target_name].iloc[0]
        
        st.info(f"Targeting products with mood: **{target_info['mood']}**")
        
        # Lọc gợi ý
        recs = df_articles
