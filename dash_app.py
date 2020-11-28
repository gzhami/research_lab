"""
Dash application code.
Input: a list of strategy ids.
"""
import sys
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash
import plotly.graph_objects as go
from dash.dependencies import Input, Output, State
from utils import s3_util, rds
from config import S3_BUCKET
import base64

# create an s3 client
s3_client = s3_util.init_s3_client()
BUCKET_NAME = S3_BUCKET

dash_app = Dash(__name__)
dash_app.layout = html.Div()

TOTAL_CAPITAL = 10 ** 6


def fig_update(file_path):
    """
    Given the file path, return an updated fig graph to display.
    :param file_path: string, to get csv file.
    :return: fig, the styled graph.
    """

    split_path = file_path.split('/')
    prefix = "/".join(split_path[3:])

    csv_obj = s3_client.get_object(Bucket=BUCKET_NAME, Key=prefix)
    pnl_df = pd.read_csv(csv_obj['Body'])

    pnl_df['cusum'] = pnl_df['pnl'].cumsum()
    cr_fig = px.line(pnl_df, x='date', y='cusum')

    cr_fig.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )

    # Rolling sharpe ratio plot
    pnl_df['rolling_SR'] = pnl_df.pnl.rolling(180).apply(lambda x: (x.mean() - 0.02) / x.std(), raw=True)

    pnl_df.fillna(0, inplace=True)
    sr_df = pnl_df[pnl_df['rolling_SR'] > 0]
    sr_rolling = go.Figure([go.Scatter(x=sr_df['date'], y=sr_df['rolling_SR'],
                                       line=dict(color="DarkOrange"), mode='lines+markers')])
    sr_rolling.update_xaxes(
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1y", step="year", stepmode="backward"),
                dict(step="all")
            ])
        )
    )
    mean = np.mean(sr_df['rolling_SR'])
    avg_title = "Average value={:.3f}".format(mean)
    sr_rolling.add_hline(y=mean, line_width=3, line_dash="dash", line_color="green",
                         annotation_text=avg_title,
                         annotation_position="bottom right")

    # pnl histogram plot
    pnl_hist = go.Figure()
    profit = pnl_df[pnl_df['pnl'] > 0]
    loss = pnl_df[pnl_df['pnl'] < 0]

    pnl_hist.add_trace(go.Bar(x=profit['date'], y=loss['pnl'],
                         marker_color='crimson',
                         name='loss'))
    pnl_hist.add_trace(go.Bar(x=loss['date'], y=profit['pnl'],
                         marker_color='lightslategrey',
                         name='profit'
                         ))

    return cr_fig, sr_rolling, pnl_hist, pnl_df


def make_table(data):
    """
    Given the file path, return an updated table to display.
    :param data: string, to get csv file.
    :return: html.Div, the component in Dash containing table.
    """
    return html.Div(
        [
            dt.DataTable(
                data=data.to_dict('rows'),
                columns=[{'id': c, 'name': c} for c in data.columns],
                style_as_list_view=True,
                selected_rows=[],
                style_cell={'padding': '5px',
                            'whiteSpace': 'no-wrap',
                            'overflow': 'hidden',
                            'textOverflow': 'ellipsis',
                            'maxWidth': 0,
                            'height': 30,
                            'textAlign': 'left'},
                style_header={
                    'backgroundColor': 'white',
                    'fontWeight': 'bold',
                    'color': 'black'
                },
                style_cell_conditional=[],
                virtualization=True,
                n_fixed_rows=1
            ),
        ], className="seven columns", style={'margin-top': '35',
                                             'margin-left': '15',
                                             'border': '1px solid #C6CCD5'}
    )


def construct_plot(strategy_names, pnl_paths):
    """
    Construct whole structure of plots by given strategy_names, pnl_paths and table_paths.
    :param strategy_names: A dictionary to map strategy id to strategy name.
                           Key is strategy id, value is strategy name
    :param pnl_paths: A dictionary to map strategy id to corresponding pnl path of csv file.
                        Key is strategy id, value is a path string.
    :return: Lively dash layout.
    """
    options = []
    for name in strategy_names.keys():
        options.append({'label': '{}-{}'.format(strategy_names[name], name),
                        'value': strategy_names[name]})

    table_style = {
        "position": "fixed",
        "top": 70,
        "left": 0,
        "bottom": 5,
        "width": "30rem",
        "padding": "2rem 1rem",
        "background-color": "#f8f9fa",
    }

    content_style = {
        "margin-left": "32rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    }

    tabs_styles = {
        'height': '55px',
        'font-size': '150%',
        'fontWeight': 'bold'
    }

    contents = []
    for str_key, str_name in strategy_names.items():
        pnl_fig, sr_rolling, pnl_hist, pnl_df = fig_update(pnl_paths[str_key])
        table_df = pnl_summary(pnl_df)

        contents.append(
            dcc.Tab(label=str_name, children=[

                html.Div(
                    [
                        html.H1('Cumulative Return',
                                style={'textAlign': 'center'}),
                        html.Hr(),
                        dbc.Row(
                            [
                                dbc.Col(dcc.Graph(figure=pnl_fig),
                                        width={"size": 8, "offset": 2}),
                            ]
                        )
                    ],
                    style=content_style
                ),
                html.Div(
                    [
                        html.H1('Rolling Sharpe Ratio (6-months)',
                                style={'textAlign': 'center'}),
                        html.Hr(),
                        dbc.Row(
                            [
                                dbc.Col(dcc.Graph(figure=sr_rolling),
                                        width={"size": 8, "offset": 2}),
                            ]
                        )
                    ],
                    style=content_style
                ),
                html.Div(
                    [
                        html.H1('Profit and Loss histogram',
                                style={'textAlign': 'center'}),
                        html.Hr(),
                        dbc.Row(
                            [
                                dbc.Col(dcc.Graph(figure=pnl_hist),
                                        width={"size": 8, "offset": 2}),
                            ]
                        )
                    ],
                    style=content_style
                ),

                html.Div(
                    [
                        html.H1('Statistic Table',
                                style={'font_size': '80',
                                       'text_align': 'center'}),
                        html.Hr(),
                        dt.DataTable(
                            data=table_df.to_dict('records'),
                            columns=[{'id': c, 'name': c} for c in table_df.columns],

                            style_cell={'front_size': '16px'},
                            style_cell_conditional=[
                                {
                                    'if': {'column_id': 'Backtest'},
                                    'textAlign': 'left'
                                },

                                {
                                    'if': {'column_id': 'Category'},
                                    'textAlign': 'left'
                                },

                            ],
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                },
                                {
                                    'if': {'column_id': 'Category'},
                                    'fontWeight': 'bold'
                                }
                            ],
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            }
                        ),
                        dcc.Loading(html.A(
                            id="img-download",
                            href="",
                            children=[html.Button("Download Image", id="download-btn")],
                            target="_blank",
                            download="my-figure.pdf"
                        )),
                    ],
                    style=table_style
                )
            ]
            )
        )

    return html.Div([dcc.Tabs(contents, style=tabs_styles)])


@dash_app.callback(Output('img-download', 'href'),
              [Input('graph', 'figure')])
def make_image(figure):
    """ Make a picture """

    fmt = "pdf"
    mimetype = "application/pdf"

    data = base64.b64encode(to_image(figure, format=fmt)).decode("utf-8")
    pdf_string = f"data:{mimetype};base64,{data}"

    return pdf_string


def get_plot(strategy_ids):
    """
    Get two dictionaries, one mapping from strategy id to strategy name,
    another is mapping from strategy id to strategy location. And then construct dash plot.
    :return:
    """
    backtests = rds.get_all_locations(strategy_ids)
    strategy_names = {}
    pnl_paths = {}
    for idx, strategy_id in enumerate(strategy_ids):
        strategy_names[strategy_id] = backtests['strategy_name'].iloc[idx]
        pnl_paths[strategy_id] = backtests['pnl_location'].iloc[idx]

    dash_app.layout = construct_plot(strategy_names, pnl_paths)


def pnl_summary(data):
    """
    Statistic analysis of backtest result.
    :param data: A dataframe including the backtest results, contains date and pnl two columns.
    :return: A dataframe for making the table, it contains two columns,
    category name and corresponding values.
    """
    data['cumulative'] = data['pnl'].cumsum()
    result = {'Category': [], 'Value': []}
    total_date = data.shape[0]
    return_value = (data['cumulative'].iloc[-1]) / TOTAL_CAPITAL

    # Annual return
    annual_return = round(return_value / (total_date / 365) * 100, 2)
    result['Category'].append('Annual Return')
    result['Value'].append(str(annual_return) + '%')

    # Cumulative return
    cumulative_return = round(return_value * 100, 2)
    result['Category'].append('Cumulative Return')
    result['Value'].append(str(cumulative_return) + '%')

    # Annual volatility
    daily_change = data['pnl'].iloc[1:].div(TOTAL_CAPITAL)
    annual_volatility = round(daily_change.std() * np.sqrt(365), 2)
    result['Category'].append('Annual Volatility')
    result['Value'].append(str(annual_volatility))

    # Sharpe ratio
    ratio_value = data['pnl'].div(TOTAL_CAPITAL)
    sharpe_ratio = round(ratio_value.mean() / ratio_value.std() * np.sqrt(365), 2)
    result['Category'].append('Sharpe Ratio')
    result['Value'].append(str(sharpe_ratio))

    # Max Dropdown
    max_drop = round((np.max(data['pnl']) - np.min(data['pnl'])) / np.max(data['pnl']), 2)
    result['Category'].append('Max Dropdown')
    result['Value'].append(str(max_drop))

    # Skew
    skew = round(data['pnl'].skew(), 2)
    result['Category'].append('Skew')
    result['Value'].append(str(skew))

    # Kurtosis
    kurtosis = round(data['pnl'].kurtosis(), 2)
    result['Category'].append('Kurtosis')
    result['Value'].append(str(kurtosis))

    return pd.DataFrame(result)


def call_dash(*args):
    """
    Call dash process and construct plot.
    :param args: args should be ids, like 15, 20, 24
    :return:
    """
    ids = [str(item) for item in args[0][1:]]
    print(ids)
    get_plot(ids)
    dash_app.run_server(host='127.0.0.1', port=8050, debug=False, threaded=True)


def main(*args):
    """

    :param args:
    :return:
    """
    ids = args[0][1:]
    get_plot(ids)
    dash_app.run_server(debug=False)


if __name__ == "__main__":
    call_dash(sys.argv)
