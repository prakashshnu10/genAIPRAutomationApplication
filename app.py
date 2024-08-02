import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text, Table, MetaData

# Replace with your actual database URI
DATABASE_URI = 'postgresql+psycopg2://sonar:sonarqube@65.1.55.202/sonarqube'
engine = create_engine(DATABASE_URI)
metadata = MetaData()

# Set page config at the top of your script
st.set_page_config(layout="wide", page_title="Automated Code Peer Review Application")

# Define tables
tables = {
    'code_complexity': Table('code_complexity', metadata, autoload_with=engine),
    'api_versioning': Table('api_versioning', metadata, autoload_with=engine),
    'swagger_documentation': Table('swagger_documentation', metadata, autoload_with=engine),
    'sonar_analysis_results': Table('sonar_analysis_results', metadata, autoload_with=engine)
}

def fetch_sonar_data():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT * FROM sonar_analysis_results"))
        data = result.fetchall()
        return pd.DataFrame(data, columns=result.keys())

def fetch_llm_report(pr_number):
    with engine.connect() as connection:
        query = text("SELECT analysis_text FROM analysis_results WHERE pr_number = :pr_number ORDER BY created_at DESC")
        result = connection.execute(query, {'pr_number': pr_number})
        data = result.fetchone()
        return data[0] if data else "No report found."

def fetch_table_data(table_name, pr_number):
    table = tables[table_name]
    with engine.connect() as connection:
        query = table.select().where(table.c.pr_number == pr_number)
        result = connection.execute(query)
        data = result.fetchall()
        df = pd.DataFrame(data, columns=result.keys())
        if 'pr_number' in df.columns:
            df = df.drop(columns=['pr_number'])
        if 'id' in df.columns:
            df = df.drop(columns=['id'])
        return df

def display_table(df, title, width='100%', height='400px'):
    html = df.to_html(index=False, classes='dataframe', escape=False)
    st.markdown(f"<h2>{title}</h2>", unsafe_allow_html=True)
    st.markdown(f"""
        <div style="overflow-x: auto; width: {width}; height: {height};">
            {html}
        </div>
        <style>
            .dataframe {{
                width: 100% !important;
                border-collapse: collapse;
            }}
            .dataframe th, .dataframe td {{
                padding: 10px;
                border: 1px solid #ddd;
                text-align: left;
            }}
        </style>
    """, unsafe_allow_html=True)

def fetch_developer_scores():
    query = text("""
        SELECT 
            developer,
            COUNT(*) AS total_prs,
            SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) AS accepted_prs,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) AS rejected_prs,
            ROUND(
                (SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) * 1.0) / 
                COUNT(*), 
                2
            ) AS coding_score
        FROM 
            sonar_analysis_results
        GROUP BY 
            developer
    """)
    with engine.connect() as connection:
        result = connection.execute(query)
        data = result.fetchall()
        return pd.DataFrame(data, columns=result.keys())

def main():
    if 'view_scores' not in st.session_state:
        st.session_state.view_scores = False
    
    # Check if 'view_scores' is True or False and render accordingly
    if st.session_state.view_scores:
        st.sidebar.image('nu10-logo.png', width=200)
        st.title('Developer Coding Scores')
        df_scores = fetch_developer_scores()
        developers = df_scores['developer'].unique()
        selected_developer = st.sidebar.selectbox('Select Developer', developers)
        if selected_developer:
            st.subheader(f'Coding Scores for {selected_developer}')
            developer_data = df_scores[df_scores['developer'] == selected_developer]
            st.dataframe(developer_data)
            if st.sidebar.button('Back to Dashboard'):
                st.session_state.view_scores = False
    else:
        query_params = st.query_params
        pr_number_str = query_params.get('pr_number', ['0'])[0]
        pr_number = int(pr_number_str) if pr_number_str.isdigit() else None

        if pr_number:
            st.markdown(f'<h1>GenAI Report for PR Number: {pr_number}</h1>', unsafe_allow_html=True)
            with st.expander('Code Complexity Details', expanded=True):
                df_complexity = fetch_table_data('code_complexity', pr_number)
                display_table(df_complexity, 'Code Complexity Details')
            with st.expander('API Versioning Details', expanded=True):
                df_versioning = fetch_table_data('api_versioning', pr_number)
                display_table(df_versioning, 'API Versioning Details')
            with st.expander('Swagger Documentation Details', expanded=True):
                df_swagger = fetch_table_data('swagger_documentation', pr_number)
                display_table(df_swagger, 'Swagger Documentation Details')
            st.markdown("[Back to Dashboard](./)")
        else:
            df_sonar = fetch_sonar_data()
            st.sidebar.image('nu10-logo.png', width=200)
            st.title('Automated Code Peer Review Application')
            branches = df_sonar['branch'].unique()
            selected_branch = st.sidebar.selectbox('Select Branch', branches)
            filtered_data = df_sonar[df_sonar['branch'] == selected_branch].copy()
            st.sidebar.write(f"Selected Branch: {selected_branch}")
            st.subheader(f'Pull Request Status for Branch: {selected_branch}')

            def create_pr_link(pr_number):
                return f"/?pr_number={pr_number}"

            filtered_data['Gen AI Report'] = filtered_data.apply(
                lambda row: f'<a href="{create_pr_link(row["pr_number"])}">View Report</a>',
                axis=1
            )

            filtered_data = filtered_data.rename(columns={
                'pr_number': 'PR Number',
                'status': 'Merge Status',
                'developer': 'Developer Name',
                'Gen AI Report': 'Gen AI Report'
            })

            st.markdown(
                filtered_data[['PR Number', 'Merge Status', 'Developer Name', 'Gen AI Report']].to_html(index=False, escape=False),
                unsafe_allow_html=True
            )

            st.sidebar.write("\n" * 2)
            if st.sidebar.button('View Developer Coding Scores'):
                st.session_state.view_scores = True

            st.sidebar.write("\n" * 10)
            st.sidebar.write("Peer: Gaurav Kumar")

if __name__ == "__main__":
    main()
