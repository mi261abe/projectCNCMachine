# Step 4 Perform Parameter Tuning
print("Prepare parameter tuning")

def remove_near_labels(timestamps, labels, window_size=4 * 60 * 60):
    labels.sort_index(inplace=True)
    labels = labels[labels.group < 3]
    label_timestamps = labels["end"]
    selected_indices = []
    for i in range(len(timestamps)):
        timestamp = timestamps[i]
        timestamp = np.datetime64(timestamp)
        nearest_index = np.argmin(np.abs(labels.index - timestamp))
        while nearest_index < len(label_timestamps) and timestamp > label_timestamps[nearest_index]:
            nearest_index += 1

        if nearest_index >= len(label_timestamps) or timestamp > label_timestamps[nearest_index]:
            selected_indices.append(i)
        else:
            difference = label_timestamps[nearest_index] - timestamp
            diff = difference / np.timedelta64(1, 's')
            if diff > window_size:
                selected_indices.append(i)
    return selected_indices


def index_labels(timestamps, labels, window_size=4 * 60 * 60):
    labels.sort_index(inplace=True)
    timestamp_label_index = defaultdict(list)
    labels_ts = labels["end"]
    for i in range(len(timestamps)):
        for j in range(len(labels_ts) - 1, -1, -1):
            timestamp_label = labels_ts[j]
            timestamp_measurement = timestamps[i]
            difference = timestamp_label - timestamp_measurement
            diff = difference / np.timedelta64(1, 's')

            if timestamp_label >= timestamp_measurement and diff < window_size:
                timestamp_label_index[timestamp_measurement].append(timestamp_label)

            elif timestamp_label < timestamp_measurement:
                if len(timestamp_label_index[timestamp_measurement]) == 0:
                    timestamp_label_index[timestamp_measurement].append(timestamp_label)
                assert len(timestamp_label_index[timestamp_measurement]) > 0
                break
        assert len(timestamp_label_index[timestamps[i]]) > 0
    return timestamp_label_index

used_for_training = remove_near_labels(ts_tr, labels, CLEANING_WINDOW_SIZE)

Xs_tr_cleaned = Xs_tr[used_for_training]
types_tr_cleaned = types_tr[used_for_training]

from sklearn.preprocessing import MaxAbsScaler

max_abs_sc = MaxAbsScaler()
Xs_tr_cleaned = max_abs_sc.fit_transform(Xs_tr_cleaned)
Xs_val_scaled = max_abs_sc.transform(Xs_val)

print("Shape: " + str(Xs_tr_cleaned.shape))
from collections import defaultdict

Xs_tr_by_type = defaultdict(list)
for i in range(len(types_tr_cleaned)):
    Xs_tr_by_type[types_tr_cleaned[i][1]].append(Xs_tr_cleaned[i])

measurement_label_index = index_labels(ts_val, labels, SCORE_WINDOW_SIZE)

Xs_val_by_type = defaultdict(list)
for i in range(len(Xs_val_scaled)):
    Xs_val_by_type[types_val[i][1]].append(i)


def calculate_sigmodial_scoring(relative_position):
    if relative_position >= 3.0:
        val = 0.0
    else:
        val = 2 * (1 / (1 + exp(5 * relative_position)))
    return val - 1.0


def score(detections, measurement_label_index, labels_in_period, profile, window_size=4 * 60 * 60):
    tp_values = {}
    fp_value = 0
    with_detection = set()
    for detection_timestamp in detections:
        next_labels = measurement_label_index[detection_timestamp]

        assert len(measurement_label_index[detection_timestamp]) > 0
        for label in next_labels:
            if label > detection_timestamp:
                with_detection.add(detection_timestamp)
                relative_position = ((detection_timestamp - label) / np.timedelta64(1, 's')) / window_size
                score_value = profile["a_tp"] * calculate_sigmodial_scoring(relative_position)
                if label not in tp_values or tp_values[label] < score_value:
                    tp_values[label] = score_value
            else:
                relative_position = ((detection_timestamp - label) / np.timedelta64(1, 's')) / window_size
                fp_value += profile["a_fp"] * calculate_sigmodial_scoring(relative_position)

    missed_windows = 0
    tp_value = 0
    for index in labels_in_period.end:
        if index in tp_values:
            tp_value += tp_values[index]
        else:
            missed_windows += 1
    unnormalized_score = tp_value + fp_value + profile["a_fn"] * missed_windows
    s_null = profile["a_fn"] * len(labels_in_period)
    s_perfect = (calculate_sigmodial_scoring(-1.0) * profile["a_tp"]) * len(labels_in_period)

    recall = (len(labels_in_period) - missed_windows) / len(labels_in_period)
    if len(detections) == 0:
        precision = 0
    else:
        precision = len(with_detection) / len(detections)

    return 100 * (unnormalized_score - s_null) / (s_perfect - s_null), recall, precision


def get_labels_in_period(ts, labels):
    start_validation_period = pd.Timestamp(min(ts))
    end_validation_period = pd.Timestamp(max(ts))
    print(str(start_validation_period))
    print(str(end_validation_period))
    in_period = labels[
        (labels.start >= start_validation_period) & (labels.start <= end_validation_period)]
    last_before = labels[labels.start < start_validation_period]["start"].argmax()
    in_period = in_period.append(labels.iloc[last_before])
    first_after = labels[labels.start > end_validation_period]["start"].argmin()
    in_period = in_period.append(
        labels[labels.start > end_validation_period].iloc[first_after])
    return in_period


def clear_tensorflow_session():
    import pkg_resources
    missing = {'tensorflow'} - {pkg.key for pkg in pkg_resources.working_set}
    if not missing:
        from tensorflow import keras as keras
        import os, psutil
        import gc
        print(psutil.Process(os.getpid()).memory_info().rss)
        keras.backend.clear_session()
        gc.collect()
        print("cleared session")
        print(psutil.Process(os.getpid()).memory_info().rss)


labels_in_validation_period = get_labels_in_period(ts_val, labels)
print("Prepared parameter tuning")

print("Starting parameter tuning")

best_params_map = {}

def fit_models(Xs, Xs_by_type, params, constructor, method):
    if method == "VAE":
        params["decoder_neurons"] = params["encoder_neurons"][::-1]
    model_all = constructor(params)
    model_all.fit(Xs)

    assert len(Xs) == sum([len(Xs_by_type[x]) for x in Xs_by_type.keys()])

    model_by_type = {}
    for type in Xs_by_type.keys():
        Xs_of_type = Xs_by_type[type]
        try:
            model_by_type[type] = constructor(params).fit(Xs_of_type)
        except Exception as e:
            if isinstance(model_all, KNN):
                n_samples = len(Xs_of_type) - 1
                params_c = params.copy()
                params_c["n_neighbors"] = n_samples
                model_by_type[type] = constructor(params_c).fit(Xs_of_type)
            else:
                raise e
    return model_all, model_by_type


def perform_anomaly_detection(Xs, types, timestamps, Xs_by_type, model_all, model_by_type, save_raw):
    temp = []
    anomalies = []

    assert len(Xs) == len(types)
    assert len(types) == len(timestamps)
    assert len(Xs) == sum([len(Xs_by_type[x]) for x in Xs_by_type.keys()])

    y_all = model_all.predict(Xs)

    y_type = np.zeros(len(Xs))

    for key in Xs_by_type.keys():
        if key in model_by_type:
            y_type[Xs_by_type[key]] = model_by_type[key].predict(Xs[Xs_by_type[key]])
        else:
            y_type[Xs_by_type[key]] = None

    for i in range(len(Xs)):

        if isinstance(model_all, (BaseDetector)):
            if y_all[i] > 0 and ((not np.isnan(y_type[i])) and y_type[i] > 0):
                anomalies.append(timestamps[i])
        else:
            if y_all[i] < 1 and ((not np.isnan(y_type[i])) and y_type[i] < 1):
                anomalies.append(timestamps[i])

        if save_raw:
            temp.append([i, types[i][1], timestamps[i], y_all[i], y_type[i]])

    return anomalies, temp


for method in methods.keys():
    print("Performing parameter tuning for %s" % method)
    constructor = methods[method]
    param_map = param_maps[method]
    parameters = list(ParameterSampler(param_map, n_iter=N_RAND_TUNING_ITER, random_state=RANDOM_STATE))
    best_score = -sys.float_info.max
    best_params = None
    ctr = 1
    for params in parameters:
        print("Iteration %s/%s" % (ctr, len(parameters)))
        ctr += 1
        param_name = ""
        for key in params:
            param_name += key + "-" + str(params[key]) + "_"
        param_name = param_name.replace(".", ",")
        print(param_name)

        model_all, model_by_type = fit_models(Xs_tr_cleaned, Xs_tr_by_type, params, constructor, method)

        anomalies, temp = perform_anomaly_detection(Xs_val_scaled, types_val, ts_val, Xs_val_by_type, model_all,
                                                    model_by_type, SAVE_RAW)
        if SAVE_RAW:
            os.makedirs(os.path.join(base_results_location, "val_results", method + "_" + str(SCORE_WINDOW_SIZE)), exist_ok=True)
            pd.DataFrame(temp).to_excel(os.path.join(base_results_location, "val_results", method + "_" + str(
                SCORE_WINDOW_SIZE), method + "_" + param_name + ".xls"))

        param_score, _, _ = score(anomalies, measurement_label_index, labels_in_validation_period,
                                  reward_standard_profile, SCORE_WINDOW_SIZE)
        print("Score: " + str(param_score))
        if param_score > best_score:
            best_params = params
            best_score = param_score

        clear_tensorflow_session()

    best_params_map[method] = best_params
    print("Best parameters for %s with score %f: %s" % (method, best_score, best_params))

f = open(os.path.join(base_results_location, "val_results", "best_params_" + str(SCORE_WINDOW_SIZE) + ".txt"), "w")
f.write(str(best_params_map))
f.close()
print("Performed parameter tuning")
