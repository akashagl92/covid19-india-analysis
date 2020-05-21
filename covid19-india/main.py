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
from bokeh.models import ColumnDataSource, Legend, LegendItem, Scatter, Label, GroupFilter, CDSView, DataTable, TableColumn
from bokeh.plotting import figure, output_file, show, output_notebook, curdoc
from bokeh.models.tools import HoverTool
from bokeh.core.properties import value
from bokeh.palettes import Spectral11, Dark2_8
import itertools
from bokeh.layouts import row, column
from bokeh.models.annotations import Title
from bokeh.models import Panel, Tabs, Select
from datetime import timedelta
from bokeh.models import LinearAxis, Range1d
from bokeh.models import Div
from bokeh.embed import components
from bokeh.resources import CDN
from scipy.signal import savgol_filter


bokeh_doc=curdoc()

cases_summary = requests.get('https://api.rootnet.in/covid19-in/stats/history')

json_data = cases_summary.json()
cases_summary=pd.json_normalize(json_data['data'], record_path='regional', meta='day')

cases_summary['loc']=np.where(cases_summary['loc']=='Nagaland#', 'Nagaland', cases_summary['loc'])
cases_summary['loc']=np.where(cases_summary['loc']=='Madhya Pradesh#', 'Madhya Pradesh', cases_summary['loc'])
cases_summary['loc']=np.where(cases_summary['loc']=='Jharkhand#', 'Jharkhand', cases_summary['loc'])

cases_summary = cases_summary.dropna(axis=0)

latest_date=cases_summary['day'].max()
highest_state=cases_summary[cases_summary['totalConfirmed']==cases_summary['totalConfirmed'].max()]['loc'].tolist()[0]

cases_summary['newConfirmed']=cases_summary['totalConfirmed'].groupby(cases_summary['loc']).diff(1)

#Cumulative Days count since 1st reported case for each state
cases_summary['day_count']=(cases_summary['day'].groupby(cases_summary['loc']).cumcount())+1

#Cumulative Days count since 1st reported case
cases_summary['day'] = pd.to_datetime(cases_summary['day'])
cases_summary['cum_day_count']=(cases_summary['day']-cases_summary['day'].min())+timedelta(days=1)
cases_summary['cum_day_count']= cases_summary['cum_day_count'].astype('str').str.replace(' days 00:00:00.000000000', '')
cases_summary['cum_day_count'] = pd.to_numeric(cases_summary['cum_day_count'])

#Preparing Dataset for DataTable
cases_summary['growth-rate']=cases_summary['totalConfirmed'].groupby(cases_summary['loc']).diff(10)
case_growth_latest=pd.DataFrame(cases_summary.groupby('loc')['growth-rate'].last().reset_index())
case_growth_positive=case_growth_latest.sort_values(by='growth-rate',ascending=False).head(6)
cases_zero_growth=case_growth_latest.loc[case_growth_latest['growth-rate']==0]
case_growth_negative=case_growth_latest[-(case_growth_latest['growth-rate']==0)].sort_values(by='growth-rate',ascending=True).head(6)


#Cases Trends - Statewise

newConfirmed=cases_summary['newConfirmed'].groupby(cases_summary['day']).sum()

cases=pd.DataFrame({'newConfirmed': newConfirmed, 'totalConfirmed':cases_summary['totalConfirmed'].groupby(cases_summary['day']).sum()})\
   .reset_index()

cases['day'] = cases['day'].astype('str')


length = len(cases)

def window_size(length):
    if ((length // 2) % 2 == 1):
        return length // 2
    else:
        return (length // 2) + 1

cases['yhat']=savgol_filter(cases['newConfirmed'],window_size(length), 3)

source=ColumnDataSource(cases)

#Statewise Smoothing to view cases trajectory
newConfirmed=cases_summary.groupby(['loc','day'])['newConfirmed'].sum()
cases_states=pd.DataFrame({'newConfirmed': newConfirmed, 'totalConfirmed':cases_summary.groupby(['loc','day'])['totalConfirmed'].sum()})\
    .reset_index()

cases_new_final= pd.DataFrame()
for i in cases_states['loc'].unique():
    if len(cases_states[cases_states['loc']==i])<=7:
        continue
    else:
        def window_size(length):
            if ((length // 2) % 2 == 1):
                return length // 2
            else:
                return (length // 2) + 1
        cases_new=DataFrame({'loc':i,'yhat':savgol_filter(cases_states[cases_states['loc']==i]['newConfirmed'], window_size(len(cases_states[cases_states['loc']==i])), 3), 'day': cases_states[cases_states['loc']==i]['day'], 'newConfirmed': cases_states[cases_states['loc']==i]['newConfirmed'], 'totalConfirmed': cases_states[cases_states['loc']==i]['totalConfirmed']})
        cases_new_final=cases_new_final.append(cases_new)

cases_new_final['day'] = cases_new_final['day'].astype('str')

a = figure(plot_width=1200, plot_height=600, sizing_mode="scale_both", name="All cases - Statewise")
a.title.text = 'New Confirmed Case Trajectory'
a.title.align = 'center'
a.title.text_font_size = '17px'
a.xaxis.axis_label = 'Total Confirmed Cases'
a.yaxis.axis_label = 'New Confirmed Cases'

legend_it=[]
source=ColumnDataSource(data=cases_new_final)

for i, color in zip(range(len(cases_new_final['loc'].unique())),itertools.cycle(Dark2_8)):
    view=CDSView(source=source,
    filters=[GroupFilter(column_name='loc', group=cases_new_final['loc'].unique()[i])])

    renderer_yhat = a.line('totalConfirmed',
                       'yhat', line_width=2,  alpha=1,
                       muted_alpha=0.1, source=source, view=view, color=color)

    renderer_yhat_bold = a.line('totalConfirmed',
                       'yhat', line_width=2,  alpha=1,
                       muted_alpha=0.1, source=source, view=view, color=color)

    renderer_yhat.visible = False
    renderer_yhat_bold.muted = True

    legend_it.append((cases_new_final['loc'].unique()[i], [renderer_yhat]))

legend1=Legend(items=legend_it[0:17], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:36], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

a.add_layout(legend1,'right')
a.add_layout(legend2,'right')

citation = Label(x=0, y=0, x_units='screen', y_units='screen',
             text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')

a.add_layout(citation, 'above')

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@day'),
          ('Total Confirmed', '@totalConfirmed{0000}'),
          ('New Confirmed', '@newConfirmed{0000}'),
          ('State', '@loc')
            ]
a.add_tools(hover)

citation = Label(x=-50, y=-15, x_units='screen', y_units='screen',
             text='The data has been smoothened using Savitzky-Golay filter with a polynomial of 3rd degree. This chart helps understand the trajectory of case growth for each state and understand the impact of lockdown and containment efforts by administration and frontline warriors.', render_mode='css', text_font_size='14px', text_align='left')

a.add_layout(citation, 'below')


daily_insight = Div(text="""<br><br>New Confirmed cases has grown at the fastest rate in Tamil Nadu.<br><br>The number of cases has increased at the fastest rate from April 26th with 1821 Total Confirmed cases at the time.<br>""",
                      width=150, margin=(0,0,0,20))

daily_stats = Div(text="""<b> Total Cases</b> : {:,}<br>                                                                     
                          <b> Total Deaths</b> : {:,}<br>                                                                    
                          <b> Total Recovered</b> : {:,}"""
                        .format(cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum(),
                                cases_summary[cases_summary['day']==latest_date]['deaths'].sum(),
                                cases_summary[cases_summary['day']==latest_date]['discharged'].sum()), margin=(50,0,0,20))

a= row(a,column(daily_stats, daily_insight))

div = Div(text="""<br><br><b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
    width=300, height=50, align='start')

fig1 = column(a,div, sizing_mode='scale_both')


def update(attr,old,new):
    if(select.value=='All India'):
        newSource = ColumnDataSource(cases)
    if(select.value=='All States'):
        newSource = ColumnDataSource(cases_new_final)
    source.data = dict(newSource.data)


select=Select(title="Select:", value="All States", options=['All India', 'All States'], align='end', width=150, margin=(20,0,0,20))
select.on_change('value', update)

layout = column(select,fig1)

#Tables for Last 10 Days Cases Growth

source1=ColumnDataSource(data=case_growth_positive)
source2=ColumnDataSource(data=case_growth_negative)
source3=ColumnDataSource(data=cases_zero_growth)

columns = [
    TableColumn(field="loc", title="State"),
    TableColumn(field="growth-rate", title="New Cases (Last 10 days)")
]

data_table_growth = DataTable(source=source1, columns=columns, width=400, height=280, index_position=None, margin=(20,0,0,20),align='center')
data_table_improv = DataTable(source=source2, columns=columns, width=400, height=280, index_position=None, margin=(20,0,0,20),align='center')
data_table_stable = DataTable(source=source3, columns=columns, width=400, height=280, index_position=None, margin=(20,0,0,20),align='center')

div = Div(text="""<br>
                <b>Below are the top states that have shown the largest growth, least growth and no growth in new cases in last 10 Days.</b>""",
    width=800, height=50, align='center')

layout=column(layout,column(div, row(data_table_growth,data_table_improv,data_table_stable)))

tab12 = Panel(child=layout, title="Cases Trajectory")

#Statewise Cases Over Time
legend_it=[]

p = figure(plot_width=1200, plot_height=600, x_axis_type="datetime",  sizing_mode="scale_both")
p.title.text='Statewise Cases over Time'
p.title.align='center'
p.title.text_font_size='17px'
p.xaxis.axis_label = 'Date'
p.yaxis.axis_label = 'Number of Cases'


for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Dark2_8)):
    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
    renderer=p.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['totalConfirmed'], line_width=2, color=color, alpha=1,
          muted_alpha=0.2)

    renderer.visible = False

    legend_it.append((name, [renderer]))

legend1=Legend(items=legend_it[0:17], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:36], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

p.add_layout(legend1,'right')
p.add_layout(legend2,'right')

cases_summary['day']=cases_summary['day'].astype('str')
source1=ColumnDataSource(cases_summary)

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@x{%F}'),
                  ('Cases', '@y{0000}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}
p.add_tools(hover)

daily_stats1 = Label(x=-300, y=550, x_units='screen', y_units='screen',
                 text='Total Cases : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum()), render_mode='css', text_font_size='14px', text_align='right')
daily_stats2 = Label(x=-321, y=520, x_units='screen', y_units='screen',
                 text='Total Deaths : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['deaths'].sum()), render_mode='css', text_font_size='14px', text_align='right')
daily_stats3 = Label(x=-305, y=490, x_units='screen', y_units='screen',
                 text='Total Discharged : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['discharged'].sum()), render_mode='css', text_font_size='14px', text_align='right')

p.add_layout(daily_stats1, 'right')
p.add_layout(daily_stats2, 'right')
p.add_layout(daily_stats3, 'right')

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

for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Dark2_8)):
    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
    renderer=q.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['deaths'], line_width=2, color=color, alpha=1,
          muted_alpha=0.2)

    renderer.visible = False

    legend_it.append((name, [renderer]))

legend1=Legend(items=legend_it[0:17], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:36], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

q.add_layout(legend1,'right')
q.add_layout(legend2,'right')

cases_summary['day']=cases_summary['day'].astype('str')

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@x{%F}'),
                  ('Deaths', '@y{0000}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}
q.add_tools(hover)


daily_stats1 = Label(x=-300, y=550, x_units='screen', y_units='screen',
                 text='Total Cases : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum()), render_mode='css', text_font_size='14px', text_align='right')
daily_stats2 = Label(x=-321, y=520, x_units='screen', y_units='screen',
                 text='Total Deaths : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['deaths'].sum()), render_mode='css', text_font_size='14px', text_align='right')
daily_stats3 = Label(x=-305, y=490, x_units='screen', y_units='screen',
                 text='Total Discharged : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['discharged'].sum()), render_mode='css', text_font_size='14px', text_align='right')

q.add_layout(daily_stats1, 'right')
q.add_layout(daily_stats2, 'right')
q.add_layout(daily_stats3, 'right')


citation = Label(x=0, y=0, x_units='screen', y_units='screen',
                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')
q.add_layout(citation, 'above')

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

fig = column(q,div, sizing_mode='scale_both')


tab2 = Panel(child=fig, title="All Deaths - Statewise")


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
cases_summary['fatality_rate']=1/cases_summary['case-death-ratio']
cases_summary['fatality_rate']=cases_summary['fatality_rate'].replace(np.inf,0)
cases_summary['fatality_rate']=cases_summary['fatality_rate'].replace(np.nan,0)

for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Dark2_8)):
    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
    renderer=s.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['case-death-ratio'], line_width=2, color=color, alpha=1,
          muted_alpha=0.2)

    renderer.visible = False

    legend_it.append((name, [renderer]))

legend1=Legend(items=legend_it[0:17], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:36], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

s.add_layout(legend1,'right')
s.add_layout(legend2,'right')

cases_summary['day']=cases_summary['day'].astype('str')

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@x{%F}'),
                  ('Case-to-death Ratio', '@y{000.000}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}
s.add_tools(hover)


daily_stats1 = Label(x=-300, y=550, x_units='screen', y_units='screen',
                 text='Total Cases : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum()), render_mode='css', text_font_size='14px', text_align='right')
daily_stats2 = Label(x=-321, y=520, x_units='screen', y_units='screen',
                 text='Total Deaths : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['deaths'].sum()), render_mode='css', text_font_size='14px', text_align='right')
daily_stats3 = Label(x=-305, y=490, x_units='screen', y_units='screen',
                 text='Total Discharged : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['discharged'].sum()), render_mode='css', text_font_size='14px', text_align='right')

s.add_layout(daily_stats1, 'right')
s.add_layout(daily_stats2, 'right')
s.add_layout(daily_stats3, 'right')

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

cases_summary_latest_date=cases_summary[cases_summary['day']==latest_date][['loc','case-death-ratio', 'totalConfirmed', 'deaths', 'discharged', 'fatality_rate']].reset_index()
highest_case_death_ratio_state=cases_summary_latest_date[cases_summary_latest_date['case-death-ratio']==cases_summary_latest_date['case-death-ratio'].max()]['loc'].tolist()[0]
highest_fatality_rate_state=cases_summary_latest_date[cases_summary_latest_date['fatality_rate']==cases_summary_latest_date['fatality_rate'].max()]['loc'].tolist()[0]
source1=ColumnDataSource(cases_summary_latest_date)

t = figure(x_range=cases_summary_latest_date['loc'],plot_width=1200, plot_height=700,  sizing_mode="scale_both")
t.title.text='Statewise Case-to-Death Ratio'
t.title.align='center'
t.title.text_font_size='17px'
t.xaxis.axis_label = 'States'
t.yaxis.axis_label = 'Case-to-Death ratio'
t.xaxis.major_label_orientation = math.pi/2

#top_states=cases_summary['case-death-ratio'].sort_values(ascending=False)['loc']

t.vbar(cases_summary_latest_date['loc'],top=cases_summary_latest_date['case-death-ratio'], width=0.9, color=[color for name, color in zip(cases_summary_latest_date['loc'], itertools.cycle(Dark2_8))])

hover = HoverTool(line_policy='next')
hover.tooltips = [('State', '@x'),
                  ('Case-to-Death ratio', '@top')  # @$name gives the value corresponding to the legend
]
t.add_tools(hover)


div1 = Div(text="""<b>Latest Date</b>: {} <br> <br>
                <b>Total Cases</b>: {:,} <br> 
                <b>Total Deaths</b>: {:,} <br> 
                 <b>Total Recovered</b>: {:,} <br> <br>
                <b>{} </b> has {:,} cases having 1 death in {:.2f} cases (the highest of all the states). <br><br> 
                <b>{} </b> has the highest number of cases of {:,} having 1 death in {:.2f} cases. """
          .format(latest_date,cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum(),
                  cases_summary[cases_summary['day']==latest_date]['deaths'].sum(),
                  cases_summary[cases_summary['day']==latest_date]['discharged'].sum(),
                  highest_case_death_ratio_state,
                  cases_summary[cases_summary['loc']==highest_case_death_ratio_state]['totalConfirmed'][-1:].tolist()[0],
                  cases_summary_latest_date['case-death-ratio'].max(),
                  highest_state,
                  cases_summary[cases_summary['loc']==highest_state]['totalConfirmed'][-1:].tolist()[0],
                  cases_summary_latest_date[cases_summary_latest_date['loc']==highest_state]['case-death-ratio'].tolist()[0]),
width=200, height=280, margin=(30,0,0,20))

div2=Div(text="""<b>Top 6 states with highest cases per death (1/fatality-rate)</b>: <br><br> {} <br> {} <br> {} <br> {} <br> {} <br> {} <br>"""
           .format(cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[0],
                   cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[1],
                   cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[2],
                   cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[3],
                   cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[4],
                   cases_summary_latest_date.sort_values('case-death-ratio',ascending=False)['loc'].head(6).tolist()[5]),
 width=200, height=200, margin=(0,0,0,20))

layout = column(div1, div2)
layout1= row(t,layout)

a = figure(x_range=cases_summary_latest_date['loc'],plot_width=1200, plot_height=700,  sizing_mode="scale_both")
a.title.text='Statewise Fatality Rate'
a.title.align='center'
a.title.text_font_size='17px'
a.xaxis.axis_label = 'States'
a.yaxis.axis_label = 'Fatality Rate (%)'
a.xaxis.major_label_orientation = math.pi/2

#top_states=cases_summary['case-death-ratio'].sort_values(ascending=False)['loc']

a.vbar(cases_summary_latest_date['loc'],top=cases_summary_latest_date['fatality_rate'], width=0.9, color=[color for name, color in zip(cases_summary_latest_date['loc'], itertools.cycle(Dark2_8))])

hover = HoverTool(line_policy='next')
hover.tooltips = [('State', '@x'),
                  ('fatality-rate', '@top{:.2%}')  # @$name gives the value corresponding to the legend
]
a.add_tools(hover)

div3 = Div(text="""<b>Highest Fatality Rate: </b><br><br>
            <b>{} </b> - {:,} deaths in {:,} cases. <br><br> 
            <b>Fatality Rate of state with highest cases: </b><br><br>
            <b>{} </b> - {:,} deaths in {:,} cases.<br><br> """
          .format(highest_fatality_rate_state,
                  cases_summary[cases_summary['loc']==highest_fatality_rate_state]['deaths'][-1:].tolist()[0],
                  cases_summary[cases_summary['loc']==highest_fatality_rate_state]['totalConfirmed'][-1:].tolist()[0],
                  highest_state,
                  cases_summary[cases_summary['loc']==highest_state]['deaths'][-1:].tolist()[0],
                  cases_summary_latest_date[cases_summary_latest_date['loc']==highest_state]['totalConfirmed'].tolist()[0]),
width=200, height=280, margin=(30,0,0,20))


div4=Div(text="""<b>Top 6 states with highest fatality-rate</b>: <br><br> {} <br> {} <br> {} <br> {} <br> {} <br> {} <br>"""
           .format(cases_summary_latest_date.sort_values('fatality_rate',ascending=False)['loc'].head(6).tolist()[0],
                   cases_summary_latest_date.sort_values('fatality_rate',ascending=False)['loc'].head(6).tolist()[1],
                   cases_summary_latest_date.sort_values('fatality_rate',ascending=False)['loc'].head(6).tolist()[2],
                   cases_summary_latest_date.sort_values('fatality_rate',ascending=False)['loc'].head(6).tolist()[3],
                   cases_summary_latest_date.sort_values('fatality_rate',ascending=False)['loc'].head(6).tolist()[4],
                   cases_summary_latest_date.sort_values('fatality_rate',ascending=False)['loc'].head(6).tolist()[5]),
 width=200, height=200, margin=(10,0,0,20))

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/history' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

layout2=row(a,column(div3,div4))
layout1=column(layout1, margin=(0,0,40,0))
layout=column(layout1, layout2)

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
discharged_bar=u.vbar(cases_summary['day'], top=cases_summary['daily discharged'], width=0.9, legend_label='Daily Recovered', color='#66c2a5')
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
                  ('Daily Recovered', '@top')  # @$name gives the value corresponding to the legend
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
                 <b>Total Recovered</b>: {:,} <br> <br>
                 <b>Fatality Rate</b>: {:.2%} <br>
                 <b>Recovery Rate</b>: {:.2%} <br><br>
                 <b> Important Dates: </b> <br><br>
                {}: <br>The highest number of cases - {:,}  <br><br> 
                {}: <br>The highest number of deaths - {:,} <br><br>
                {}: <br>The highest number of Recovery - {:,} """
          .format(latest_date,
                  cases_summary.iloc[-1]['total'],
                  cases_summary.iloc[-1]['deaths'],
                  cases_summary.iloc[-1]['discharged'],
                  (cases_summary['deaths'][-1:]/cases_summary['total'][-1:]).tolist()[0],
                  (cases_summary['discharged'][-1:]/cases_summary['total'][-1:]).tolist()[0],
                  cases_summary[cases_summary['daily confirmed']==cases_summary['daily confirmed'].max()]['day'].tolist()[0],
                  cases_summary['daily confirmed'].max().astype('int64'),
                  cases_summary[cases_summary['daily deaths']==cases_summary['daily deaths'].max()]['day'].tolist()[0],
                  cases_summary['daily deaths'].max().astype('int64'),
                  cases_summary[cases_summary['daily discharged'] == cases_summary['daily discharged'].max()]['day'].tolist()[0],
                  cases_summary['daily discharged'].max().astype('int64')),
width=200, height=100,  margin=(30,0,0,20))
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
discharge_growth_line=v.line(cases_summary['day'],cases_summary['discharged'].pct_change(), line_width=2, legend_label='Daily Recovered Growth Rate', color='#66c2a5')

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
                  ('Daily Recovered Growth Rate', '@y{0:.0%}')  # @$name gives the value corresponding to the legend
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

div = Div(text="""<b>Latest Date</b>: {} <br> <b>Total Cases</b>: {:,} <br> <b>Total Deaths</b>: {:,} <br> <br> <b>Latest Case Growth Rate</b>: {:.2%} <br> <b>Latest Death Growth Rate</b>: {:.2%} <br> <b>Latest Revovered Growth Rate</b>: {:.2%} <br><br>
                <b> Fatality Rate</b>: {:.2%} <br>
                <b> Recovery Rate</b>: {:.2%}"""
                .format(latest_date,cases_summary.iloc[-1]['total'],cases_summary.iloc[-1]['deaths'],cases_summary.iloc[-1]['daily_case_growth'],cases_summary.iloc[-1]['daily_death_growth'],cases_summary.iloc[-1]['daily_discharge_growth'],
                                                    (cases_summary['deaths'][-1:] / cases_summary['total'][-1:]).tolist()[0], (cases_summary['discharged'][-1:]/cases_summary['total'][-1:]).tolist()[0] ),
width=200, height=100, margin=(30,0,0,20))
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
cases_summary['loc']=np.where(cases_summary['loc']=='Madhya Pradesh#', 'Madhya Pradesh', cases_summary['loc'])
cases_summary['loc']=np.where(cases_summary['loc']=='Jharkhand#', 'Jharkhand', cases_summary['loc'])

cases_summary = cases_summary.dropna(axis=0)

latest_date=cases_summary['day'].max()
highest_state=cases_summary[cases_summary['totalConfirmed']==cases_summary['totalConfirmed'].max()]['loc'].tolist()[0]

cases_summary['newConfirmed']=cases_summary['totalConfirmed'].groupby(cases_summary['loc']).diff(1)
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


for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Dark2_8)):
    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
    #cases_summary['daily confirmed'] = cases_summary[cases_summary['loc'] == name]['totalConfirmed'].diff(1)
    renderer=w.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['totalConfirmed'].pct_change(), line_width=2, color=color, alpha=1,
          muted_alpha=0.2)

    renderer.visible = False

    check_negative_growth = lambda name: name + '*' if (
        (cases_summary[cases_summary['loc'] == name]['totalConfirmed'].pct_change() < 0).any()) else name
    legend_it.append((check_negative_growth(name), [renderer]))

legend1=Legend(items=legend_it[0:17], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:36], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

w.add_layout(legend1,'right')
w.add_layout(legend2,'right')

cases_summary['day']=cases_summary['day'].astype('str')
source1=ColumnDataSource(cases_summary)

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@x{%F}'),
                  ('All Cases Growth Rate', '@y{0:.0%}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}
w.add_tools(hover)

citation = Label(x=0, y=0, x_units='screen', y_units='screen',
                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')

w.add_layout(citation, 'above')

daily_stats1 = Label(x=-300, y=550, x_units='screen', y_units='screen',
                 text='Total Cases : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum()), render_mode='css', text_font_size='14px', text_align='right')
daily_stats2 = Label(x=-321, y=520, x_units='screen', y_units='screen',
                 text='Total Deaths : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['deaths'].sum()), render_mode='css', text_font_size='14px', text_align='right')
daily_stats3 = Label(x=-305, y=490, x_units='screen', y_units='screen',
                text='Total Discharged : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['discharged'].sum()), render_mode='css', text_font_size='14px', text_align='right')

w.add_layout(daily_stats1, 'right')
w.add_layout(daily_stats2, 'right')
w.add_layout(daily_stats3, 'right')

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

for name, color in zip(cases_summary['loc'].unique(), itertools.cycle(Dark2_8)):
    cases_summary['day'] = pd.to_datetime(cases_summary['day'])
    renderer=x.line(cases_summary[cases_summary['loc']==name]['day'], cases_summary[cases_summary['loc']==name]['deaths'].pct_change(), line_width=2, color=color, alpha=1,
          muted_alpha=0.2)

    renderer.visible = False

    check_negative_growth = lambda name: name + '*' if (
        (cases_summary[cases_summary['loc'] == name]['deaths'].pct_change() < 0).any()) else name
    legend_it.append((check_negative_growth(name), [renderer]))


legend1=Legend(items=legend_it[0:17], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")
legend2=Legend(items=legend_it[17:36], location=(10,0), click_policy='hide', title="Click on States to Switch ON/OFF", title_text_font_style = "bold")

x.add_layout(legend1,'right')
x.add_layout(legend2,'right')

cases_summary['day']=cases_summary['day'].astype('str')
source1=ColumnDataSource(cases_summary)

hover = HoverTool(line_policy='next')
hover.tooltips = [('Date', '@x{%F}'),
                  ('Fatality Growth Rate', '@y{0:.0%}')  # @$name gives the value corresponding to the legend
]
hover.formatters = {'@x': 'datetime'}
x.add_tools(hover)

citation = Label(x=0, y=0, x_units='screen', y_units='screen',
                 text='Last Updated : {}'.format(latest_date), render_mode='css', text_font_size='12px')

x.add_layout(citation, 'above')

daily_stats1 = Label(x=-300, y=550, x_units='screen', y_units='screen',
                 text='Total Cases : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum()), render_mode='css', text_font_size='14px', text_align='right')
daily_stats2 = Label(x=-321, y=520, x_units='screen', y_units='screen',
                 text='Total Deaths : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['deaths'].sum()), render_mode='css', text_font_size='14px', text_align='right')
daily_stats3 = Label(x=-305, y=490, x_units='screen', y_units='screen',
                 text='Total Discharged : {:,}'.format(cases_summary[cases_summary['day']==latest_date]['discharged'].sum()), render_mode='css', text_font_size='14px', text_align='right')

x.add_layout(daily_stats1, 'right')
x.add_layout(daily_stats2, 'right')
x.add_layout(daily_stats3, 'right')

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

cases_tests['daily_tests']=cases_tests['totalSamplesTested'].diff(1)
cases_copy=pd.DataFrame(cases_summary.groupby(['day'])['totalConfirmed'].sum().diff(1)).reset_index()
cases_copy['day']=pd.to_datetime(cases_copy['day'])

cases_tests=cases_tests.merge(cases_copy, how='left', left_on='timestamp',right_on='day')

#Testing Growth Rate


z = figure(plot_width=1200, plot_height=700,sizing_mode="scale_both", x_axis_type='datetime')
z.title.text='COVID19 Tests over Time'
z.title.align='center'
z.title.text_font_size='17px'
z.xaxis.axis_label = 'Date'
z.yaxis.axis_label = 'Tests Count'
#z.extra_y_ranges = {'tests_growth_rate': Range1d(start=cases_tests['daily_tests'].pct_change().min(), end=cases_tests['daily_tests'].pct_change().max())}

#z.add_layout(LinearAxis(y_range_name='tests_growth_rate'), 'right')

sample_test=z.vbar(x=cases_tests['timestamp'], bottom=cases_tests['daily_tests'], width=timedelta(days=0.5), color='#5e4fa2', alpha=1,
          legend_label="Samples Tested")
positive_test=z.vbar(x=cases_tests['timestamp'], top=cases_summary.groupby(['day'])['newConfirmed'].sum(), width=timedelta(days=0.5),  color='#3288bd', alpha=1,
          legend_label="Tested Positive")
#sample_test_growth=z.line(cases_tests['timestamp'], cases_tests['daily_tests'].pct_change() , color='#e7298a', alpha=1, y_range_name='tests_growth_rate', legend_label='Tests Growth Rate', line_width = 2)



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

#hover_growth = HoverTool(line_policy='next', renderers=[sample_test_growth])
#hover_growth.tooltips = [('Date', '@x{%F}'),
#                  ('Tests Growth Rate', '@y{0.:00%}')  # @$name gives the value corresponding to the legend
#]
#hover_growth.formatters = {'@x': 'datetime'}

z.add_tools(hover)
z.add_tools(hover_pos)
#z.add_tools(hover_growth)

z.legend.click_policy='hide'
z.legend.title='Click to Switch Legend ON/OFF'
z.legend.location='top_left'

div=Div(text="""<b>Latest Date</b>: {} <br> <br> <b>Total Tests</b>: {:,} <br><br> <b>Total Cases</b>: {:,} <br> <b>Total Deaths</b>: {:,} <br><br> <b>Test Positive Rate</b>: {:.2%}<br><br> This rate means that 1 confirmed positive case for every {:,} tests. """.format(latest_date,cases_tests.iloc[-1]['totalSamplesTested'].astype('int64'), cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum(), cases_summary[cases_summary['day']==latest_date]['deaths'].sum(),
             cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum()/cases_tests.iloc[-1]['totalSamplesTested'].astype('int64'), round(cases_tests.iloc[-1]['totalSamplesTested'].astype('int64')/cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum()) ),
width=200, height=100, margin=(30,0,0,20))

layout = row(z, div)

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/testing/raw' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

layout = column(layout,div, sizing_mode='scale_both')

tab10 = Panel(child=layout, title="All India Tests")


#Correlation between Tests Count and Confirmed Cases
cases_tests=cases_tests.drop(labels=['totalIndividualsTested','totalPositiveCases'], axis=1)
cases_tests_without_na=cases_tests.dropna(axis=0, how='any')

fig=figure(plot_width=1200, plot_height=700,sizing_mode="scale_both")
fig.title.text='Correlation of Tests Vs Confirmed Cases'
fig.title.align='center'
fig.title.text_font_size='17px'
fig.xaxis.axis_label = 'Confirmed Cases'
fig.yaxis.axis_label = 'Daily Tests Count'
fig.x_range=Range1d(0,cases_tests_without_na['totalConfirmed'].max() )


scatterplot=fig.circle(cases_tests_without_na['totalConfirmed'],cases_tests_without_na['daily_tests'], legend_label='Daily Tests Vs Confirmed Cases')

par = np.polyfit(cases_tests_without_na['totalConfirmed'],cases_tests_without_na['daily_tests'], 1, full=True)
slope=par[0][0]
intercept=par[0][1]
y_predicted = [slope*i + intercept  for i in cases_tests_without_na['totalConfirmed']]

LinearRegression = fig.line(cases_tests_without_na['totalConfirmed'],y_predicted,color='red',legend_label='y='+str(round(slope,2))+'x+'+str(round(intercept,2)))
correlation=cases_tests_without_na[['totalConfirmed','daily_tests']].corr('pearson')['daily_tests'][0]

hover = HoverTool(line_policy='next', renderers=[scatterplot])
hover.tooltips = [('Confirmed Cases', '@x'),
                  ('Tests Count', '@y')  # @$name gives the value corresponding to the legend
]

hover_line = HoverTool(line_policy='next', renderers=[LinearRegression])
hover_line.tooltips = [('Estimated Confirmed Cases at given rate', '@x'),
                  ('Tests Count ', '@y{,}')  # @$name gives the value corresponding to the legend
]
fig.add_tools(hover)
fig.add_tools(hover_line)
fig.legend.location='top_left'

label=Label(x=-300, y=50, x_units='screen', y_units='screen', text="Pearson Correlation (R\u00b2): {:.2}".format(correlation), render_mode='css', text_font_size='14px')
fig.add_layout(label, 'right')

div = Div(text="""<b>Latest Date</b>: {} <br><br> 
                <b>Total Tests</b>: {:,} <br>
                <b>Total Cases</b>: {:,} <br> <br>
                <b>Test Positive Rate</b>: {:.2%}<br>
                This rate means that 1 confirmed positive case for every {:,} tests. <br><br>
                <b>Pearson Correlation (R\u00b2):</b> {:.2} <br><br>
                    For <br> 
                     0  < R\u00b2 < 0.3  - Poor Correlation <br>
                   0.3  < R\u00b2 < 0.75 - Moderate Correlation <br>
                  0.75  < R\u00b2 < 1    - High Correlation <br>"""
                .format(latest_date,
                        cases_tests.iloc[-1]['totalSamplesTested'].astype('int64'),
                        cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum(),
                        cases_summary[cases_summary['day']==latest_date]['totalConfirmed'].sum()/cases_tests.iloc[-1]['totalSamplesTested'].astype('int64'),
                        round(cases_tests.iloc[-1]['totalSamplesTested'].astype('int64') / cases_summary[cases_summary['day'] == latest_date]['totalConfirmed'].sum()),
                        correlation),
width=200, height=100, margin=(30,0,0,20))

layout = row(fig, div)

div = Div(text="""<b>Source:</b>
                COVID-19 REST API for India: <a href='https://api.rootnet.in/covid19-in/stats/testing/raw' target="_blank"> The Ministry of Health and Family Welfare</a> """,
width=300, height=50, align='start')

layout = column(layout,div, sizing_mode='scale_both')

tab11 = Panel(child=layout, title="Correlation - Tests Vs Cases")

tabs = Tabs(tabs=[tab12, tab1, tab2, tab3,  tab4, tab5, tab6,  tab7, tab8, tab10, tab11], name='tabs')

curdoc().add_root(tabs)
curdoc().title="COVID19 Analysis India"
