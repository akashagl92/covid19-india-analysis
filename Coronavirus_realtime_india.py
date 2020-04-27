import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pandas import DataFrame
import seaborn as sns
import json
import requests
import os.path
import lxml
from matplotlib.ticker import AutoMinorLocator
import csv
from pandas.io.json import json_normalize
import math
from bokeh.io import show, output_file
from bokeh.models import ColumnDataSource, Legend, LegendItem, Scatter, Label
from bokeh.plotting import figure, output_file, show, output_notebook, curdoc
from bokeh.models.tools import HoverTool
from bokeh.core.properties import value
from bokeh.palettes import Spectral11
import itertools
from bokeh.layouts import row, column
from bokeh.models.annotations import Title
from bokeh.models import Panel, Tabs
from datetime import timedelta
from bokeh.models import LinearAxis, Range1d
from bokeh.models import Div


bokeh_doc=curdoc()

cases_summary = requests.get('https://api.rootnet.in/covid19-in/stats/history')

json_data = cases_summary.json()
cases_summary=pd.json_normalize(json_data['data'], record_path='regional', meta='day')

cases_summary['loc']=np.where(cases_summary['loc']=='Nagaland#', 'Nagaland', cases_summary['loc'])

latest_date=cases_summary['day'].max()
highest_state=cases_summary[cases_summary['totalConfirmed']==cases_summary['totalConfirmed'].max()]['loc'].tolist()[0]

legend_it=[]

p = figure(plot_width=1200, plot_height=600, x_axis_type="datetime",  sizing_mode="scale_both")
p.title.text='Statewise Cases over Time'
p.title.align='center'
p.title.text_font_size='17px'
p.xaxis.axis_label = 'Date'
p.yaxis.axis_label = 'Number of Cases'


for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Spectral11)):
    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
    renderer=p.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['totalConfirmed'], line_width=2, color=color, alpha=1,
          muted_alpha=0.2)

    renderer.visible = False

    legend_it.append((name, [renderer]))

legend1=Legend(items=legend_it[0:16], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:33], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

p.add_layout(legend1,'right')
p.add_layout(legend2,'right')

cases_summary['day']=cases_summary['day'].astype('str')
source=ColumnDataSource(cases_summary)

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@x{%F}'),
                  ('Cases', '@y{0000}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}
p.add_tools(hover)

citation = Label(x=0, y=0, x_units='screen', y_units='screen',
                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')
p.add_layout(citation, 'above')

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

fig = column(p,div, sizing_mode='scale_both')
tab1 = Panel(child=fig, title="All Cases - Statewise")

#statewise death count over time

legend_it=[]

q = figure(plot_width=1200, plot_height=600, x_axis_type="datetime",  sizing_mode="scale_both")
q.title.text='Statewise Deaths over Time'
q.title.align='center'
q.title.text_font_size='17px'
q.xaxis.axis_label = 'Date'
q.yaxis.axis_label = 'Number of Deaths'

for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Spectral11)):
    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
    renderer=q.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['deaths'], line_width=2, color=color, alpha=1,
          muted_alpha=0.2)

    renderer.visible = False

    legend_it.append((name, [renderer]))

legend1=Legend(items=legend_it[0:16], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:33], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

q.add_layout(legend1,'right')
q.add_layout(legend2,'right')

cases_summary['day']=cases_summary['day'].astype('str')

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@x{%F}'),
                  ('Deaths', '@y{0000}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}
q.add_tools(hover)

citation = Label(x=0, y=0, x_units='screen', y_units='screen',
                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')
q.add_layout(citation, 'above')

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

fig = column(q,div, sizing_mode='scale_both')


tab2 = Panel(child=fig, title="All Deaths - Statewise")

#statwise death and total case over time

#r = figure(plot_width=1200, plot_height=700, x_axis_type="datetime",  sizing_mode="scale_both")
#r.title.text='statewise deaths over time'
#r.title.align='center'
#r.title.text_font_size='17px'
#r.xaxis.axis_label = 'date'
#r.yaxis.axis_label = 'cases/deaths'
#
#
#for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Spectral11)):
#    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
#    renderer=r.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['totalconfirmed'], line_width=2, color=color, alpha=1,
#          muted_alpha=0.2, line_color=color)
#    if renderer.on_change('visible'):
#        renderer_deaths.visible = true
#        renderer_deaths=r.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['deaths'], line_width=2, color=color, alpha=1,
#          muted_alpha=0.2, legend_label='deceased', line_color=color)
#
#    else:
#        renderer_deaths.visible=false
#
#    renderer.visible = false
#    renderer_deaths.visible = false
#
#    legend_it.append((name, [renderer]))
#
#legend1=legend(items=legend_it[0:16], location=(10,110), click_policy='hide', title="toggle states to activate", title_text_font_style = "bold")
#legend2=legend(items=legend_it[17:33], location=(10,110), click_policy='hide', title="toggle states to activate", title_text_font_style = "bold")
#
#r.add_layout(legend1,'right')
#r.add_layout(legend2,'right')
#
#cases_summary['day']=cases_summary['day'].astype('str')
#
#hover = hovertool(line_policy='next')
#hover.tooltips = [('date', '@x{%f}'),
#                  ('deaths', '@y{0000}')  # @$name gives the value corresponding to the legend
#]
#hover.formatters = {'@x': 'datetime'}
#r.add_tools(hover)
#tab3 = panel(child=r, title="cases/deaths")


#statewise case-to-death ratio over time

legend_it=[]

s = figure(plot_width=1200, plot_height=600, x_axis_type="datetime",  sizing_mode="scale_both")
s.title.text='Statewise Case-to-Death Ratio over Time'
s.title.align='center'
s.title.text_font_size='17px'
s.xaxis.axis_label = 'Date'
s.yaxis.axis_label = 'Case-to-Death Ratio'

cases_summary['case-death-ratio']=cases_summary['totalConfirmed']/cases_summary['deaths']
cases_summary['case-death-ratio']=cases_summary['case-death-ratio'].replace(np.inf,0)
cases_summary['case-death-ratio']=cases_summary['case-death-ratio'].replace(np.nan,0)


for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Spectral11)):
    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
    renderer=s.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['case-death-ratio'], line_width=2, color=color, alpha=1,
          muted_alpha=0.2)

    renderer.visible = False

    legend_it.append((name, [renderer]))

legend1=Legend(items=legend_it[0:16], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:33], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

s.add_layout(legend1,'right')
s.add_layout(legend2,'right')

cases_summary['day']=cases_summary['day'].astype('str')

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@x{%F}'),
                  ('Case-to-death Ratio', '@y{000.000}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}
s.add_tools(hover)

citation = Label(x=0, y=0, x_units='screen', y_units='screen',
                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')
s.add_layout(citation, 'above')

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

fig = column(s,div, sizing_mode='scale_both')


tab3 = Panel(child=fig, title="Cases-to-Death Ratio over Time - Statewise" )

#comparison of states for case-to-death ratio on the latest date

cases_summary['case-death-ratio']=cases_summary['case-death-ratio'].replace(np.inf,0)
cases_summary['case-death-ratio']=cases_summary['case-death-ratio'].replace(np.nan,0)

cases_summary_latest_date=cases_summary[cases_summary['day']==latest_date][['loc','case-death-ratio']].reset_index()
highest_case_death_ratio_state=cases_summary_latest_date[cases_summary_latest_date['case-death-ratio']==cases_summary_latest_date['case-death-ratio'].max()]['loc'].tolist()[0]

source=ColumnDataSource(cases_summary_latest_date)

t = figure(x_range=cases_summary_latest_date['loc'],plot_width=1200, plot_height=700,  sizing_mode="scale_both")
t.title.text='Statewise Case-to-Death Ratio'
t.title.align='center'
t.title.text_font_size='17px'
t.xaxis.axis_label = 'States'
t.yaxis.axis_label = 'Case-to-Death ratio'
t.xaxis.major_label_orientation = math.pi/2

#top_states=cases_summary['case-death-ratio'].sort_values(ascending=False)['loc']

t.vbar(cases_summary_latest_date['loc'],top=cases_summary_latest_date['case-death-ratio'], width=0.9, color=[color for name, color in zip(cases_summary_latest_date['loc'], itertools.cycle(Spectral11))])

hover = HoverTool(line_policy='next')
hover.tooltips = [('State', '@x'),
                  ('Case-to-Death ratio', '@top')  # @$name gives the value corresponding to the legend
]
t.add_tools(hover)

div1 = Div(text="""<b>Latest Date</b>: {} <br> <br>
                <b>Total Cases</b>: {:,} <br> 
                <b>Total Deaths</b>: {:,} <br> 
                 <b>Total Discharged</b>: {:,} <br> <br>
                <b>{} </b> has {:,} cases with the highest number of cases per death: {:.2f} <br><br> 
                <b>{} </b> has the highest number of cases of {:,} with {:.2f} cases per death. """
          .format(latest_date,cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum(),
                  cases_summary[cases_summary['day']==latest_date]['deaths'].sum(),
                  cases_summary[cases_summary['day']==latest_date]['discharged'].sum(),
                  highest_case_death_ratio_state,
                  cases_summary[cases_summary['loc']==highest_case_death_ratio_state]['totalConfirmed'][-1:].tolist()[0],
                  cases_summary_latest_date['case-death-ratio'].max(),
                  highest_state,
                  cases_summary[cases_summary['loc']==highest_state]['totalConfirmed'][-1:].tolist()[0],
                  cases_summary_latest_date[cases_summary_latest_date['loc']==highest_state]['case-death-ratio'].tolist()[0]),
width=200, height=280)

div2=Div(text="""<b>Top 6 states with highest cases per death</b>: <br> {} <br> {} <br> {} <br> {} <br> {} <br> {} <br>"""
           .format(cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[0],
                   cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[1],
                   cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[2],
                   cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[3],
                   cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[4],
                   cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[5]),
 width=200, height=200)

layout = column(div1, div2)
layout= row(t,layout)

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

layout = column(layout,div, sizing_mode='scale_both')


tab4 = Panel(child=layout, title="Case-to-Death Ratio - Statewise" )


#Deceased data from cases summary
cases_summary = requests.get('https://api.rootnet.in/covid19-in/stats/history')
json_data = cases_summary.json()
cases_summary=pd.json_normalize(json_data['data'])
cases_summary.columns=cases_summary.columns.str.replace('summary.','')

cases_summary['daily deaths']=cases_summary['deaths'].diff(1)
cases_summary['daily confirmed']=cases_summary['total'].diff(1)
cases_summary['daily discharged']=cases_summary['discharged'].diff(1)

#Total cases over time
cases_summary['day'] =cases_summary['day'].astype('str')
u = figure(x_range=cases_summary['day'], plot_width=1200, plot_height=700,  sizing_mode="scale_both")
u.title.text='Cases over Time - Daily'
u.title.align='center'
u.title.text_font_size='17px'
u.xaxis.axis_label = 'Date'
u.yaxis.axis_label = 'Cases'
u.xaxis.major_label_orientation = math.pi/2

total_bar=u.vbar(cases_summary['day'], top=cases_summary['daily confirmed'], width=0.9, legend_label='Daily Confirmed', color='#5e4fa2')
discharged_bar=u.vbar(cases_summary['day'], top=cases_summary['daily discharged'], width=0.9, legend_label='Daily Discharged', color='#66c2a5')
deceased_bar=u.vbar(cases_summary['day'], top=cases_summary['daily deaths'], width=0.9, legend_label='Daily Deaths', color='#3288bd')

hover_total_bar = HoverTool(line_policy='next', renderers=[total_bar])
hover_total_bar.tooltips = [('Day', '@x'),
                 ('Daily Cases', '@top')  # @$name gives the value corresponding to the legend
]

hover_deceased_bar = HoverTool(line_policy='next', renderers=[deceased_bar])
hover_deceased_bar.tooltips = [('Day', '@x'),
                  ('Daily Deaths', '@top')  # @$name gives the value corresponding to the legend
]

hover_discharged_bar = HoverTool(line_policy='next', renderers=[discharged_bar])
hover_discharged_bar.tooltips = [('Day', '@x'),
                  ('Daily Discharged', '@top')  # @$name gives the value corresponding to the legend
]

u.add_tools(hover_total_bar)
u.add_tools(hover_deceased_bar)
u.add_tools(hover_discharged_bar)

u.legend.location='top_left'
u.legend.click_policy='hide'
u.legend.title='Click to Switch Legend ON/OFF'

total_bar.visible=False
deceased_bar.visible=False
discharged_bar.visible=False

#citation = Label(x=0, y=0, x_units='screen', y_units='screen',
#                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')
#u.add_layout(citation, 'above')

div = Div(text="""<b>Latest Date</b>: {} <br> <br>
                <b>Total Cases</b>: {:,} <br> 
                <b>Total Deaths</b>: {:,} <br> 
                 <b>Total Discharged</b>: {:,} <br> <br>
                 <b> Important Dates: </b> <br><br>
                {}: <br>The highest number of cases - {:,}  <br><br> 
                {}: <br>The highest number of deaths - {:,} <br><br>
                {}: <br>The highest number of discharges - {:,} """
          .format(latest_date,
                  cases_summary.iloc[-1]['total'],
                  cases_summary.iloc[-1]['deaths'],
                  cases_summary.iloc[-1]['discharged'],
                  cases_summary[cases_summary['daily confirmed']==cases_summary['daily confirmed'].max()]['day'].tolist()[0],
                  cases_summary['daily confirmed'].max().astype('int64'),
                  cases_summary[cases_summary['daily deaths']==cases_summary['daily deaths'].max()]['day'].tolist()[0],
                  cases_summary['daily deaths'].max().astype('int64'),
                  cases_summary[cases_summary['daily discharged'] == cases_summary['daily discharged'].max()]['day'].tolist()[0],
                  cases_summary['daily discharged'].max().astype('int64')),
width=200, height=100)
layout = row(u, div)

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

layout = column(layout,div, sizing_mode='scale_both')

tab5 = Panel(child=layout, title="Total Cases over Time" )


#daily growth rate in cases and deaths
cases_summary['daily_case_growth']=cases_summary['total'].pct_change()
cases_summary['daily_death_growth']=cases_summary['deaths'].pct_change()
cases_summary['daily_discharge_growth']=cases_summary['discharged'].pct_change()


cases_summary['day'] = cases_summary['day'].astype('str')
v = figure(x_range= cases_summary['day'], plot_width=1200, plot_height=700,  sizing_mode="scale_both")
v.title.text='Growth Rate over Time - All India'
v.title.align='center'
v.title.text_font_size='17px'
v.xaxis.axis_label = 'Date'
v.yaxis.axis_label = 'Growth Rate'
v.xaxis.major_label_orientation = math.pi/2

case_growth_line=v.line(cases_summary['day'], cases_summary['total'].pct_change(), line_width=2, legend_label='Daily Case Growth Rate', color='#5e4fa2')
death_growth_line=v.line(cases_summary['day'],cases_summary['deaths'].pct_change(), line_width=2, legend_label='Daily Deceased Growth Rate', color='#3288bd')
discharge_growth_line=v.line(cases_summary['day'],cases_summary['discharged'].pct_change(), line_width=2, legend_label='Daily Discharged Growth Rate', color='#66c2a5')

cases_summary['day'] = cases_summary['day'].astype('str')
hover_case_growth = HoverTool(line_policy='next', renderers=[case_growth_line])
hover_case_growth.tooltips = [('Day', '@x'),
                 ('Daily Cases Growth Rate', '@y{0:.0%}')  # @$name gives the value corresponding to the legend
]

hover_death_growth = HoverTool(line_policy='next', renderers=[death_growth_line])
hover_death_growth.tooltips = [('Day', '@x{%F}'),
                  ('Daily Deceased Growth Rate', '@y{0:.0%}')  # @$name gives the value corresponding to the legend
]

hover_discharge_growth = HoverTool(line_policy='next', renderers=[discharge_growth_line])
hover_discharge_growth.tooltips = [('Day', '@x{%F}'),
                  ('Daily Discharged Growth Rate', '@y{0:.0%}')  # @$name gives the value corresponding to the legend
]

hover_death_growth.formatters = {'@x': 'datetime'}
hover_case_growth.formatters = {'@x': 'datetime'}
hover_discharge_growth.formatters = {'@x': 'datetime'}

v.add_tools(hover_case_growth)
v.add_tools(hover_death_growth)
v.add_tools(hover_discharge_growth)

v.legend.location='top_right'
v.legend.click_policy='hide'
v.legend.title='Click to Switch Legend ON/OFF'

case_growth_line.visible=False
death_growth_line.visible=False
discharge_growth_line.visible=False

#citation = Label(x=0, y=0, x_units='screen', y_units='screen',
#                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')
#v.add_layout(citation, 'above')

div = Div(text="""<b>Latest Date</b>: {} <br> <b>Total Cases</b>: {:,} <br> <b>Total Deaths</b>: {:,} <br> <br> <b>Latest Case Growth Rate</b>: {:.2%} <br> <b>Latest Death Growth Rate</b>: {:.2%} <br> <b>Latest Discharge Growth Rate</b>: {:.2%}""".format(latest_date,cases_summary.iloc[-1]['total'],cases_summary.iloc[-1]['deaths'],cases_summary.iloc[-1]['daily_case_growth'],cases_summary.iloc[-1]['daily_death_growth'],cases_summary.iloc[-1]['daily_discharge_growth'] ),
width=200, height=100)
layout = row(v, div)

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

layout = column(layout,div, sizing_mode='scale_both')

tab6 = Panel(child=layout, title="Growth Rate over Time" )


#Daily cases growth rate - statewise

cases_summary = requests.get('https://api.rootnet.in/covid19-in/stats/history')
json_data = cases_summary.json()
cases_summary=pd.json_normalize(json_data['data'], record_path='regional', meta='day')
cases_summary['loc']=np.where(cases_summary['loc']=='Nagaland#', 'Nagaland', cases_summary['loc'])

legend_it=[]

w = figure(plot_width=1200, plot_height=600, x_axis_type="datetime",  sizing_mode="scale_both")
w.title.text='Case Growth Rate'
w.title.align='center'
w.title.text_font_size='17px'
w.xaxis.axis_label = 'Date'
w.yaxis.axis_label = 'Cases Growth Rate'

cases_summary['daily_case_growth']=cases_summary['totalConfirmed'].groupby(cases_summary['loc']).pct_change()
cases_summary['daily_death_growth']=cases_summary['deaths'].groupby(cases_summary['loc']).pct_change()
cases_summary['daily_case_growth']=cases_summary['discharged'].groupby(cases_summary['loc']).pct_change()


for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Spectral11)):
    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
    #cases_summary['daily confirmed'] = cases_summary[cases_summary['loc'] == name]['totalConfirmed'].diff(1)
    renderer=w.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['totalConfirmed'].pct_change(), line_width=2, color=color, alpha=1,
          muted_alpha=0.2)

    renderer.visible = False

    check_negative_growth = lambda name: name + '*' if (
        (cases_summary[cases_summary['loc'] == name]['totalConfirmed'].pct_change() < 0).any()) else name
    legend_it.append((check_negative_growth(name), [renderer]))

legend1=Legend(items=legend_it[0:16], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:33], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

w.add_layout(legend1,'right')
w.add_layout(legend2,'right')

cases_summary['day']=cases_summary['day'].astype('str')
source=ColumnDataSource(cases_summary)

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@x{%F}'),
                  ('All Cases Growth Rate', '@y{0:.0%}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}
w.add_tools(hover)

#citation = Label(x=0, y=0, x_units='screen', y_units='screen',
#                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')
#w.add_layout(citation, 'above')

div1 = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=700, height=50, align='start')

div2 = Div(text="""* States with Data Corrected implied through negative growth on a particular date on the timescale""",
width=700, height=100, align='end')

layout = column(w, row(div1,div2), sizing_mode='scale_both')

tab7 = Panel(child=layout, title="Cases Growth Rate - Statewise")

#Daily death growth rate- statewise

legend_it=[]

x = figure(plot_width=1200, plot_height=600, x_axis_type="datetime",  sizing_mode="scale_both")
x.title.text='Fatality Growth Rate'
x.title.align='center'
x.title.text_font_size='17px'
x.xaxis.axis_label = 'Date'
x.yaxis.axis_label = 'Fatality Growth Rate'

cases_summary['daily_case_growth']=cases_summary['totalConfirmed'].groupby(cases_summary['loc']).pct_change()
cases_summary['daily_death_growth']=cases_summary['deaths'].groupby(cases_summary['loc']).pct_change()
cases_summary['daily_case_growth']=cases_summary['discharged'].groupby(cases_summary['loc']).pct_change()

for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Spectral11)):
    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
    #cases_summary['daily deaths'] = cases_summary[cases_summary['loc'] == name]['deaths'].diff(1)
    #cases_summary['daily discharged'] = cases_summary[cases_summary['loc'] == name]['discharged'].diff(1)
    #cases_summary['daily_death_growth'] = cases_summary[cases_summary['loc'] == name]['daily deaths'] / cases_summary[cases_summary['loc'] == name]['deaths']
    renderer=x.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['deaths'].pct_change(), line_width=2, color=color, alpha=1,
          muted_alpha=0.2)

    renderer.visible = False

    check_negative_growth = lambda name: name + '*' if (
        (cases_summary[cases_summary['loc'] == name]['deaths'].pct_change() < 0).any()) else name
    legend_it.append((check_negative_growth(name), [renderer]))


legend1=Legend(items=legend_it[0:16], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:33], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

x.add_layout(legend1,'right')
x.add_layout(legend2,'right')

cases_summary['day']=cases_summary['day'].astype('str')
source=ColumnDataSource(cases_summary)

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@x{%F}'),
                  ('Death Growth Rate', '@y{0:.0%}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}
x.add_tools(hover)

#citation = Label(x=0, y=0, x_units='screen', y_units='screen',
#                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')
#x.add_layout(citation, 'above')

div1 = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=700, height=50, align='start')

div2 = Div(text="""* States with Data Corrected implied through negative growth on a particular date on the timescale""",
width=700, height=100, align='end')

layout = column(x, row(div1,div2), sizing_mode='scale_both')

tab8 = Panel(child=layout, title="Fatality Growth Rate - Statewise")

#Total Tests done over time

cases_tests=requests.get('https://api.rootnet.in/covid19-in/stats/testing/raw')
json_data=cases_tests.json()
cases_tests=pd.json_normalize(data=json_data['data'])

cases_tests['timestamp']=pd.to_datetime(cases_tests['timestamp'], format=r'%Y-%m-%d')
cases_tests['timestamp']=cases_tests['timestamp'].dt.date

cases_tests['timestamp']=pd.to_datetime(cases_tests['timestamp'], format=r'%Y-%m-%d')
source=ColumnDataSource(cases_tests)
y = figure(plot_width=1200, plot_height=700,sizing_mode="scale_both", x_axis_type='datetime')
y.title.text='COVID19 Tests over Time'
y.title.align='center'
y.title.text_font_size='17px'
y.xaxis.axis_label = 'Date'
y.yaxis.axis_label = 'Tests Count'

sample_test=y.vbar(x=cases_tests['timestamp'], bottom=cases_tests['totalSamplesTested'], width=timedelta(days=0.5), color='#5e4fa2', alpha=1,
          legend_label="Samples Tested")
positive_test=y.vbar(x=cases_tests['timestamp'], top=cases_tests['totalPositiveCases'], width=timedelta(days=0.5),  color='#3288bd', alpha=1,
          legend_label="Tested Positive")

#cases_summary['day']=cases_summary['day'].astype('str')

hover = HoverTool(line_policy='next', renderers=[sample_test])
hover.tooltips = [('Date', '@x{%F}'),
                  ('Tests Count', '@bottom')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}

hover_pos = HoverTool(line_policy='next', renderers=[positive_test])
hover_pos.tooltips = [('Date', '@x{%F}'),
                  ('Positive Count', '@top')  # @$name gives the value corresponding to the legend
]
hover_pos.formatters = {'@x': 'datetime'}

y.add_tools(hover)
y.add_tools(hover_pos)
y.legend.location='top_left'
#citation = Label(x=0, y=0, x_units='screen', y_units='screen',
#                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')
#y.add_layout(citation, 'above')

div = Div(text="""<b>Latest Date</b>: {} <br> <br> <b>Total Tests</b>: {:,} <br><br> <b>Total Cases</b>: {:,} <br> <b>Total Deaths</b>: {:,}""".format(latest_date,cases_tests.iloc[-1]['totalSamplesTested'].astype('int64'), cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum(), cases_summary[cases_summary['day']==latest_date]['deaths'].sum()),
width=200, height=100)
layout = row(y, div)

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/testing/raw' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

layout = column(layout,div, sizing_mode='scale_both')

tab9 = Panel(child=layout, title="All India Tests over Time")


#Testing Growth Rate
cases_tests['timestamp']=pd.to_datetime(cases_tests['timestamp'], format=r'%Y-%m-%d')
cases_tests['daily_tests']=cases_tests['totalSamplesTested'].diff(1)
cases_tests['daily_confirmed']=cases_tests['totalPositiveCases'].diff(1)


z = figure(plot_width=1200, plot_height=700,sizing_mode="scale_both", x_axis_type='datetime', y_range=Range1d(start=0, end=cases_tests['totalSamplesTested'].max()))
z.title.text='COVID19 Tests Growth Rate over Time'
z.title.align='center'
z.title.text_font_size='17px'
z.xaxis.axis_label = 'Date'
z.yaxis.axis_label = 'Tests Count'

z.extra_y_ranges = {'tests_growth_rate': Range1d(start=cases_tests['totalSamplesTested'].pct_change().min(), end=cases_tests['totalSamplesTested'].pct_change().max())}
z.add_layout(LinearAxis(y_range_name='tests_growth_rate'), 'right')

sample_test_growth=z.vbar(x=cases_tests['timestamp'],top=cases_tests['totalSamplesTested'].pct_change() , width=timedelta(days=0.5), color='#5e4fa2', alpha=1, y_range_name='tests_growth_rate', legend_label='Tests Growth Rate')
sample_test=z.line(cases_tests['timestamp'], cases_tests['daily_tests'], line_width=2, color='#d53e4f', alpha=1, legend_label="Daily Tests Count")

#cases_summary['day']=cases_summary['day'].astype('str')

hover = HoverTool(line_policy='next', renderers=[sample_test_growth])
hover.tooltips = [('Date', '@x{%F}'),
                  ('Tests Growth Rate', '@top{0.:00%}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}

hover_growth = HoverTool(line_policy='next', renderers=[sample_test])
hover_growth.tooltips = [('Date', '@x{%F}'),
                  ('Tests Count', '@y')  # @$name gives the value corresponding to the legend
]
hover_growth.formatters = {'@x': 'datetime'}

z.add_tools(hover)
z.add_tools(hover_growth)
z.legend.click_policy='hide'
z.legend.title='Click to Switch Legend ON/OFF'

#citation = Label(x=0, y=0, x_units='screen', y_units='screen',
#                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')
#z.add_layout(citation, 'above')

div = Div(text="""<b>Latest Date</b>: {} <br><br> <b>Total Tests</b>: {:,} <br><br> <b>Total Cases</b>: {:,} <br> <b>Total Deaths</b>: {:,}""".format(latest_date,cases_tests.iloc[-1]['totalSamplesTested'].astype('int64'), cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum(), cases_summary[cases_summary['day']==latest_date]['deaths'].sum()),
width=200, height=100)

layout = row(z, div)

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/testing/raw' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

layout = column(layout,div, sizing_mode='scale_both')

tab10 = Panel(child=layout, title="All India Tests Growth Rate")


#Correlation between Tests Count and Confirmed Cases

cases_tests=cases_tests.dropna(axis=0, how='any')

fig=figure(plot_width=1200, plot_height=700,sizing_mode="scale_both")
fig.title.text='Correlation of Tests Vs Confirmed Cases'
fig.title.align='center'
fig.title.text_font_size='17px'
fig.xaxis.axis_label = 'Confirmed Cases'
fig.yaxis.axis_label = 'Tests Count'
fig.x_range=Range1d(0,cases_tests['daily_confirmed'].max() )


scatterplot=fig.circle(cases_tests['daily_confirmed'],cases_tests['daily_tests'], legend_label='Daily Tests Vs Confirmed Cases')

par = np.polyfit(cases_tests['daily_confirmed'],cases_tests['daily_tests'], 1, full=True)
slope=par[0][0]
intercept=par[0][1]
y_predicted = [slope*i + intercept  for i in cases_tests['daily_confirmed']]

LinearRegression = fig.line(cases_tests['daily_confirmed'],y_predicted,color='red',legend_label='y='+str(round(slope,2))+'x+'+str(round(intercept,2)))
correlation=cases_tests[['daily_confirmed','daily_tests']].corr('pearson')['daily_tests'][0]

hover = HoverTool(line_policy='next', renderers=[scatterplot])
hover.tooltips = [('Confirmed Cases', '@x'),
                  ('Tests Count', '@y')  # @$name gives the value corresponding to the legend
]

hover_line = HoverTool(line_policy='next', renderers=[LinearRegression])
hover_line.tooltips = [('Estimated Confirmed Cases at given rate', '@x'),
                  ('Tests Count ', '@y')  # @$name gives the value corresponding to the legend
]
fig.add_tools(hover)
fig.add_tools(hover_line)
fig.legend.location='top_left'

label=Label(x=-300, y=50, x_units='screen', y_units='screen', text="Pearson Correlation (R\u00b2): {:.2}".format(correlation), render_mode='css', text_font_size='14px')
fig.add_layout(label, 'right')

div = Div(text="""<b>Latest Date</b>: {} <br><br> 
                <b>Total Tests</b>: {:,} <br>
                <b>Total Cases</b>: {:,} <br> <br>
                <b>Pearson Correlation (R\u00b2):</b> {:.2} <br><br>"""
                .format(latest_date,
                        cases_tests.iloc[-1]['totalSamplesTested'].astype('int64'),
                        cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum(),
                        correlation),
width=200, height=100)

layout = row(fig, div)

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/testing/raw' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

layout = column(layout,div, sizing_mode='scale_both')

tab11 = Panel(child=layout, title="Correlation - Tests Vs Cases")

tabs = Tabs(tabs=[tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11])

output_file('Statewise Cases and Deaths-Bokeh.html')
show(tabs)

bokeh_doc.add_root(tabs)


#cases_summary = requests.get('https://api.rootnet.in/covid19-in/stats/history')
#
#json_data = cases_summary.json()
#cases_summary=pd.json_normalize(json_data['data'], record_path='regional', meta='day')
#
#cases_summary['loc']=np.where(cases_summary['loc']=='Nagaland#', 'Nagaland', cases_summary['loc'])
#
#latest_date=cases_summary['day'].max()
#highest_state=cases_summary[cases_summary['totalConfirmed']==cases_summary['totalConfirmed'].max()]['loc'].tolist()[0]
#
#plot=figure(plot_width=1200, plot_height=700, x_axis_type="datetime",  sizing_mode="scale_both")
#plot.title.text='COVID19 India Analysis Dashboard'
#plot.title.align='center'
#plot.title.text_font_size='17px'
##plot.xaxis.axis_label = 'Date'
##plot.yaxis.axis_label = 'Number of Cases'








#from bokeh.events import ButtonClick
#from bokeh.models import Button
#
#def callback(event):
#    print('Python:Click')
#
#button = Button(label="TEST")
#
#button.on_event(ButtonClick, callback)

#layout=row(plot, button)
#show(layout)

