#Step 3 Prepare Data
print("Preparing data")
def transform_aggregate(Xs_raw, types_raw):
    transformer = PiecewiseAggregateApproximation(window_size=None, output_size=100)
    xs_transformed = []
    types = []
    timestamps = []
    for i in range(len(Xs_raw)):
        df = Xs_raw[i]
        if len(df.index) > 100:
            values = np.transpose(df.to_numpy())
            if len(values.shape) == 1:
                values = values.reshape(1, -1)
            xs_transformed.append(transformer.transform(values).transpose().reshape(1, -1)[0])
            timestamps.append(df.index.values[0])
            types.append(types_raw[i])
    return xs_transformed, timestamps, types


print("Approximate time series")
print("Aggreate Spindle")
Xs_spindle, timestamps_spindle, types_spindle = transform_aggregate(Xs_spindle, types_spindle)
print("Aggreate Servo")
Xs_servometer, timestamps_servometer, types_servometer = transform_aggregate(Xs_servometer, types_servometer)
print("Aggreate Spindlemeter")
Xs_spindlemeter, timestamps_spindlemeter, types_spindlemeter = transform_aggregate(Xs_spindlemeter, types_spindlemeter)
print("Joining Features")


def join_measurements(ts_sp, ts_sm, ts_servo, types_sp, types_sm, types_servo):
    indices_sp = []
    indices_sm = []
    indices_serv = []
    for i in range(len(ts_sp)):

        ts = ts_sp[i]

        index_sm = find_index_with_same_timestamp(ts, i, ts_sm)
        index_serv = find_index_with_same_timestamp(ts, i, ts_servo)

        if index_sm is not None and index_serv is not None:
            all_same_type = types_sp[i][1] == types_sm[index_sm][1]
            all_same_type &= types_sp[i][1] == types_servo[index_serv][1]

            if not all_same_type:
                print("Type miss match at %s" % types_sp[i][0])
            else:
                indices_sp.append(i)
                indices_sm.append(index_sm)
                indices_serv.append(index_serv)

    return indices_sp, indices_sm, indices_serv


indices_sp, indices_sm, indices_serv = join_measurements(timestamps_spindle, timestamps_spindlemeter,
                                                         timestamps_servometer, types_spindle, types_spindlemeter,
                                                         types_servometer)

print("Data:")
print((len(indices_sp), len(indices_sm), len(indices_serv)))

assert len(indices_sp) == len(indices_sm) and len(indices_sp) == len(indices_serv)

Xs_spindle = np.array(Xs_spindle)[indices_sp]
Xs_servometer = np.array(Xs_servometer)[indices_serv]
Xs_spindlemeter = np.array(Xs_spindlemeter)[indices_sm]

timestamps = np.array(timestamps_spindle)[indices_sp]

types = np.array(types_spindle)[indices_sp]

Xs = np.concatenate((Xs_spindle, Xs_spindlemeter), axis=1)
Xs = np.concatenate((Xs, Xs_servometer), axis=1)

Xs_sp, Xs_sv, Xs_sm = None, None, None
timestamps_sp, timestamps_sv,timestamps_sm = None, None, None
types_sp, types_sv, types_sm = None, None, None
print("Split dataset into three parts")


def split(Xs, timestamps, types):
    Xs_tr = np.array(Xs[: int(len(Xs) * 0.5)])
    ts_tr = timestamps[: int(len(Xs) * 0.5)]
    types_tr = types[: int(len(Xs) * 0.5)]

    Xs_val = np.array(Xs[int(len(Xs) * 0.5): int(len(Xs) * 0.75)])
    ts_val = timestamps[int(len(Xs) * 0.5): int(len(Xs) * 0.75)]
    types_val = types[int(len(Xs) * 0.5): int(len(Xs) * 0.75)]

    Xs_test = np.array(Xs[int(len(Xs) * 0.75):])
    ts_test = timestamps[int(len(Xs) * 0.75):]
    types_test = types[int(len(Xs) * 0.75):]
    return Xs_tr, ts_tr, types_tr, Xs_val, ts_val, types_val, Xs_test, ts_test, types_test


Xs_tr, ts_tr, types_tr, Xs_val, ts_val, types_val, Xs_test, ts_test, types_test = split(Xs, timestamps, types)
print("Dataset prepared")
