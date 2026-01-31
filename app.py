# SIDEBAR NAVIGATION
# ============================================================================
st.sidebar.markdown("## 🎯 H & M Navigation")
page = st.sidebar.radio(
    "Select Page",
    ["📊 Executive Pulse", "🔍 Inventory & Pricing", "😊 Emotion Analytics", 
     "👥 Customer DNA", "🤖 AI Recommendation", "📈 Performance & Financial"]
)

# ============================================================================
# PAGE 1: EXECUTIVE PULSE
# ============================================================================
if page == "📊 Executive Pulse":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Executive Pulse - Strategic Overview</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        df_customers = data.get('customer_dna_master')
        
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📦 Total SKUs", f"{len(df_articles):,}", "↑ 2.3%")
        with col2:
            st.metric("💰 Avg Price", f"${df_articles['price'].mean():.2f}", "↑ 1.2%")
        with col3:
            st.metric("🔥 Avg Hotness", f"{df_articles['hotness_score'].mean():.2f}", "↑ 0.8%")
        with col4:
            st.metric("👥 Customers", f"{len(df_customers):,}" if df_customers is not None else "N/A", "↑ 5.1%")
        with col5:
            df_articles['revenue_potential'] = df_articles['price'] * df_articles['hotness_score']
            st.metric("💵 Revenue Potential", f"${df_articles['revenue_potential'].sum():,.0f}", "↑ 3.4%")
        
        st.divider()
        
        st.subheader("😊 Emotion Matrix (Price vs Hotness vs Revenue)")
        
        emotion_stats = df_articles.groupby('mood').agg({
            'price': 'mean',
            'hotness_score': 'mean',
            'revenue_potential': 'sum',
            'article_id': 'count'
        }).reset_index()
        emotion_stats.columns = ['Emotion', 'Avg_Price', 'Avg_Hotness', 'Total_Revenue', 'Product_Count']
        
        fig_bubble = px.scatter(
            emotion_stats,
            x='Avg_Price',
            y='Avg_Hotness',
            size='Total_Revenue',
            color='Emotion',
            hover_data=['Product_Count', 'Total_Revenue'],
            title="Emotion Performance Matrix",
            labels={'Avg_Price': 'Average Price ($)', 'Avg_Hotness': 'Average Hotness Score'},
            color_discrete_sequence=px.colors.qualitative.Set2,
            size_max=60
        )
        fig_bubble.update_layout(height=500, showlegend=True)
        st.plotly_chart(fig_bubble, use_container_width=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Emotion Distribution**")
            emotion_counts = df_articles['mood'].value_counts()
            fig_dist = px.pie(
                values=emotion_counts.values,
                names=emotion_counts.index,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col2:
            st.markdown("**Revenue by Emotion**")
            revenue_by_emotion = df_articles.groupby('mood')['revenue_potential'].sum().sort_values(ascending=False)
            fig_revenue = px.bar(
                x=revenue_by_emotion.index,
                y=revenue_by_emotion.values,
                color=revenue_by_emotion.values,
                color_continuous_scale='Reds',
                labels={'x': 'Emotion', 'y': 'Revenue Potential ($)'}
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 2: INVENTORY & PRICING INTELLIGENCE
# ============================================================================
elif page == "🔍 Inventory & Pricing":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Inventory & Pricing Intelligence - 4-Tier Strategy</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        images_dir = data.get('images_dir')
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_emotion = st.selectbox(
                "Select Emotion",
                ["All"] + sorted(df_articles['mood'].unique().tolist()),
                key="inv_emotion"
            )
        
        with col2:
            selected_category = st.selectbox(
                "Category",
                ["All"] + sorted(df_articles['section_name'].unique().tolist())
            )
        
        with col3:
            selected_group = st.selectbox(
                "Product Group",
                ["All"] + sorted(df_articles['product_group_name'].unique().tolist())
            )
        
        # Filter data
        filtered_df = df_articles.copy()
        
        if selected_emotion != "All":
            filtered_df = filtered_df[filtered_df['mood'] == selected_emotion]
        
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df['section_name'] == selected_category]
        
        if selected_group != "All":
            filtered_df = filtered_df[filtered_df['product_group_name'] == selected_group]
        
        st.info(f"📊 Analyzing {len(filtered_df)} products")
        
        st.divider()
        
        # 4-Tier Strategy Buttons
        st.subheader("💰 4-Tier Pricing Strategy - Click to View Products")
        
        tier_data = {
            'premium': (0.8, 1.0, 'tier-premium', '💎 Premium Tier (>0.8)'),
            'trend': (0.5, 0.8, 'tier-trend', '🔥 Trend Tier (0.5-0.8)'),
            'stability': (0.3, 0.5, 'tier-stability', '⚖️ Stability Tier (0.3-0.5)'),
            'liquidation': (0.0, 0.3, 'tier-liquidation', '📉 Liquidation Tier (<0.3)')
        }
        
        cols = st.columns(4)
        
        for idx, (tier_key, (min_h, max_h, color_class, tier_label)) in enumerate(tier_data.items()):
            tier_products = filtered_df[
                (filtered_df['hotness_score'] >= min_h) &
                (filtered_df['hotness_score'] < max_h)
            ]
            
            avg_price = tier_products['price'].mean() if len(tier_products) > 0 else 0
            avg_hotness = tier_products['hotness_score'].mean() if len(tier_products) > 0 else 0
            
            with cols[idx]:
                if st.button(f"""
{tier_label}
📦 {len(tier_products)} products
💰 ${avg_price:.2f} avg
🔥 {avg_hotness:.2f} hotness
                """, key=f"tier_{tier_key}", use_container_width=True):
                    st.session_state.selected_tier = tier_key
        
        st.divider()
        
        # Display products for selected tier
        if st.session_state.selected_tier:
            tier_key = st.session_state.selected_tier
            min_h, max_h, color_class, tier_label = tier_data[tier_key]
            
            tier_products = filtered_df[
                (filtered_df['hotness_score'] >= min_h) &
                (filtered_df['hotness_score'] < max_h)
            ].sort_values('hotness_score', ascending=False)
            
            st.markdown(f"### {tier_label} - Top Products")
            
            if len(tier_products) > 0:
                cols = st.columns(5)
                
                for idx, (_, product) in enumerate(tier_products.head(20).iterrows()):
                    col_idx = idx % 5
                    
                    with cols[col_idx]:
                        with st.container(border=True):
                            image_path = get_image_path(product['article_id'], images_dir)
                            if image_path:
                                st.image(image_path, use_column_width=True)
                            else:
                                st.info("📷 No image")
                            
                            st.markdown(f"**{product['prod_name'][:25]}...**")
                            st.write(f"💰 ${product['price']:.2f}")
                            st.write(f"🔥 {product['hotness_score']:.2f}")
                            st.write(f"😊 {product['mood']}")
            else:
                st.warning("No products in this tier")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 3: DEEP EMOTION ANALYTICS
# ============================================================================
elif page == "😊 Emotion Analytics":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Deep Emotion Analytics</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        
        selected_emotion = st.selectbox(
            "Select Emotion",
            ["All"] + sorted(df_articles['mood'].unique().tolist()),
            key="emotion_select"
        )
        
        if selected_emotion == "All":
            emotion_df = df_articles
            title_suffix = "All Emotions"
        else:
            emotion_df = df_articles[df_articles['mood'] == selected_emotion]
            title_suffix = f"{selected_emotion}"
        
        st.info(f"📊 Analyzing {len(emotion_df)} products - {title_suffix}")
        
        st.divider()
        
        st.subheader("📊 Emotion Statistics")
        
        emotion_stats = df_articles.groupby('mood')['price'].agg([
            ('Mean', 'mean'),
            ('Median', 'median'),
            ('Std Dev', 'std'),
            ('Min', 'min'),
            ('Max', 'max'),
            ('Count', 'count')
        ]).round(2)
        
        st.dataframe(emotion_stats, use_container_width=True)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Category Affinity by Emotion**")
            category_affinity = emotion_df['section_name'].value_counts().head(10)
            fig_cat = px.bar(
                x=category_affinity.values,
                y=category_affinity.index,
                orientation='h',
                color=category_affinity.values,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_cat, use_container_width=True)
        
        with col2:
            st.markdown("**Price Distribution**")
            fig_price = px.histogram(
                emotion_df, x='price', nbins=30,
                color_discrete_sequence=['#E50019']
            )
            st.plotly_chart(fig_price, use_container_width=True)
        
        st.divider()
        
        st.subheader("⭐ Top 10 Emotion Heroes")
        
        top_products = emotion_df.nlargest(10, 'hotness_score')[[
            'prod_name', 'section_name', 'price', 'hotness_score', 'mood'
        ]].reset_index(drop=True)
        
        top_products.index = top_products.index + 1
        st.dataframe(top_products, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 4: CUSTOMER DNA & BEHAVIOR
# ============================================================================
elif page == "👥 Customer DNA":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Customer DNA & Behavior</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        df_customers = data.get('customer_dna_master')
        df_transactions = data.get('customer_test_validation')
        
        if df_customers is None:
            st.warning("Customer data not available")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                selected_emotion = st.selectbox(
                    "Select Emotion",
                    ["All"] + sorted(df_articles['mood'].unique().tolist()),
                    key="cust_emotion"
                )
            
            with col2:
                selected_segment = st.selectbox(
                    "Customer Segment",
                    ["All"] + sorted(df_customers['segment'].unique().tolist()) if 'segment' in df_customers.columns else ["All"],
                    key="cust_segment"
                )
            
            # Filter customers based on segment
            filtered_customers = df_customers.copy()
            if selected_segment != "All":
                filtered_customers = filtered_customers[filtered_customers['segment'] == selected_segment]
            
            # Filter transactions by emotion if available
            filtered_transactions = df_transactions.copy() if df_transactions is not None else None
            if selected_emotion != "All" and filtered_transactions is not None:
                # Filter transactions by exact emotion match
                filtered_trans_by_emotion = filtered_transactions[filtered_transactions['actual_purchased_mood'] == selected_emotion]
                # Get customers who bought from this emotion
                emotion_customers = filtered_trans_by_emotion['customer_id'].unique()
                filtered_customers = filtered_customers[filtered_customers['customer_id'].isin(emotion_customers)]
            
            st.divider()
            
            # Dynamic KPIs based on filters
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
                    fig_scatter = px.scatter(
                        filtered_customers,
                        x='age',
                        y='avg_spending',
                        color='segment' if 'segment' in filtered_customers.columns else None,
                        hover_data=['purchase_count'],
                        color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
                    )
                    st.plotly_chart(fig_scatter, use_container_width=True)
                else:
                    st.info("No data available for selected filters")
            
            with col2:
                st.markdown("**Segment Distribution**")
                if 'segment' in filtered_customers.columns and len(filtered_customers) > 0:
                    segment_counts = filtered_customers['segment'].value_counts()
                    fig_segment = px.pie(
                        values=segment_counts.values,
                        names=segment_counts.index,
                        color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'}
                    )
                    st.plotly_chart(fig_segment, use_container_width=True)
                else:
                    st.info("No segment data available")
            
            st.divider()
            
            st.subheader("⭐ Top Loyalists")
            
            # Build Top Loyalists based on BOTH emotion and segment filters
            top_loyalists_data = df_customers.copy()
            
            # Apply segment filter
            if selected_segment != "All":
                top_loyalists_data = top_loyalists_data[top_loyalists_data['segment'] == selected_segment]
            
            # Apply emotion filter
            if selected_emotion != "All" and df_transactions is not None:
                emotion_customers = df_transactions[df_transactions['actual_purchased_mood'] == selected_emotion]['customer_id'].unique()
                top_loyalists_data = top_loyalists_data[top_loyalists_data['customer_id'].isin(emotion_customers)]
            
            if len(top_loyalists_data) > 0:
                top_customers = top_loyalists_data.nlargest(15, 'purchase_count').copy()
                
                # Select columns
                display_cols = ['customer_id', 'age', 'segment', 'avg_spending', 'purchase_count']
                top_customers = top_customers[display_cols].reset_index(drop=True)
                
                # Add emotion column if transactions available
                if df_transactions is not None and len(df_transactions) > 0:
                    emotions = []
                    for cid in top_customers['customer_id']:
                        cust_trans = df_transactions[df_transactions['customer_id'] == cid]
                        if len(cust_trans) > 0:
                            mode_emotion = cust_trans['actual_purchased_mood'].mode()
                            emotion = mode_emotion[0] if len(mode_emotion) > 0 else 'N/A'
                        else:
                            emotion = 'N/A'
                        emotions.append(emotion)
                    top_customers['emotion'] = emotions
                    top_customers = top_customers[['customer_id', 'age', 'segment', 'emotion', 'avg_spending', 'purchase_count']]
                
                # Format display
                top_customers.index = top_customers.index + 1
                top_customers.columns = ['Customer ID', 'Age', 'Segment', 'Emotion', 'Avg Spending', 'Purchases']
                st.dataframe(top_customers, use_container_width=True)
            else:
                st.info("No customers found for selected filters")
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 5: AI RECOMMENDATION ENGINE
# ============================================================================
elif page == "🤖 AI Recommendation":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">AI Recommendation Engine - Smart Discovery</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        images_dir = data.get('images_dir')
        
        st.subheader("🔍 Product Selection")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            selected_emotion = st.selectbox(
                "Emotion",
                sorted(df_articles['mood'].unique().tolist()),
                key="rec_emotion"
            )
        
        with col2:
            selected_category = st.selectbox(
                "Category",
                ["All"] + sorted(df_articles['section_name'].unique().tolist()),
                key="rec_cat"
            )
        
        with col3:
            selected_group = st.selectbox(
                "Product Group",
                ["All"] + sorted(df_articles['product_group_name'].unique().tolist()),
                key="rec_group"
            )
        
        with col4:
            price_range = st.slider(
                "Price Range",
                float(df_articles['price'].min()),
                float(df_articles['price'].max()),
                (float(df_articles['price'].min()), float(df_articles['price'].max())),
                key="rec_price"
            )
        
        # Filter products
        filtered_products = df_articles[df_articles['mood'] == selected_emotion].copy()
        
        if selected_category != "All":
            filtered_products = filtered_products[filtered_products['section_name'] == selected_category]
        
        if selected_group != "All":
            filtered_products = filtered_products[filtered_products['product_group_name'] == selected_group]
        
        filtered_products = filtered_products[
            (filtered_products['price'] >= price_range[0]) &
            (filtered_products['price'] <= price_range[1])
        ]
        
        # Dynamic KPIs based on filters
        st.divider()
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📦 Products", f"{len(filtered_products):,}")
        with col2:
            avg_price = filtered_products['price'].mean() if len(filtered_products) > 0 else 0
            st.metric("💰 Avg Price", f"${avg_price:.2f}")
        with col3:
            avg_hotness = filtered_products['hotness_score'].mean() if len(filtered_products) > 0 else 0
            st.metric("🔥 Avg Hotness", f"{avg_hotness:.2f}")
        with col4:
            high_perf = len(filtered_products[filtered_products['hotness_score'] > 0.7])
            st.metric("⭐ High Performers", high_perf)
        with col5:
            filtered_products['revenue'] = filtered_products['price'] * filtered_products['hotness_score']
            total_revenue = filtered_products['revenue'].sum() if len(filtered_products) > 0 else 0
            st.metric("💵 Revenue Potential", f"${total_revenue:,.0f}")
        
        st.divider()
        
        if len(filtered_products) == 0:
            st.warning("No products found with selected filters")
        else:
            selected_product_name = st.selectbox(
                "Choose Product",
                filtered_products['prod_name'].tolist(),
                key="product_select"
            )
            
            selected_product = df_articles[df_articles['prod_name'] == selected_product_name].iloc[0]
            
            st.divider()
            
            st.subheader("📦 Main Product Spotlight")
            
            col_img, col_info = st.columns([1.2, 2])
            
            with col_img:
                image_path = get_image_path(selected_product['article_id'], images_dir)
                if image_path:
                    st.image(image_path, use_column_width=True)
                else:
                    st.info("📷 Image not available")
            
            with col_info:
                st.markdown(f"""
                ### {selected_product['prod_name']}
                
                **Category:** {selected_product['section_name']}  
                **Group:** {selected_product['product_group_name']}  
                **Emotion:** {selected_product['mood']}  
                """)
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.markdown(f"<div class='metric-badge'>💰 ${selected_product['price']:.2f}</div>", unsafe_allow_html=True)
                with col_b:
                    st.markdown(f"<div class='metric-badge'>🔥 {selected_product['hotness_score']:.2f}</div>", unsafe_allow_html=True)
                with col_c:
                    tier_name, _, _ = get_tier_info(selected_product['hotness_score'])
                    st.markdown(f"<div class='metric-badge'>{tier_name}</div>", unsafe_allow_html=True)
                
                with st.expander("📝 Full Description"):
                    st.write(selected_product.get('detail_desc', 'No description available'))
            
            st.divider()
            
            st.subheader("🎯 Smart Match Engine - Top 10 Similar Products")
            
            recommendations = get_smart_recommendations(selected_product, df_articles, n_recommendations=10)
            
            if len(recommendations) == 0:
                st.warning("No similar products found")
            else:
                cols = st.columns(5)
                
                for idx, (_, product) in enumerate(recommendations.iterrows()):
                    col_idx = idx % 5
                    
                    with cols[col_idx]:
                        with st.container(border=True):
                            image_path = get_image_path(product['article_id'], images_dir)
                            if image_path:
                                st.image(image_path, use_column_width=True)
                            else:
                                st.info("📷")
                            
                            st.markdown(f"**{product['prod_name'][:18]}...**")
                            st.write(f"💰 ${product['price']:.2f}")
                            st.write(f"🔥 {product['hotness_score']:.2f}")
                            
                            match_pct = product['match_score'] * 100
                            st.markdown(
                                f"<div style='background: linear-gradient(135deg, #E50019 0%, #FF6B6B 100%); color: white; padding: 8px; border-radius: 10px; text-align: center; font-weight: bold; margin-top: 8px;'>✅ {match_pct:.0f}% Match</div>",
                                unsafe_allow_html=True
                            )
                            
                            if st.button("View", key=f"view_{product['article_id']}", use_container_width=True):
                                st.session_state.show_detail_modal = True
                                st.session_state.detail_product_id = product['article_id']
                                st.rerun()
            
            # Detail Modal for Recommended Products
            if st.session_state.show_detail_modal and st.session_state.detail_product_id:
                detail_product = df_articles[df_articles['article_id'] == st.session_state.detail_product_id]
                
                if len(detail_product) > 0:
                    detail_product = detail_product.iloc[0]
                    
                    st.divider()
                    st.subheader(f"🔍 Detailed View - {detail_product['prod_name']}")
                    
                    col_img, col_info = st.columns([1, 2])
                    
                    with col_img:
                        image_path = get_image_path(detail_product['article_id'], images_dir)
                        if image_path:
                            st.image(image_path, use_column_width=True)
                        else:
                            st.info("📷 Image not available")
                    
                    with col_info:
                        st.markdown(f"""
                        ### {detail_product['prod_name']}
                        
                        **Category:** {detail_product['section_name']}  
                        **Group:** {detail_product['product_group_name']}  
                        **Emotion:** {detail_product['mood']}  
                        **Article ID:** {detail_product['article_id']}  
                        
                        **Pricing & Performance:**
                        - Price: ${detail_product['price']:.2f}
                        - Hotness Score: {detail_product['hotness_score']:.2f}
                        - Tier: {get_tier_info(detail_product['hotness_score'])[0]}
                        """)
                    
                    st.markdown("**📝 Full Description:**")
                    st.write(detail_product.get('detail_desc', 'No description available'))
                    
                    if st.button("Close Details", key="close_detail"):
                        st.session_state.show_detail_modal = False
                        st.session_state.detail_product_id = None
                        st.rerun()
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# PAGE 6: PERFORMANCE & FINANCIAL OUTLOOK
# ============================================================================
elif page == "📈 Performance & Financial":
    st.markdown('<div class="header-title">H & M Fashion BI</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Performance & Financial Outlook</div>', unsafe_allow_html=True)
    
    try:
        df_articles = data['article_master_web'].copy()
        
        selected_emotion = st.selectbox(
            "Select Emotion",
            ["All"] + sorted(df_articles['mood'].unique().tolist()),
            key="perf_emotion"
        )
        
        if selected_emotion == "All":
            analysis_df = df_articles
        else:
            analysis_df = df_articles[df_articles['mood'] == selected_emotion]
        
        analysis_df['revenue_potential'] = analysis_df['price'] * analysis_df['hotness_score']
        analysis_df['estimated_margin'] = analysis_df['price'] * 0.4
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Revenue Potential", f"${analysis_df['revenue_potential'].sum():,.0f}")
        with col2:
            st.metric("📊 Avg Margin", f"${analysis_df['estimated_margin'].mean():.2f}")
        with col3:
            high_performers = len(analysis_df[analysis_df['hotness_score'] > 0.7])
            st.metric("⭐ High Performers", high_performers)
        with col4:
            low_performers = len(analysis_df[analysis_df['hotness_score'] < 0.3])
            st.metric("📉 Low Performers", low_performers)
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Revenue by Category**")
            revenue_by_cat = analysis_df.groupby('section_name')['revenue_potential'].sum().sort_values(ascending=False).head(15)
            fig_revenue = px.bar(
                x=revenue_by_cat.values,
                y=revenue_by_cat.index,
                orientation='h',
                color=revenue_by_cat.values,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig_revenue, use_container_width=True)
        
        with col2:
            st.markdown("**Hotness Performance**")
            hotness_bins = pd.cut(analysis_df['hotness_score'],
                                 bins=[0, 0.3, 0.5, 0.7, 1.0],
                                 labels=['Low', 'Medium', 'High', 'Very High'])
            hotness_dist = hotness_bins.value_counts()
            fig_hotness = px.pie(
                values=hotness_dist.values,
                names=hotness_dist.index,
                color_discrete_sequence=['#FF6B6B', '#FFA500', '#FFD700', '#E50019']
            )
            st.plotly_chart(fig_hotness, use_container_width=True)
        
        st.divider()
        
        st.subheader("📦 Inventory Health & Optimization")
        
        analysis_df['performance_tier'] = pd.cut(
            analysis_df['hotness_score'],
            bins=[0, 0.3, 0.5, 0.7, 1.0],
            labels=['Low', 'Medium', 'High', 'Very High']
        )
        
        inventory_rec = analysis_df.groupby('performance_tier').agg({
            'article_id': 'count',
            'price': 'mean',
            'hotness_score': 'mean',
            'revenue_potential': 'sum'
        }).round(2)
        
        inventory_rec.columns = ['Product Count', 'Avg Price', 'Avg Hotness', 'Total Revenue']
        st.dataframe(inventory_rec, use_container_width=True)
        
        st.markdown("""
        <div class="insight-box">
        <strong>📋 Inventory Recommendations:</strong>
        <ul>
        <li><strong>Very High:</strong> Increase stock 30-50%</li>
        <li><strong>High:</strong> Maintain levels</li>
        <li><strong>Medium:</strong> Reduce stock 20%</li>
        <li><strong>Low:</strong> Discontinue or clearance</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")

# ============================================================================
# FOOTER
# ============================================================================
st.divider()
st.markdown("""
    <div style="text-align: center; color: #999; font-size: 0.9rem; margin-top: 2rem;">
    <p><strong>H & M Fashion BI Dashboard</strong></p>
    <p>Deep Learning-Driven Business Intelligence For Personalized Fashion Retail</p>
    <p>Integrating Emotion Analytics And Recommendation System</p>
    </div>
""", unsafe_allow_html=True)
