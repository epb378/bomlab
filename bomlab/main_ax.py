import pandas as pd
import numpy as np
import random
import os
import tempfile
import matplotlib.pyplot as plt
import building_blocks_functions as bbp
from flask import Flask, render_template, request
import pandas as pd
from ax import *
import numpy as np


experiment_name="nedexpt"
batch_size=5
sobol_size=batch_size
batch_number=0
data=[]
df=pd.DataFrame(data,columns=["arm_name","x1","x2","x3","score","trial_index"])
experiment=bbp.initialise_experiment(experiment_name, sobol_size)
experiment.trials[batch_number].run()
def set_batch_data(experiment,batch_number,df):
	records=[]
	for arm_name, arm in experiment.trials[batch_number].arms_by_name.items():
		print(df.loc[df["arm_name"]==arm_name].iloc[0]["score"])
		params=arm.parameters
		records.append({
		"arm_name":arm_name,
		"x1":params["x1"],
		"x2":params["x2"],
		"x3":params["x3"],
		"mean" : df.loc[df["arm_name"]==arm_name].iloc[0]["score"],
		"sem" : 0.0,
		"metric_name": "booth",
		"trial_index":batch_number})
	return Data(df=pd.DataFrame.from_records(records))
def get_batch_data(experiment,batch_number,df):
	for arm_name, arm in experiment.trials[batch_number].arms_by_name.items():
		params=arm.parameters
		arm_data={
		"arm_name":arm_name,
		"x1":params["x1"],
		"x2":params["x2"],
		"x3":params["x3"],
		"score":np.nan,
		"trial_index":batch_number}
		df=df.append(arm_data, ignore_index=True)
	return df
	#print(arm_name)
	#print(arm.parameters)
df=get_batch_data(experiment,batch_number,df)
print(df)

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
def html_table(df=df,filename=filename, batch_number=batch_number, batch_size=batch_size, experiment=experiment):
	
	if request.method == 'POST':
		sampleID = request.values['sampleID']
		score = request.values['score']
		ID=int(sampleID)
		#score=float(score)
		df.at[ID,"score"]=score
		if df["score"].isnull().values.any()==False:
			df.to_csv('./static/ongoing_data.csv')
			Data=set_batch_data(experiment,batch_number,df)
			batch_number+=1
			bbp.generate_run(experiment, batch_size,batch_number,Data)
			df=get_batch_data(experiment,batch_number,df)
			for arm in experiment.trials[batch_number].arms:
				print(arm)
		plotdf=df[df.score.notnull()]
		plotdf['xbar'] = plotdf.apply(lambda row: np.sqrt((row.x1)**2 + (row.x2)**2 + (row.x3)**3), axis=1)

		a=tempfile.NamedTemporaryFile()
		filename=remove_prefix(a.name, '/tmp/')
		filename='./static/'+filename+'.png'
		plotdf.plot(kind='scatter',x='xbar',y='score')
		plt.savefig(filename)
		#plt.show
	return render_template('simple.html',  tables=[df.to_html(classes='data')], titles=df.columns.values, plot=filename)



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
