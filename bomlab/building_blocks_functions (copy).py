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

search_space=set_range_searchspace()


class BoothMetric(Metric):
    def fetch_trial_data(self, trial):  
        records = []
        for arm_name, arm in trial.arms_by_name.items():
            print("for")
            print(arm_name)
            val=input("enter trial result")
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
experiment=set_experiment("nedexpt",search_space)
sobol = Models.SOBOL(search_space=experiment.search_space)
generator_run = sobol.gen(5)

optimization_config = OptimizationConfig(
    objective = Objective(
        metric=BoothMetric(name="booth"), 
        minimize=True,
    ),
)

experiment.optimization_config = optimization_config


class MyRunner(Runner):
	def run(self, trial):
		return {"name": str(trial.index)}
    
experiment.runner = MyRunner()
experiment.new_batch_trial(generator_run=generator_run)
for arm in experiment.trials[0].arms:
    print(arm)
experiment.trials[0].run()
data=experiment.fetch_data()
print(data.df)

gpei = Models.BOTORCH(experiment=experiment, data=data)
generator_run = gpei.gen(5)
experiment.new_batch_trial(generator_run=generator_run)
for arm in experiment.trials[1].arms:
    print(arm)
