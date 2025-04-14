# Step 2: Read the data
# load labels
print("Loading ground truth")
labels = pd.read_excel(os.path.join(base_data_location, "Events.xlsx"), index_col=1, parse_dates=True)
labels.sort_index(inplace=True)
labels['end'] = pd.to_datetime(labels['end'])
labels['start'] = pd.to_datetime(labels['start'])
labels = labels[labels.group < 3]


def diff_in_seconds(one, other):
    return abs((one - other) / np.timedelta64(1, 's'))


def find_index_with_same_timestamp(target_ts, target_index, tss):
    other_at_point = tss[target_index]
    seconds = diff_in_seconds(target_ts, other_at_point)
    if seconds > 10:
        print("Deviation of ts at index: " + str(target_index))
        end_j = target_index + 15 if target_index + 15 < len(tss) else len(tss)
        start_j = target_index - 15 if target_index - 15 > 0 else 0
        for j in range(start_j, end_j):
            if diff_in_seconds(target_ts, tss[j]) <= 10:
                return j
    else:
        return target_index
    return None


def read_h5_file(file_name):
    s = pd.HDFStore(file_name)
    all = []
    types = []
    ctr = 0
    for path, grps, leaves in s.walk("/"):
        if len(leaves) > 0:
            for leaf in leaves:
                df = s[path + "/" + leaf]
                types.append((df.index.values[0], path.split("/")[2]))
                ctr += 1
                all.append(df)
    s.close()
    return all, types

print("Loading measurement data")
Xs_spindle, types_spindle = read_h5_file(os.path.join(base_data_location, 'spindle.h5'))
Xs_spindlemeter, types_spindlemeter = read_h5_file(os.path.join(base_data_location, "spindlemeter.h5"))
Xs_servometer, types_servometer = read_h5_file(os.path.join(base_data_location, "servometer.h5"))

list.sort(Xs_spindle, key=lambda x: x.index.values[0])
list.sort(Xs_servometer, key=lambda x: x.index.values[0])
list.sort(Xs_spindlemeter, key=lambda x: x.index.values[0])

list.sort(types_spindle, key=lambda x: x[0])
list.sort(types_servometer, key=lambda x: x[0])
list.sort(types_spindlemeter, key=lambda x: x[0])