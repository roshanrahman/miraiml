from time import sleep
import pandas as pd
import numpy as np

import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.metrics import roc_auc_score

from miraiml import HyperSearchSpace, Config, Engine


class LightGBM:
    def __init__(self, n_folds, **parameters):
        self.n_folds = n_folds
        parameters.update(dict(
            objective='binary',
            metric='auc',
            verbosity=-1
        ))
        self.parameters = parameters

        # List to save trained models:
        self.models = None

    def fit(self, X, y):
        self.models = []

        folds = StratifiedKFold(n_splits=self.n_folds)

        for _, (index_train, index_valid) in enumerate(folds.split(X, y)):
            X_train, y_train = X.iloc[index_train], y.iloc[index_train]
            X_valid, y_valid = X.iloc[index_valid], y.iloc[index_valid]

            dtrain = lgb.Dataset(X_train, y_train)
            dvalid = lgb.Dataset(X_valid, y_valid)

            model = lgb.train(
                params=self.parameters,
                train_set=dtrain,
                num_boost_round=1000000,  # Early stop will be used instead
                valid_sets=dvalid,
                early_stopping_rounds=30,
                verbose_eval=False
            )

            self.models.append(model)

    def predict_proba(self, X):

        y_test = None

        # Averaging predictions:
        for model in self.models:
            if y_test is None:
                y_test = model.predict(X)
            else:
                y_test += model.predict(X)

        y_test /= self.n_folds

        # Returning a 2-columns numpy.ndarray:
        return np.array([1-y_test, y_test]).transpose()


# You know the drill...
hyper_search_spaces = [
    HyperSearchSpace(
        model_class=LightGBM,
        id='LightGBM',
        parameters_values=dict(
            n_folds=[5],
            max_leaves=[3, 7, 15, 31],
            colsample_bytree=[0.2, 0.4, 0.6, 0.8, 1],
            learning_rate=[0.1]
        )
    )
]

config = Config(
    local_dir='miraiml_local_lightgbm_wrapper',
    problem_type='classification',
    hyper_search_spaces=hyper_search_spaces,
    score_function=roc_auc_score
)

engine = Engine(config)

data = pd.read_csv('pulsar_stars.csv')
train_data, test_data = train_test_split(data, stratify=data['target_class'],
                                         test_size=0.2, random_state=0)
engine.load_data(train_data, 'target_class', test_data)

print('Training...')
engine.restart()
sleep(10)

engine.interrupt()

status = engine.request_status()
print('\nScores:', status['scores'])
