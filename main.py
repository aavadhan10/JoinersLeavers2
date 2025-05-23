import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import io

# Set page configuration
st.set_page_config(page_title="Rimon Personnel Changes", page_icon="👥", layout="wide")

# Basic styling
st.markdown("""
<style>
    .main-header {font-size: 2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 1rem; text-align: center;}
    .section-header {font-size: 1.5rem; font-weight: 600; color: #1E3A8A; margin: 1rem 0; border-bottom: 2px solid #E5E7EB;}
    .kpi-card {background-color: #f8f9fa; border-radius: 10px; padding: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center;}
    .green-text {color: #10B981;}
    .red-text {color: #EF4444;}
    .personnel-table {width: 100%; border-collapse: collapse;}
    .personnel-table th {background-color: #1E3A8A; color: white; text-align: left; padding: 10px;}
    .personnel-table td {padding: 8px 10px; border-bottom: 1px solid #ddd;}
    .join-row {background-color: rgba(16, 185, 129, 0.1);}
    .leave-row {background-color: rgba(239, 68, 68, 0.1);}
    .badge {display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: 600;}
    .badge-join {background-color: #10B981; color: white;}
    .badge-leave {background-color: #EF4444; color: white;}
    .download-button {background-color: #1E40AF; color: white; padding: 0.5rem 1rem; border-radius: 5px; 
                     text-decoration: none; display: inline-block; margin-top: 1rem;}
</style>
""", unsafe_allow_html=True)

# Load invoice data
@st.cache_data(ttl=3600)
def load_invoice_data():
    try:
        df = pd.read_csv("Cleaned_Invoice_Data.csv", encoding='utf-8')
        df.columns = df.columns.str.strip()
        
        # Clean money columns
        money_cols = ['Invoice_Total_in_USD', 'Invoice_Labor_Total_in_USD', 'Invoice_Expense_Total_in_USD', 
                      'Invoice_Balance_Due_in_USD', 'Payments_Applied_Against_Invoice_in_USD', 
                      'Original Inv. Total', 'Payments Received']
        
        for col in money_cols:
            if col in df.columns:
                try:
                    df[col] = df[col].astype(str).str.replace('$', '', regex=False)
                    df[col] = df[col].str.replace(',', '', regex=False)
                    df[col] = df[col].str.replace('-', '0', regex=False)
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                except Exception as e:
                    st.sidebar.warning(f"Could not convert {col}: {e}")
        
        # Convert date columns
        date_cols = ['Invoice_Date', 'Last payment date', 'Invoice Date']
        for col in date_cols:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                except Exception as e:
                    st.sidebar.warning(f"Could not convert {col} to date: {e}")
        
        return df
    except Exception as e:
        st.error(f"Error loading invoice data: {e}")
        return pd.DataFrame(columns=['Invoice_Number'])

# Load personnel data
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
    personnel_changes['date'] = pd.to_datetime(personnel_changes['date'], format='%m/%d/%Y', errors='coerce')
    personnel_changes = personnel_changes.sort_values('date')
    
    return personnel_changes

# Create personnel summary metrics
def create_personnel_summary(personnel_df):
    summary = personnel_df.groupby(['quarter', 'type']).size().unstack(fill_value=0).reset_index()
    if 'Joiner' not in summary.columns:
        summary['Joiner'] = 0
    if 'Leaver' not in summary.columns:
        summary['Leaver'] = 0
    summary['Net Change'] = summary['Joiner'] - summary['Leaver']
    return summary

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
    filtered_df = personnel_df.copy()
    if quarter:
        filtered_df = filtered_df[filtered_df['quarter'] == quarter]
    if change_type:
        filtered_df = filtered_df[filtered_df['type'] == change_type]
    
    filtered_df['formatted_date'] = filtered_df['date'].dt.strftime('%m/%d/%Y')
    filtered_df = filtered_df.sort_values('date')
    
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

def format_currency(value):
    return f"${value:,.2f}"

def main():
    st.markdown("<h1 class='main-header'>Rimon Personnel Changes Dashboard</h1>", unsafe_allow_html=True)
    
    # Load data
    df = load_invoice_data()
    personnel_changes = load_personnel_changes()
    
    if df.empty:
        st.warning("Invoice data could not be loaded. Some features will be limited.")
    
    # Sidebar filters (simplified)
    st.sidebar.markdown("## 🔧 Filters")
    df_filtered = df.copy() if not df.empty else pd.DataFrame()

    # Calculate summary statistics
    personnel_summary = create_personnel_summary(personnel_changes)
    
    # Use radio button instead of tabs to avoid NameError issues
    view_selection = st.radio(
        "Select View:",
        ["📊 Summary", "📈 Invoice Analysis", "📋 Detailed Log"],
        horizontal=True
    )
    
    # ===== SUMMARY VIEW =====
    if view_selection == "📊 Summary":
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
                    <p>Q4 2024 Summary</p>
                    <p><span class="green-text">{joiners} Joiners</span> | <span class="red-text">{leavers} Leavers</span></p>
                    <p class='{net_color}'>{net_change:+d} Net Change</p>
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
                    <p>Q1 2025 Summary</p>
                    <p><span class="green-text">{joiners} Joiners</span> | <span class="red-text">{leavers} Leavers</span></p>
                    <p class='{net_color}'>{net_change:+d} Net Change</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            # Overall summary
            total_joiners = personnel_summary['Joiner'].sum()
            total_leavers = personnel_summary['Leaver'].sum()
            total_net_change = total_joiners - total_leavers
            
            net_color = "green-text" if total_net_change > 0 else "red-text" if total_net_change < 0 else ""
            st.markdown(f"""
            <div class='kpi-card'>
                <p>Overall Summary (Q4 2024-Q1 2025)</p>
                <p><span class="green-text">{total_joiners} Joiners</span> | <span class="red-text">{total_leavers} Leavers</span></p>
                <p class='{net_color}'>{total_net_change:+d} Net Change</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Bar chart - Quarterly comparison
        st.subheader("Quarterly Personnel Changes")
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
            labels={'quarter': 'Quarter', 'Count': 'Number of Personnel', 'Type': 'Change Type'},
            color_discrete_map={'Joiner': '#10B981', 'Leaver': '#EF4444'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Monthly trend chart
        st.subheader("Monthly Personnel Activity")
        personnel_changes['month'] = personnel_changes['date'].dt.strftime('%Y-%m')
        monthly_joiners = personnel_changes[personnel_changes['type'] == 'Joiner'].groupby('month').size().reset_index()
        monthly_joiners.columns = ['month', 'count']
        
        monthly_leavers = personnel_changes[personnel_changes['type'] == 'Leaver'].groupby('month').size().reset_index()
        monthly_leavers.columns = ['month', 'count']
        
        fig = go.Figure()
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
        
        fig.update_layout(
            xaxis=dict(title='Month'),
            yaxis=dict(title='Number of Personnel'),
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ===== INVOICE ANALYSIS VIEW =====
    elif view_selection == "📈 Invoice Analysis":
        st.markdown("<h2 class='section-header'>Invoice-Based Personnel Analysis</h2>", unsafe_allow_html=True)
        
        if not df_filtered.empty and 'Originator' in df_filtered.columns and 'Invoice_Date' in df_filtered.columns:
            # Top attorneys by billing
            if 'Invoice_Total_in_USD' in df_filtered.columns:
                st.subheader("Top Attorneys by Billing")
                
                attorney_billing = df_filtered.groupby('Originator')['Invoice_Total_in_USD'].sum().reset_index()
                attorney_billing = attorney_billing.sort_values('Invoice_Total_in_USD', ascending=False)
                
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
                        st.warning(f"⚠️ {len(top_leavers)} of the top {top_n} billing attorneys are leaving: {', '.join(top_leavers)}")
                    
                    if top_joiners:
                        st.success(f"✅ {len(top_joiners)} of the top {top_n} billing attorneys are recent joiners: {', '.join(top_joiners)}")
            
            # Leaver financial impact
            st.subheader("Financial Impact of Departing Attorneys")
            all_leavers = personnel_changes[personnel_changes['type'] == 'Leaver']['name'].tolist()
            
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
                leaver_impact_df = pd.DataFrame(leaver_impact)
                leaver_impact_df = leaver_impact_df.sort_values('Total_Billed', ascending=False)
                
                fig = px.bar(
                    leaver_impact_df,
                    x='Attorney',
                    y='Total_Billed',
                    labels={'Total_Billed': 'Total Billed (USD)', 'Attorney': ''},
                    color='Total_Billed',
                    color_continuous_scale='Reds'
                )
                
                fig.update_layout(xaxis_tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No revenue data found for departing attorneys in the selected time period.")
        else:
            st.warning("Missing invoice data required for this analysis.")
    
    # ===== DETAILED LOG VIEW =====
    else:  # "📋 Detailed Log"
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

        # Notes section
        with st.expander("Notes on Personnel Categories"):
            st.markdown("""
            - **PCT Team**: Patent Cooperation Treaty team members
            - **Associates**: Junior attorneys supporting senior partners
            - **BOB**: Back Office Business (administrative staff)
            - **Did not originate**: Personnel who did not generate revenue
            """)

if __name__ == "__main__":
    main()
