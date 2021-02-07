import dask.dataframe as dd
import pandas as pd

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table
import plotly.graph_objs as go
import plotly.express as px

from plotly.subplots import make_subplots
from dash.dependencies import Input, Output, State

df_schema = pd.read_json('/srv/retail_schema.json', lines=True)

def json_engine(*args, **kwargs):
    df = pd.read_json(*args, **kwargs)
    for c in (set(df_schema.columns) - set(df.columns)):
        df[c] = pd.Series(dtype=df_schema[c].dtype)
    df.drop(set(df.columns) - set(df_schema.columns))
    return df.loc[:, df_schema.columns]

nunique = dd.Aggregation(
    name="nunique",
    chunk=lambda s : s.apply(lambda x: list(set(x))),
    agg=lambda s0 : s0._selected_obj.groupby(level=list(range(s0._selected_obj.index.nlevels))).sum(),
    finalize=lambda s1 : s1.apply(lambda final: len(set(final))),
)

df = dd.read_json(
    "s3://retail-bucket/topics/retail/**.json",
    lines=True,
    engine=json_engine,
    storage_options={
        "key": "access_me",
        "secret": "i_am_a_secret",
        "client_kwargs": {"endpoint_url": "http://minio:9000"},
    },
)
df['InvoiceDate'] = df['InvoiceDate'].astype('datetime64[ns]')

df["total_sales"] = df["Quantity"] * df["UnitPrice"]

df_dt = df.groupby([pd.Grouper(key='InvoiceDate', freq='D')]).agg({
    'total_sales': 'sum',
    'CustomerID': nunique,
    'InvoiceNo': nunique
}).compute()
df_dt_country = df.groupby([pd.Grouper(key='InvoiceDate', freq='D'), 'Country']).agg({
    'total_sales': 'sum',
    'CustomerID': nunique,
    'InvoiceNo': nunique
})

df_dt_country_pivot = df_dt_country.compute().pivot_table(values='total_sales', index='InvoiceDate', columns='Country')
df_top_country = df.groupby([pd.Grouper(key='InvoiceDate', freq='M'), 'Country']).agg({
    'total_sales': 'sum'
}).compute()
last_data_month = df_top_country.index[-1][0]
top_countries = df_top_country.loc[pd.IndexSlice[last_data_month, :]].sort_values('total_sales', ascending=False)
top_countries['total_sales_pc'] = (top_countries / top_countries.sum()) * 100
top_countries.columns = ['Total Sales', 'Sales %']

df = None
df_dt_country = None
df_top_country = None

app = dash.Dash(__name__)

# create sales/customer plot with timerange slider
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=df_dt.index, y=df_dt['total_sales'], name='Sales'), secondary_y=False)
fig.add_trace(go.Scatter(x=df_dt.index, y=df_dt['CustomerID'], name='Customers'), secondary_y=True)
fig.add_trace(go.Scatter(x=df_dt.index, y=df_dt['InvoiceNo'], name='Transactions'), secondary_y=True)
fig.update_layout(
    xaxis=dict(
        rangeselector=dict(
            buttons=list([
                dict(count=1,
                     label="1m",
                     step="month",
                     stepmode="backward"),
                dict(count=6,
                     label="6m",
                     step="month",
                     stepmode="backward"),
                dict(step="all")
            ])
        ),
        rangeslider=dict(
            visible=True
        ),
        type="date"
    ),
    title_text="Total Customers and Sales",
    yaxis_title="Sales ($)",
    hovermode='x'
)
fig.update_yaxes(title_text='Count', secondary_y=True)

stripe_style = {
        'if': {'row_index': 'odd'},
        'backgroundColor': 'rgb(248, 248, 248)'
    }
header_style = {
    'backgroundColor': 'rgb(230, 230, 230)',
    'fontWeight': 'bold'
}

app.layout = html.Div(children=[
    html.Div([
        html.Div(
            dcc.Graph(figure=fig, id='sales_graph'),
            style={'width': '70%', 'display': 'inline-block', 'vertical-align': 'top'}
        ),
        html.Div([
            html.H3(f'Top Countries by Total Sales (MTD, {last_data_month.strftime("%b %Y")})'),
            dash_table.DataTable(
                id='top_country_table',
                columns=[{
                    'name': i,
                    'id': i,
                    'type': 'numeric',
                    'format': {
                        'nully': '--',
                        'specifier': '.2f'
                    },
                } for i in top_countries.reset_index().columns],
                data=top_countries.iloc[:5, :].reset_index().to_dict('records'),
                style_data_conditional=[stripe_style],
                style_header=header_style
            )],
            style={'width': '30%', 'display': 'inline-block'}
        )
    ],
    style={'width': '100%'}
    ),
    html.Div([
        dash_table.DataTable(
            id='country_table',
            columns=[{
                'name': i,
                'id': i,
                'type': 'numeric',
                'format': {
                    'nully': '--',
                    'specifier': '.2f'
                },
            } for i in df_dt_country_pivot.reset_index().columns],
            style_data_conditional=[stripe_style],
            style_header=header_style
        )
    ],
    style={'width': '100%', 'max-height': '300px', 'overflow': 'scroll'}
    ),
    html.Pre(id='test_out', style={'color': 'white'})
])

@app.callback(Output('country_table', 'data'),
              [Input('sales_graph', 'relayoutData')])
def update_muni(sg_data):
    min_dt = df_dt_country_pivot.index[0]
    max_dt = df_dt_country_pivot.index[-1]
    if sg_data is not None:
        if 'xaxis.range' in sg_data: # moved using the range slider
            min_dt = sg_data['xaxis.range'][0]
            max_dt = sg_data['xaxis.range'][-1]
        elif 'xaxis.range[0]' in sg_data: # moved using the graph
            min_dt = sg_data['xaxis.range[0]']
            max_dt = sg_data['xaxis.range[1]']
        elif 'xaxis.autorange' in sg_data or 'autosize' in sg_data: # used the all/reset button
            pass
    # ToDo should not refresh if there are no range changes
    return (df_dt_country_pivot[(df_dt_country_pivot.index >= min_dt) &
            (df_dt_country_pivot.index <= max_dt)].reset_index().to_dict('records'))

if __name__ == '__main__':
    app.css.config.serve_locally = True
    app.scripts.config.serve_locally = True
    app.run_server(debug=False, host='0.0.0.0', port=8080)