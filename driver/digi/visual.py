#!/usr/bin/env python3

import digi

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

app = dash.Dash(digi.name)
elements = [html.Button(digi.name)]

app.layout = html.Div([
    html.Div(id="digis"),
    dcc.Interval(
        id='interval',
        interval=1 * 1000,
        n_intervals=0
    ),
])

@app.callback(Output('digis', 'children'),
              Input('interval', 'n_intervals'))
def update_digis(n):
    digis, models = list(), digi.view.NameView(digi.rc.view()).m()
    digis.append(html.Button(digi.name))
    for name, _ in models.items():
        if name == "root":
            continue
        digis.append(html.Button(name))
    return digis


def main():
    digi.run()
    app.run_server(debug=True, port=7534)


if __name__ == '__main__':
    main()
