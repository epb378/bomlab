#!/usr/bin/env python
# coding: utf-8

# # Building Blocks of Ax

# This tutorial illustrates the core Ax classes and their usage by constructing, running, and saving an experiment through the Developer API.

# In[1]:


import pandas as pd
from ax import *


# ## 1. Define the search space

# The core `Experiment` class only has one required parameter, `search_space`. A SearchSpace is composed of a set of parameters to be tuned in the experiment, and optionally a set of parameter constraints that define restrictions across these parameters.
# 
# Here we range over two parameters, each of which can take on values between 0 and 10.

# In[2]:


range_param1 = RangeParameter(name="x1", lower=0.0, upper=1.0, parameter_type=ParameterType.FLOAT)
range_param2 = RangeParameter(name="x2", lower=0.0, upper=1.0, parameter_type=ParameterType.FLOAT)
range_param3 = RangeParameter(name="x3", lower=0.0, upper=1.0, parameter_type=ParameterType.FLOAT)

search_space = SearchSpace(
    parameters=[range_param1, range_param2, range_param3],
)


# Note that there are two other types of parameters, FixedParameter and ChoiceParameter. Although we won't use these in this example, you can create them as follows.

# In[3]:


#choice_param = ChoiceParameter(name="choice", values=["foo", "bar"], parameter_type=ParameterType.STRING)
#fixed_param = FixedParameter(name="fixed", value=[True], parameter_type=ParameterType.BOOL)


# Sum constraints enforce that the sum of a set of parameters is greater or less than some bound, and order constraints enforce that one parameter is smaller than the other. We won't use these either, but see two examples below.

# In[4]:


#sum_constraint = SumConstraint(
#    parameters=[range_param1, range_param2], 
#    is_upper_bound=True, 
#    bound=5.0,
#)

#order_constraint = OrderConstraint(
#    lower_parameter = range_param1,
#    upper_parameter = range_param2,
#)


# ## 2. Define the experiment

# Once we have a search space, we can create an experiment.

# In[5]:


experiment = Experiment(
    name="experiment_building_blocks",
    search_space=search_space,
)


# We can also define control values for each parameter by adding a status quo arm to the experiment.

# In[6]:


experiment.status_quo = Arm(
    name="control", 
    parameters={"x1": 0.0, "x2": 0.0, "x3":0.0,},
)


# ## 3. Generate arms

# We can now generate arms, i.e. assignments of parameters to values, that lie within the search space. Below we use a Sobol generator to generate ten quasi-random arms. The `Models` registry provides a set of standard models Ax contains.

# In[7]:


sobol = Models.SOBOL(search_space=experiment.search_space)
generator_run = sobol.gen(5)
print('printing SOBOL')
for arm in generator_run.arms:
    print(arm)


# To inspect available model settings, we can call `view_kwargs` or `view_defaults` on a specific model:

# In[8]:


Models.SOBOL.view_kwargs()  # Shows keyword argument names and typing.


# Any of the default arguments can be overriden by simply passing that keyword argument to the model constructor (e.g. `Models.SOBOL`).

# ## 4. Define an optimization config with custom metrics

# In order to perform an optimization, we also need to define an optimization config for the experiment. An optimization config is composed of an objective metric to be minimized or maximized in the experiment, and optionally a set of outcome constraints that place restrictions on how other metrics can be moved by the experiment. 
# 
# In order to define an objective or outcome constraint, we first need to subclass `Metric`. Metrics are used to evaluate trials, which are individual steps of the experiment sequence. Each trial contains one or more arms for which we will collect data at the same time.
# 
# Our custom metric(s) will determine how, given a trial, to compute the mean and sem of each of the trial's arms.
# 
# The only method that needs to be defined for most metric subclasses is `fetch_trial_data`, which defines how a single trial is evaluated, and returns a pandas dataframe.

# In[9]:


class BoothMetric(Metric):
    def fetch_trial_data(self, trial):  
        records = []
        for arm_name, arm in trial.arms_by_name.items():
            params = arm.parameters
            records.append({
                "arm_name": arm_name,
                "metric_name": self.name,
                "mean": (params["x1"]**2 + params["x2"]**2 + params["x3"]**2),
                "sem": 0.0,
                "trial_index": trial.index,
            })
        return Data(df=pd.DataFrame.from_records(records))


# Once we have our metric subclasses, we can define on optimization config.

# In[10]:


optimization_config = OptimizationConfig(
    objective = Objective(
        metric=BoothMetric(name="booth"), 
        minimize=True,
    ),
)

experiment.optimization_config = optimization_config


# Outcome constraints can also be defined as follows and passed into the optimization config.

# In[11]:


outcome_constraint = OutcomeConstraint(
    metric=Metric("constraint"), 
    op=ComparisonOp.LEQ, 
    bound=0.5,
)


# ## 5. Define a runner

# Before an experiment can collect data, it must have a `Runner` attached. A runner handles the deployment of trials. A trial must be "run" before it can be evaluated.
# 
# Here, we have a dummy runner that does nothing. In practice, a runner might be in charge of pushing an experiment to production.
# 
# The only method that needs to be defined for runner subclasses is `run`, which performs any necessary deployment logic, and returns a dictionary of resulting metadata.

# In[12]:


class MyRunner(Runner):
    def run(self, trial):
        return {"name": str(trial.index)}
    
experiment.runner = MyRunner()


# ## 6. Create a trial

# Now we can collect data for arms within our search space and begin the optimization. We do this by:
# 1. Generating arms for an initial exploratory batch (already done above, using Sobol)
# 2. Adding these arms to a trial
# 3. Running the trial
# 4. Evaluating the trial
# 5. Generating new arms based on the results, and repeating

# In[13]:


experiment.new_batch_trial(generator_run=generator_run)


# Note that the arms attached to the trial are the same as those in the generator run above, except for the status quo, which is automatically added to each trial.

# In[14]:


for arm in experiment.trials[0].arms:
    print(arm)


# If our trial should contain contain only one arm, we can use `experiment.new_trial` instead.

# In[15]:


experiment.new_trial().add_arm(Arm(name='single_arm', parameters={'x1': 1, 'x2': 1, 'x3':1,}))


# In[16]:


print(experiment.trials[1].arm)


# ## 7. Fetch data

# In[17]:


experiment.trials[0].run()


# In[18]:


data = experiment.fetch_data()


# We can inspect the data that was fetched for each (arm, metric) pair.

# In[19]:


data.df


# ## 8. Iterate using GP+EI

# Now we can model the data collected for the initial set of arms via Bayesian optimization (using the Botorch model default of Gaussian Process with Expected Improvement acquisition function) to determine the new arms for which to fetch data next.

# In[20]:


gpei = Models.BOTORCH(experiment=experiment, data=data)
generator_run = gpei.gen(5)
experiment.new_batch_trial(generator_run=generator_run)


# In[21]:


for arm in experiment.trials[2].arms:
    print(arm)


# In[22]:


experiment.trials[2].run()
data = experiment.fetch_data()
data.df


# ## 9. Save to JSON or SQL

# At any point, we can also save our experiment to a JSON file. To ensure that our custom metrics and runner are saved properly, we first need to register them.

# In[23]:


from ax.storage.metric_registry import register_metric
from ax.storage.runner_registry import register_runner

register_metric(BoothMetric)
register_runner(MyRunner)

save(experiment, "experiment.json")


# In[24]:


loaded_experiment = load("experiment.json")




