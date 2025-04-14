# Step 1
# Initial Setup
from math import exp
# TODO test with isolation tree and hbos
from pyod.models.base import BaseDetector
from sklearn.ensemble import IsolationForest
from sklearn.model_selection import ParameterSampler
from sklearn.svm import OneClassSVM
from pyod.models.auto_encoder import AutoEncoder
from pyod.models.vae import VAE
from pyod.models.mcd import MCD
from pyod.models.knn import KNN
from pyod.models.hbos import HBOS
import os
from pyts.approximation import PiecewiseAggregateApproximation
import numpy as np
import pandas as pd
import sys

# Check packages installed
import pkg_resources
required = {'pandas', 'numpy', 'pyts', 'pyod', 'sklearn'}
installed = {pkg.key for pkg in pkg_resources.working_set}
missing = required - installed

if missing:
    print(f"Missing the following libraries: {missing}")
    raise Exception

# Configuration
# Directory that contains the data
base_data_location = r"..\..\data"
# Base results directory
base_results_location = r"..\..\analysis_results2"
# Size of the window around events that removes measurements close to events
CLEANING_WINDOW_SIZE = 4 * 60 * 60
# Size of the window around events for the scoring method
SCORE_WINDOW_SIZE = 4 * 60 * 60
# Random state
RANDOM_STATE = 42
# Number of random parameter combination that will tested during tuning
N_RAND_TUNING_ITER = 30
# Persist raw results in files
SAVE_RAW = True

# Methods that will be used
methods = {   "IsolationForest": lambda params: IsolationForest(**params),
     "OneClassSVM": lambda params: OneClassSVM(**params),
    # "Autoencoder": lambda params: AutoEncoder(**params)
    # "VAE": lambda params: VAE(**params)
     "KNN": lambda params: KNN(**params),
    # "MCD": lambda params: MCD(**params),
    "HBOS": lambda params: HBOS(**params)
}

# Parameters for tuning
param_map_if = {"contamination": ["auto", 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.2],
                "n_estimators": [80, 90, 100, 110, 120]}
param_map_svm = {"kernel": ["rbf"], "nu": [0.001, 0.01, 0.025, 0.05, 0.1],
                 "gamma": ["auto"], "tol": [1e-3, 1e-4], "coef0": [0.0, 0.1, 0.2]}
param_map_autoencoder = {
    "hidden_neurons": [[200], [200, 100, 200], [200, 100, 50, 100, 200], [100], [100, 50, 100], [100, 50, 25, 50, 100]]
    , "epochs": [25, 50, 100, 125], "contamination": [ 0.005, 0.01, 0.025, 0.05, 0.1, 0.2], "verbose": [0]}
param_map_vae = {"encoder_neurons": [[200, 100, 50], [300, 200, 100], [300, 100, 50], [200, 150, 75]]
   , "epochs": [75, 87, 100], "latent_dim": [4, 2],
                 "contamination": [0.005, 0.01, 0.025, 0.05, 0.1, 0.2], "gamma": [1.0], "verbose": [0]}
param_map_knn = {"contamination": [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.2], "metric": ["manhattan", "euclidean"],
                 "n_neighbors": [1, 3, 5, 10, 15], "method": ["largest", "mean", "median"]}
param_map_mcd = {"contamination": [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.2]}
param_map_hbos = {"n_bins": [5,10,15], "alpha": [0.1, 0.15, 0.2], "tol": [0.45, 0.5, 0.55], "contamination": [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.2]}
param_maps = {"IsolationForest": param_map_if, "OneClassSVM": param_map_svm,
              "Autoencoder": param_map_autoencoder, "VAE": param_map_vae,
              "KNN": param_map_knn,
              "MCD": param_map_mcd,
              "HBOS": param_map_hbos}

# Reward parameters for the scoring profiles used
reward_low_fn_profile = {"a_tp": 1.0, "a_fn": -2.0,  "a_fp": 0.11, "a_tn": 1.0}
reward_low_fp_profile = {"a_tp": 1.0, "a_fn": -1.0, "a_fp": 0.22, "a_tn": 1.0}
reward_standard_profile = {"a_tp": 1.0, "a_fn": -1.0, "a_fp": 0.11, "a_tn": 1.0}
