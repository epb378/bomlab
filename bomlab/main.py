import pandas as pd
import numpy as np
import random
import os
import tempfile
import matplotlib.pyplot as plt
import building_blocks_functions as bbp
from flask import Flask, render_template, request
data = [[0.1,0.3,0.15,np.nan],[0.9,0.2,0.4,np.nan],[0.7,0.35,0.1,np.nan],[0.2,0.4,0.65,np.nan],[0.2,0.7,0.1,np.nan]]
df=pd.DataFrame(data,columns=['x1','x2','x3','optimiser_score'])
def rand2():
	return round(random.uniform(0,1),2)
def randomrow():
	return pd.DataFrame([[rand2(),rand2(),rand2(),np.nan]],columns=['x1','x2','x3','optimiser_score'] )
def dummy_optimise(dataframe):
	for i in range(5): dataframe.append(randomrow())
	return dataframe
def remove_prefix(text, prefix):
    if text.startswith(prefix):
        return text[len(prefix):]
    return text
app = Flask(__name__)

a=tempfile.NamedTemporaryFile()
filename=a.name+'.png'

@app.route('/', methods=['GET','POST'])
def html_table(df=df,filename=filename):
	
	if request.method == 'POST':
		sampleID = request.values['sampleID']
		score = request.values['score']
		ID=int(sampleID)
		#score=float(score)
		df.at[ID,"optimiser_score"]=score
		if df["optimiser_score"].isnull().values.any()==False:
			df.to_csv('./static/ongoing_data.csv')
			for i in range(5):
				df2=randomrow()
				df=df.append(df2, ignore_index=True)
		plotdf=df[df.optimiser_score.notnull()]
		plotdf['xbar'] = plotdf.apply(lambda row: np.sqrt((row.x1)**2 + (row.x2)**2 + (row.x3)**3), axis=1)

		a=tempfile.NamedTemporaryFile()
		filename=remove_prefix(a.name, '/tmp/')
		filename='./static/'+filename+'.png'
		plotdf.plot(kind='scatter',x='xbar',y='optimiser_score')
		plt.savefig(filename)
		#plt.show
	return render_template('simple.html',  tables=[df.to_html(classes='data')], titles=df.columns.values, plot=filename)

"""def update_team_members():
    teamform = ExperimentForm()
    teamform.title.data = "My Experiment" # change the field's data
    for index, row in df.iterrows():
        member_form = DataForm()
        member_form.samplenum = row['samplenum'] # These fields don't use 'data'
        member_form.x1 = row['x1']
        member_form.x2 = row['x2']
        member_form.x3 = row['x3']
        member_form.optimiser_score = row['optimiser_score']

        teamform.teammembers.append_entry(member_form)

    return render_template('edit-team.html', teamform = teamform)
"""

if __name__ == '__main__':
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host='127.0.0.1', port=8080, debug=True)
# [START gae_python37_render_template]
