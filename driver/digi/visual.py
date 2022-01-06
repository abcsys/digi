#!/usr/bin/env python3

import digi

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State

app = dash.Dash(digi.name)

@digi.on.model
def h(m):
    print(m)

app.layout = html.Div([
    html.Div(
        html.Button(digi.name)
    )
])

def main():
    digi.run()
    app.run_server(debug=True, port=7534)

if __name__ == '__main__':
    main()
