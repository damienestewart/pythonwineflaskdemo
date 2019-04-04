from flask import Flask, render_template, request, redirect, flash
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import datetime
import uuid
import os
import base64

#%matplotlib inline


app = Flask(__name__)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/upload", methods=["POST"])
def upload():
    skill = request.form['skill']
    print(skill)

    if 'spreadsheet' not in request.files:
        flash('No file part')
        redirect(request.url)

    file = request.files['spreadsheet']

    if file.filename == '':
        flash('No file part')
        redirect(request.url)

    spreadsheet_data = file.stream

    graph = chandler_awesome_code(spreadsheet_data, skill)
    enc = base64.b64encode(graph).decode()

    return render_template('image.html', image_data = enc)


def chandler_awesome_code(file, skill):
    plt.style.use('fivethirtyeight')
    matplotlib.rcParams['axes.labelsize'] = 14
    matplotlib.rcParams['xtick.labelsize'] = 12
    matplotlib.rcParams['ytick.labelsize'] = 12
    matplotlib.rcParams['text.color'] = 'k'
    
    dat = pd.read_csv(file).fillna(0)

    #Calculating percent of total share
    for column in dat.iloc[:,1:]:
        dat[column + ' %'] = dat[column] / sum(dat[column])* 100

    growth = dat.iloc[:,24:]
    dat = pd.concat([dat['TagName'], growth], axis=1, join='inner')

    #calculate growth rates from most recent months
    dat['Overall Growth'] = dat.iloc[:,-1] - dat.iloc[:,1]
    dat['Overall Growth Rate'] = (dat.iloc[:,-1] - dat.iloc[:,1])/ dat.iloc[:,1]

    #Replace NaN Values with zero
    dat = dat.replace([np.inf, -np.inf], np.nan)
    dat = dat.fillna(0)

    #sorts values by overall growth, from the last month to the first month
    dat = dat.sort_values(by='Overall Growth', ascending = False)

    #transpose the data
    dat_t = dat.transpose()
    dat_t.columns = dat_t.iloc[0]
    dat_t = dat_t[1:]
    dat_t = dat_t.reset_index()
    dat_t = dat_t.rename(columns={'level_0': 'Month'})

    #visualize the data
    dat_t.iloc[:-3,:10].plot(subplots=False, figsize=(15,9), title= 'Growth of SE Market Overtime'); plt.legend(loc='upper right')
    plt.xticks(np.arange((len(dat.columns)-4)), (dat.columns[1:]), rotation=45)

    #removing outliers to see growth (excludes high volume tags)
    limit = dat['Jan 18 %'].std() * 1.5
    outliers = []

    #only looks at the most recent growth rate to determine if its an outlier
    for x in dat['Jan 18 %']:
        if x > limit:
            outliers.append('Outlier')
        else:
            outliers.append('Normal')
    dat['Outliers'] = outliers

    #only pulls non-outliers
    no_outliers = dat.loc[dat['Outliers'] == 'Normal'].sort_values(by = 'Overall Growth', ascending=False)

    #transpose the data
    dat_t = no_outliers.transpose()
    dat_t.columns = dat_t.iloc[0]
    dat_t = dat_t[1:]
    dat_t = dat_t.reset_index()
    dat_t = dat_t.rename(columns={'level_0': 'Month'})

    #visualize the data
    dat_t.iloc[:-3,:10].plot(subplots=False, figsize=(15,9), title= 'Growth of SE Market Overtime, Excluding Outliers'); plt.legend(loc='upper right')
    plt.xticks(np.arange((len(dat.columns)-4)), (dat.columns[1:]), rotation=45)

    #shows the change in growth over time for a specific skill
    #transpose the data
    dat_t = dat.transpose()
    dat_t.columns = dat_t.iloc[0]
    dat_t = dat_t[1:]
    dat_t = dat_t.reset_index()
    dat_t = dat_t.rename(columns={'level_0': 'Month'})

    tag = skill
    skill = dat_t[['Month',tag]]

    skill.iloc[:-3, :].plot(subplots=False, figsize=(15,10), title="SE Share Growth of Skill:" + str(tag) + ' Over Time'); 
    plt.legend(loc='upper right', fontsize=20)
    plt.xticks(np.arange((len(dat.columns)-4)), (dat.columns[1:]), rotation=45)

    fileid = str(uuid.uuid4()) 
    plt.savefig('temp/' + fileid + '.png')

    graph_file = open('temp/' + fileid + '.png', 'rb')
    print(graph_file)
    graph = graph_file.read()

    graph_file.close()
    
    # delete temp file:
    os.remove('temp/' + fileid + '.png')

    return graph
