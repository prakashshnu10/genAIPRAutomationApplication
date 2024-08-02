import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text, Table, MetaData, Column, Integer, String

# Replace with your actual database URI
DATABASE_URI = 'postgresql+psycopg2://sonar:sonarqube@65.1.55.202/sonarqube'
engine = create_engine(DATABASE_URI)
metadata = MetaData()

# Define the table schemas
complexity_table = Table(
    'code_complexity',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('pr_number', Integer, nullable=False),
    Column('file_path', String, nullable=False),
    Column('complexity_level', String, nullable=False),
    Column('details', String, nullable=False)
)

versioning_table = Table(
    'api_versioning',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('pr_number', Integer, nullable=False),
    Column('file_path', String, nullable=False),
    Column('versioning_followed', String, nullable=False),
    Column('analysis', String, nullable=False)
)

swagger_table = Table(
    'swagger_documentation',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('pr_number', Integer, nullable=False),
    Column('file_path', String, nullable=False),
    Column('swagger_implemented', String, nullable=False),
    Column('details', String, nullable=False)
)

def fetch_table_data(pr_number):
    with engine.connect() as connection:
        # Fetch data from code_complexity
        complexity_query = text("SELECT * FROM code_complexity WHERE pr_number = :pr_number")
        complexity_data = connection.execute(complexity_query, {'pr_number': pr_number}).fetchall()
        complexity_df = pd.DataFrame(complexity_data, columns=['id', 'pr_number', 'file_path', 'complexity_level', 'details'])

        # Fetch data from api_versioning
        versioning_query = text("SELECT * FROM api_versioning WHERE pr_number = :pr_number")
        versioning_data = connection.execute(versioning_query, {'pr_number': pr_number}).fetchall()
        versioning_df = pd.DataFrame(versioning_data, columns=['id', 'pr_number', 'file_path', 'versioning_followed', 'analysis'])

        # Fetch data from swagger_documentation
        swagger_query = text("SELECT * FROM swagger_documentation WHERE pr_number = :pr_number")
        swagger_data = connection.execute(swagger_query, {'pr_number': pr_number}).fetchall()
        swagger_df = pd.DataFrame(swagger_data, columns=['id', 'pr_number', 'file_path', 'swagger_implemented', 'details'])

        return complexity_df, versioning_df, swagger_df

# Streamlit app
query_params = st.experimental_get_query_params()
pr_number = query_params.get('pr_number', [''])[0]
branch = query_params.get('branch_name', [''])[0]

if pr_number and branch:
    # Display the LLM report page
    st.title('LLM Report')
    report = fetch_llm_report(pr_number, branch)
    st.subheader(f'LLM Report for PR: {pr_number} on Branch: {branch}')
    st.text(report)  # Display the report text
    
    # Fetch and display details for the selected PR number
    st.subheader('Details for PR Number: {}'.format(pr_number))
    complexity_df, versioning_df, swagger_df = fetch_table_data(pr_number)

    # Display details
    st.write('### Code Complexity')
    st.dataframe(complexity_df)

    st.write('### API Versioning')
    st.dataframe(versioning_df)

    st.write('### Swagger Documentation')
    st.dataframe(swagger_df)
    
    st.markdown("[Back to Dashboard](./)")

else:
    # Display the main page
    df_sonar = fetch_sonar_data()
    st.title('Pull Request Dashboard')

    # Display company logo and title at the top
    st.image('nu10-logo.png', width=200)  # Adjust path and width as needed
    st.markdown("# Company Name")  # Adjust this to your actual company name

    # Sidebar for branch selection
    branches = df_sonar['branch'].unique()
    selected_branch = st.sidebar.selectbox('Select Branch', branches)

    # Filter data based on selected branch
    filtered_data = df_sonar[df_sonar['branch'] == selected_branch].copy()  # Make a copy to avoid SettingWithCopyWarning

    # Display branch name in sidebar
    st.sidebar.write(f"Selected Branch: {selected_branch}")

    # Display pull request status for the selected branch with links
    st.subheader(f'Pull Request Status for Branch: {selected_branch}')

    # Add links to the DataFrame
    def create_link(pr_number, branch):
        return f"/?pr_number={pr_number}&branch={branch}"  # Relative path for Streamlit routing

    filtered_data['LLM Report'] = filtered_data.apply(
        lambda row: f'<a href="{create_link(row["pr_number"], row["branch"])}">View Report</a>',
        axis=1
    )

    # Display the DataFrame with links
    st.markdown(
        filtered_data[['pr_number', 'status', 'merge_status', 'LLM Report']].to_html(escape=False),
        unsafe_allow_html=True
    )
