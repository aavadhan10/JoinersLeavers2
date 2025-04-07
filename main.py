import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import io

# Set page configuration
st.set_page_config(
    page_title="Rimon Personnel Changes Dashboard",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 1rem;
        text-align: center;
    }
    .kpi-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin-bottom: 1rem;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: 600;
    }
    .kpi-title {
        font-size: 1rem;
        color: #6B7280;
    }
    .green-text {
        color: #10B981;
    }
    .red-text {
        color: #EF4444;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E3A8A;
        margin: 1.5rem 0 1rem 0;
        border-bottom: 2px solid #E5E7EB;
        padding-bottom: 0.5rem;
    }
    .personnel-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }
    .personnel-table th {
        background-color: #1E3A8A;
        color: white;
        text-align: left;
        padding: 10px;
    }
    .personnel-table td {
        padding: 8px 10px;
        border-bottom: 1px solid #E5E7EB;
    }
    .personnel-table tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    .join-row {
        background-color: rgba(16, 185, 129, 0.1) !important;
    }
    .leave-row {
        background-color: rgba(239, 68, 68, 0.1) !important;
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-join {
        background-color: #10B981;
        color: white;
    }
    .badge-leave {
        background-color: #EF4444;
        color: white;
    }
    .download-button {
        background-color: #1E40AF;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        text-decoration: none;
        display: inline-block;
        margin-top: 1rem;
    }
    .filter-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Safe function to get unique values from a column
def safe_get_unique(df, column_name):
    try:
        if column_name in df.columns:
            values = df[column_name].dropna().unique().tolist()
            if len(values) > 0:
                if isinstance(values[0], str):
                    return sorted(values)
                return sorted(values, key=lambda x: str(x))
        return []
    except:
        return []

# Load invoice data
@st.cache_data(ttl=3600)  # Cache data for 1 hour
def load_invoice_data():
    try:
        # Load the actual data from CSV file
        df = pd.read_csv("Cleaned_Invoice_Data.csv", encoding='utf-8')
        
        # Cleanup column names - remove any leading/trailing whitespace
        df.columns = df.columns.str.strip()
        
        # Fix the TTM column if it exists
        if 'TTM?' in df.columns:
            df.rename(columns={'TTM?': 'TTM'}, inplace=True)
            
        # Clean data - handle currency symbols and convert to numeric
        money_columns = [
            'Invoice_Total_in_USD', 'Invoice_Labor_Total_in_USD', 
            'Invoice_Expense_Total_in_USD', 'Invoice_Balance_Due_in_USD',
            'Payments_Applied_Against_Invoice_in_USD', 'Original Inv. Total',
            'Payments Received'
        ]
        
        for col in money_columns:
            if col in df.columns:
                try:
                    df[col] = df[col].astype(str).str.replace('$', '', regex=False)
                    df[col] = df[col].str.replace(',', '', regex=False)
                    df[col] = df[col].str.replace('-', '0', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                except Exception as e:
                    st.sidebar.warning(f"Could not convert {col}: {e}")
                
        # Convert date columns
        date_columns = ['Invoice_Date', 'Last payment date', 'Invoice Date']
        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception as e:
                    st.sidebar.warning(f"Could not convert {col} to date: {e}")
        
        return df
    except Exception as e:
        st.error(f"Error loading invoice data: {e}")
        # Return empty DataFrame with basic columns
        return pd.DataFrame(columns=['Invoice_Number'])

# Load joiners and leavers data
def load_personnel_changes():
    # Q4 2024 Leavers
    leavers_q4_2024 = [
        {"name": "Matthew Poppe", "date": "10/16/2024", "notes": ""},
        {"name": "Marc Kaufman", "date": "11/13/2024", "notes": ""},
        {"name": "Steven Eichel", "date": "11/19/2024", "notes": ""},
        {"name": "Chelsea Ellis", "date": "11/19/2024", "notes": "Did not originate"},
        {"name": "Sam Finkelstein", "date": "11/19/2024", "notes": "Did not originate"},
        {"name": "T. James Min", "date": "11/19/2024", "notes": ""},
        {"name": "Jeffrey Fromm", "date": "11/21/2024", "notes": ""},
        {"name": "David Mahoney", "date": "11/21/2024", "notes": ""},
        {"name": "J Paul Gignac", "date": "12/2/2024", "notes": ""},
        {"name": "Deborah Turofsky", "date": "12/5/2024", "notes": "Did not originate"},
        {"name": "David Mittelman", "date": "12/18/2024", "notes": ""},
        {"name": "Dale Rieger", "date": "12/20/2024", "notes": ""}
    ]
    
    # Q1 2025 Leavers
    leavers_q1_2025 = [
        {"name": "Dror Futter", "date": "2/28/2025", "notes": ""},
        {"name": "Leo Liu", "date": "3/1/2025", "notes": ""}
    ]
    
    # Q4 2024 Joiners
    joiners_q4_2024 = [
        {"name": "Tim Kennedy", "date": "10/7/2024", "notes": "PCT Team Associate"},
        {"name": "Patrick McCormick", "date": "10/15/2024", "notes": ""},
        {"name": "Jake Mendoza", "date": "11/18/2024", "notes": "PCT Team Partner"},
        {"name": "Sarah Challen McKee", "date": "11/18/2024", "notes": "PCT Team Associate"},
        {"name": "Ruben Salcido Monreal", "date": "11/18/2024", "notes": "Associate"},
        {"name": "Robert Pepple", "date": "12/2/2024", "notes": ""},
        {"name": "Sydney Blomstrom", "date": "12/2/2024", "notes": "Associate"},
        {"name": "Edwin Barkel", "date": "12/16/2024", "notes": "BOB shared with Hilary Wells"},
        {"name": "Hilary Wells", "date": "12/16/2024", "notes": "BOB shared with Ed Barkel"}
    ]
    
    # Q1 2025 Joiners
    joiners_q1_2025 = [
        {"name": "Ivan Moskowitz", "date": "1/6/2025", "notes": ""},
        {"name": "Chip Fisher", "date": "2/3/2025", "notes": "PCT Team Counsel"},
        {"name": "Lisel Ferguson", "date": "2/24/2025", "notes": ""},
        {"name": "Hua Howard Wang", "date": "3/12/2025", "notes": ""}
    ]
    
    # Create DataFrames
    leavers_q4_df = pd.DataFrame(leavers_q4_2024)
    leavers_q4_df['quarter'] = 'Q4 2024'
    leavers_q4_df['type'] = 'Leaver'
    
    leavers_q1_df = pd.DataFrame(leavers_q1_2025)
    leavers_q1_df['quarter'] = 'Q1 2025'
    leavers_q1_df['type'] = 'Leaver'
    
    joiners_q4_df = pd.DataFrame(joiners_q4_2024)
    joiners_q4_df['quarter'] = 'Q4 2024'
    joiners_q4_df['type'] = 'Joiner'
    
    joiners_q1_df = pd.DataFrame(joiners_q1_2025)
    joiners_q1_df['quarter'] = 'Q1 2025'
    joiners_q1_df['type'] = 'Joiner'
    
    # Combine all data
    personnel_changes = pd.concat([leavers_q4_df, leavers_q1_df, joiners_q4_df, joiners_q1_df])
    
    # Convert dates to datetime
    personnel_changes['date'] = pd.to_datetime(personnel_changes['date'], format='%m/%d/%Y', errors='coerce')
    
    # Sort by date
    personnel_changes = personnel_changes.sort_values('date')
    
    return personnel_changes

# Find payment column in invoice data
def get_payment_column(df):
    # Check for exact column matches
    payment_columns = [
        'Payments_Applied_Against_Invoice_in_USD', 
        ' Payments_Applied_Against_Invoice_in_USD ',  # Note the spaces
        'Payments Received',
        'Payment Amount',
        'Payments Applied'
    ]
    
    for col in payment_columns:
        if col in df.columns:
            return col
    
    # Fuzzy matching for payment-related columns
    for col in df.columns:
        if any(term in col.lower() for term in ['payment', 'paid', 'received']):
            return col
    
    return None

# Download data as CSV
def download_csv(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="personnel_changes.csv" class="download-button">Download CSV</a>'
    return href

# Download data as Excel
def download_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Personnel Changes')
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="personnel_changes.xlsx" class="download-button">Download Excel</a>'
    return href

# Display personnel changes table
def display_personnel_table(personnel_df, quarter=None, change_type=None):
    # Filter data if quarter or type is specified
    filtered_df = personnel_df.copy()
    
    if quarter:
        filtered_df = filtered_df[filtered_df['quarter'] == quarter]
    
    if change_type:
        filtered_df = filtered_df[filtered_df['type'] == change_type]
    
    # Format date for display
    filtered_df['formatted_date'] = filtered_df['date'].dt.strftime('%m/%d/%Y')
    
    # Sort by date
    filtered_df = filtered_df.sort_values('date')
    
    # Generate HTML table
    table_html = """
    <table class="personnel-table">
        <thead>
            <tr>
                <th>Date</th>
                <th>Name</th>
                <th>Type</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for _, row in filtered_df.iterrows():
        row_class = "join-row" if row['type'] == 'Joiner' else "leave-row"
        badge_class = "badge-join" if row['type'] == 'Joiner' else "badge-leave"
        
        table_html += f"""
        <tr class="{row_class}">
            <td>{row['formatted_date']}</td>
            <td>{row['name']}</td>
            <td><span class="badge {badge_class}">{row['type']}</span></td>
            <td>{row['notes']}</td>
        </tr>
        """
    
    table_html += """
        </tbody>
    </table>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)

# Create personnel summary metrics
def create_personnel_summary(personnel_df):
    # Get counts by quarter and type
    summary = personnel_df.groupby(['quarter', 'type']).size().unstack(fill_value=0).reset_index()
    
    if 'Joiner' not in summary.columns:
        summary['Joiner'] = 0
    if 'Leaver' not in summary.columns:
        summary['Leaver'] = 0
    
    # Calculate net change
    summary['Net Change'] = summary['Joiner'] - summary['Leaver']
    
    return summary

# Create invoice-based analysis for joiners/leavers
def invoice_based_joiners_leavers(df):
    # Add year and month columns
    df['Year'] = df['Invoice_Date'].dt.year
    df['Month'] = df['Invoice_Date'].dt.month
    df['YearMonth'] = df['Invoice_Date'].dt.strftime('%Y-%m')
    
    # Get monthly attorney counts
    monthly_attorneys = df.groupby('YearMonth')['Originator'].nunique().reset_index()
    monthly_attorneys.columns = ['YearMonth', 'Attorney_Count']
    monthly_attorneys = monthly_attorneys.sort_values('YearMonth')
    
    # Calculate joiners and leavers if possible
    if len(monthly_attorneys) > 1:
        monthly_attorneys['Previous_Count'] = monthly_attorneys['Attorney_Count'].shift(1)
        monthly_attorneys['Net_Change'] = monthly_attorneys['Attorney_Count'] - monthly_attorneys['Previous_Count']
        
        # Split into joiners and leavers
        monthly_attorneys['Joiners'] = monthly_attorneys['Net_Change'].apply(lambda x: max(0, x))
        monthly_attorneys['Leavers'] = monthly_attorneys['Net_Change'].apply(lambda x: abs(min(0, x)))
        
        return monthly_attorneys
    
    return pd.DataFrame()

def format_currency(value):
    return f"${value:,.2f}"

def main():
    # Display title
    st.markdown("<h1 class='main-header'>Rimon Personnel Changes Dashboard</h1>", unsafe_allow_html=True)
    
    # Load data
    df = load_invoice_data()
    personnel_changes = load_personnel_changes()
    
    # Check if data is loaded properly
    if df.empty:
        st.warning("Invoice data could not be loaded. Some features will be limited.")
    
    # Find payment column for invoice data calculations
    payment_col = get_payment_column(df) if not df.empty else None
    
    # ===== SIDEBAR FILTERS =====
    st.sidebar.markdown("## 🔧 Filters")
    
    # Initialize filtered dataframe
    df_filtered = df.copy() if not df.empty else pd.DataFrame()
    
    # Date range filter
    if not df.empty and 'Invoice_Date' in df.columns and not df['Invoice_Date'].isna().all():
        try:
            min_date = df['Invoice_Date'].min()
            max_date = df['Invoice_Date'].max()
            
            if pd.notna(min_date) and pd.notna(max_date):
                date_range = st.sidebar.date_input(
                    "Date Range",
                    value=(min_date.date(), max_date.date()),
                    min_value=min_date.date(),
                    max_value=max_date.date()
                )
                
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    df_filtered = df[(df['Invoice_Date'].dt.date >= start_date) & 
                                    (df['Invoice_Date'].dt.date <= end_date)]
        except Exception as e:
            st.sidebar.warning(f"Could not apply date filter: {str(e)}")
    
    # Client filter
    if not df.empty:
        try:
            clients = ['All'] + safe_get_unique(df, 'Client')
            selected_client = st.sidebar.selectbox("Client", options=clients, index=0)
            
            if selected_client != 'All' and 'Client' in df.columns:
                df_filtered = df_filtered[df_filtered['Client'] == selected_client]
        except Exception as e:
            st.sidebar.warning(f"Could not apply client filter: {str(e)}")
    
    # Attorney filter
    if not df.empty:
        try:
            attorneys = ['All'] + safe_get_unique(df, 'Originator')
            selected_attorney = st.sidebar.selectbox("Attorney", options=attorneys, index=0)
            
            if selected_attorney != 'All' and 'Originator' in df.columns:
                df_filtered = df_filtered[df_filtered['Originator'] == selected_attorney]
        except Exception as e:
            st.sidebar.warning(f"Could not apply attorney filter: {str(e)}")
    
    # Status filter
    if not df.empty:
        try:
            if 'Invoice Status' in df.columns:
                statuses = ['All'] + safe_get_unique(df, 'Invoice Status')
                selected_status = st.sidebar.selectbox("Invoice Status", options=statuses, index=0)
                
                if selected_status != 'All':
                    df_filtered = df_filtered[df_filtered['Invoice Status'] == selected_status]
        except Exception as e:
            st.sidebar.warning(f"Could not apply status filter: {str(e)}")
    
    # Office/Team filter
    if not df.empty:
        try:
            if 'Accounting Entity' in df.columns:
                entities = ['All'] + safe_get_unique(df, 'Accounting Entity')
                selected_entity = st.sidebar.selectbox("Office/Team", options=entities, index=0)
                
                if selected_entity != 'All':
                    df_filtered = df_filtered[df_filtered['Accounting Entity'] == selected_entity]
        except Exception as e:
            st.sidebar.warning(f"Could not apply office filter: {str(e)}")
    
    # Calculate summary statistics
    personnel_summary = create_personnel_summary(personnel_changes)
    
    # Main sections
    tab1, tab2, tab3 = st.tabs(["📊 Summary", "📈 Invoice Analysis", "📋 Detailed Log"])
    
    # Summary Tab
    with tab1:
        st.markdown("<h2 class='section-header'>Personnel Changes Summary</h2>", unsafe_allow_html=True)
        
        # Display summary cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Q4 2024 summary
            q4_data = personnel_summary[personnel_summary['quarter'] == 'Q4 2024']
            if not q4_data.empty:
                joiners = q4_data['Joiner'].values[0]
                leavers = q4_data['Leaver'].values[0]
                net_change = q4_data['Net Change'].values[0]
                
                net_color = "green-text" if net_change > 0 else "red-text" if net_change < 0 else ""
                st.markdown(f"""
                <div class='kpi-card'>
                    <p class='kpi-title'>Q4 2024 Summary</p>
                    <p><span class="green-text">{joiners} Joiners</span> | <span class="red-text">{leavers} Leavers</span></p>
                    <p class='kpi-value {net_color}'>{net_change:+d} Net Change</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            # Q1 2025 summary
            q1_data = personnel_summary[personnel_summary['quarter'] == 'Q1 2025']
            if not q1_data.empty:
                joiners = q1_data['Joiner'].values[0]
                leavers = q1_data['Leaver'].values[0]
                net_change = q1_data['Net Change'].values[0]
                
                net_color = "green-text" if net_change > 0 else "red-text" if net_change < 0 else ""
                st.markdown(f"""
                <div class='kpi-card'>
                    <p class='kpi-title'>Q1 2025 Summary</p>
                    <p><span class="green-text">{joiners} Joiners</span> | <span class="red-text">{leavers} Leavers</span></p>
                    <p class='kpi-value {net_color}'>{net_change:+d} Net Change</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            # Overall summary (Q4 2024 + Q1 2025)
            total_joiners = personnel_summary['Joiner'].sum()
            total_leavers = personnel_summary['Leaver'].sum()
            total_net_change = total_joiners - total_leavers
            
            net_color = "green-text" if total_net_change > 0 else "red-text" if total_net_change < 0 else ""
            st.markdown(f"""
            <div class='kpi-card'>
                <p class='kpi-title'>Overall Summary (Q4 2024-Q1 2025)</p>
                <p><span class="green-text">{total_joiners} Joiners</span> | <span class="red-text">{total_leavers} Leavers</span></p>
                <p class='kpi-value {net_color}'>{total_net_change:+d} Net Change</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Visualizations
        st.markdown("<h3>Quarterly Personnel Changes</h3>", unsafe_allow_html=True)
        
        # Bar chart - Quarterly comparison
        quarter_summary = personnel_summary.melt(
            id_vars=['quarter'],
            value_vars=['Joiner', 'Leaver'],
            var_name='Type',
            value_name='Count'
        )
        
        fig = px.bar(
            quarter_summary,
            x='quarter',
            y='Count',
            color='Type',
            barmode='group',
            title='Personnel Changes by Quarter',
            labels={'quarter': 'Quarter', 'Count': 'Number of Personnel', 'Type': 'Change Type'},
            color_discrete_map={'Joiner': '#10B981', 'Leaver': '#EF4444'}
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Monthly trend chart
        st.markdown("<h3>Monthly Personnel Activity</h3>", unsafe_allow_html=True)
        
        personnel_changes['month'] = personnel_changes['date'].dt.strftime('%Y-%m')
        monthly_joiners = personnel_changes[personnel_changes['type'] == 'Joiner'].groupby('month').size().reset_index()
        monthly_joiners.columns = ['month', 'count']
        
        monthly_leavers = personnel_changes[personnel_changes['type'] == 'Leaver'].groupby('month').size().reset_index()
        monthly_leavers.columns = ['month', 'count']
        
        # Create visualization
        fig = go.Figure()
        
        # Add joiners and leavers bars
        fig.add_trace(go.Bar(
            x=monthly_joiners['month'],
            y=monthly_joiners['count'],
            name='Joiners',
            marker_color='#10B981'
        ))
        
        fig.add_trace(go.Bar(
            x=monthly_leavers['month'],
            y=monthly_leavers['count'],
            name='Leavers',
            marker_color='#EF4444'
        ))
        
        # Update layout
        fig.update_layout(
            title='Monthly Personnel Changes (Q4 2024-Q1 2025)',
            xaxis=dict(title='Month'),
            yaxis=dict(title='Number of Personnel'),
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Add impact analysis if invoice data is available
        if not df_filtered.empty and 'Invoice_Total_in_USD' in df_filtered.columns and 'Originator' in df_filtered.columns:
            st.markdown("<h3>Financial Impact Analysis</h3>", unsafe_allow_html=True)
            
            # List all leavers
            all_leavers = personnel_changes[personnel_changes['type'] == 'Leaver']['name'].tolist()
            
            # Check if leavers exist in invoice data
            leaver_impact = []
            for leaver in all_leavers:
                if leaver in df_filtered['Originator'].values:
                    leaver_df = df_filtered[df_filtered['Originator'] == leaver]
                    total_billed = leaver_df['Invoice_Total_in_USD'].sum()
                    leaver_impact.append({
                        'Attorney': leaver,
                        'Total_Billed': total_billed,
                    })
            
            if leaver_impact:
                # Convert to DataFrame and sort
                leaver_impact_df = pd.DataFrame(leaver_impact)
                leaver_impact_df = leaver_impact_df.sort_values('Total_Billed', ascending=False)
                
                # Display chart
                fig = px.bar(
                    leaver_impact_df,
                    x='Attorney',
                    y='Total_Billed',
                    title='Revenue Impact of Departing Attorneys',
                    labels={'Total_Billed': 'Total Billed (USD)', 'Attorney': ''},
                    color='Total_Billed',
                    color_continuous_scale='Reds'
                )
                
                fig.update_layout(
                    xaxis_tickangle=45,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Summary metrics
                total_leaver_revenue = leaver_impact_df['Total_Billed'].sum()
                total_revenue = df_filtered['Invoice_Total_in_USD'].sum() if not df_filtered.empty else 0
                
                if total_revenue > 0:
                    impact_percent = (total_leaver_revenue / total_revenue * 100)
                    st.info(f"💰 Departing attorneys represented approximately {format_currency(total_leaver_revenue)} in billings, which is {impact_percent:.1f}% of total revenue.")
            else:
                st.info("No revenue data found for departing attorneys in the selected time period.")
        
        # Notes on types of personnel
        with st.expander("Notes on Personnel Categories"):
            st.markdown("""
            ### Personnel Categories
            
            **PCT Team**: Patent Cooperation Treaty team members. These specialized attorneys and staff focus on international patent applications.
            
            **Associates**: Junior attorneys who support partners and other senior attorneys.
            
            **BOB (Back Office Business)**: Administrative and operational staff who support the firm.
            
            **Did not originate**: Personnel who did not generate revenue as originators. This typically refers to staff members or attorneys who weren't responsible for bringing in clients.
            """)
    
    # Invoice Analysis Tab
with tab2:
    st.markdown("<h2 class='section-header'>Invoice-Based Personnel Analysis</h2>", unsafe_allow_html=True)
    
    if not df_filtered.empty and 'Originator' in df_filtered.columns and 'Invoice_Date' in df_filtered.columns:
        # Calculate invoice-based joiners/leavers
        monthly_attorneys = invoice_based_joiners_leavers(df_filtered)
        
        if not monthly_attorneys.empty and len(monthly_attorneys) > 1:
            st.info("This analysis shows personnel changes based on invoice activity patterns, which may differ from official personnel records.")
            
            # Create visualization
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=monthly_attorneys['YearMonth'],
                y=monthly_attorneys['Joiners'],
                name='Joiners (Invoice Activity)',
                marker_color='#10B981'
            ))
            
            fig.add_trace(go.Bar(
                x=monthly_attorneys['YearMonth'],
                y=monthly_attorneys['Leavers'],
                name='Leavers (Invoice Activity)',
                marker_color='#EF4444'
            ))
            
            fig.add_trace(go.Scatter(
                x=monthly_attorneys['YearMonth'],
                y=monthly_attorneys['Net_Change'],
                name='Net Change',
                mode='lines+markers',
                line=dict(color='#3B82F6', width=3),
                marker=dict(size=8)
            ))
            
            fig.update_layout(
                title='Monthly Joiners vs Leavers (Based on Invoice Activity)',
                xaxis=dict(title='Month', tickangle=45),
                yaxis=dict(title='Number of Attorneys'),
                barmode='group',
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate yearly summary if possible
            df_filtered['Year'] = df_filtered['Invoice_Date'].dt.year
            yearly_attorneys = df_filtered.groupby('Year')['Originator'].nunique().reset_index()
            yearly_attorneys.columns = ['Year', 'Attorney_Count']
            yearly_attorneys = yearly_attorneys.sort_values('Year')
            
            if len(yearly_attorneys) > 1:
                yearly_attorneys['Previous_Count'] = yearly_attorneys['Attorney_Count'].shift(1)
                yearly_attorneys['Net_Change'] = yearly_attorneys['Attorney_Count'] - yearly_attorneys['Previous_Count']
                yearly_attorneys['Joiners'] = yearly_attorneys['Net_Change'].apply(lambda x: max(0, x))
                yearly_attorneys['Leavers'] = yearly_attorneys['Net_Change'].apply(lambda x: abs(min(0, x)))
                
                # Drop NaN rows
                yearly_attorneys = yearly_attorneys.dropna()
                
                if not yearly_attorneys.empty:
                    st.subheader("Year-wise Trend (Invoice Activity)")
                    st.dataframe(yearly_attorneys[['Year', 'Attorney_Count', 'Joiners', 'Leavers', 'Net_Change']], use_container_width=True)
                    
                    # Compare with official data
                    st.markdown("""
                    <div style="background-color: #fef3c7; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;">
                        <p><strong>Note:</strong> This analysis is based on invoice patterns and may differ from official personnel records.</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Top attorneys by billing
            if 'Invoice_Total_in_USD' in df_filtered.columns:
                st.subheader("Top Attorneys by Billing")
                
                attorney_billing = df_filtered.groupby('Originator')['Invoice_Total_in_USD'].sum().reset_index()
                attorney_billing = attorney_billing.sort_values('Invoice_Total_in_USD', ascending=False)
                
                # Create bar chart
                top_n = min(10, len(attorney_billing))
                top_attorneys = attorney_billing.head(top_n)
                
                fig = px.bar(
                    top_attorneys,
                    x='Originator',
                    y='Invoice_Total_in_USD',
                    title=f'Top {top_n} Attorneys by Billing',
                    labels={'Invoice_Total_in_USD': 'Total Billed (USD)', 'Originator': 'Attorney'},
                    color='Invoice_Total_in_USD',
                    color_continuous_scale='Blues'
                )
                
                fig.update_layout(
                    xaxis_tickangle=45,
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show which top attorneys are among joiners/leavers
                if not personnel_changes.empty:
                    joiners = personnel_changes[personnel_changes['type'] == 'Joiner']['name'].tolist()
                    leavers = personnel_changes[personnel_changes['type'] == 'Leaver']['name'].tolist()
                    
                    top_joiners = [atty for atty in top_attorneys['Originator'] if atty in joiners]
                    top_leavers = [atty for atty in top_attorneys['Originator'] if atty in leavers]
                    
                    if top_leavers:
                        st.warning(f"⚠️ {len(top_leavers)} of the top {top_n} billing attorneys are among recent leavers: {', '.join(top_leavers)}")
                    
                    if top_joiners:
                        st.success(f"✅ {len(top_joiners)} of the top {top_n} billing attorneys are recent joiners: {', '.join(top_joiners)}")
        else:
            st.warning("Not enough invoice data to analyze personnel changes by invoice activity.")
    else:
        st.warning("Missing invoice data required for this analysis. Please check if invoice data is loaded correctly.")

# Detailed Log Tab
with tab3:
    st.markdown("<h2 class='section-header'>Personnel Changes Log</h2>", unsafe_allow_html=True)
    
    # Filter controls
    col1, col2 = st.columns(2)
    
    with col1:
        # Quarter filter
        quarters = ['All'] + list(personnel_changes['quarter'].unique())
        selected_quarter = st.selectbox("Select Quarter", options=quarters)
    
    with col2:
        # Change type filter
        change_types = ['All', 'Joiner', 'Leaver']
        selected_type = st.selectbox("Select Change Type", options=change_types)
    
    # Apply filters
    filtered_quarter = None if selected_quarter == 'All' else selected_quarter
    filtered_type = None if selected_type == 'All' else selected_type
    
    # Display personnel table
    display_personnel_table(personnel_changes, quarter=filtered_quarter, change_type=filtered_type)
    
    # Download data section
    st.subheader("Download Data")
    
    # Prepare download data
    personnel_download = personnel_changes.copy()
    personnel_download['date'] = personnel_download['date'].dt.strftime('%m/%d/%Y')
    
    # Download buttons
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(download_csv(personnel_download), unsafe_allow_html=True)
    
    with col2:
        st.markdown(download_excel(personnel_download), unsafe_allow_html=True)

# Run the main application
if __name__ == "__main__":
    main()
