import json
import os
import string

from bs4 import BeautifulSoup
import requests

import plotly
import dash_html_components as html
import dash


def test_rddd001_initial_state(dash_duo):
    app = dash.Dash(__name__)
    my_class_attrs = {
        "id": "p.c.4",
        "className": "my-class",
        "title": "tooltip",
        "style": {"color": "red", "fontSize": 30},
    }
    # fmt:off
    app.layout = html.Div([
        'Basic string',
        3.14,
        True,
        None,
        html.Div('Child div with basic string', **my_class_attrs),
        html.Div(id='p.c.5'),
        html.Div([
            html.Div('Grandchild div', id='p.c.6.p.c.0'),
            html.Div([
                html.Div('Great grandchild', id='p.c.6.p.c.1.p.c.0'),
                3.14159,
                'another basic string'
            ], id='p.c.6.p.c.1'),
            html.Div([
                html.Div(
                    html.Div([
                        html.Div([
                            html.Div(
                                id='p.c.6.p.c.2.p.c.0.p.c.p.c.0.p.c.0'
                            ),
                            '',
                            html.Div(
                                id='p.c.6.p.c.2.p.c.0.p.c.p.c.0.p.c.2'
                            )
                        ], id='p.c.6.p.c.2.p.c.0.p.c.p.c.0')
                    ], id='p.c.6.p.c.2.p.c.0.p.c'),
                    id='p.c.6.p.c.2.p.c.0'
                )
            ], id='p.c.6.p.c.2')
        ], id='p.c.6')
    ])
    # fmt:on

    dash_duo.start_server(app)

    # Note: this .html file shows there's no undo/redo button by default
    with open(
        os.path.join(
            os.path.dirname(__file__), "initial_state_dash_app_content.html"
        )
    ) as fp:
        expected_dom = BeautifulSoup(fp.read().strip(), "lxml")

    fetched_dom = dash_duo.dash_outerhtml_dom

    assert (
        fetched_dom.decode() == expected_dom.decode()
    ), "the fetching rendered dom is expected"

    assert (
        dash_duo.get_logs() == []
    ), "Check that no errors or warnings were displayed"

    assert dash_duo.driver.execute_script(
        "return JSON.parse(JSON.stringify("
        "window.store.getState().layout"
        "))"
    ) == json.loads(
        json.dumps(app.layout, cls=plotly.utils.PlotlyJSONEncoder)
    ), "the state layout is identical to app.layout"

    r = requests.get("{}/_dash-dependencies".format(dash_duo.server_url))
    assert r.status_code == 200
    assert (
        r.json() == []
    ), "no dependencies present in app as no callbacks are defined"

    assert dash_duo.redux_state_paths == {
        abbr: [
            int(token)
            if token in string.digits
            else token.replace("p", "props").replace("c", "children")
            for token in abbr.split(".")
        ]
        for abbr in (
            child.get("id")
            for child in fetched_dom.find(id="react-entry-point").findChildren(
                id=True
            )
        )
    }, "paths should reflect to the component hierarchy"

    rqs = dash_duo.redux_state_rqs
    assert not rqs, "no callback => no requestQueue"

    dash_duo.percy_snapshot(name="layout")
    assert dash_duo.get_logs() == [], "console has no errors"
