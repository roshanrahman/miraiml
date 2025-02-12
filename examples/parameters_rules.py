from time import sleep
import pandas as pd
import numpy as np
import warnings

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

from miraiml import HyperSearchSpace, Config, Engine

# Hiding LogisticRegression's convergence warnings
warnings.filterwarnings('ignore')

# Logistic Regression cannot use the 'l1' penalty for the solvers 'newton-cg',
# 'sag' and 'lbfgs' and the engine is designed to work with general model classes.

# So, the way that we can let it know this is by providing a function that
# implements such parameters rules. The function receives a dictionary of parameters
# and changes what is needed.

# We just need to make sure that those parameters will exist in the set of
# parameters tested by the engine, otherwise it will attempt to access an invalid
# key from the dictionary.


def logistic_regression_parameters_rules(parameters):
    if parameters['solver'] in ['newton-cg', 'sag', 'lbfgs']:
        parameters['penalty'] = 'l2'


# Now we create the list of search spaces containing only one element to keep it
# simple.
hyper_search_spaces = [
    HyperSearchSpace(
        model_class=LogisticRegression,
        id='Logistic Regression',
        parameters_values={
            'penalty': ['l1', 'l2'],
            'C': np.arange(0.1, 2, 0.1),
            'max_iter': np.arange(50, 300),
            'solver': ['newton-cg', 'lbfgs', 'liblinear', 'sag', 'saga'],
            'random_state': [0]
        },
        parameters_rules=logistic_regression_parameters_rules
    )
]

# Quick configuration
config = Config(
    local_dir='miraiml_local_parameters_rules',
    problem_type='classification',
    hyper_search_spaces=hyper_search_spaces,
    score_function=roc_auc_score
)

# Instantiating the engine
engine = Engine(config)

# Load data
data = pd.read_csv('pulsar_stars.csv')
train_data, test_data = train_test_split(data, stratify=data['target_class'],
                                         test_size=0.2, random_state=0)
engine.load_data(train_data, 'target_class', test_data)

# Fire!
print('Training...')
engine.restart()

# Let's wait 5 seconds and interrupt it
sleep(5)
engine.interrupt()

status = engine.request_status()
print('\nScores:', status['scores'])
