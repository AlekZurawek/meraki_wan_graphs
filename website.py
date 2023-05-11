import sqlite3
from flask import Flask, render_template, request
import plotly
import plotly.graph_objs as go
import json
from datetime import datetime, timedelta

app = Flask(__name__)

def create_table(data, start_datetime, end_datetime):
    filtered_data = [row for row in data if start_datetime < datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f") < end_datetime]
    sorted_data = sorted(filtered_data, key=lambda x: x[0], reverse=True)
    table = """<table style="border-collapse: collapse; border: 1px solid black;">
    <tr>
        <th style="border: 1px solid black; padding: 5px;">Time</th>
        <th style="border: 1px solid black; padding: 5px;">Sent (Mbps)</th>
        <th style="border: 1px solid black; padding: 5px;">Received (Mbps)</th>
    </tr>"""
    for row in sorted_data:
        time_formatted = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f").strftime("%Y-%m-%d %H:%M")
        table += f"<tr><td style='border: 1px solid black; padding: 5px;'>{time_formatted}</td><td style='border: 1px solid black; padding: 5px;'>{row[1]:.1f}</td><td style='border: 1px solid black; padding: 5px;'>{row[2]:.1f}</td></tr>"
    table += "</table>"
    return table

def get_serials():
    conn = sqlite3.connect("meraki_data.db")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT serial FROM meraki_usage")
    serials = [serial[0] for serial in cur.fetchall()]
    conn.close()
    return serials

def get_interfaces(serial):
    conn = sqlite3.connect("meraki_data.db")
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT interface FROM meraki_usage WHERE serial=?", (serial,))
    interfaces = [interface[0] for interface in cur.fetchall()]
    conn.close()
    return interfaces

@app.route("/")
def index():
    serials = get_serials()
    return render_template("index.html", serials=serials)

@app.route("/graphs/<serial>", methods=["GET", "POST"])
def graphs(serial):
    start_datetime = None
    end_datetime = None
    if request.method == "POST":
        start_datetime = datetime.fromisoformat(request.form.get("start_datetime"))
        end_datetime = datetime.fromisoformat(request.form.get("end_datetime"))

    interfaces = get_interfaces(serial)
    all_graphs = []
    all_tables = []

    for interface in interfaces:
        conn = sqlite3.connect("meraki_data.db")
        cur = conn.cursor()
        cur.execute("SELECT time, sent, received FROM meraki_usage WHERE serial=? AND interface=?", (serial, interface))
        data = cur.fetchall()
        conn.close()

        time, sent, received = zip(*data)

        sent_trace = go.Scatter(x=time, y=sent, mode="lines", name=f"Sent (Mbps) - {interface}")
        received_trace = go.Scatter(x=time, y=received, mode="lines", name=f"Received (Mbps) - {interface}")

        graphJSON = json.dumps([sent_trace, received_trace], cls=plotly.utils.PlotlyJSONEncoder)
        all_graphs.append(graphJSON)

        if start_datetime and end_datetime:
            table = create_table(data, start_datetime, end_datetime)
        else:
            table = create_table(data, datetime.now() - timedelta(hours=1), datetime.now())
        all_tables.append(table)

    return render_template("graphs.html", all_graphs=all_graphs, all_tables=all_tables, serial=serial)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
