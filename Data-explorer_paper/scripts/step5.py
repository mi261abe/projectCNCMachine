#Step5
print("Performing test")

from sklearn.preprocessing import MaxAbsScaler

Xs_tr = np.concatenate((Xs_tr, Xs_val))
ts_tr = np.concatenate((ts_tr, ts_val))
types_tr = np.concatenate((types_tr, types_val))

used_for_training = remove_near_labels(ts_tr, labels, CLEANING_WINDOW_SIZE)
Xs_tr = Xs_tr[used_for_training]
types_tr = types_tr[used_for_training]

max_abs_sc = MaxAbsScaler()
Xs_tr = max_abs_sc.fit_transform(Xs_tr)
Xs_test = max_abs_sc.transform(Xs_test)

from collections import defaultdict

Xs_tr_by_type = defaultdict(list)
for i in range(len(types_tr)):
    Xs_tr_by_type[types_tr[i][1]].append(Xs_tr[i])

Xs_test_by_type = defaultdict(list)
for i in range(len(Xs_test)):
    Xs_test_by_type[types_test[i][1]].append(i)

test_label_index = index_labels(ts_test, labels, SCORE_WINDOW_SIZE)

labels_in_test_period = get_labels_in_period(ts_test, labels)

anomalies_by_method = {}
for method in methods.keys():
    print("Performing test with %s" % method)
    constructor = methods[method]
    params = best_params_map[method]
    print("Using parameters %s" % str(params))

    param_name = ""
    for key in params:
        param_name += key + "-" + str(params[key]) + "_"
    param_name = param_name.replace(".", ",")

    model_all, model_by_type = fit_models(Xs_tr, Xs_tr_by_type, params, constructor, method)

    anomalies, temp = perform_anomaly_detection(Xs_test, types_test, ts_test, Xs_test_by_type, model_all, model_by_type,
                                                SAVE_RAW)
    if SAVE_RAW:
        os.makedirs(os.path.join(base_results_location, "test_results",   method + "_" + str(SCORE_WINDOW_SIZE)), exist_ok=True)
        pd.DataFrame(temp).to_excel(os.path.join(base_results_location, "test_results", method + "_" + str(
            SCORE_WINDOW_SIZE),  method + "_" + param_name + ".xls"))

    anomalies_by_method[method] = anomalies

    std_score, recall, precision = score(anomalies, test_label_index, labels_in_test_period, reward_standard_profile,
                                         SCORE_WINDOW_SIZE)
    low_fp_score, _, _ = score(anomalies, test_label_index, labels_in_test_period, reward_low_fp_profile,
                               SCORE_WINDOW_SIZE)
    low_fn_score, _, _ = score(anomalies, test_label_index, labels_in_test_period, reward_low_fn_profile,
                               SCORE_WINDOW_SIZE)

    print("%s Std Score: %f, Low FP: %f, Low FN: %s, Recall: %s, Precision: %s" % (
        method, std_score, low_fp_score, low_fn_score, recall, precision))
    os.makedirs(os.path.join(base_results_location, "test_results",  method + "_" + str(SCORE_WINDOW_SIZE)), exist_ok=True)
    f = open(os.path.join(base_results_location, "test_results", method + "_" + str(SCORE_WINDOW_SIZE), method + ".txt"), "w")
    f.write("Std Score: %f, Low FP: %f, Low FN: %s, Recall: %s, Precision: %s" % (
        std_score, low_fp_score, low_fn_score, recall, precision))
    f.close()
    clear_tensorflow_session()

from matplotlib import pyplot as plt
import pickle

pickle_file = open(os.path.join(base_results_location, "test_results", "anomalies_by_method_" + str(SCORE_WINDOW_SIZE) + ".pkl"), "wb")
pickle.dump(anomalies_by_method, pickle_file)
pickle_file.close()


def visualize_anomaly_detection(anomalies_by_method, defects, rule="30T"):
    severe_defects = defects[defects.group == 1]
    severe_defects["Group 1 Defects"] = 1
    severe_defects = severe_defects["Group 1 Defects"].resample(rule=rule, base=0).sum().rename("Group 1 Defects")
    standard_defects = defects[defects.group == 2]
    standard_defects["Group 2 Defects"] = 1
    standard_defects = standard_defects["Group 2 Defects"].resample(rule=rule, base=0).sum().rename("Group 2 Defects")

    f, axes = plt.subplots(len(anomalies_by_method.keys()) + 1, 1, sharey='all')

    methods = list(anomalies_by_method.keys())
    for i in range(len(methods)):
        method = methods[i]
        anomalies_df = pd.DataFrame(anomalies_by_method[method])
        anomalies_df["Value"] = 1
        anomalies_df.set_index(0, inplace=True)
        if len(anomalies) > 0:
            anomalies_df.resample(rule=rule, base=0).sum()["Value"].rename("Anomalies with " + method).plot(ax=axes[i],
                                                                                                            legend=True)
        else:
            anomalies_df["Value"].rename("Anomalies with " + method).plot(ax=axes[i], legend=True)
        axes[i].set_xlabel("date")
        axes[i].set_ylabel("count")

    severe_defects.plot(ax=axes[-1], legend=True)
    standard_defects.plot(ax=axes[-1], legend=True)
    axes[-1].set_xlabel("date")
    axes[-1].set_ylabel("count")


#visualize_anomaly_detection(anomalies_by_method, labels_in_test_period)
