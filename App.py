import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Page configuration
st.set_page_config(
    page_title="CHS Complaint Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS for styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #ffffff;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
        text-align: center;
    }
    .metric-title { font-size: 0.85rem; color: #64748b; font-weight: 600; margin-bottom: 4px; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #0f172a; }
    .metric-sub { font-size: 0.8rem; color: #10b981; font-weight: 500; }
    </style>
""", unsafe_allow_html=True)

# ----------------- DATA LOADER & GENERATOR -----------------
@st.cache_data
def get_sample_data():
    """Generates realistic sample data if no file is uploaded."""
    np.random.seed(42)
    categories = ['Supply Related', 'Smart Meter Related', 'Bill Related', 'Meter Related', 'Miscellaneous', 'Roof Top Solar']
    discoms = ['NBPDCL', 'SBPDCL']
    divisions_nbpdcl = ['Sitamarhi', 'Hazipur', 'Bettiah', 'Siwan', 'Muzaffarpur-East', 'Chapra(W)']
    divisions_sbpdcl = ['Bhagalpur(U)', 'Jamui', 'Sasaram', 'Gaya(U)', 'Aurangabad', 'Buxar']
    
    dates = pd.date_range(end=pd.Timestamp.today(), periods=30)
    data = []
    
    for d in dates:
        for _ in range(np.random.randint(60, 120)):
            disc = np.random.choice(discoms, p=[0.6, 0.4])
            div = np.random.choice(divisions_nbpdcl if disc == 'NBPDCL' else divisions_sbpdcl)
            cat = np.random.choice(categories, p=[0.45, 0.25, 0.15, 0.08, 0.05, 0.02])
            status = np.random.choice(['Closed', 'Pending'], p=[0.94, 0.06])
            within_sla = True if status == 'Closed' and np.random.rand() > 0.3 else False
            
            data.append({
                'Date': d,
                'DISCOM': disc,
                'Division': div,
                'Category': cat,
                'Status': status,
                'Closed_Within_SLA': within_sla
            })
    return pd.DataFrame(data)

# ----------------- SIDEBAR: UPLOADER & CONTROLS -----------------
st.sidebar.title("⚡ CHS Complaints Dashboard")
uploaded_file = st.sidebar.file_uploader("Upload Daily Dump (.xlsx / .csv)", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        st.sidebar.success("Custom data loaded!")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")
        df = get_sample_data()
else:
    df = get_sample_data()
    st.sidebar.info("Viewing sample demo data. Upload your file to update.")

# DISCOM Filter
discom_choice = st.sidebar.radio("Select DISCOM:", ["All Bihar", "NBPDCL", "SBPDCL"])
if discom_choice != "All Bihar":
    filtered_df = df[df['DISCOM'] == discom_choice]
else:
    filtered_df = df

# ----------------- MAIN DASHBOARD HEADER -----------------
st.title("⚡ CHS Complaint Dashboard")
st.caption(f"Consumer Complaint Monitoring System • Scope: **{discom_choice}**")

# ----------------- TOP METRIC RIBBON -----------------
total_registered = len(filtered_df)
total_closed = len(filtered_df[filtered_df['Status'] == 'Closed'])
total_pending = len(filtered_df[filtered_df['Status'] == 'Pending'])
disposal_rate = (total_closed / total_registered * 100) if total_registered > 0 else 0

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">DISPOSAL RATE</div>
            <div class="metric-value">{disposal_rate:.1f}%</div>
            <div class="metric-sub">{total_closed:,} of {total_registered:,} closed</div>
        </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">TOTAL REGISTERED</div>
            <div class="metric-value">{total_registered:,}</div>
            <div class="metric-sub">Across 30 days</div>
        </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">TOTAL PENDING</div>
            <div class="metric-value" style="color: #ef4444;">{total_pending:,}</div>
            <div class="metric-sub" style="color: #ef4444;">Active Backlog</div>
        </div>
    """, unsafe_allow_html=True)

with kpi4:
    sla_closed = len(filtered_df[filtered_df['Closed_Within_SLA'] == True])
    sla_pct = (sla_closed / total_closed * 100) if total_closed > 0 else 0
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">CLOSED WITHIN TIME LIMIT</div>
            <div class="metric-value">{sla_pct:.1f}%</div>
            <div class="metric-sub">{sla_closed:,} complaints</div>
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# ----------------- 30-DAY DAILY COMPLAINT TREND -----------------
st.subheader("Daily Complaint Trend — Last 30 Days")

daily_cat = filtered_df.groupby([filtered_df['Date'].dt.date, 'Category']).size().reset_index(name='Count')
fig_daily = px.bar(
    daily_cat,
    x='Date',
    y='Count',
    color='Category',
    color_discrete_map={
        'Supply Related': '#f59e0b',
        'Smart Meter Related': '#eab308',
        'Bill Related': '#f43f5e',
        'Meter Related': '#a855f7',
        'Miscellaneous': '#0ea5e9',
        'Roof Top Solar': '#10b981'
    },
    barmode='stack',
    height=340
)
fig_daily.update_layout(margin=dict(l=20, r=20, t=10, b=20), legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig_daily, use_container_width=True)

# ----------------- LOWER SECTION: BREAKDOWNS -----------------
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("Category-wise Distribution")
    cat_summary = filtered_df.groupby('Category').agg(
        Total=('Status', 'count'),
        Closed=('Status', lambda x: (x == 'Closed').sum())
    ).reset_index()
    cat_summary['Disposed %'] = ((cat_summary['Closed'] / cat_summary['Total']) * 100).round(1).astype(str) + '%'
    st.dataframe(cat_summary[['Category', 'Total', 'Disposed %']], use_container_width=True, hide_index=True)

with col_right:
    st.subheader("Top Divisions by Complaint Volume")
    div_summary = filtered_df.groupby('Division').size().reset_index(name='Total Complaints')
    div_summary = div_summary.sort_values(by='Total Complaints', ascending=False).head(8)
    
    fig_div = px.bar(
        div_summary,
        x='Total Complaints',
        y='Division',
        orientation='h',
        text='Total Complaints',
        color_discrete_sequence=['#f97316']
    )
    fig_div.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=10, b=20), height=300)
    st.plotly_chart(fig_div, use_container_width=True)