import matplotlib.pyplot as plt
import pandas as pd
import random
import os

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
                if ctr > 1500:
                    s.close()
                    return all, types
    s.close()
    return all, types

print('execute initial script now')
print('read sample data')
base_data_location = r"..\..\data"
Xs_spindle, types_spindle = read_h5_file(os.path.join(base_data_location, 'spindle.h5'))
Xs_spindlemeter, types_spindlemeter = read_h5_file(os.path.join(base_data_location, "spindlemeter.h5"))
Xs_servometer, types_servometer = read_h5_file(os.path.join(base_data_location, "servometer.h5"))

list.sort(types_spindle, key=lambda x: x[0])
list.sort(Xs_spindle, key=lambda x: x.index.values[0])
list.sort(types_spindlemeter, key=lambda x: x[0])
list.sort(Xs_spindlemeter, key=lambda x: x.index.values[0])
list.sort(types_servometer, key=lambda x: x[0])
list.sort(Xs_servometer, key=lambda x: x.index.values[0])


print("visualize sample data")
fig, ((ax1, ax2, ax3), (ax4, ax5, ax6), (ax7, ax8, ax9)) = plt.subplots(nrows=3, ncols=3)
fig.suptitle("Example Time Series")

print(types_spindlemeter[0])
print(types_servometer[0])
to_show = set()
types = set()
while len(to_show) < 3:
    idx = random.randint(0, len(Xs_spindle) - 1)
    if types_spindle[idx][1] == types_spindlemeter[idx][1] and types_servometer[idx][1] == types_spindle[idx][1] and \
        types_spindle[idx][0].astype('datetime64[s]') == types_spindlemeter[idx][0].astype('datetime64[s]') and types_servometer[idx][0].astype('datetime64[s]') == types_spindle[idx][0].astype('datetime64[s]'):

        idx = random.randint(0, len(Xs_spindle) - 1)

        if len(to_show) == 2 and len(types) < 2 and types_spindle[idx][1] in types:
            continue

        to_show.add(idx)
        types.add(types_spindle[idx][1])


idx_one = to_show.pop()
date_and_type_one = types_spindle[idx_one]
ax1.set_ylabel(f"Type {date_and_type_one[1]} at {date_and_type_one[0].astype('datetime64[s]')}", rotation=0, size='large')
Xs_spindle[idx_one].plot(ax=ax1)
Xs_spindlemeter[idx_one].plot(ax=ax2)
Xs_servometer[idx_one].plot(ax=ax3)

idx_two = to_show.pop()
date_and_type_two = types_spindle[idx_two]
ax4.set_ylabel(f"Type {date_and_type_one[1]} at {date_and_type_two[0].astype('datetime64[s]')}", rotation=0, size='large')
Xs_spindle[idx_two].plot(ax=ax4)
Xs_spindlemeter[idx_two].plot(ax=ax5)
Xs_servometer[idx_two].plot(ax=ax6)

idx_three = to_show.pop()
date_and_type_three = types_spindle[idx_three]
ax7.set_ylabel(f"Type {date_and_type_one[1]} at {date_and_type_three[0].astype('datetime64[s]')}", rotation=0, size='large')
Xs_spindle[idx_three].plot(ax=ax7)
Xs_spindlemeter[idx_three].plot(ax=ax8)
Xs_servometer[idx_three].plot(ax=ax9)
print('finished initial script')