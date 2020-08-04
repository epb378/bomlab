import pandas as pd
from ax import *
import numpy as np

def set_range_searchspace():
	range_param1 = RangeParameter(name="x1", lower=0.0, upper=1.0, parameter_type=ParameterType.FLOAT)
	range_param2 = RangeParameter(name="x2", lower=0.0, upper=1.0, parameter_type=ParameterType.FLOAT)
	range_param3 = RangeParameter(name="x3", lower=0.0, upper=1.0, parameter_type=ParameterType.FLOAT)
	search_space = SearchSpace(
	    parameters=[range_param1, range_param2, range_param3],
	)
	return search_space
class BoothMetric(Metric):
    def fetch_trial_data(self, trial):  
        records = []
        for arm_name, arm in trial.arms_by_name.items():
            val=input("enter trial result") ## how do i get this to take values from my df...
            params = arm.parameters

            records.append({
                "arm_name": arm_name,
		"x1":params["x1"],
		"x2":params["x2"],
		"x3":params["x3"],
                "metric_name": self.name,
                "mean": val,
                "sem": 0.0,
                "trial_index": trial.index,
            })
        return Data(df=pd.DataFrame.from_records(records))


def set_experiment(label, search_space):
	experiment = Experiment(
 	   name=label,
  	   search_space=search_space,
	)
	
	experiment.status_quo = Arm(
	    name="control", 
	    parameters={"x1": 0.0, "x2": 0.0, "x3":0.0,},
	)
	return experiment
class MyRunner(Runner):
	def run(self, trial):
		return {"name": str(trial.index)}

##should do this all OOP
def initialise_experiment(expt_name, sobol_size):
	search_space=set_range_searchspace()
	experiment=set_experiment(expt_name,search_space)
	sobol = Models.SOBOL(search_space=experiment.search_space)
	generator_run = sobol.gen(sobol_size)
	optimization_config = OptimizationConfig(
		objective = Objective(
			metric=BoothMetric(name="booth"), 
			minimize=True,
		),
	)
	experiment.optimization_config = optimization_config
	experiment.runner = MyRunner()
	experiment.new_batch_trial(generator_run=generator_run)
	return experiment

def get_batch_data(experiment, batch_number):
	experiment.trials[batch_number].run()
	data=experiment.fetch_data()
	return data
def generate_run(experiment, batch_size,batch_number,data):
	#data=experiment.fetch_data()
	gpei = Models.BOTORCH(experiment=experiment, data=data)
	generator_run = gpei.gen(batch_size)
	experiment.new_batch_trial(generator_run=generator_run)
	experiment.trials[batch_number].run()
	return experiment

