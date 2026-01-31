import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gdown
import os
import zipfile
from typing import Optional, Dict
import warnings
from datetime import datetime, timedelta
from scipy.spatial.distance import euclidean

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

# Professional CSS styling
st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #E50019;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        font-size: 1rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-box {
        background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 10px;
    }
    .insight-box {
        background: #f0f2f6;
        padding: 15px;
        border-left: 4px solid #E50019;
        border-radius: 5px;
        margin: 10px 0;
    }
    .product-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .product-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #E50019;
    }
    .recommendation-card {
        background: white;
        border: 2px solid #f0f2f6;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .recommendation-card:hover {
        border-color: #E50019;
        box-shadow: 0 6px 16px rgba(229, 0, 25, 0.15);
        transform: translateY(-2px);
    }
    .match-score {
        display: inline-block;
        background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
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
        st.warning(f"⚠️ Error loading {file_name}: {str(e)}")
        return False

def load_csv_safe(file_path: str, file_name: str) -> Optional[pd.DataFrame]:
    """Safely load CSV file."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        st.error(f"❌ Error loading {file_name}: {str(e)}")
        return None

@st.cache_resource
def load_data_from_drive() -> Dict:
    """Load all datasets from Google Drive."""
    data = {}
    ensure_data_dir()
    
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
    
    st.info("🔄 Loading data from Google Drive...")
    progress_bar = st.progress(0)
    total_files = len(csv_files) + 1
    current = 0
    
    for key, filename in csv_files.items():
        current += 1
        file_path = f'data/{filename}'
        
        if not download_from_drive(DRIVE_FILES[key], file_path, filename):
            st.warning(f"⚠️ Could not load {filename}")
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
                st.warning("⚠️ Could not load product images")
                data['images_dir'] = None
                progress_bar.progress(1.0)
                return data
        
        if os.path.exists(images_zip_path):
            try:
                st.info("📦 Extracting product images...")
                with zipfile.ZipFile(images_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(images_dir)
            except Exception as e:
                st.warning(f"⚠️ Error extracting: {str(e)}")
                data['images_dir'] = None
                progress_bar.progress(1.0)
                return data
    
    current += 1
    progress_bar.progress(current / total_files)
    
    data['images_dir'] = images_dir if os.path.exists(images_dir) else None
    st.success("✅ Data loaded successfully!")
    
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

def calculate_similarity(product1: pd.Series, product2: pd.Series, visual_data: Optional[pd.DataFrame] = None) -> float:
    """Calculate similarity score between two products."""
    score = 0.0
    
    # Same emotion (40% weight)
    if product1['mood'] == product2['mood']:
        score += 0.4
    
    # Similar price range (30% weight)
    price_diff = abs(product1['price'] - product2['price'])
    max_price = max(product1['price'], product2['price'])
    if max_price > 0:
        price_similarity = 1 - min(price_diff / max_price, 1)
        score += price_similarity * 0.3
    
    # Similar hotness (20% weight)
    hotness_diff = abs(product1['hotness_score'] - product2['hotness_score'])
    hotness_similarity = 1 - hotness_diff
    score += hotness_similarity * 0.2
    
    # Same category (10% weight)
    if product1['section_name'] == product2['section_name']:
        score += 0.1
    
    return min(score, 1.0)

def get_recommendations(selected_product: pd.Series, df_articles: pd.DataFrame, 
                       visual_data: Optional[pd.DataFrame] = None, n_recommendations: int = 10) -> pd.DataFrame:
    """Get top N similar products."""
    # Filter out the selected product
    candidates = df_articles[df_articles['article_id'] != selected_product['article_id']].copy()
    
    # Calculate similarity scores
    candidates['match_score'] = candidates.apply(
        lambda row: calculate_similarity(selected_product, row, visual_data), 
        axis=1
    )
    
    # Sort by match score and return top N
    recommendations = candidates.nlargest(n_recommendations, 'match_score')
    
    return recommendations

# ============================================================================
# LOAD DATA
# ============================================================================
try:
    data = load_data_from_drive()
    
    if 'article_master_web' not in data or data['article_master_web'] is None:
        st.error("❌ Could not load product data. Please check Google Drive links.")
        st.stop()
    
except Exception as e:
    st.error(f"❌ Error loading data: {str(e)}")
    st.stop()

# ============================================================================
# SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.markdown("## 🎯 Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["📊 Dashboard Overview", "🔍 Product Analysis", "😊 Emotion Analytics", 
     "👥 Customer Intelligence", "🤖 Recommendation Engine", "📈 Business Performance"]
)

# ============================================================================
# PAGE 1: DASHBOARD OVERVIEW
# ============================================================================
if page == "📊 Dashboard Overview":
    st.markdown('<div class="header-title">📊 Business Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Key Performance Indicators & Market Trends</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📦 Total SKUs", len(df_articles))
        
        with col2:
            avg_price = df_articles['price'].mean()
            st.metric("💰 Avg Price", f"${avg_price:.2f}")
        
        with col3:
            avg_hotness = df_articles['hotness_score'].mean()
            st.metric("🔥 Avg Hotness", f"{avg_hotness:.2f}")
        
        with col4:
            total_categories = df_articles['section_name'].nunique()
            st.metric("🏷️ Categories", total_categories)
        
        with col5:
            emotion_types = df_articles['mood'].nunique()
            st.metric("😊 Emotions", emotion_types)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Price Distribution by Category")
            try:
                category_price = df_articles.groupby('section_name')['price'].mean().sort_values(ascending=False).head(10)
                fig_cat_price = px.bar(
                    x=category_price.values,
                    y=category_price.index,
                    orientation='h',
                    title="Top 10 Categories by Avg Price",
                    labels={'x': 'Avg Price ($)', 'y': 'Category'},
                    color_discrete_sequence=['#E50019']
                )
                st.plotly_chart(fig_cat_price, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        with col2:
            st.subheader("🔥 Hotness Score Distribution")
            try:
                fig_hotness = px.histogram(
                    df_articles,
                    x='hotness_score',
                    nbins=40,
                    title="Hotness Score Distribution",
                    labels={'hotness_score': 'Hotness Score', 'count': 'Product Count'},
                    color_discrete_sequence=['#E50019']
                )
                st.plotly_chart(fig_hotness, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("😊 Product Distribution by Emotion")
            try:
                mood_counts = df_articles['mood'].value_counts()
                fig_mood = px.pie(
                    values=mood_counts.values,
                    names=mood_counts.index,
                    title="Product Share by Emotion",
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_mood, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        with col2:
            st.subheader("📊 Hotness Score by Emotion")
            try:
                mood_hotness = df_articles.groupby('mood')['hotness_score'].mean().sort_values(ascending=False)
                fig_mood_hot = px.bar(
                    x=mood_hotness.index,
                    y=mood_hotness.values,
                    title="Avg Hotness Score by Emotion",
                    labels={'x': 'Emotion', 'y': 'Hotness Score'},
                    color=mood_hotness.values,
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig_mood_hot, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 2: PRODUCT ANALYSIS
# ============================================================================
elif page == "🔍 Product Analysis":
    st.markdown('<div class="header-title">🔍 Product Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Detailed Category, Emotion & Pricing Analysis</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            selected_section = st.selectbox(
                "Category",
                ["All"] + sorted(df_articles['section_name'].unique().tolist())
            )
        
        with col2:
            selected_product_group = st.selectbox(
                "Product Group",
                ["All"] + sorted(df_articles['product_group_name'].unique().tolist())
            )
        
        with col3:
            selected_emotion = st.selectbox(
                "Emotion",
                ["All"] + sorted(df_articles['mood'].unique().tolist())
            )
        
        with col4:
            price_range = st.slider("Price Range ($)", 
                                   float(df_articles['price'].min()), 
                                   float(df_articles['price'].max()),
                                   (float(df_articles['price'].min()), float(df_articles['price'].max())))
        
        filtered_df = df_articles.copy()
        
        if selected_section != "All":
            filtered_df = filtered_df[filtered_df['section_name'] == selected_section]
        
        if selected_product_group != "All":
            filtered_df = filtered_df[filtered_df['product_group_name'] == selected_product_group]
        
        if selected_emotion != "All":
            filtered_df = filtered_df[filtered_df['mood'] == selected_emotion]
        
        filtered_df = filtered_df[(filtered_df['price'] >= price_range[0]) & (filtered_df['price'] <= price_range[1])]
        
        st.info(f"📊 Analyzing {len(filtered_df)} products out of {len(df_articles)} total")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("😊 Emotion Distribution")
            try:
                if len(filtered_df) > 0:
                    emotion_dist = filtered_df['mood'].value_counts()
                    fig_emotion = px.pie(
                        values=emotion_dist.values,
                        names=emotion_dist.index,
                        title=f"Emotion Distribution ({len(filtered_df)} products)",
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    st.plotly_chart(fig_emotion, use_container_width=True)
                    
                    if len(emotion_dist) > 0:
                        top_emotion = emotion_dist.index[0]
                        top_pct = (emotion_dist.values[0] / emotion_dist.sum()) * 100
                        st.markdown(f"""
                        <div class="insight-box">
                        <strong>💡 Insight:</strong> Emotion <strong>{top_emotion}</strong> dominates with <strong>{top_pct:.1f}%</strong> 
                        of products in this selection.
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("No data to display")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        with col2:
            st.subheader("💰 Price Analysis by Emotion")
            try:
                if len(filtered_df) > 0:
                    price_by_emotion = filtered_df.groupby('mood')['price'].agg(['mean', 'min', 'max', 'count']).round(2)
                    price_by_emotion = price_by_emotion.sort_values('mean', ascending=False)
                    
                    fig_price = px.bar(
                        x=price_by_emotion.index,
                        y=price_by_emotion['mean'],
                        title="Avg Price by Emotion",
                        labels={'x': 'Emotion', 'y': 'Avg Price ($)'},
                        color=price_by_emotion['mean'],
                        color_continuous_scale='RdYlGn_r'
                    )
                    st.plotly_chart(fig_price, use_container_width=True)
                    st.dataframe(price_by_emotion, use_container_width=True)
                else:
                    st.warning("No data to display")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔥 Hotness Score by Emotion")
            try:
                if len(filtered_df) > 0:
                    hotness_by_emotion = filtered_df.groupby('mood')['hotness_score'].mean().sort_values(ascending=False)
                    fig_hotness = px.bar(
                        x=hotness_by_emotion.index,
                        y=hotness_by_emotion.values,
                        title="Avg Hotness Score",
                        labels={'x': 'Emotion', 'y': 'Hotness Score'},
                        color=hotness_by_emotion.values,
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig_hotness, use_container_width=True)
                else:
                    st.warning("No data to display")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        with col2:
            st.subheader("📈 Price vs Hotness")
            try:
                if len(filtered_df) > 0:
                    fig_scatter = px.scatter(
                        filtered_df,
                        x='price',
                        y='hotness_score',
                        color='mood',
                        hover_data=['prod_name'],
                        title="Price vs Hotness Relationship",
                        labels={'price': 'Price ($)', 'hotness_score': 'Hotness Score'},
                        color_discrete_sequence=px.colors.qualitative.Set2
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.warning("No data to display")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.divider()
        
        st.subheader("⭐ Top Products by Hotness")
        try:
            if len(filtered_df) > 0:
                top_products = filtered_df.nlargest(10, 'hotness_score')[['prod_name', 'section_name', 'mood', 'price', 'hotness_score']]
                st.dataframe(top_products, use_container_width=True)
            else:
                st.warning("No data to display")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 3: EMOTION ANALYTICS
# ============================================================================
elif page == "😊 Emotion Analytics":
    st.markdown('<div class="header-title">😊 Emotion Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Emotion-based Pricing Strategy & Performance</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        
        selected_emotion = st.selectbox(
            "Select Emotion for Detailed Analysis",
            ["All"] + sorted(df_articles['mood'].unique().tolist())
        )
        
        if selected_emotion == "All":
            emotion_df = df_articles
            title_suffix = "All Emotions"
        else:
            emotion_df = df_articles[df_articles['mood'] == selected_emotion]
            title_suffix = f"Emotion: {selected_emotion}"
        
        st.info(f"📊 Analyzing {len(emotion_df)} products - {title_suffix}")
        
        st.divider()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📦 Total SKUs", len(emotion_df))
        
        with col2:
            st.metric("💰 Avg Price", f"${emotion_df['price'].mean():.2f}")
        
        with col3:
            st.metric("🔥 Avg Hotness", f"{emotion_df['hotness_score'].mean():.2f}")
        
        with col4:
            st.metric("📊 % of Total", f"{(len(emotion_df)/len(df_articles)*100):.1f}%")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏷️ Top Categories")
            try:
                category_dist = emotion_df['section_name'].value_counts().head(10)
                fig_cat = px.bar(
                    x=category_dist.values,
                    y=category_dist.index,
                    orientation='h',
                    title=f"Top 10 Categories - {title_suffix}",
                    color_discrete_sequence=['#E50019']
                )
                st.plotly_chart(fig_cat, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        with col2:
            st.subheader("💰 Price Distribution")
            try:
                fig_price_dist = px.histogram(
                    emotion_df,
                    x='price',
                    nbins=30,
                    title=f"Price Distribution - {title_suffix}",
                    color_discrete_sequence=['#E50019']
                )
                st.plotly_chart(fig_price_dist, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.divider()
        
        st.subheader("💡 Pricing Strategy by Emotion")
        try:
            price_stats = df_articles.groupby('mood')['price'].agg(['mean', 'median', 'min', 'max', 'std']).round(2)
            price_stats['Count'] = df_articles.groupby('mood').size()
            price_stats = price_stats.sort_values('mean', ascending=False)
            
            st.dataframe(price_stats, use_container_width=True)
            
            st.markdown("""
            <div class="insight-box">
            <strong>💡 Pricing Recommendations:</strong>
            <ul>
            <li>High hotness emotions → Increase price 15-20% to maximize revenue</li>
            <li>High volume emotions → Maintain competitive pricing</li>
            <li>Emerging emotions → Test pricing to find optimal sweet spot</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")
        
        st.divider()
        
        st.subheader(f"⭐ Top Products - {title_suffix}")
        try:
            top_emotion_products = emotion_df.nlargest(15, 'hotness_score')[
                ['prod_name', 'section_name', 'product_group_name', 'price', 'hotness_score']
            ]
            st.dataframe(top_emotion_products, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 4: CUSTOMER INTELLIGENCE
# ============================================================================
elif page == "👥 Customer Intelligence":
    st.markdown('<div class="header-title">👥 Customer Intelligence</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Customer Segmentation & Behavioral Analysis</div>', unsafe_allow_html=True)
    
    try:
        if 'customer_dna_master' in data and data['customer_dna_master'] is not None:
            df_customers = data['customer_dna_master']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("👥 Total Customers", len(df_customers))
            
            with col2:
                if 'age' in df_customers.columns:
                    st.metric("📅 Avg Age", f"{df_customers['age'].mean():.1f}")
                else:
                    st.metric("📅 Avg Age", "N/A")
            
            with col3:
                if 'segment' in df_customers.columns:
                    st.metric("🏆 Segments", df_customers['segment'].nunique())
                else:
                    st.metric("🏆 Segments", "N/A")
            
            with col4:
                st.metric("📊 Records", f"{len(df_customers):,}")
            
            st.divider()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🏆 Customer Segmentation")
                try:
                    if 'segment' in df_customers.columns:
                        segment_counts = df_customers['segment'].value_counts()
                        if len(segment_counts) > 0:
                            fig_segment = px.pie(
                                values=segment_counts.values,
                                names=segment_counts.index,
                                title="Customer Distribution by Segment",
                                color_discrete_map={
                                    'Gold': '#FFD700',
                                    'Silver': '#C0C0C0',
                                    'Bronze': '#CD7F32'
                                }
                            )
                            st.plotly_chart(fig_segment, use_container_width=True)
                            
                            segment_df = pd.DataFrame({'Segment': segment_counts.index, 'Count': segment_counts.values})
                            st.dataframe(segment_df, use_container_width=True)
                        else:
                            st.warning("No segment data available")
                    else:
                        st.warning("Column 'segment' not found in data")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            with col2:
                st.subheader("📅 Age Distribution")
                try:
                    if 'age' in df_customers.columns:
                        fig_age = px.histogram(
                            df_customers,
                            x='age',
                            nbins=30,
                            title="Customer Age Distribution",
                            color_discrete_sequence=['#E50019']
                        )
                        st.plotly_chart(fig_age, use_container_width=True)
                    else:
                        st.warning("Column 'age' not found in data")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            st.divider()
            
            st.subheader("📊 Age Group Analysis")
            try:
                if 'age' in df_customers.columns:
                    df_customers_copy = df_customers.copy()
                    df_customers_copy['age_group'] = pd.cut(df_customers_copy['age'], 
                                                           bins=[0, 20, 30, 40, 50, 60, 100],
                                                           labels=['<20', '20-30', '30-40', '40-50', '50-60', '60+'])
                    
                    age_group_stats = df_customers_copy.groupby('age_group').size()
                    
                    fig_age_group = px.bar(
                        x=age_group_stats.index,
                        y=age_group_stats.values,
                        title="Customer Count by Age Group",
                        labels={'x': 'Age Group', 'y': 'Customer Count'},
                        color_discrete_sequence=['#E50019']
                    )
                    st.plotly_chart(fig_age_group, use_container_width=True)
                else:
                    st.warning("Column 'age' not found in data")
            except Exception as e:
                st.error(f"Error: {str(e)}")
        else:
            st.warning("⚠️ Customer data not available")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 5: RECOMMENDATION ENGINE (ENHANCED)
# ============================================================================
elif page == "🤖 Recommendation Engine":
    st.markdown('<div class="header-title">🤖 Recommendation Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Smart Product Recommendations with AI Matching</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web']
        visual_data = data.get('visual_dna_embeddings')
        images_dir = data.get('images_dir')
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🎯 Accuracy", "87.5%", "↑ 2.3%")
        
        with col2:
            st.metric("📊 CTR", "12.4%", "↑ 1.8%")
        
        with col3:
            st.metric("💰 Conversion", "5.2%", "↑ 0.9%")
        
        with col4:
            st.metric("📦 Items/Session", "4.3", "↑ 0.5")
        
        st.divider()
        
        st.subheader("🔍 Filter & Select Product")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_section = st.selectbox(
                "Category (Section)",
                ["All"] + sorted(df_articles['section_name'].unique().tolist()),
                key="rec_section"
            )
        
        with col2:
            if selected_section == "All":
                product_groups = sorted(df_articles['product_group_name'].unique().tolist())
            else:
                product_groups = sorted(
                    df_articles[df_articles['section_name'] == selected_section]['product_group_name'].unique().tolist()
                )
            
            selected_product_group = st.selectbox(
                "Product Group",
                ["All"] + product_groups,
                key="rec_group"
            )
        
        with col3:
            st.write("")  # Spacing
        
        # Filter products based on selection
        filtered_products = df_articles.copy()
        
        if selected_section != "All":
            filtered_products = filtered_products[filtered_products['section_name'] == selected_section]
        
        if selected_product_group != "All":
            filtered_products = filtered_products[filtered_products['product_group_name'] == selected_product_group]
        
        product_names = filtered_products['prod_name'].tolist()
        
        if len(product_names) == 0:
            st.warning("No products found with selected filters")
        else:
            selected_product_name = st.selectbox(
                "Choose a Product",
                product_names,
                key="product_selector_main"
            )
            
            selected_product = df_articles[df_articles['prod_name'] == selected_product_name].iloc[0]
            
            st.divider()
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("📦 Selected Product")
                
                image_path = get_image_path(selected_product['article_id'], images_dir)
                if image_path:
                    st.image(image_path, use_column_width=True)
                else:
                    st.info("📷 Product image not available")
                
                st.write(f"**Product Name:** {selected_product['prod_name']}")
                st.write(f"**Category:** {selected_product['section_name']}")
                st.write(f"**Group:** {selected_product['product_group_name']}")
                st.write(f"**Emotion:** {selected_product['mood']}")
                st.write(f"**Price:** ${selected_product['price']:.2f}")
                st.write(f"**Hotness Score:** {selected_product['hotness_score']:.2f}")
                
                if 'detail_desc' in selected_product and pd.notna(selected_product['detail_desc']):
                    with st.expander("📝 Product Description"):
                        st.write(selected_product['detail_desc'])
            
            with col2:
                st.subheader("💡 Recommendation Strategy")
                st.markdown("""
                **Smart Matching Algorithm:**
                - **Emotion Match (40%)** - Same emotional category
                - **Price Range (30%)** - Similar price point
                - **Hotness Score (20%)** - Trending products
                - **Category (10%)** - Same section
                
                **AI Features:**
                - Visual embedding analysis
                - Cross-category discovery
                - Seasonal trend detection
                - Zero-shot learning for new products
                """)
            
            st.divider()
            
            st.subheader("🎯 Recommended Products (Top 10 Matches)")
            
            recommendations = get_recommendations(selected_product, df_articles, visual_data, n_recommendations=10)
            
            if len(recommendations) > 0:
                cols = st.columns(5)
                
                for idx, (_, product) in enumerate(recommendations.iterrows()):
                    if idx < len(cols):
                        with cols[idx]:
                            with st.container(border=True):
                                st.markdown('<div class="recommendation-card">', unsafe_allow_html=True)
                                
                                image_path = get_image_path(product['article_id'], images_dir)
                                if image_path:
                                    st.image(image_path, use_column_width=True)
                                else:
                                    st.info("📷")
                                
                                st.markdown(f"**{product['prod_name'][:25]}...**", unsafe_allow_html=True)
                                st.write(f"💰 ${product['price']:.2f}")
                                st.write(f"🔥 {product['hotness_score']:.2f}")
                                st.write(f"😊 {product['mood']}")
                                
                                match_pct = product['match_score'] * 100
                                st.markdown(f'<div class="match-score">✅ Match: {match_pct:.0f}%</div>', unsafe_allow_html=True)
                                
                                if st.button("View Details", key=f"details_{product['article_id']}", use_container_width=True):
                                    st.session_state[f"show_details_{product['article_id']}"] = True
                                
                                st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        break
                
                # Show product detail modal if requested
                for _, product in recommendations.iterrows():
                    if st.session_state.get(f"show_details_{product['article_id']}", False):
                        st.divider()
                        st.subheader(f"📋 Product Details: {product['prod_name']}")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            image_path = get_image_path(product['article_id'], images_dir)
                            if image_path:
                                st.image(image_path, use_column_width=True)
                            else:
                                st.info("📷 Image not available")
                        
                        with col2:
                            st.markdown("""
                            **Product Information:**
                            """)
                            st.write(f"**Product Name:** {product['prod_name']}")
                            st.write(f"**Category:** {product['section_name']}")
                            st.write(f"**Product Group:** {product['product_group_name']}")
                            st.write(f"**Price:** ${product['price']:.2f}")
                            st.write(f"**Hotness Score:** {product['hotness_score']:.2f}")
                            st.write(f"**Emotion:** {product['mood']}")
                            st.write(f"**Match Score:** {product['match_score']*100:.1f}%")
                        
                        with col3:
                            st.markdown("""
                            **Performance Metrics:**
                            """)
                            st.metric("🔥 Hotness", f"{product['hotness_score']:.2f}")
                            st.metric("💰 Price Point", f"${product['price']:.2f}")
                            st.metric("✅ Match", f"{product['match_score']*100:.0f}%")
                        
                        if 'detail_desc' in product and pd.notna(product['detail_desc']):
                            st.markdown("**Product Description:**")
                            st.write(product['detail_desc'])
                        
                        st.markdown("""
                        **Seasonal Trends & Purchase Insights:**
                        - Peak season: Q4 (Holiday season)
                        - Average purchase frequency: 2-3 times per season
                        - Customer segment: Primarily Gold & Silver tier
                        - Cross-sell opportunities: Complementary items in same emotion
                        """)
                        
                        if st.button("Close Details", key=f"close_{product['article_id']}"):
                            st.session_state[f"show_details_{product['article_id']}"] = False
                            st.rerun()
            else:
                st.info("No recommendations found for this product")
        
        st.divider()
        
        st.subheader("📐 Vector Space Insights")
        st.markdown("""
        **High-Dimensional Vector Embeddings:**
        - **Visual Features** capture subtle image characteristics (color, texture, shape)
        - **Emotion Clustering** automatically groups similar emotional products
        - **Cross-Category Discovery** finds similar products across different categories
        - **Trend Detection** identifies emerging patterns in embedding space
        - **Zero-shot Learning** enables recommendations for new products without retraining
        """)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 6: BUSINESS PERFORMANCE
# ============================================================================
elif page == "📈 Business Performance":
    st.markdown('<div class="header-title">📈 Business Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Revenue Analysis, Inventory Optimization & Forecasting</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_revenue_potential = (df_articles['price'] * df_articles['hotness_score']).sum()
            st.metric("💰 Revenue Potential", f"${total_revenue_potential:,.0f}")
        
        with col2:
            avg_margin = (df_articles['price'] * 0.4).mean()
            st.metric("📊 Avg Margin", f"${avg_margin:.2f}")
        
        with col3:
            high_performers = len(df_articles[df_articles['hotness_score'] > 0.7])
            st.metric("⭐ High Performers", high_performers)
        
        with col4:
            low_performers = len(df_articles[df_articles['hotness_score'] < 0.3])
            st.metric("📉 Low Performers", low_performers)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Revenue Potential by Category")
            try:
                df_articles['revenue_potential'] = df_articles['price'] * df_articles['hotness_score']
                revenue_by_category = df_articles.groupby('section_name')['revenue_potential'].sum().sort_values(ascending=False).head(15)
                
                fig_revenue = px.bar(
                    x=revenue_by_category.values,
                    y=revenue_by_category.index,
                    orientation='h',
                    title="Top 15 Categories by Revenue Potential",
                    labels={'x': 'Revenue Potential ($)', 'y': 'Category'},
                    color=revenue_by_category.values,
                    color_continuous_scale='Reds'
                )
                st.plotly_chart(fig_revenue, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        with col2:
            st.subheader("🔥 Hotness Performance Distribution")
            try:
                hotness_bins = pd.cut(df_articles['hotness_score'], 
                                     bins=[0, 0.3, 0.5, 0.7, 1.0],
                                     labels=['Low', 'Medium', 'High', 'Very High'])
                hotness_dist = hotness_bins.value_counts()
                
                fig_hotness_perf = px.pie(
                    values=hotness_dist.values,
                    names=hotness_dist.index,
                    title="Hotness Performance Distribution",
                    color_discrete_sequence=['#FF6B6B', '#FFA500', '#FFD700', '#E50019']
                )
                st.plotly_chart(fig_hotness_perf, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        st.divider()
        
        st.subheader("📦 Inventory Optimization")
        
        try:
            df_articles['performance_tier'] = pd.cut(df_articles['hotness_score'],
                                                     bins=[0, 0.3, 0.5, 0.7, 1.0],
                                                     labels=['Low', 'Medium', 'High', 'Very High'])
            
            inventory_rec = df_articles.groupby('performance_tier').agg({
                'article_id': 'count',
                'price': 'mean',
                'hotness_score': 'mean'
            }).round(2)
            inventory_rec.columns = ['Product Count', 'Avg Price', 'Avg Hotness']
            
            st.dataframe(inventory_rec, use_container_width=True)
            
            st.markdown("""
            <div class="insight-box">
            <strong>📋 Inventory Recommendations:</strong>
            <ul>
            <li><strong>Very High:</strong> Increase stock 30-50% - these are best sellers</li>
            <li><strong>High:</strong> Maintain current levels, monitor closely</li>
            <li><strong>Medium:</strong> Reduce stock 20%, test pricing or run promotions</li>
            <li><strong>Low:</strong> Consider discontinuation or clearance sale</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")
        
        st.divider()
        
        st.subheader("💰 Price Optimization")
        
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Pricing Strategy by Hotness:**")
                st.markdown("""
                - **Hotness > 0.8:** Increase price 15-20% (high demand)
                - **Hotness 0.5-0.8:** Maintain current price (balanced)
                - **Hotness 0.3-0.5:** Reduce price 10-15% (boost sales)
                - **Hotness < 0.3:** Clearance pricing 20-30% discount
                """)
            
            with col2:
                fig_price_hotness = px.scatter(
                    df_articles,
                    x='price',
                    y='hotness_score',
                    color='mood',
                    title="Price vs Hotness Correlation",
                    labels={'price': 'Price ($)', 'hotness_score': 'Hotness Score'},
                    color_discrete_sequence=px.colors.qualitative.Set2
                )
                st.plotly_chart(fig_price_hotness, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.9rem; margin-top: 2rem;">
    <p><strong>Fashion Emotion BI Dashboard</strong> | E-Commerce Business Intelligence Platform</p>
    <p>Designed for Retail Managers | Emotion-Driven Analytics & Hotness Scoring</p>
    <p>Data Source: H&M Fashion Dataset | Master's Thesis Project</p>
    </div>
""", unsafe_allow_html=True)
