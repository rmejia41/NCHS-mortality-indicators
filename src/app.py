#Final App
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback_context
import plotly.express as px
import pandas as pd

# Load the original dataset
df = pd.read_csv('https://github.com/rmejia41/open_datasets/raw/main/NCHS_mortality.csv')

# Pivot the original dataset to include gender-specific rates
pivot_df = df.pivot_table(index='Year and Quarter',
                          columns='Cause of Death',
                          values=['Overall Rate', 'Rate Sex Female', 'Rate Sex Male'] +
                                 [col for col in df.columns if col.startswith('Rate Age')],
                          aggfunc='first')

# Flatten the MultiIndex in columns resulting from pivot_table
pivot_df.columns = [' '.join(col).strip() for col in pivot_df.columns.values]

# Reset index to make 'Year and Quarter' a column again
pivot_df.reset_index(inplace=True)

# Initialize the Dash app with the PULSE Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.PULSE]) #LUX PULSE # MINTY COSMO SPACELAB GRID SUPERHERO
server = app.server

# Define the app layout
app.layout = dbc.Container([
    html.H1("Mortality Indicators, CDC-NCHS Dashboard", className='mb-5 mt-5 text-center'),
    dbc.Row([
        dbc.Col(dcc.Graph(id='indicator-graph'), width=12)
    ], className='mb-3'),
    dbc.Row([
        dbc.Col([
            html.Label('Select Cause of Death:', className='me-2', style={'fontSize': '20px'}),
            dcc.Dropdown(
                id='cause-dropdown',
                options=[{'label': cause, 'value': cause} for cause in df['Cause of Death'].unique()],
                value=df['Cause of Death'].unique()[0],  # Default value
                style={'fontSize': '16px', 'width': '70%'}
            )
        ], width=4),
        dbc.Col([
            html.Label('Select Gender:', className='me-2', style={'fontSize': '20px'}),
            dcc.Dropdown(
                id='gender-dropdown',
                options=[
                    {'label': 'Overall', 'value': 'Overall Rate'},
                    {'label': 'Female', 'value': 'Rate Sex Female'},
                    {'label': 'Male', 'value': 'Rate Sex Male'}
                ],
                value='Overall Rate',  # Default value
                style={'fontSize': '16px', 'width': '70%'}
            )
        ], width=4),
        dbc.Col([
            html.Label('Select Age Range:', className='me-2', style={'fontSize': '20px'}),
            dcc.Dropdown(
                id='age-rate-dropdown',
                options=[{'label': 'No Selection', 'value': 'None'}] +
                        [{'label': col, 'value': col} for col in pivot_df.columns if col.startswith('Rate Age')],
                value='None',  # Default value to indicate no selection
                style={'fontSize': '16px', 'width': '70%'}
            )
        ], width=4)
    ])
], fluid=True)


@app.callback(
    Output('indicator-graph', 'figure'),
    [Input('cause-dropdown', 'value'), Input('gender-dropdown', 'value'), Input('age-rate-dropdown', 'value')]
)
def update_graph(selected_cause, selected_gender, selected_age_rate):
    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # Building the rate column name based on selections
    if triggered_id == 'gender-dropdown' or triggered_id == 'cause-dropdown':
        gender_specific_rate = f"{selected_gender} {selected_cause}" if selected_gender != 'Overall Rate' else f"Overall Rate {selected_cause}"
    elif triggered_id == 'age-rate-dropdown' and selected_age_rate != 'None':
        gender_specific_rate = selected_age_rate
    else:
        gender_specific_rate = f"Overall Rate {selected_cause}"

    if gender_specific_rate not in pivot_df.columns:
        gender_specific_rate = pivot_df.columns[0]

    # Determine line color dynamically
    line_color = "blue" if "Male" in gender_specific_rate else "red" if "Female" in gender_specific_rate else "grey"

    fig = px.line(
        pivot_df,
        x='Year and Quarter',
        y=gender_specific_rate,
        title=f'{selected_cause} Mortality Rate Over Time',
        markers=True,  # Adds markers at each data point
        color_discrete_sequence=[line_color]
    )

    # Update the hover template to include detailed information
    fig.update_traces(
        hovertemplate="<b>Year and Quarter:</b> %{x}<br><b>Rate:</b> %{y:.2f}<br>"
                      f"<b>Cause of Death:</b> {selected_cause}<br>"
                      f"<b>Gender:</b> {selected_gender.replace('Rate ', '')}<br>"
                      f"<b>Age Range:</b> {('All Ages' if selected_age_rate == 'None' else selected_age_rate.replace('Rate Age ', '').replace('_', ' to '))}<extra></extra>"
    )

    fig.update_layout(
            xaxis_title='Year and Quarter',
            yaxis_title="Rate",
            xaxis_showgrid=False,  # Removes x-axis gridlines
            yaxis_showgrid=False   # Removes y-axis gridlines
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=False, port=8060)