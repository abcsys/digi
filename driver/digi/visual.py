#!/usr/bin/env python3

import digi

import dash
from dash import dcc
from dash import html
from dash import dash_table
from dash.dependencies import Input, Output, State

import pandas as pd

app = dash.Dash(digi.name)
elements = [html.Button(digi.name)]

app.layout = html.Div([
    html.Div(id="digi"),
    html.Div(id="data"),
    dcc.Interval(
        id='interval',
        interval=digi.visual_refresh_interval,
        n_intervals=0
    ),
])


@app.callback(
    Output('digi', 'children'),
    Output('data', 'children'),
    Input('interval', 'n_intervals'),
)
def update_layout(n):
    digis, models = list(), digi.view.NameView(digi.rc.view()).m()
    digis.append(html.Button(digi.name))
    for name, _ in models.items():
        if name == "root":
            continue
        digis.append(html.Button(name))

    readings = digi.pool.query(f"from {digi.name} | not _type=='model' | head 10")
    df = pd.DataFrame(readings)
    data = dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
    )
    return digis, data


def main():
    digi.run()
    app.run_server(debug=True, port=7534)


if __name__ == '__main__':
    main()
