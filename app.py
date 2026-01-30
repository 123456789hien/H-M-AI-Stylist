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

warnings.filterwarnings('ignore')

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="Fashion Emotion BI Dashboard",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #E50019;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def ensure_data_dir():
    """Ensure data directory exists."""
    os.makedirs('data', exist_ok=True)

def download_from_drive(file_id: str, file_path: str, file_name: str) -> bool:
    """Download file from Google Drive."""
    try:
        if os.path.exists(file_path):
            return True
        
        url = f"https://drive.google.com/uc?id={file_id}"
        gdown.download(url, file_path, quiet=False)
        return os.path.exists(file_path)
    except Exception as e:
        st.warning(f"⚠️ Lỗi tải {file_name}: {str(e)}")
        return False

def load_csv_safe(file_path: str, file_name: str) -> Optional[pd.DataFrame]:
    """Safely load CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"❌ Lỗi tải {file_name}: {str(e)}")
        return None

@st.cache_resource
def load_data_from_drive() -> Dict:
    """Load all datasets from Google Drive."""
    data = {}
    ensure_data_dir()
    
    # Google Drive file IDs
    DRIVE_FILES = {
        'article_master_web': '1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK',
        'customer_dna_master': '182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH',
        'customer_test_validation': '1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB',
        'visual_dna_embeddings': '1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54',
        'hm_web_images': '1J3bLgVE5PzRB24Y1gaUB01tsxOk0plHT'
    }
    
    csv_files = {
        'article_master_web': 'article_master_web.csv',
        'customer_dna_master': 'customer_dna_master.csv',
        'customer_test_validation': 'customer_test_validation.csv',
        'visual_dna_embeddings': 'visual_dna_embeddings.csv'
    }
    
    st.info("🔄 Đang tải dữ liệu từ Google Drive...")
    progress_bar = st.progress(0)
    total_files = len(csv_files) + 1
    current = 0
    
    # Load CSV files
    for key, filename in csv_files.items():
        current += 1
        file_path = f'data/{filename}'
        
        if not download_from_drive(DRIVE_FILES[key], file_path, filename):
            st.warning(f"⚠️ Không thể tải {filename}")
            progress_bar.progress(current / total_files)
            continue
        
        df = load_csv_safe(file_path, filename)
        if df is not None:
            data[key] = df
        
        progress_bar.progress(current / total_files)
    
    # Load and extract images
    images_zip_path = 'data/hm_web_images.zip'
    images_dir = 'data/hm_web_images'
    
    if not os.path.exists(images_dir):
        if not os.path.exists(images_zip_path):
            if not download_from_drive(DRIVE_FILES['hm_web_images'], images_zip_path, 'hm_web_images.zip'):
                st.warning("⚠️ Không thể tải hình ảnh sản phẩm")
                data['images_dir'] = None
                progress_bar.progress(1.0)
                return data
        
        if os.path.exists(images_zip_path):
            try:
                st.info("📦 Đang giải nén hình ảnh...")
                with zipfile.ZipFile(images_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(images_dir)
            except Exception as e:
                st.warning(f"⚠️ Lỗi giải nén: {str(e)}")
                data['images_dir'] = None
                progress_bar.progress(1.0)
                return data
    
    current += 1
    progress_bar.progress(current / total_files)
    
    data['images_dir'] = images_dir if os.path.exists(images_dir) else None
    st.success("✅ Tải dữ liệu thành công!")
    
    return data

def get_image_path(article_id: str, images_dir: Optional[str]) -> Optional[str]:
    """Get image path for article."""
    if images_dir is None:
        return None
    
    try:
        article_id = str(article_id).zfill(10)
        image_path = os.path.join(images_dir, f"{article_id}.jpg")
        
        if os.path.exists(image_path):
            return image_path
    except:
        pass
    
    return None

def filter_products(df: pd.DataFrame, 
                   mood: Optional[str] = None,
                   price_range: Optional[Tuple[float, float]] = None,
                   color: Optional[str] = None,
                   hotness_min: Optional[float] = None) -> pd.DataFrame:
    """Filter products based on criteria."""
    try:
        result = df.copy()
        
        if mood and mood != "Tất Cả Cảm Xúc":
            result = result[result['mood'] == mood]
        
        if price_range:
            result = result[(result['price'] >= price_range[0]) & (result['price'] <= price_range[1])]
        
        if color and color != "Tất Cả Màu":
            result = result[result['perceived_colour_master_name'] == color]
        
        if hotness_min:
            result = result[result['hotness_score'] >= hotness_min]
        
        return result
    except:
        return df

# ============================================================================
# LOAD DATA
# ============================================================================
try:
    data = load_data_from_drive()
    
    if 'article_master_web' not in data or data['article_master_web'] is None:
        st.error("❌ Không thể tải dữ liệu sản phẩm. Vui lòng kiểm tra Google Drive links.")
        st.stop()
    
except Exception as e:
    st.error(f"❌ Lỗi tải dữ liệu: {str(e)}")
    st.stop()

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.markdown("## 🎯 Điều Hướng")
page = st.sidebar.radio(
    "Chọn trang",
    ["📊 Tổng Quan", "🛍️ Khám Phá Sản Phẩm", "😊 Phân Tích Cảm Xúc", 
     "👥 Thông Tin Khách Hàng", "🤖 Hệ Thống Gợi Ý", "📈 Hiệu Suất Mô Hình"]
)

# ============================================================================
# PAGE 1: DASHBOARD OVERVIEW
# ============================================================================
if page == "📊 Tổng Quan":
    st.markdown('<div class="header-title">👗 Bảng Điều Khiển Fashion Emotion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Phân Tích Thông Minh Dựa Trên Cảm Xúc Cho Bán Lẻ Thời Trang</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Tổng Sản Phẩm", len(df_articles))
        
        with col2:
            st.metric("🔥 Điểm Hotness TB", f"{df_articles['hotness_score'].mean():.2f}")
        
        with col3:
            st.metric("💰 Giá TB", f"${df_articles['price'].mean():.2f}")
        
        with col4:
            st.metric("😊 Loại Cảm Xúc", df_articles['mood'].nunique())
        
        st.divider()
        
        # Emotion distribution
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                mood_counts = df_articles['mood'].value_counts()
                fig_mood = px.pie(
                    values=mood_counts.values,
                    names=mood_counts.index,
                    title="Phân Bố Sản Phẩm Theo Cảm Xúc",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_mood, use_container_width=True)
            except Exception as e:
                st.error(f"Lỗi vẽ biểu đồ: {str(e)}")
        
        with col2:
            try:
                fig_hotness = px.histogram(
                    df_articles,
                    x='hotness_score',
                    nbins=30,
                    title="Phân Bố Điểm Hotness",
                    labels={'hotness_score': 'Điểm Hotness', 'count': 'Số Sản Phẩm'},
                    color_discrete_sequence=['#E50019']
                )
                st.plotly_chart(fig_hotness, use_container_width=True)
            except Exception as e:
                st.error(f"Lỗi vẽ biểu đồ: {str(e)}")
        
        st.divider()
        
        # Mood vs Price analysis
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                fig_mood_price = px.box(
                    df_articles,
                    x='mood',
                    y='price',
                    title="Phân Bố Giá Theo Cảm Xúc",
                    color='mood',
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_mood_price, use_container_width=True)
            except Exception as e:
                st.error(f"Lỗi: {str(e)}")
        
        with col2:
            try:
                fig_mood_hotness = px.box(
                    df_articles,
                    x='mood',
                    y='hotness_score',
                    title="Điểm Hotness Theo Cảm Xúc",
                    color='mood',
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_mood_hotness, use_container_width=True)
            except Exception as e:
                st.error(f"Lỗi: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Lỗi: {str(e)}")

# ============================================================================
# PAGE 2: PRODUCT EXPLORER
# ============================================================================
elif page == "🛍️ Khám Phá Sản Phẩm":
    st.markdown('<div class="header-title">🛍️ Khám Phá Sản Phẩm</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Tìm kiếm và lọc sản phẩm theo cảm xúc, giá, màu sắc và độ phổ biến</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        images_dir = data.get('images_dir')
        
        # Filters
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            selected_mood = st.selectbox(
                "Lọc theo Cảm Xúc",
                ["Tất Cả Cảm Xúc"] + sorted(df_articles['mood'].unique().tolist())
            )
        
        with col2:
            price_range = st.slider(
                "Khoảng Giá",
                float(df_articles['price'].min()),
                float(df_articles['price'].max()),
                (float(df_articles['price'].min()), float(df_articles['price'].max()))
            )
        
        with col3:
            colors = df_articles['perceived_colour_master_name'].unique()
            selected_color = st.selectbox(
                "Lọc theo Màu",
                ["Tất Cả Màu"] + sorted([c for c in colors if pd.notna(c)])
            )
        
        with col4:
            hotness_min = st.slider(
                "Điểm Hotness Tối Thiểu",
                0.0,
                1.0,
                0.0,
                0.1
            )
        
        # Apply filters
        filtered_df = filter_products(
            df_articles,
            mood=selected_mood,
            price_range=price_range,
            color=selected_color,
            hotness_min=hotness_min
        )
        
        st.info(f"📊 Hiển thị {len(filtered_df)} sản phẩm từ {len(df_articles)}")
        
        # Display products in grid
        if len(filtered_df) > 0:
            cols = st.columns(4)
            for idx, (_, product) in enumerate(filtered_df.head(20).iterrows()):
                col = cols[idx % 4]
                
                with col:
                    try:
                        img_path = get_image_path(product['article_id'], images_dir)
                        
                        if img_path:
                            st.image(img_path, use_column_width=True)
                        else:
                            st.image("https://via.placeholder.com/250x300?text=No+Image", use_column_width=True)
                        
                        st.markdown(f"**{str(product['prod_name'])[:30]}...**")
                        st.markdown(f"**Cảm Xúc:** {product['mood']}")
                        st.markdown(f"**Màu:** {product['perceived_colour_master_name']}")
                        st.markdown(f"**Giá:** ${product['price']:.2f}")
                        st.markdown(f"**Hotness:** {product['hotness_score']:.2f} 🔥")
                    except Exception as e:
                        st.warning(f"Lỗi: {str(e)}")
        else:
            st.warning("❌ Không tìm thấy sản phẩm phù hợp")
    
    except Exception as e:
        st.error(f"❌ Lỗi: {str(e)}")

# ============================================================================
# PAGE 3: EMOTION ANALYTICS
# ============================================================================
elif page == "😊 Phân Tích Cảm Xúc":
    st.markdown('<div class="header-title">😊 Phân Tích Cảm Xúc</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Mối Quan Hệ Thiết Kế-Cảm Xúc & Chiến Lược Giá Theo Mood</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        
        # Research Question 1: Design-Emotion Relationship
        st.subheader("1️⃣ Mối Quan Hệ Thiết Kế-Cảm Xúc")
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                section_mood = pd.crosstab(df_articles['section_name'], df_articles['mood'])
                fig_section = px.bar(
                    section_mood,
                    title="Phần Hàng Theo Cảm Xúc",
                    barmode='group',
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_section, use_container_width=True)
            except Exception as e:
                st.error(f"Lỗi: {str(e)}")
        
        with col2:
            try:
                group_mood = pd.crosstab(df_articles['product_group_name'], df_articles['mood'])
                fig_group = px.bar(
                    group_mood,
                    title="Nhóm Sản Phẩm Theo Cảm Xúc",
                    barmode='group',
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_group, use_container_width=True)
            except Exception as e:
                st.error(f"Lỗi: {str(e)}")
        
        st.divider()
        
        # Research Question 2: Mood-Based Pricing Strategy
        st.subheader("2️⃣ Chiến Lược Giá Theo Mood")
        
        try:
            mood_price_stats = df_articles.groupby('mood').agg({
                'price': ['mean', 'min', 'max', 'std'],
                'hotness_score': 'mean',
                'article_id': 'count'
            }).round(2)
            mood_price_stats.columns = ['Giá TB', 'Giá Min', 'Giá Max', 'Std Dev', 'Hotness TB', 'Số SP']
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_price_mood = px.box(
                    df_articles,
                    x='mood',
                    y='price',
                    points='outliers',
                    title="Phân Bố Giá Theo Cảm Xúc",
                    color='mood',
                    color_discrete_sequence=px.c
(Content truncated due to size limit. Use line ranges to read remaining content)
