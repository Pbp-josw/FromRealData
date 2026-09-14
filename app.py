import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO

# ------------------------------------------------------------------------------
# 1. Page Configuration & Session State
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Analytics & Visualization Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

if "df" not in st.session_state:
    st.session_state.df = None

# ------------------------------------------------------------------------------
# 2. Helper Functions
# ------------------------------------------------------------------------------
@st.cache_data
def load_data(uploaded_file):
    """Parses uploaded CSV/Excel files into a pandas DataFrame with encoding error handling."""
    try:
        filename = uploaded_file.name
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(uploaded_file, encoding="utf-8")
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding="cp949")
        elif filename.endswith((".xls", ".xlsx")):
            df = pd.read_excel(uploaded_file)
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return None
        return df
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return None

def convert_df_to_excel(df):
    """Converts a DataFrame to an Excel file buffer for download."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Filtered_Data")
    return output.getvalue()

def generate_sample_data():
    """Generates a default synthetic dataset when no file is uploaded."""
    return pd.DataFrame({
        "Date": pd.date_range(start="2026-01-01", periods=100, freq="D"),
        "Category": ["Electronics", "Apparel", "Food", "Books"] * 25,
        "Region": ["North", "South", "East", "West", "Central"] * 20,
        "Sales": (pd.Series(range(100)) * 150 + 5000).tolist(),
        "Quantity": [i % 10 + 1 for i in range(100)],
        "Satisfaction": [round(3.5 + (i % 15) * 0.1, 1) for i in range(100)]
    })

# ------------------------------------------------------------------------------
# 3. Sidebar Setup & File Upload
# ------------------------------------------------------------------------------
st.sidebar.title("⚙️ Control Panel")
st.sidebar.markdown("Upload your dataset or explore using sample data.")

uploaded_file = st.sidebar.file_uploader(
    "Upload Dataset (CSV / XLSX)",
    type=["csv", "xlsx", "xls"],
    help="Select a CSV or Excel spreadsheet to analyze."
)

if uploaded_file is not None:
    st.session_state.df = load_data(uploaded_file)
else:
    st.sidebar.info("💡 No file uploaded. Displaying sample dataset.")
    st.session_state.df = generate_sample_data()

# ------------------------------------------------------------------------------
# 4. Application Body
# ------------------------------------------------------------------------------
st.title("📊 Interactive Analytics & Visualization Dashboard")
st.markdown("Upload data to inspect KPIs, generate interactive Plotly visualizations, filter datasets, and export results.")
st.divider()

if st.session_state.df is not None:
    df = st.session_state.df.copy()

    # Dynamic Filter Section
    st.sidebar.subheader("🔍 Filters")
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    
    filtered_df = df.copy()
    if categorical_cols:
        selected_col = st.sidebar.selectbox("Filter by Column", options=["None"] + categorical_cols)
        if selected_col != "None":
            unique_vals = df[selected_col].dropna().unique().tolist()
            selected_vals = st.sidebar.multiselect(
                f"Select Values from '{selected_col}'",
                options=unique_vals,
                default=unique_vals
            )
            if selected_vals:
                filtered_df = filtered_df[filtered_df[selected_col].isin(selected_vals)]

    # Main Tabs
    tab1, tab2, tab3 = st.tabs(["📈 KPI Summary", "📊 Interactive Charts", "📋 Data Explorer & Export"])

    # --------------------------------------------------------------------------
    # Tab 1: Key Performance Indicators & Descriptive Stats
    # --------------------------------------------------------------------------
    with tab1:
        st.subheader("📌 Metrics Overview")
        numeric_cols = filtered_df.select_dtypes(include=["number"]).columns.tolist()

        if numeric_cols:
            kpi_cols = st.columns(min(len(numeric_cols), 4))
            for idx, col_name in enumerate(numeric_cols[:4]):
                col = kpi_cols[idx % 4]
                total_val = filtered_df[col_name].sum()
                avg_val = filtered_df[col_name].mean()
                col.metric(
                    label=f"Total {col_name}",
                    value=f"{total_val:,.2f}",
                    delta=f"Avg: {avg_val:,.2f}"
                )
        else:
            st.warning("No numeric columns found to calculate KPIs.")

        st.markdown("---")
        st.subheader("💡 Statistical Summary")
        st.dataframe(filtered_df.describe(), use_container_width=True)

    # --------------------------------------------------------------------------
    # Tab 2: Plotly Visualizations
    # --------------------------------------------------------------------------
    with tab2:
        st.subheader("📈 Custom Visualization Builder")
        
        control_col, chart_col = st.columns([1, 2])

        with control_col:
            chart_type = st.selectbox(
                "Select Chart Type",
                ["Bar Chart", "Line Chart", "Scatter Plot", "Histogram"]
            )
            
            all_cols = filtered_df.columns.tolist()
            x_axis = st.selectbox("X-Axis Column", options=all_cols, index=0)
            
            if numeric_cols:
                y_axis = st.selectbox("Y-Axis Column", options=numeric_cols, index=0)
            else:
                y_axis = None
                st.warning("No numeric column available for Y-Axis.")

            color_col = st.selectbox("Color Grouping (Optional)", options=["None"] + categorical_cols)
            color_param = None if color_col == "None" else color_col

        with chart_col:
            try:
                if x_axis:
                    if chart_type == "Bar Chart" and y_axis:
                        fig = px.bar(filtered_df, x=x_axis, y=y_axis, color=color_param, title=f"{y_axis} by {x_axis}")
                    elif chart_type == "Line Chart" and y_axis:
                        fig = px.line(filtered_df, x=x_axis, y=y_axis, color=color_param, title=f"{y_axis} over {x_axis}")
                    elif chart_type == "Scatter Plot" and y_axis:
                        fig = px.scatter(filtered_df, x=x_axis, y=y_axis, color=color_param, title=f"{x_axis} vs {y_axis}")
                    elif chart_type == "Histogram":
                        fig = px.histogram(filtered_df, x=x_axis, color=color_param, title=f"Distribution of {x_axis}")
                    else:
                        fig = None

                    if fig:
                        fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Select appropriate numeric metrics to generate the chart.")
            except Exception as e:
                st.error(f"Error rendering chart: {str(e)}")

    # --------------------------------------------------------------------------
    # Tab 3: Data Table & Download Options
    # --------------------------------------------------------------------------
    with tab3:
        st.subheader("📋 Data Preview")
        st.dataframe(filtered_df, use_container_width=True)

        st.subheader("📥 Export Filtered Data")
        dl_col1, dl_col2 = st.columns(2)

        with dl_col1:
            csv_data = filtered_df.to_csv(index=False, encoding="utf-8-sig")
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name="filtered_dataset.csv",
                mime="text/csv",
                use_container_width=True
            )

        with dl_col2:
            try:
                excel_data = convert_df_to_excel(filtered_df)
                st.download_button(
                    label="📊 Download Excel",
                    data=excel_data,
                    file_name="filtered_dataset.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Failed to create Excel export: {str(e)}")
else:
    st.error("Failed to load dataset.")