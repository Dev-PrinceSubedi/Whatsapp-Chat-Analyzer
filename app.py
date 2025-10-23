from io import StringIO
from wordcloud import WordCloud
import preprocessor
import pandas as pd
import streamlit as st
import helper
import matplotlib.pyplot as plt
import seaborn as sns
import guide

st.set_page_config(layout="wide")


from helper import most_common_words

st.markdown("""
    <style>
        [data-testid="stSidebar"] > div:first-child {
            display: flex;
            flex-direction: column;
            height: 100vh;  /* Full sidebar height */
        }
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.markdown(
    "<span style='text-align: left; color: #25D366;'>Chat_</span><span></span> <span>Analytics</span>",
    unsafe_allow_html=True
)

uploaded_file = st.sidebar.file_uploader(
    "📂 Choose a WhatsApp chat file",
    type=["txt"],
    accept_multiple_files=False,
    help="Upload your exported WhatsApp chat (.txt file)",
    label_visibility="visible"
)

# Initialize session state
if 'analyzed_user' not in st.session_state:
    st.session_state.analyzed_user = None

# Reset analysis when a new file is uploaded
if uploaded_file is not None:
    file_id = uploaded_file.file_id
    if 'current_file_id' not in st.session_state or st.session_state.current_file_id != file_id:
        st.session_state.current_file_id = file_id
        st.session_state.analyzed_user = None

if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")

    try:
        df = preprocessor.preprocess(data)

        # Check if dataframe is empty or doesn't have required columns
        if df.empty or 'User' not in df.columns or 'Message' not in df.columns:
            st.error("❌ Please upload a valid WhatsApp chat export file!")
            st.info("💡 Make sure you've exported the chat correctly from WhatsApp. Check the tutorial below for help.")
            guide.show_guide()
            st.stop()

        # fetching unique user
        user_list = df["User"].unique().tolist()
        user_list.sort()
        user_list.insert(0, "Overall")

    except Exception as e:
        st.error("❌ Please upload a valid WhatsApp chat export file!")
        st.info("💡 Make sure you've exported the chat correctly from WhatsApp. Check the tutorial below for help.")
        guide.show_guide()
        st.stop()

    selected_user = st.sidebar.selectbox("Show analysis wrt", user_list)

    # Button is always visible when file is uploaded
    if st.sidebar.button("Show analysis"):
        st.session_state.analyzed_user = selected_user

    # Display analysis only if button has been clicked
    if st.session_state.analyzed_user is not None:
        # CRITICAL: Use the analyzed_user from session state for ALL analysis
        display_user = st.session_state.analyzed_user

        # Stats Area
        st.markdown(
            f"<h1> Top Statistics: <span style='color: #25D366; font-weight: bold; font-size: 1.1em;'>{display_user}</span></h1>",
            unsafe_allow_html=True)

        num_messages, num_words, num_media, num_links = helper.fetch_stats(display_user, df)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(label="Total Messages", value=num_messages)

        with col2:
            st.metric(label="Total Words", value=num_words)

        with col3:
            st.metric(label="Media Shared", value=num_media)

        with col4:
            st.metric(label="Links Shared", value=num_links)

        # Finding the busiest user in the group(Only for Overall)
        if display_user == "Overall":
            st.markdown("---")
            st.title("Most Busy Users")

            x, new_df = helper.most_busy_users(df)

            # Calculate dynamic height based on number of users
            num_users = len(new_df)
            row_height = 35  # pixels per row
            header_height = 38  # header height
            dynamic_height = (num_users * row_height) + header_height

            col1, col2 = st.columns(2)

            with col1:
                # Calculate figure height to match dataframe
                fig_height = dynamic_height / 72  # Convert pixels to inches (72 DPI)
                fig, ax = plt.subplots(figsize=(5, fig_height))
                ax.bar(x.index, x.values, color='steelblue')
                plt.xticks(rotation=45, ha='right')
                ax.set_xlabel('Users')
                ax.set_ylabel('No. of Messages')
                plt.tight_layout()
                st.pyplot(fig)

            with col2:
                # Format the percentage values to include % sign
                new_df_display = new_df.copy()
                new_df_display = new_df_display.rename(columns={'Percent': 'Percentage'})
                new_df_display['Percentage'] = new_df_display['Percentage'].apply(lambda x: f"{x}%")
                # Reset index to start from 1
                new_df_display.index = range(1, len(new_df_display) + 1)
                st.dataframe(new_df_display, height=dynamic_height, use_container_width=True)

        # Timeline Analysis
        st.markdown("---")
        st.title(" Message Timeline")

        # Monthly Timeline - USE display_user
        timeline = helper.monthly_timeline(display_user, df)

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(timeline["time"], timeline["Message"], marker='o', linewidth=2, markersize=6, color='#4ECDC4')

        # Fill area under the line
        ax.fill_between(timeline["time"], timeline["Message"], alpha=0.3, color='#4ECDC4')

        # Styling
        ax.set_xlabel('Month', fontsize=14, fontweight='bold')
        ax.set_ylabel('Number of Messages', fontsize=14, fontweight='bold')
        ax.set_title('Message Activity Over Time', fontsize=16, fontweight='bold', pad=20)

        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right', fontsize=10)
        plt.yticks(fontsize=10)

        # Add grid for better readability
        ax.grid(True, alpha=0.3, linestyle='--')

        # Add background color
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('white')

        # Tight layout to prevent label cutoff
        plt.tight_layout()

        st.pyplot(fig)

        col1, col2 = st.columns(2)

        # ------------------- Most Active Weekday -------------------
        with col1:
            st.subheader(" Most Active Weekday")
            weekday_counts = helper.most_active_weekdays(display_user, df)
            weekday_counts.index = weekday_counts.index.str[:3]  # Mon, Tue, Wed...

            fig, ax = plt.subplots()
            ax.bar(weekday_counts.index, weekday_counts.values, color='skyblue')
            for i, v in enumerate(weekday_counts.values):
                ax.text(i, v + 0.5, str(v), ha='center', va='bottom', fontsize=9)

            ax.set_ylim(0,
                        max(weekday_counts.values.max(),
                            helper.most_active_months(display_user, df).values.max()) * 1.1)
            ax.set_xlabel("Day of the Week")
            ax.set_ylabel("Number of Messages")
            ax.set_title("Messages per Weekday", fontsize=12, fontweight='bold')
            ax.grid(axis='y', linestyle='--', alpha=0.3)

            # Stretch to fill the column
            fig.tight_layout(pad=1.0)
            st.pyplot(fig, use_container_width=True)

        # ------------------- Most Active Month -------------------
        with col2:
            st.subheader(" Most Active Month")
            month_counts = helper.most_active_months(display_user, df)
            month_counts_sorted = month_counts[::-1]

            fig, ax = plt.subplots()
            ax.bar(month_counts_sorted.index, month_counts_sorted.values, color='orange')
            for i, v in enumerate(month_counts_sorted.values):
                ax.text(i, v + 0.5, str(v), ha='center', va='bottom', fontsize=9)

            ax.set_ylim(0, max(weekday_counts.values.max(), month_counts_sorted.values.max()) * 1.1)
            ax.set_xlabel("Month")
            ax.set_ylabel("Number of Messages")
            ax.set_title("Messages per Month", fontsize=12, fontweight='bold')
            plt.xticks(rotation=45)
            ax.grid(axis='y', linestyle='--', alpha=0.3)

            # Stretch to fill the column
            fig.tight_layout(pad=1.0)
            st.pyplot(fig, use_container_width=True)

        # word cloud
        st.markdown("---")
        st.title("Word Cloud")
        # Cache the wordcloud to prevent regeneration on sidebar changes
        df_wc = helper.create_wordcloud(display_user, df.copy())
        if df_wc is not None:
            fig, ax = plt.subplots()
            ax.imshow(df_wc)
            ax.axis("off")
            st.pyplot(fig)
        else:
            st.write("No words available to generate word cloud!")

        # Most_Common_Words - USE display_user
        st.title("Most Common Words")
        most_common_df = helper.most_common_words(display_user, df)

        if not most_common_df.empty:
            fig, ax = plt.subplots(figsize=(10, 8))
            bars = ax.barh(most_common_df[0], most_common_df[1], color='skyblue')

            # Add the exact numbers at the end of each bar
            for i, (word, count) in enumerate(zip(most_common_df[0], most_common_df[1])):
                ax.text(count, i, f' {count}', va='center', fontsize=10)

            ax.set_xlabel('Count', fontsize=12)
            ax.set_ylabel('Words', fontsize=12)
            ax.set_title('Most Common Words', fontsize=14)
            ax.invert_yaxis()

            st.pyplot(fig)
        else:
            st.write("No common words found!")

        # Emoji Analysis
        st.title("Emoji Analysis")
        emoji_df = helper.emoji_helper(display_user, df)

        if not emoji_df.empty:
            styled_df = emoji_df.style \
                .background_gradient(subset=['Count'], cmap='YlOrRd') \
                .background_gradient(subset=['Percentage'], cmap='Greens') \
                .set_properties(subset=['Count', 'Percentage'], **{
                'font-weight': 'bold',
                'font-size': '30px',
                'text-align': 'center'
            }) \
                .set_properties(subset=['Emoji'], **{
                'font-size': '30px',
                'text-align': 'center'
            }) \
                .format({'Percentage': '{:.2f}%'})

            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.write("No emojis found in the chat!")

        st.markdown("---")
        st.title(f" {display_user}'s Most Active Times")

        # Heatmap - USE display_user
        heatmap_data = helper.activity_heatmap_normalized(display_user, df)

        fig, ax = plt.subplots(figsize=(12, 6))
        sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=.5, cbar=True, ax=ax,
                    yticklabels=True, xticklabels=True)

        ax.set_xlabel("Hour of Day")
        ax.set_ylabel("Weekday")
        ax.set_title(f"Most Active Times for {display_user}")

        st.pyplot(fig, use_container_width=True)
        st.markdown("---")

    else:
        # Show tutorial when "Show analysis" button hasn't been clicked yet
        guide.show_guide()

else:
    # Show tutorial when no file is uploaded
    guide.show_guide()