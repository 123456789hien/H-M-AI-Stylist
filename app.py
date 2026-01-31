import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gdown
import zipfile
import os
from datetime import datetime

# ============================================================================
# 1. PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="H&M Fashion BI",
    page_icon="👗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 2. FAST DATA ENGINE
# ============================================================================
@st.cache_resource
def init_resources():
    """Initialize data directory and download files"""
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Drive IDs (Original files provided by user)
    files = {
        "data/article_master_web.csv": "1rLdTRGW2iu50edIDWnGSBkZqWznnNXLK",
        "data/customer_dna_master.csv": "182gmD8nYPAuy8JO_vIqzVJy8eMKqrGvH",
        "data/customer_test_validation.csv": "1mAufyQbOrpXdjkYXE4nhYyleGBoB6nXB",
        "data/visual_dna_embeddings.csv": "1VLNeGstZhn0_TdMiV-6nosxvxyFO5a54",
        "images.zip": "1z27fEDUpgXfiFzb1eUv5i5pbIA_cI7UA"
    }
    
    for path, fid in files.items():
        if not os.path.exists(path):
            try:
                st.info(f"📥 Downloading {path}...")
                gdown.download(f'https://drive.google.com/uc?id={fid}', path, quiet=False)
            except Exception as e:
                st.warning(f"⚠️ Could not download {path}: {str(e)}")
    
    # Optimize Unzipping: Only unzip if the images folder doesn't exist or is empty
    if os.path.exists("images.zip"):
        if not os.path.exists('images') or len(os.listdir('images')) < 100:
            if not os.path.exists('images'):
                os.makedirs('images')
            try:
                st.info("📦 Extracting images...")
                with zipfile.ZipFile("images.zip", 'r') as z:
                    z.extractall('images')
                st.success("✅ Images extracted successfully!")
            except Exception as e:
                st.warning(f"⚠️ Could not extract images: {str(e)}")

@st.cache_data
def load_and_clean_data():
    """Load and clean data from CSV files"""
    try:
        df_a = pd.read_csv("data/article_master_web.csv")
        df_e = pd.read_csv("data/visual_dna_embeddings.csv")
        df_c = pd.read_csv("data/customer_dna_master.csv")
        df_t = pd.read_csv("data/customer_test_validation.csv")
        
        # Standardize Article IDs (Fixing leading zeros)
        df_a['article_id'] = df_a['article_id'].astype(str).str.zfill(10)
        df_e['article_id'] = df_e['article_id'].astype(str).str.zfill(10)
        
        return df_a, df_e, df_c, df_t
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return None, None, None, None

# Initialize with spinner
with st.spinner("🚀 Booting Strategic Engine... This may take a moment for 3GB assets."):
    init_resources()
    df_art, df_emb, df_cust, df_trans = load_and_clean_data()

if df_art is None:
    st.error("❌ Failed to load data. Please check your internet connection.")
    st.stop()

# ============================================================================
# 3. NAVIGATION
# ============================================================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/53/H%26M-Logo.svg", width=100)
st.sidebar.title("H&M Emotion BI")

page = st.sidebar.selectbox(
    "Select Page",
    [
        "📊 Executive Pulse",
        "🔍 Inventory & Pricing",
        "😊 Emotion Analytics",
        "👥 Customer DNA",
        "🤖 AI Recommendation",
        "📈 Business Performance"
    ]
)

# ============================================================================
# 4. STYLING
# ============================================================================
st.markdown("""
<style>
    .header-title {
        font-size: 2.5em;
        font-weight: 900;
        background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.2em;
    }
    .subtitle {
        font-size: 1.2em;
        color: #666;
        margin-bottom: 1em;
    }
    .tier-premium { background: linear-gradient(135deg, #1e5631 0%, #52b788 100%); color: white; }
    .tier-trend { background: linear-gradient(135deg, #52b788 0%, #a8dadc 100%); color: white; }
    .tier-stability { background: linear-gradient(135deg, #ffd60a 0%, #ffc300 100%); color: black; }
    .tier-liquidation { background: linear-gradient(135deg, #ffb4a2 0%, #ff8b7b 100%); color: white; }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# PAGE 1: EXECUTIVE PULSE
# ============================================================================
if page == "📊 Executive Pulse":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Executive Pulse - Strategic Overview</div>', unsafe_allow_html=True)
    
    try:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📦 Total SKUs", f"{len(df_art):,}")
        with col2:
            st.metric("💰 Avg Price", f"${df_art['price'].mean():.2f}")
        with col3:
            st.metric("🔥 Avg Hotness", f"{df_art['hotness_score'].mean():.2f}")
        with col4:
            st.metric("😊 Emotions", f"{df_art['mood'].nunique()}")
        with col5:
            st.metric("👥 Customers", f"{len(df_cust):,}")
        
        st.divider()
        
        st.subheader("Emotion Matrix - Price vs Hotness vs Revenue")
        emotion_stats = df_art.groupby('mood').agg({
            'price': 'mean',
            'hotness_score': 'mean',
            'article_id': 'count'
        }).reset_index()
        emotion_stats.columns = ['Emotion', 'Avg Price', 'Avg Hotness', 'Count']
        emotion_stats['Revenue'] = emotion_stats['Avg Price'] * emotion_stats['Count']
        
        fig_bubble = px.scatter(
            emotion_stats,
            x='Avg Price',
            y='Avg Hotness',
            size='Revenue',
            color='Emotion',
            hover_data=['Count'],
            title="Emotion Performance Matrix"
        )
        st.plotly_chart(fig_bubble, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Emotion Distribution")
            emotion_dist = df_art['mood'].value_counts()
            fig_emotion = px.pie(values=emotion_dist.values, names=emotion_dist.index)
            st.plotly_chart(fig_emotion, use_container_width=True)
        
        with col2:
            st.subheader("Hotness by Emotion")
            fig_hotness = px.bar(emotion_stats, x='Emotion', y='Avg Hotness', color='Emotion')
            st.plotly_chart(fig_hotness, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 2: INVENTORY & PRICING
# ============================================================================
elif page == "🔍 Inventory & Pricing":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Inventory & Pricing Intelligence</div>', unsafe_allow_html=True)
    
    try:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            selected_emotion = st.selectbox("Select Emotion", ["All"] + sorted(df_art['mood'].unique().tolist()), key="inv_emotion")
        with col2:
            selected_category = st.selectbox("Select Category", ["All"] + sorted(df_art['section_name'].unique().tolist()), key="inv_cat")
        with col3:
            selected_group = st.selectbox("Select Product Group", ["All"] + sorted(df_art['product_group_name'].unique().tolist()), key="inv_group")
        with col4:
            price_range = st.slider("Price Range", 0.0, df_art['price'].max(), (0.0, df_art['price'].max()))
        
        filtered_df = df_art.copy()
        if selected_emotion != "All":
            filtered_df = filtered_df[filtered_df['mood'] == selected_emotion]
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df['section_name'] == selected_category]
        if selected_group != "All":
            filtered_df = filtered_df[filtered_df['product_group_name'] == selected_group]
        filtered_df = filtered_df[(filtered_df['price'] >= price_range[0]) & (filtered_df['price'] <= price_range[1])]
        
        st.divider()
        st.subheader("💰 4-Tier Pricing Strategy")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            premium = filtered_df[filtered_df['hotness_score'] > 0.8]
            avg_price_p = premium["price"].mean() if len(premium) > 0 else 0
            st.markdown(f'<div class="tier-premium" style="padding: 20px; border-radius: 10px; text-align: center;"><h3>💎 Premium</h3><p>Hotness > 0.8</p><p style="font-size: 2em;">{len(premium)}</p><p>Avg: ${avg_price_p:.2f}</p></div>', unsafe_allow_html=True)
        
        with col2:
            trend = filtered_df[(filtered_df['hotness_score'] >= 0.5) & (filtered_df['hotness_score'] <= 0.8)]
            avg_price_t = trend["price"].mean() if len(trend) > 0 else 0
            st.markdown(f'<div class="tier-trend" style="padding: 20px; border-radius: 10px; text-align: center;"><h3>🔥 Trend</h3><p>Hotness 0.5-0.8</p><p style="font-size: 2em;">{len(trend)}</p><p>Avg: ${avg_price_t:.2f}</p></div>', unsafe_allow_html=True)
        
        with col3:
            stability = filtered_df[(filtered_df['hotness_score'] >= 0.3) & (filtered_df['hotness_score'] < 0.5)]
            avg_price_s = stability["price"].mean() if len(stability) > 0 else 0
            st.markdown(f'<div class="tier-stability" style="padding: 20px; border-radius: 10px; text-align: center;"><h3>⚖️ Stability</h3><p>Hotness 0.3-0.5</p><p style="font-size: 2em;">{len(stability)}</p><p>Avg: ${avg_price_s:.2f}</p></div>', unsafe_allow_html=True)
        
        with col4:
            liquidation = filtered_df[filtered_df['hotness_score'] < 0.3]
            avg_price_l = liquidation["price"].mean() if len(liquidation) > 0 else 0
            st.markdown(f'<div class="tier-liquidation" style="padding: 20px; border-radius: 10px; text-align: center;"><h3>📉 Liquidation</h3><p>Hotness < 0.3</p><p style="font-size: 2em;">{len(liquidation)}</p><p>Avg: ${avg_price_l:.2f}</p></div>', unsafe_allow_html=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Price Distribution")
            fig_price = px.histogram(filtered_df, x='price', nbins=30)
            st.plotly_chart(fig_price, use_container_width=True)
        
        with col2:
            st.subheader("Hotness Distribution")
            fig_hotness = px.histogram(filtered_df, x='hotness_score', nbins=30)
            st.plotly_chart(fig_hotness, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 3: EMOTION ANALYTICS
# ============================================================================
elif page == "😊 Emotion Analytics":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Deep Emotion Analytics</div>', unsafe_allow_html=True)
    
    try:
        selected_emotion = st.selectbox("Select Emotion", ["All"] + sorted(df_art['mood'].unique().tolist()), key="emo_select")
        st.divider()
        
        emotion_data = df_art if selected_emotion == "All" else df_art[df_art['mood'] == selected_emotion]
        title_suffix = "All Emotions" if selected_emotion == "All" else selected_emotion
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 Products", len(emotion_data))
        with col2:
            st.metric("💰 Avg Price", f"${emotion_data['price'].mean():.2f}")
        with col3:
            st.metric("🔥 Avg Hotness", f"{emotion_data['hotness_score'].mean():.2f}")
        with col4:
            st.metric("📊 Categories", emotion_data['section_name'].nunique())
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Top Categories - {title_suffix}")
            top_cat = emotion_data['section_name'].value_counts().head(10)
            fig_cat = px.bar(x=top_cat.values, y=top_cat.index, orientation='h')
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            st.subheader(f"Price Distribution - {title_suffix}")
            fig_price = px.box(emotion_data, y='price')
            st.plotly_chart(fig_price, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 4: CUSTOMER DNA
# ============================================================================
elif page == "👥 Customer DNA":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Customer DNA & Behavior</div>', unsafe_allow_html=True)
    
    try:
        col1, col2 = st.columns(2)
        with col1:
            selected_emotion = st.selectbox("Select Emotion", ["All"] + sorted(df_art['mood'].unique().tolist()), key="cust_emotion")
        with col2:
            selected_segment = st.selectbox("Customer Segment", ["All"] + sorted(df_cust['segment'].unique().tolist()) if 'segment' in df_cust.columns else ["All"], key="cust_segment")
        
        filtered_customers = df_cust.copy()
        if selected_segment != "All":
            filtered_customers = filtered_customers[filtered_customers['segment'] == selected_segment]
        
        if selected_emotion != "All" and df_trans is not None:
            emotion_customers = df_trans[df_trans['actual_purchased_mood'] == selected_emotion]['customer_id'].unique()
            filtered_customers = filtered_customers[filtered_customers['customer_id'].isin(emotion_customers)]
        
        st.divider()
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("👥 Customers", f"{len(filtered_customers):,}")
        with col2:
            avg_age = filtered_customers['age'].mean() if 'age' in filtered_customers.columns and len(filtered_customers) > 0 else 0
            st.metric("📅 Avg Age", f"{avg_age:.1f}")
        with col3:
            avg_spending = filtered_customers['avg_spending'].mean() if 'avg_spending' in filtered_customers.columns and len(filtered_customers) > 0 else 0
            st.metric("💰 Avg Spending", f"${avg_spending:.2f}")
        with col4:
            avg_purchases = filtered_customers['purchase_count'].mean() if 'purchase_count' in filtered_customers.columns and len(filtered_customers) > 0 else 0
            st.metric("🛍️ Avg Purchases", f"{avg_purchases:.1f}")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Spending vs Age**")
            if len(filtered_customers) > 0:
                fig_scatter = px.scatter(filtered_customers, x='age', y='avg_spending', color='segment' if 'segment' in filtered_customers.columns else None, color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'})
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("No data available")
        
        with col2:
            st.markdown("**Segment Distribution**")
            if 'segment' in filtered_customers.columns and len(filtered_customers) > 0:
                segment_counts = filtered_customers['segment'].value_counts()
                fig_segment = px.pie(values=segment_counts.values, names=segment_counts.index, color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'})
                st.plotly_chart(fig_segment, use_container_width=True)
        
        st.divider()
        st.subheader("⭐ Top Loyalists")
        
        top_loyalists_data = df_cust.copy()
        if selected_segment != "All":
            top_loyalists_data = top_loyalists_data[top_loyalists_data['segment'] == selected_segment]
        if selected_emotion != "All" and df_trans is not None:
            emotion_customers = df_trans[df_trans['actual_purchased_mood'] == selected_emotion]['customer_id'].unique()
            top_loyalists_data = top_loyalists_data[top_loyalists_data['customer_id'].isin(emotion_customers)]
        
        if len(top_loyalists_data) > 0:
            top_customers = top_loyalists_data.nlargest(15, 'purchase_count').copy()
            display_cols = ['customer_id', 'age', 'segment', 'avg_spending', 'purchase_count']
            top_customers = top_customers[display_cols].reset_index(drop=True)
            
            if df_trans is not None and len(df_trans) > 0:
                emotions = []
                for cid in top_customers['customer_id']:
                    cust_trans = df_trans[df_trans['customer_id'] == cid]
                    if len(cust_trans) > 0:
                        mode_emotion = cust_trans['actual_purchased_mood'].mode()
                        emotion = mode_emotion[0] if len(mode_emotion) > 0 else 'N/A'
                    else:
                        emotion = 'N/A'
                    emotions.append(emotion)
                top_customers['emotion'] = emotions
                top_customers = top_customers[['customer_id', 'age', 'segment', 'emotion', 'avg_spending', 'purchase_count']]
            
            top_customers.index = top_customers.index + 1
            top_customers.columns = ['Customer ID', 'Age', 'Segment', 'Emotion', 'Avg Spending', 'Purchases']
            st.dataframe(top_customers, use_container_width=True)
        else:
            st.info("No customers found")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 5: AI RECOMMENDATION ENGINE
# ============================================================================
elif page == "🤖 AI Recommendation":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI Recommendation Engine - Smart Discovery</div>', unsafe_allow_html=True)
    
    try:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            selected_emotion_rec = st.selectbox("Select Emotion", ["All"] + sorted(df_art['mood'].unique().tolist()), key="rec_emotion")
        with col2:
            selected_category_rec = st.selectbox("Select Category", ["All"] + sorted(df_art['section_name'].unique().tolist()), key="rec_cat")
        with col3:
            selected_group_rec = st.selectbox("Select Product Group", ["All"] + sorted(df_art['product_group_name'].unique().tolist()), key="rec_group")
        with col4:
            price_range_rec = st.slider("Price Range", 0.0, df_art['price'].max(), (0.0, df_art['price'].max()), key="rec_price")
        
        filtered_products = df_art.copy()
        if selected_emotion_rec != "All":
            filtered_products = filtered_products[filtered_products['mood'] == selected_emotion_rec]
        if selected_category_rec != "All":
            filtered_products = filtered_products[filtered_products['section_name'] == selected_category_rec]
        if selected_group_rec != "All":
            filtered_products = filtered_products[filtered_products['product_group_name'] == selected_group_rec]
        filtered_products = filtered_products[(filtered_products['price'] >= price_range_rec[0]) & (filtered_products['price'] <= price_range_rec[1])]
        
        st.divider()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📦 Products", len(filtered_products))
        with col2:
            st.metric("💰 Avg Price", f"${filtered_products['price'].mean():.2f}")
        with col3:
            st.metric("🔥 Avg Hotness", f"{filtered_products['hotness_score'].mean():.2f}")
        with col4:
            high_performers = len(filtered_products[filtered_products['hotness_score'] > 0.7])
            st.metric("⭐ High Performers", high_performers)
        with col5:
            revenue_potential = (filtered_products['price'] * filtered_products['hotness_score']).sum()
            st.metric("💵 Revenue Potential", f"${revenue_potential:.0f}")
        
        st.divider()
        
        if len(filtered_products) > 0:
            selected_product_name = st.selectbox("Select Product", filtered_products['prod_name'].unique())
            selected_product = filtered_products[filtered_products['prod_name'] == selected_product_name].iloc[0]
            
            st.subheader(f"📌 Main Product: {selected_product['prod_name']}")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.write(f"**Category:** {selected_product['section_name']}")
                st.write(f"**Group:** {selected_product['product_group_name']}")
                st.write(f"**Price:** ${selected_product['price']:.2f}")
                st.write(f"**Hotness Score:** {selected_product['hotness_score']:.2f}")
                st.write(f"**Emotion:** {selected_product['mood']}")
                if 'detail_desc' in selected_product and pd.notna(selected_product['detail_desc']):
                    with st.expander("📝 Product Description"):
                        st.write(selected_product['detail_desc'])
            
            with col2:
                st.metric("Price", f"${selected_product['price']:.2f}")
            with col3:
                st.metric("Hotness", f"{selected_product['hotness_score']:.2f}")
            
            st.divider()
            st.subheader("🎯 Smart Match Engine - Top 10 Similar Products")
            
            similar_products = filtered_products[
                (filtered_products['product_group_name'] == selected_product['product_group_name']) &
                (filtered_products['mood'] == selected_product['mood']) &
                (filtered_products['article_id'] != selected_product['article_id'])
            ].copy()
            
            similar_products['price_diff'] = abs(similar_products['price'] - selected_product['price'])
            similar_products['hotness_diff'] = abs(similar_products['hotness_score'] - selected_product['hotness_score'])
            similar_products['match_score'] = 100 - (
                (similar_products['price_diff'] / (selected_product['price'] + 1)) * 30 +
                (similar_products['hotness_diff'] / (selected_product['hotness_score'] + 1)) * 30 +
                (similar_products['price_diff'] / similar_products['price'].max()) * 20 +
                (similar_products['hotness_diff'] / similar_products['hotness_score'].max()) * 20
            )
            
            similar_products = similar_products.nlargest(10, 'match_score')
            
            if len(similar_products) > 0:
                cols = st.columns(5)
                for idx, (_, product) in enumerate(similar_products.iterrows()):
                    with cols[idx % 5]:
                        st.write(f"**{product['prod_name'][:20]}...**")
                        st.write(f"💰 ${product['price']:.2f}")
                        st.write(f"🔥 {product['hotness_score']:.2f}")
                        st.write(f"😊 {product['mood']}")
                        st.write(f"**Match: {product['match_score']:.0f}%**")
            else:
                st.info("No similar products found")
        else:
            st.info("No products match your filters")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 6: BUSINESS PERFORMANCE
# ============================================================================
elif page == "📈 Business Performance":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Performance & Financial Outlook</div>', unsafe_allow_html=True)
    
    try:
        selected_emotion_perf = st.selectbox("Select Emotion", ["All"] + sorted(df_art['mood'].unique().tolist()), key="perf_emotion")
        st.divider()
        
        perf_data = df_art.copy() if selected_emotion_perf == "All" else df_art[df_art['mood'] == selected_emotion_perf]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📦 Products", len(perf_data))
        with col2:
            revenue = (perf_data['price'] * perf_data['hotness_score']).sum()
            st.metric("💵 Revenue Potential", f"${revenue:.0f}")
        with col3:
            margin = (perf_data['price'] * 0.4 * perf_data['hotness_score']).sum()
            st.metric("📊 Margin Potential", f"${margin:.0f}")
        with col4:
            high_perf = len(perf_data[perf_data['hotness_score'] > 0.7])
            st.metric("⭐ High Performers", high_perf)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Revenue by Category")
            cat_revenue = perf_data.groupby('section_name').apply(lambda x: (x['price'] * x['hotness_score']).sum()).sort_values(ascending=False).head(10)
            fig_cat = px.bar(x=cat_revenue.values, y=cat_revenue.index, orientation='h')
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            st.subheader("Hotness Distribution")
            fig_hotness = px.histogram(perf_data, x='hotness_score', nbins=20)
            st.plotly_chart(fig_hotness, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

st.sidebar.divider()
st.sidebar.info("🎯 Deep Learning-Driven Fashion BI with Emotion Analytics")
