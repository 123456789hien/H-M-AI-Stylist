import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gdown
import os
import zipfile
from typing import Optional, Tuple, Dict
import warnings
from datetime import datetime, timedelta
from PIL import Image

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION (GIỮ NGUYÊN GỐC)
# ============================================================================
st.set_page_config(
    page_title="Fashion Emotion BI Dashboard",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (GIỮ NGUYÊN GỐC)
st.markdown("""
    <style>
    .main { padding-top: 1rem; }
    .header-title { font-size: 2.5rem; font-weight: 700; color: #E50019; margin-bottom: 0.5rem; }
    .subtitle { font-size: 1rem; color: #666; margin-bottom: 2rem; }
    .metric-box {
        background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%);
        padding: 20px; border-radius: 10px; color: white; text-align: center; margin-bottom: 10px;
    }
    .insight-box {
        background: #f0f2f6; padding: 15px; border-left: 4px solid #E50019; border-radius: 5px; margin: 10px 0;
    }
    .product-card {
        border: 1px solid #eee; padding: 10px; border-radius: 8px; transition: 0.3s; background: white;
    }
    .product-card:hover { border-color: #E50019; box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING & IMAGE HANDLING (KHÔI PHỤC HÀM XỬ LÝ ẢNH)
# ============================================================================
@st.cache_resource
def load_data():
    file_ids = {
        "article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "customer_dna_master.csv": "182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH",
        "customer_test_validation.csv": "1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB",
        "hm_web_images.zip": "1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT"
    }
    
    for filename, fid in file_ids.items():
        if not os.path.exists(filename):
            try:
                gdown.download(f'https://drive.google.com/uc?id={fid}', filename, quiet=True)
            except: pass

    if os.path.exists("hm_web_images.zip") and not os.path.exists("images"):
        with zipfile.ZipFile("hm_web_images.zip", 'r') as zip_ref:
            zip_ref.extractall("images")

    df_art = pd.read_csv("article_master_web.csv")
    df_art['article_id'] = df_art['article_id'].astype(str).str.zfill(10)
    df_art['revenue'] = df_art['hotness_score'] * df_art['price'] * 1000
    
    return df_art, pd.read_csv("customer_dna_master.csv"), pd.read_csv("customer_test_validation.csv")

def get_product_image(article_id):
    # Đường dẫn ảnh theo cấu trúc H&M (3 chữ số đầu là folder)
    folder = article_id[:3]
    img_path = f"images/{folder}/{article_id}.jpg"
    if os.path.exists(img_path):
        return img_path
    return "https://via.placeholder.com/200x300?text=No+Image"

df_articles, df_customers, df_validation = load_data()

# ============================================================================
# SIDEBAR (GIỮ NGUYÊN MENU GỐC)
# ============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
    st.markdown("---")
    page = st.radio("DANH MỤC PHÂN TÍCH", [
        "📊 Dashboard Tổng Quan", 
        "🔍 Chi Tiết Sản Phẩm", 
        "👤 Phân Khúc Khách Hàng", 
        "😊 Phân Tích Cảm Xúc", 
        "🤖 Hệ Thống Gợi Ý", 
        "📈 Chiến Lược & Giá Bán"
    ])

# ============================================================================
# TRANG 5: HỆ THỐNG GỢI Ý (KHÔI PHỤC CÓ ẢNH CLICK ĐƯỢC)
# ============================================================================
if page == "🤖 Hệ Thống Gợi Ý":
    st.markdown('<h1 class="header-title">Hệ Thống Gợi Ý Thông Minh</h1>', unsafe_allow_html=True)
    
    col_sel, col_info = st.columns([1, 1])
    with col_sel:
        target_name = st.selectbox("Chọn sản phẩm khách hàng quan tâm:", df_articles['prod_name'].unique())
        target_row = df_articles[df_articles['prod_name'] == target_name].iloc[0]
        st.image(get_product_image(target_row['article_id']), width=200, caption=f"Sản phẩm gốc: {target_row['article_id']}")
    
    with col_info:
        st.markdown(f"""
        <div class='insight-box'>
            <h4>Phân tích Mood: {target_row['mood']}</h4>
            <p>Hotness Score: {target_row['hotness_score']:.2f}</p>
            <p>Nhóm: {target_row['product_group_name']}</p>
        </div>
        """, unsafe_allow_html=True)

    st.subheader("Sản phẩm gợi ý (Cùng phong cách cảm xúc)")
    # Logic gợi ý theo mood từ code gốc
    recs = df_articles[(df_articles['mood'] == target_row['mood']) & (df_articles['article_id'] != target_row['article_id'])].head(10)
    
    cols = st.columns(5)
    for i, (idx, row) in enumerate(recs.iterrows()):
        with cols[i % 5]:
            st.image(get_product_image(row['article_id']), use_column_width=True)
            st.markdown(f"**{row['prod_name'][:20]}**")
            st.markdown(f"Price: ${row['price']}")
            if st.button(f"Xem chi tiết {row['article_id'][-4:]}", key=row['article_id']):
                st.session_state['selected_art'] = row['article_id']
                st.rerun()

# ============================================================================
# TRANG 6: CHIẾN LƯỢC & GIÁ BÁN (KHÔI PHỤC HOÀN TOÀN)
# ============================================================================
elif page == "📈 Chiến Lược & Giá Bán":
    st.markdown('<h1 class="header-title">Chiến Lược Kinh Doanh & Giá</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["💰 Phân Tích Giá", "🧪 Kiểm Chứng AI"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown("""
            <div class="insight-box">
            <h3>💡 Chiến Lược Theo Hotness</h3>
            <ul>
                <li><b>Hotness > 0.8:</b> Premium Pricing (Giữ giá).</li>
                <li><b>Hotness 0.5-0.8:</b> Balanced (Marketing mạnh).</li>
                <li><b>Hotness < 0.3:</b> Clearance (Giảm giá 30%+).</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            fig_p = px.scatter(df_articles, x='price', y='hotness_score', color='mood', title="Mối Quan Hệ Giá - Hotness")
            st.plotly_chart(fig_p, use_container_width=True)

    with tab2:
        st.subheader("So sánh Tồn kho (Dự báo AI) vs Nhu cầu (Thực tế)")
        # Phân phối Mood dự kiến từ danh mục sản phẩm
        pred = df_articles['mood'].value_counts(normalize=True).reset_index()
        # Phân phối Mood thực tế từ lịch sử validation
        actual = df_validation['actual_purchased_mood'].value_counts(normalize=True).reset_index()
        
        fig_val = go.Figure()
        fig_val.add_trace(go.Bar(x=pred['mood'], y=pred['proportion'], name='AI Inventory Prediction', marker_color='#E50019'))
        fig_val.add_trace(go.Bar(x=actual['actual_purchased_mood'], y=actual['proportion'], name='Actual Sales Demand', marker_color='#333333'))
        fig_val.update_layout(barmode='group')
        st.plotly_chart(fig_val, use_container_width=True)

# ============================================================================
# CÁC TRANG CÒN LẠI (GIỮ NGUYÊN GỐC)
# ============================================================================
elif page == "📊 Dashboard Tổng Quan":
    st.markdown('<h1 class="header-title">Executive Dashboard</h1>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    k1.metric("Tổng sản phẩm", f"{len(df_articles):,}")
    k2.metric("Hotness Trung Bình", f"{df_articles['hotness_score'].mean():.2f}")
    k3.metric("Doanh thu dự kiến", f"${df_articles['revenue'].sum():,.0f}")
    
    # SỬA LỖI barh duy nhất:
    group_data = df_articles.groupby('product_group_name')['revenue'].sum().reset_index()
    fig = px.bar(group_data, x='revenue', y='product_group_name', orientation='h', color='revenue')
    st.plotly_chart(fig, use_container_width=True)

elif page == "🔍 Chi Tiết Sản Phẩm":
    st.markdown('<h1 class="header-title">Inventory Detail</h1>', unsafe_allow_html=True)
    st.dataframe(df_articles, use_container_width=True)

elif page == "👤 Phân Khúc Khách Hàng":
    st.markdown('<h1 class="header-title">Customer DNA</h1>', unsafe_allow_html=True)
    st.plotly_chart(px.pie(df_customers, names='segment', hole=0.4), use_container_width=True)

elif page == "😊 Phân Tích Cảm Xúc":
    st.markdown('<h1 class="header-title">Emotion Analysis</h1>', unsafe_allow_html=True)
    st.plotly_chart(px.box(df_articles, x='mood', y='hotness_score', color='mood'), use_container_width=True)

st.divider()
st.markdown("<p style='text-align: center; color: #999;'>© 2026 Fashion Emotion BI Platform</p>", unsafe_allow_html=True)
