#!/usr/bin/python3

import sys
import math
import numpy as np
import matplotlib.pyplot as plt

flight_data = []
time_data = []

# Get some data: if no argument is given, make some
if len(sys.argv) == 1:
    flight_data = [0] * 1000
    time_data = [i/40 for i in range(1000)]
    pass
# if we do get data, parse it
else:
    with open(sys.argv[1], "r") as csvfile:
        headers = csvfile.readline().split(",")
        baro_col = headers.index("baro_altitude")
        time_col = headers.index("time")
        for line in csvfile:
            flight_data.append(float(line.split(",")[baro_col]))
            time_data.append(float(line.split(",")[time_col]))

fd_with_start = np.asarray(flight_data)
td_with_start = np.asarray(time_data)

timesteps = td_with_start[1:] - td_with_start[0:-1]

td = td_with_start[1:]
fd = fd_with_start[1:]

# We can assume our timestep is reasonably constant; to avoid outliers at the
# start/end of data skewing our results too much, we set timestep = geometric
# mean of dataset timesteps:
def geomean(a: np.ndarray) -> float:
    return np.exp(sum(np.log(a)) / a.size)
ts = geomean(timesteps)

# We care about everything up to acceleration, so define our state vector as
# x_k = [x, x', x'']
# This gives us a state-transition model of:
F_full = np.asarray([[1,    ts,   1/2*ts**2],
                     [0,    1,    ts],
                     [0,    0,    1]])

# Assume our acceleration changes randomly with some standard deviation in m/s**3
sigsq_a = 20 ** 2
G = np.asarray([[1/6*ts**3],
                   [1/2*ts**2],
                   [ts]])
# This gives our input noise covariance Q:
Q = G * G.T * sigsq_a

# We measure only position, with some other standard deviation:
sigsq_z = 5 ** 2
H = np.asarray([[1, 0, 0]])
R = np.asarray([[sigsq_z]])

# Initial state is all zeroes, with perfect certainty:
x_nn = np.zeros((3, 1))
P_nn = np.zeros((3, 3))

alt_matrix = []

for zk in fd:
    # Prediction step
    x_npred = F_full @ x_nn
    P_npred = F_full @ P_nn @ F_full.T + Q
    # Update step
    y_n = zk - H @ x_npred
    S_n = H @ P_npred @ H.T + R

    K_n = P_npred @ H.T @ np.linalg.inv(S_n)
    x_nn = x_npred + K_n @ y_n
    P_nn = (np.eye(3) - K_n @ H) @ P_npred

    alt_matrix.append(x_nn[0])

# We'll use our matrix results as our ground-truth value for future calcs.

# We can preempt a lot of annoying mess by assuming that 1/2*ts**2 is never going
# to actually matter:
F = np.asarray([[1,    ts,   0],
                [0,    1,    ts],
                [0,    0,    1]])

x_nn = np.zeros((3, 1))
P_nn = np.zeros((3, 3))
alt_matrix_nosq = []

for zk in fd:
    # Prediction step
    x_npred = F @ x_nn
    P_npred = F @ P_nn @ F.T + Q

    # Update step
    y_n = zk - H @ x_npred
    S_n = H @ P_npred @ H.T + R

    K_n = P_npred @ H.T @ np.linalg.inv(S_n)
    x_nn = x_npred + K_n @ y_n
    P_nn = (np.eye(3) - K_n @ H) @ P_npred

    alt_matrix_nosq.append(x_nn[0])

# We can check how much error this introduces:
diffs = np.asarray(alt_matrix_nosq) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by ignoring ts**2: RMS", rmse, "m, max", maxe, "m")

# This works, but it's a lot of matrix operations. Luckily most of these values
# are fixed at compile-time if we already know our timestep.

x_nn = np.zeros((3, 1))
P_nn = np.zeros((3, 3))
alt_matrix_expand1 = []

for zk in fd:
    # Expand out this matrix multiply:
    x_npred = np.asarray([[x_nn[1][0] * ts + x_nn[0][0]],
                             [x_nn[2][0] * ts + x_nn[1][0]],
                             [x_nn[2][0]]])
    x_npred = F @ x_nn
    # As well as this one, although it's going to get pretty big:
    P_npred = np.asarray([
        [
            P_nn[1][1] * ts**2 + (P_nn[0][1] + P_nn[1][0]) * ts + P_nn[0][0],
            P_nn[1][2] * ts**2 + (P_nn[0][2] + P_nn[1][1]) * ts + P_nn[0][1],
            P_nn[1][2] * ts + P_nn[0][2]
        ],
        [
            P_nn[2][1] * ts**2 + (P_nn[1][1] + P_nn[2][0]) * ts + P_nn[1][0],
            P_nn[2][2] * ts**2 + (P_nn[1][2] + P_nn[2][1]) * ts + P_nn[1][1],
            P_nn[2][2] * ts + P_nn[1][2]
        ],
        [
            P_nn[2][1] * ts + P_nn[2][0],
            P_nn[2][2] * ts + P_nn[2][1],
            P_nn[2][2]
        ]
    ]) + Q

    # Update step
    y_n = zk - H @ x_npred
    S_n = H @ P_npred @ H.T + R

    K_n = P_npred @ H.T @ np.linalg.inv(S_n)
    x_nn = x_npred + K_n @ y_n
    P_nn = (np.eye(3) - K_n @ H) @ P_npred

    alt_matrix_expand1.append(x_nn[0])

diffs = np.asarray(alt_matrix_expand1) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by expanding matrices pt1: RMS", rmse, "m, max", maxe, "m")

# Continue expanding out the matrix multiplications:

x_nn = np.zeros((3, 1))
P_nn = np.zeros((3, 3))
alt_matrix_expand2 = []

for zk in fd:
    # Expand out this matrix multiply:
    x_npred = np.asarray([[x_nn[1][0] * ts + x_nn[0][0]],
                             [x_nn[2][0] * ts + x_nn[1][0]],
                             [x_nn[2][0]]])
    x_npred = F @ x_nn
    # As well as this one, although it's going to get pretty big - also expand Q:
    P_npred = np.asarray([
        [
            P_nn[1][1] * ts**2 + (P_nn[0][1] + P_nn[1][0]) * ts + P_nn[0][0] + (sigsq_a * ts**6)/36,
            P_nn[1][2] * ts**2 + (P_nn[0][2] + P_nn[1][1]) * ts + P_nn[0][1] + (sigsq_a * ts**5)/12,
            P_nn[1][2] * ts + P_nn[0][2] + (sigsq_a * ts**4)/6
        ],
        [
            P_nn[2][1] * ts**2 + (P_nn[1][1] + P_nn[2][0]) * ts + P_nn[1][0] + (sigsq_a * ts**5)/12,
            P_nn[2][2] * ts**2 + (P_nn[1][2] + P_nn[2][1]) * ts + P_nn[1][1] + (sigsq_a * ts**4)/4,
            P_nn[2][2] * ts + P_nn[1][2] + (sigsq_a * ts**3)/2
        ],
        [
            P_nn[2][1] * ts + P_nn[2][0] + (sigsq_a * ts**4)/6,
            P_nn[2][2] * ts + P_nn[2][1] + (sigsq_a * ts**3)/2,
            P_nn[2][2] + (sigsq_a * ts**2)
        ]
    ])

    # Update step
    y_n = np.asarray([[zk - x_nn[1][0] * ts - x_nn[0][0]]])
    S_n = np.asarray([[P_nn[1][1] * ts**2
                    + (P_nn[0][1] + P_nn[1][0]) * ts
                    + P_nn[0][0] + sigsq_a*ts**6/36 + sigsq_z]])
    K_n = P_npred @ H.T @ np.linalg.inv(S_n)
    x_nn = x_npred + K_n @ y_n
    P_nn = (np.eye(3) - K_n @ H) @ P_npred

    alt_matrix_expand2.append(x_nn[0])

diffs = np.asarray(alt_matrix_expand2) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by expanding matrices pt2: RMS", rmse, "m, max", maxe, "m")

# Alright, things are starting to get a little ugly. It will behoove us to try
# to keep cutting out high powers of ts, as these will effectively round to 0
# when we actually do the math. Let's ignore all powers over 2 and see how
# that goes.

x_nn = np.zeros((3, 1))
P_nn = np.zeros((3, 3))
alt_matrix_trim1 = []

for zk in fd:
    # Expand out this matrix multiply:
    x_npred = np.asarray([[x_nn[1][0] * ts + x_nn[0][0]],
                             [x_nn[2][0] * ts + x_nn[1][0]],
                             [x_nn[2][0]]])
    x_npred = F @ x_nn
    # As well as this one, although it's going to get pretty big - also expand
    # Q:
    P_npred = np.asarray([
        [
            P_nn[1][1] * ts**2 + (P_nn[0][1] + P_nn[1][0]) * ts + P_nn[0][0],
            P_nn[1][2] * ts**2 + (P_nn[0][2] + P_nn[1][1]) * ts + P_nn[0][1],
            P_nn[1][2] * ts + P_nn[0][2]
        ],
        [
            P_nn[2][1] * ts**2 + (P_nn[1][1] + P_nn[2][0]) * ts + P_nn[1][0],
            P_nn[2][2] * ts**2 + (P_nn[1][2] + P_nn[2][1]) * ts + P_nn[1][1],
            P_nn[2][2] * ts + P_nn[1][2]
        ],
        [
            P_nn[2][1] * ts + P_nn[2][0],
            P_nn[2][2] * ts + P_nn[2][1],
            P_nn[2][2] + (sigsq_a * ts**2)
        ]
    ])

    # Update step
    y_n = np.asarray([[zk - x_nn[1][0] * ts - x_nn[0][0]]])
    S_n = np.asarray([[P_nn[1][1] * ts**2
                    + (P_nn[0][1] + P_nn[1][0]) * ts
                    + P_nn[0][0] + sigsq_z]])
    K_n = P_npred @ H.T @ np.linalg.inv(S_n)
    x_nn = x_npred + K_n @ y_n
    P_nn = (np.eye(3) - K_n @ H) @ P_npred

    alt_matrix_trim1.append(x_nn[0])

diffs = np.asarray(alt_matrix_trim1) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by trim pt1: RMS", rmse, "m, max", maxe, "m")

# In my testing, the error on this isn't too bad. The worst of it is an
# additional bit of lag when the acceleration is changing rapidly at launch,
# about the same magnitude as we saw from ditching the acceleration term
# originally; this makes sense, since we're effectively telling the system to
# underestimate its measurement error on short timescales.

# We soldier on - we can fold K_n into our calculations of X_nn and P_nn, and in
# fact the whole prediction step goes away, replaced with a bigger mess:

x_nn = np.zeros((3, 1))
P_nn = np.zeros((3, 3))
alt_matrix_expand3 = []

for zk in fd:
    # Note we have a common denominator in a lot of places in these equations:
    invdenom = 1 / (P_nn[1][1]*ts**2 + (P_nn[0][1] + P_nn[1][0])*ts + P_nn[0][0] + sigsq_z)
    x_nn = np.asarray([
        [(P_nn[1][1]*ts**2*zk + ((P_nn[0][1] + P_nn[1][0])*zk + sigsq_z*x_nn[1][0])*ts + sigsq_z*x_nn[0][0] + P_nn[0][0]*zk) * invdenom],
        [ts*x_nn[2][0] + x_nn[1][0] - (P_nn[2][1]*ts**2 + (P_nn[1][1] + P_nn[2][0])*ts + P_nn[1][0])*(ts*x_nn[1][0] + x_nn[0][0] - zk) * invdenom],
        [x_nn[2][0] - (P_nn[2][1]*ts + P_nn[2][0])*(ts*x_nn[1][0] + x_nn[0][0] - zk) * invdenom]
    ])
    P_nn = np.asarray([
        [
            sigsq_z*(P_nn[1][1]*ts**2 + (P_nn[0][1] + P_nn[1][0])*ts + P_nn[0][0]) * invdenom,
            sigsq_z*(P_nn[1][2]*ts**2 + (P_nn[0][2] + P_nn[1][1])*ts + P_nn[0][1]) * invdenom,
            sigsq_z*(P_nn[1][2]*ts + P_nn[0][2]) * invdenom
        ],
        [
            sigsq_z*(P_nn[2][1]*ts**2 + (P_nn[1][1] + P_nn[2][0])*ts + P_nn[1][0]) * invdenom,
            -(P_nn[2][1]*ts**2 + (P_nn[1][1] + P_nn[2][0])*ts + P_nn[1][0])*(P_nn[1][2]*ts**2 + (P_nn[0][2] + P_nn[1][1])*ts + P_nn[0][1]) * invdenom + P_nn[2][2]*ts**2 + (P_nn[1][2] + P_nn[2][1])*ts + P_nn[1][1],
            -(P_nn[2][1]*ts**2 + (P_nn[1][1] + P_nn[2][0])*ts + P_nn[1][0])*(P_nn[1][2]*ts + P_nn[0][2]) * invdenom
                 + ts*P_nn[2][2] + P_nn[1][2]
        ],
        [
            sigsq_z*(P_nn[2][1]*ts + P_nn[2][0]) * invdenom,
            -(P_nn[2][1]*ts + P_nn[2][0])*(P_nn[1][2]*ts**2 + (P_nn[0][2] + P_nn[1][1])*ts + P_nn[0][1]) * invdenom
                 + ts*P_nn[2][2] + P_nn[2][1],
            -(P_nn[2][1]*ts + P_nn[2][0])*(P_nn[1][2]*ts + P_nn[0][2]) * invdenom
                 + sigsq_a*ts**2 + P_nn[2][2]
        ]
    ])

    alt_matrix_expand3.append(x_nn[0])

diffs = np.asarray(alt_matrix_expand3) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by expanding matrices pt3: RMS", rmse, "m, max", maxe, "m")

# We're starting to see polynomials multiplied together in those middle terms,
# which means we're starting to get timestep^3 and timestep^4 terms again.
# Let's expand those out so we can see how significant the terms are:

x_nn = np.zeros((3, 1))
P_nn = np.zeros((3, 3))
alt_matrix_expand4 = []

for zk in fd:
    # Note we have a common denominator in a lot of places in these equations:
    invdenom = 1 / (P_nn[1][1]*ts**2 + (P_nn[0][1] + P_nn[1][0])*ts + P_nn[0][0] + sigsq_z)
    x_nn = np.asarray([
        [(
            P_nn[1][1]*zk * ts**2
          + (P_nn[0][1]*zk + P_nn[1][0]*zk + sigsq_z*x_nn[1][0]) * ts
          + P_nn[0][0]*zk + sigsq_z*x_nn[0][0]
        ) * invdenom],
        [-(
            P_nn[2][1]*x_nn[1][0] * ts**3
          + (P_nn[1][1]*x_nn[1][0] + P_nn[2][0]*x_nn[1][0] + P_nn[2][1]*x_nn[0][0] - P_nn[2][1]*zk) * ts**2
          + (P_nn[1][0]*x_nn[1][0] + P_nn[1][1]*x_nn[0][0] - P_nn[1][1]*zk + P_nn[2][0]*x_nn[0][0] - P_nn[2][0]*zk) * ts
          + P_nn[1][0]*x_nn[0][0] - P_nn[1][0]*zk
        ) * invdenom + (
            ts*x_nn[2][0] + x_nn[1][0]
        )],
        [-(
            P_nn[2][1]*x_nn[1][0] * ts**2
          + (P_nn[2][0]*x_nn[1][0] + P_nn[2][1]*x_nn[0][0] - P_nn[2][1]*zk) * ts
          + P_nn[2][0]*x_nn[0][0] - P_nn[2][0]*zk
        ) * invdenom + (
            x_nn[2][0]
        )]
    ])
    P_nn = np.asarray([
        [
            sigsq_z * invdenom * (
                (P_nn[1][1]) * ts**2
              + (P_nn[0][1] + P_nn[1][0]) * ts
              + P_nn[0][0]
            ),
            sigsq_z * invdenom * (
                P_nn[1][2] * ts**2
              + (P_nn[0][2] + P_nn[1][1]) * ts
              + P_nn[0][1]
            ),
            sigsq_z * invdenom * (
                P_nn[1][2] * ts
              + P_nn[0][2]
            )
        ],
        [
            sigsq_z * invdenom * (
                P_nn[2][1] * ts**2
              + (P_nn[1][1] + P_nn[2][0]) * ts
              + P_nn[1][0]
            ),
            -(
                (P_nn[2][1] * P_nn[1][2]) * ts**4
              + (P_nn[0][2]*P_nn[2][1] + P_nn[1][1]*P_nn[1][2] + P_nn[1][1]*P_nn[2][1] + P_nn[1][2]*P_nn[2][0]) * ts**3
              + (P_nn[0][1]*P_nn[2][1] + P_nn[0][2]*P_nn[1][1] + P_nn[0][2]*P_nn[2][0] + P_nn[1][0]*P_nn[1][2] + P_nn[1][1]**2 + P_nn[1][1]*P_nn[2][0]) * ts**2
              + (P_nn[0][1]*P_nn[1][1] + P_nn[0][1]*P_nn[2][0] + P_nn[0][2]*P_nn[1][0] + P_nn[1][0]*P_nn[1][1]) * ts
              + (P_nn[0][1]*P_nn[1][0])
            ) * invdenom + (
                P_nn[2][2] * ts**2
              + (P_nn[1][2] + P_nn[2][1]) * ts
              + P_nn[1][1]
            ),
            -(
                P_nn[1][2]*P_nn[2][1] * ts**3
              + (P_nn[0][2]*P_nn[2][1] + P_nn[1][1]*P_nn[1][2] + P_nn[1][2]*P_nn[2][0]) * ts**2
              + (P_nn[0][2]*P_nn[1][1] + P_nn[0][2]*P_nn[2][0] + P_nn[1][0]*P_nn[1][2]) * ts
              + P_nn[0][2]*P_nn[1][0]
            ) * invdenom + (
                ts*P_nn[2][2]
              + P_nn[1][2]
            )    
        ],
        [
            sigsq_z * invdenom * (
                P_nn[2][1]*ts
              + P_nn[2][0]
            ),
            -(
                P_nn[1][2]*P_nn[2][1] * ts**3
              + (P_nn[0][2]*P_nn[2][1] + P_nn[1][1]*P_nn[2][1] + P_nn[1][2]*P_nn[2][0]) * ts**2
              + (P_nn[0][1]*P_nn[2][1] + P_nn[0][2]*P_nn[2][0] + P_nn[1][1]*P_nn[2][0]) * ts
              + P_nn[0][1]*P_nn[2][0]
            ) * invdenom + (
                ts*P_nn[2][2]
              + P_nn[2][1]
            ),
            -(
                P_nn[1][2]*P_nn[2][1] * ts**2
              + (P_nn[0][2]*P_nn[2][1] + P_nn[1][2]*P_nn[2][0]) * ts
              + P_nn[0][2]*P_nn[2][0]
            ) * invdenom + (
                sigsq_a*ts**2
              + P_nn[2][2]
            )
        ]
    ])

    alt_matrix_expand4.append(x_nn[0])

diffs = np.asarray(alt_matrix_expand4) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by expanding matrices pt4: RMS", rmse, "m, max", maxe, "m")

print(P_nn)

# This is way too much math, so let's start cutting things until the numbers look
# bad. Start with everything cubic and up relative to timestep:

x_nn = np.zeros((3, 1))
P_nn = np.zeros((3, 3))
alt_matrix_trim2 = []

for zk in fd:
    # Note we have a common denominator in a lot of places in these equations:
    invdenom = 1 / (P_nn[1][1]*ts**2 + (P_nn[0][1] + P_nn[1][0])*ts + P_nn[0][0] + sigsq_z)
    x_nn = np.asarray([
        [(
            P_nn[1][1]*zk * ts**2
          + (P_nn[0][1]*zk + P_nn[1][0]*zk + sigsq_z*x_nn[1][0]) * ts
          + P_nn[0][0]*zk + sigsq_z*x_nn[0][0]
        ) * invdenom],
        [-(
            (P_nn[1][1]*x_nn[1][0] + P_nn[2][0]*x_nn[1][0] + P_nn[2][1]*x_nn[0][0] - P_nn[2][1]*zk) * ts**2
          + (P_nn[1][0]*x_nn[1][0] + P_nn[1][1]*x_nn[0][0] - P_nn[1][1]*zk + P_nn[2][0]*x_nn[0][0] - P_nn[2][0]*zk) * ts
          + P_nn[1][0]*x_nn[0][0] - P_nn[1][0]*zk
        ) * invdenom + (
            ts*x_nn[2][0] + x_nn[1][0]
        )],
        [-(
            P_nn[2][1]*x_nn[1][0] * ts**2
          + (P_nn[2][0]*x_nn[1][0] + P_nn[2][1]*x_nn[0][0] - P_nn[2][1]*zk) * ts
          + P_nn[2][0]*x_nn[0][0] - P_nn[2][0]*zk
        ) * invdenom + (
            x_nn[2][0]
        )]
    ])
    P_nn = np.asarray([
        [
            sigsq_z * invdenom * (
                (P_nn[1][1]) * ts**2
              + (P_nn[0][1] + P_nn[1][0]) * ts
              + P_nn[0][0]
            ),
            sigsq_z * invdenom * (
                P_nn[1][2] * ts**2
              + (P_nn[0][2] + P_nn[1][1]) * ts
              + P_nn[0][1]
            ),
            sigsq_z * invdenom * (
                P_nn[1][2] * ts
              + P_nn[0][2]
            )
        ],
        [
            sigsq_z * invdenom * (
                P_nn[2][1] * ts**2
              + (P_nn[1][1] + P_nn[2][0]) * ts
              + P_nn[1][0]
            ),
            -(
                (P_nn[0][1]*P_nn[2][1] + P_nn[0][2]*P_nn[1][1] + P_nn[0][2]*P_nn[2][0] + P_nn[1][0]*P_nn[1][2] + P_nn[1][1]**2 + P_nn[1][1]*P_nn[2][0]) * ts**2
              + (P_nn[0][1]*P_nn[1][1] + P_nn[0][1]*P_nn[2][0] + P_nn[0][2]*P_nn[1][0] + P_nn[1][0]*P_nn[1][1]) * ts
              + (P_nn[0][1]*P_nn[1][0])
            ) * invdenom + (
                P_nn[2][2] * ts**2
              + (P_nn[1][2] + P_nn[2][1]) * ts
              + P_nn[1][1]
            ),
            -(
                (P_nn[0][2]*P_nn[2][1] + P_nn[1][1]*P_nn[1][2] + P_nn[1][2]*P_nn[2][0]) * ts**2
              + (P_nn[0][2]*P_nn[1][1] + P_nn[0][2]*P_nn[2][0] + P_nn[1][0]*P_nn[1][2]) * ts
              + P_nn[0][2]*P_nn[1][0]
            ) * invdenom + (
                ts*P_nn[2][2]
              + P_nn[1][2]
            )    
        ],
        [
            sigsq_z * invdenom * (
                P_nn[2][1]*ts
              + P_nn[2][0]
            ),
            -(
                (P_nn[0][2]*P_nn[2][1] + P_nn[1][1]*P_nn[2][1] + P_nn[1][2]*P_nn[2][0]) * ts**2
              + (P_nn[0][1]*P_nn[2][1] + P_nn[0][2]*P_nn[2][0] + P_nn[1][1]*P_nn[2][0]) * ts
              + P_nn[0][1]*P_nn[2][0]
            ) * invdenom + (
                ts*P_nn[2][2]
              + P_nn[2][1]
            ),
            -(
                P_nn[1][2]*P_nn[2][1] * ts**2
              + (P_nn[0][2]*P_nn[2][1] + P_nn[1][2]*P_nn[2][0]) * ts
              + P_nn[0][2]*P_nn[2][0]
            ) * invdenom + (
                sigsq_a*ts**2
              + P_nn[2][2]
            )
        ]
    ])

    alt_matrix_trim2.append(x_nn[0])

diffs = np.asarray(alt_matrix_trim2) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by trim pt2: RMS", rmse, "m, max", maxe, "m")

# Huh, that's barely measurable - one millimeter RMS error in my testing. Can
# we get away with even more aggressive cuts? What if we ignore everything that
# depends on ts^2 (except the inital error term, or everything zeroes)?

x_nn = np.zeros((3, 1))
P_nn = np.zeros((3, 3))
alt_matrix_linearize = []

for zk in fd:
    invdenom = 1 / ((P_nn[0][1] + P_nn[1][0])*ts + P_nn[0][0] + sigsq_z)
    x_nn = np.asarray([
        [(
            (P_nn[0][1]*zk + P_nn[1][0]*zk + sigsq_z*x_nn[1][0]) * ts
          + P_nn[0][0]*zk + sigsq_z*x_nn[0][0]
        ) * invdenom],
        [-(
            (P_nn[1][0]*x_nn[1][0] + P_nn[1][1]*x_nn[0][0] - P_nn[1][1]*zk + P_nn[2][0]*x_nn[0][0] - P_nn[2][0]*zk) * ts
          + P_nn[1][0]*x_nn[0][0] - P_nn[1][0]*zk
        ) * invdenom + (
            ts*x_nn[2][0] + x_nn[1][0]
        )],
        [-(
            (P_nn[2][0]*x_nn[1][0] + P_nn[2][1]*x_nn[0][0] - P_nn[2][1]*zk) * ts
          + P_nn[2][0]*x_nn[0][0] - P_nn[2][0]*zk
        ) * invdenom + (
            x_nn[2][0]
        )]
    ])
    P_nn = np.asarray([
        [
            sigsq_z * invdenom * (
                (P_nn[0][1] + P_nn[1][0]) * ts
              + P_nn[0][0]
            ),
            sigsq_z * invdenom * (
                (P_nn[0][2] + P_nn[1][1]) * ts
              + P_nn[0][1]
            ),
            sigsq_z * invdenom * (
                P_nn[1][2] * ts
              + P_nn[0][2]
            )
        ],
        [
            sigsq_z * invdenom * (
                (P_nn[1][1] + P_nn[2][0]) * ts
              + P_nn[1][0]
            ),
            -(
                (P_nn[0][1]*P_nn[1][1] + P_nn[0][1]*P_nn[2][0] + P_nn[0][2]*P_nn[1][0] + P_nn[1][0]*P_nn[1][1]) * ts
              + (P_nn[0][1]*P_nn[1][0])
            ) * invdenom + (
                (P_nn[1][2] + P_nn[2][1]) * ts
              + P_nn[1][1]
            ),
            -(
                (P_nn[0][2]*P_nn[1][1] + P_nn[0][2]*P_nn[2][0] + P_nn[1][0]*P_nn[1][2]) * ts
              + P_nn[0][2]*P_nn[1][0]
            ) * invdenom + (
                ts*P_nn[2][2]
              + P_nn[1][2]
            )    
        ],
        [
            sigsq_z * invdenom * (
                P_nn[2][1]*ts
              + P_nn[2][0]
            ),
            -(
                (P_nn[0][1]*P_nn[2][1] + P_nn[0][2]*P_nn[2][0] + P_nn[1][1]*P_nn[2][0]) * ts
              + P_nn[0][1]*P_nn[2][0]
            ) * invdenom + (
                ts*P_nn[2][2]
              + P_nn[2][1]
            ),
            -(
                (P_nn[0][2]*P_nn[2][1] + P_nn[1][2]*P_nn[2][0]) * ts
              + P_nn[0][2]*P_nn[2][0]
            ) * invdenom + (
                sigsq_a*ts**2
              + P_nn[2][2]
            )
        ]
    ])

    alt_matrix_linearize.append(x_nn[0])

diffs = np.asarray(alt_matrix_linearize) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by linearization: RMS", rmse, "m, max", maxe, "m")

# Ok, that's a huge improvement, and with very little loss of accuracy - our
# plot is still almost indistinguishable from the original data in smooth areas,
# and follows a reasonable track in discontinuous ones. We're now down to only
# 71 multiplications, which is starting to be something we can handle on our
# puny 16-bit CPU.

# Let's see if there's anything else we can factor out to make our life easier.

x_nn = np.zeros((3, 1))
P_nn = np.zeros((3, 3))
alt_matrix_simplify = []

for zk in fd:
    invdenom = 1 / ((P_nn[0][1] + P_nn[1][0])*ts + P_nn[0][0] + sigsq_z)
    # This factor pops up very frequently also
    szinv = invdenom * sigsq_z
    x_nn = np.asarray([
        # Turns out our Maple results were a litle overzealous in "simplifying"
        # here, and we can cancel out zk * denom / denom with basically no 
        # additional damage
        [zk + (
            x_nn[1][0] * ts
          + x_nn[0][0]
          - zk
        ) * szinv],
        [-(
            # We can factor out the terms here a little to save multiplications
            (P_nn[1][0]*x_nn[1][0] + (P_nn[1][1] + P_nn[2][0])*(x_nn[0][0] - zk)) * ts
          + P_nn[1][0]*x_nn[0][0] - P_nn[1][0]*zk
        ) * invdenom + (
            ts*x_nn[2][0] + x_nn[1][0]
        )],
        [-(
            (P_nn[2][0]*x_nn[1][0] + P_nn[2][1]*x_nn[0][0] - P_nn[2][1]*zk) * ts
          + P_nn[2][0]*x_nn[0][0] - P_nn[2][0]*zk
        ) * invdenom + (
            x_nn[2][0]
        )]
    ])
    P_nn = np.asarray([
        [
            # Likewise here, we can pull out invdenom
            sigsq_z * (1 - szinv),
            szinv * (
                (P_nn[0][2] + P_nn[1][1]) * ts
              + P_nn[0][1]
            ),
            szinv * (
                P_nn[1][2] * ts
              + P_nn[0][2]
            )
        ],
        [
            szinv * (
                (P_nn[1][1] + P_nn[2][0]) * ts
              + P_nn[1][0]
            ),
            -(
                ((P_nn[1][1] + P_nn[2][0]) * P_nn[0][1] + (P_nn[0][2] + P_nn[1][1])*P_nn[1][0]) * ts
              + (P_nn[0][1]*P_nn[1][0])
            ) * invdenom + (
                (P_nn[1][2] + P_nn[2][1]) * ts
              + P_nn[1][1]
            ),
            -(
                ((P_nn[1][1] + P_nn[2][0]) * P_nn[0][2] + P_nn[1][0]*P_nn[1][2]) * ts
              + P_nn[0][2]*P_nn[1][0]
            ) * invdenom + (
                ts*P_nn[2][2]
              + P_nn[1][2]
            )    
        ],
        [
            szinv * (
                P_nn[2][1]*ts
              + P_nn[2][0]
            ),
            -(
                (P_nn[0][1]*P_nn[2][1] + (P_nn[0][2] + P_nn[1][1])*P_nn[2][0]) * ts
              + P_nn[0][1]*P_nn[2][0]
            ) * invdenom + (
                ts*P_nn[2][2]
              + P_nn[2][1]
            ),
            -(
                (P_nn[0][2]*P_nn[2][1] + P_nn[1][2]*P_nn[2][0]) * ts
              + P_nn[0][2]*P_nn[2][0]
            ) * invdenom + (
                sigsq_a*ts**2
              + P_nn[2][2]
            )
        ]
    ])

    alt_matrix_simplify.append(x_nn[0])

diffs = np.asarray(alt_matrix_simplify) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by simplification: RMS", rmse, "m, max", maxe, "m")

# One important observation is that the covariance matrix is always symmetric.
# Instead of a grid, let's represent it as
# 0, 0 -> 0
# 0, 1 = 1, 0 -> 1
# 0, 2 = 2, 0 -> 2
# 1, 1 -> 3
# 1, 2 = 2, 1 -> 4
# 2, 2 -> 5
# This cuts out 1/4 of our needed calculations, as well as allowing a few
# simplifications that weren't apparent before.

x_nn = np.zeros(3)
P_nn = np.zeros(6)
alt_matrix_symmetrize = []
ts = float(ts)


for zk in fd:
    invdenom = 1 / (2*P_nn[1]*ts + P_nn[0] + sigsq_z)
    # This factor pops up very frequently also
    szinv = invdenom * sigsq_z
    x_nn = [
        # Turns out our Maple results were a litle overzealous in "simplifying"
        # here, and we can cancel out zk * denom / denom with basically no 
        # additional damage
        zk + (
            x_nn[1] * ts
          + x_nn[0]
          - zk
        ) * szinv,
        -(

            P_nn[1]*x_nn[1]*ts 
          + ((P_nn[3] + P_nn[2]) * ts + P_nn[1])*(x_nn[0] - zk)
        ) * invdenom + (
            ts*x_nn[2] + x_nn[1]
        ),
        -(
            ((x_nn[0] - zk)*P_nn[4]) * ts
          + (x_nn[1]*ts + x_nn[0] - zk) * P_nn[2]
        ) * invdenom + (
            x_nn[2]
        )
    ]
    P_nn = [
        # 0, 0
        sigsq_z * (1 - szinv),
        # 0, 1
        szinv * (
            (P_nn[2] + P_nn[3]) * ts
          + P_nn[1]
        ),
        # 0, 2
        szinv * (
            P_nn[4] * ts
          + P_nn[2]
        ),
        # 1, 1
        -(
            2*(P_nn[3] + P_nn[2]) * P_nn[1] * ts
          + P_nn[1]*P_nn[1]
        ) * invdenom + (
            2 * P_nn[4] * ts
          + P_nn[3]
        ),
        # 1, 2
        -(
            P_nn[1]*P_nn[4] * ts
          + ((P_nn[3] + P_nn[2])*ts + P_nn[1]) * P_nn[2] 
        ) * invdenom + (
            ts*P_nn[5]
          + P_nn[4]
        ),
        # 2, 2
        -(
            2 * P_nn[2]*P_nn[4] * ts
          + P_nn[2]*P_nn[2]
        ) * invdenom + (
            sigsq_a*ts**2
          + P_nn[5]
        )
    ]

    alt_matrix_symmetrize.append([x_nn[0]])

diffs = np.asarray(alt_matrix_symmetrize) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by symmetrization: RMS", rmse, "m, max", maxe, "m")

# Editor's note: it was at this point that I realized that, because we're taking
# time step as constant, the covariance matrix P_nn depends on only constants,
# so we can find a steady-state matrix for any given inputs. The work done
# so far is still mildly useful for computing x_nn, but we can precompute all
# the work for P_nn. This function finds that steady-state:
from kalman_steady_state import steady_state_P
# In my testing, it matters basically nothing if we use the full or trimmed F
# matrix, so let's use the good stuff
P = steady_state_P(F_full, H, R, Q, 1/(1<<16))
# The steady-state-finding function isn't performance-constrained, so it runs
# with the full ugly mess of equations. As before, though, it's always symmetric
# so we can make our nice unwrapped triangle version as before.
Pt = [P[0][0], P[0][1], P[0][2],
               P[1][1], P[1][2],
                        P[2][2]]

x_nn = np.zeros(3)
alt_matrix_steady = []
# These are constant now too!
invdenom = 1 / (2*Pt[1]*ts + Pt[0] + sigsq_z)
szinv = invdenom * sigsq_z

for zk in fd:
    # This factor pops up very frequently also
    x_nn = [
        # Turns out our Maple results were a litle overzealous in "simplifying"
        # here, and we can cancel out zk * denom / denom with basically no 
        # additional damage
        zk + (
            x_nn[1] * ts
          + x_nn[0]
          - zk
        ) * szinv,
        -(
            Pt[1]*x_nn[1]*ts 
          + ((Pt[3] + Pt[2]) * ts + Pt[1])*(x_nn[0] - zk)
        ) * invdenom + (
            ts*x_nn[2] + x_nn[1]
        ),
        -(
            ((x_nn[0] - zk)*Pt[4]) * ts
          + (x_nn[1]*ts + x_nn[0] - zk) * Pt[2]
        ) * invdenom + (
            x_nn[2]
        )
    ]
    alt_matrix_steady.append([x_nn[0]])

diffs = np.asarray(alt_matrix_steady) - np.asarray(alt_matrix)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by steady-state: RMS", rmse, "m, max", maxe, "m")

# Notably, performance actually gets a nonzero amount worse here. However, if we
# look at the data, we can see it actually tracks the flight data *better* - we
# don't have excessive confidence about our measurement being stationary at the
# beginning anymore, so we catch on to the takeoff acceleration much more quickly.

# We should compute a new ground-truth using All The Math, so we can properly
# compare against it:

x_nn = np.zeros((3, 1))
alt_steady = []
P_npred = F_full @ P @ F_full.T + Q

for zk in fd:
    # Prediction step
    x_npred = F_full @ x_nn
    # Update step
    y_n = zk - H @ x_npred
    S_n = H @ P_npred @ H.T + R

    K_n = P_npred @ H.T @ np.linalg.inv(S_n)
    x_nn = x_npred + K_n @ y_n

    alt_steady.append(x_nn[0])

print("== VS STEADY STATE ==")
diffs = np.asarray(alt_matrix_steady) - np.asarray(alt_steady)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by steady-state simplified: RMS", rmse, "m, max", maxe, "m")

# This is a significant reduction in amount of math, but it's still a lot of
# floating point operations, which we would like to avoid. As we did with the
# barometric approximations, we can solve this by incrementally converting
# things to fixed-point.

# Let's start with the x state vector. We can't quite get away with converting
# all elements to integers, so let's give ourselves 4 bits of mantissa on the
# velocity and acceleration:

x_nn = np.zeros(3)
alt_matrix_disc1 = []
invdenom = 1 / (2*Pt[1]*ts + Pt[0] + sigsq_z)

for zk in fd:
    x_nn = [
        int(zk + (
            x_nn[1] * ts / 16
          + x_nn[0]
          - zk
        ) * invdenom * sigsq_z),
        int((-(
            Pt[1]*x_nn[1]/16*ts 
          + ((Pt[3] + Pt[2]) * ts + Pt[1])*(x_nn[0] - zk)
        ) * invdenom + (
            ts*x_nn[2]/16 + x_nn[1]/16
        )) * 16),
        int((-(
            ((x_nn[0] - zk)*Pt[4]) * ts
          + (x_nn[1]*ts/16 + x_nn[0] - zk) * Pt[2]
        ) * invdenom + (
            x_nn[2] / 16
        )) * 16)
    ]
    alt_matrix_disc1.append([x_nn[0]])

diffs = np.asarray(alt_matrix_disc1) - np.asarray(alt_steady)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by discretization pt1: RMS", rmse, "m, max", maxe, "m")

# We have a lot of common factors of 16 we can pull out here:

x_nn = np.zeros(3)
alt_matrix_disc_simpl1 = []
invdenom = 1 / (2*Pt[1]*ts + Pt[0] + sigsq_z)

for zk in fd:
    x_nn = [
        int(zk + (
            x_nn[1] * ts / 16
          + x_nn[0]
          - zk
        ) * invdenom * sigsq_z),
        int((-(
            Pt[1]*x_nn[1]*ts 
          + ((Pt[3] + Pt[2]) * ts + Pt[1])*(x_nn[0] - zk)*16
        ) * invdenom + (
            ts*x_nn[2] + x_nn[1]
        ))),
        int((-(
            ((x_nn[0] - zk)*Pt[4]) * ts * 16
          + (x_nn[1]*ts + x_nn[0]*16 - zk*16) * Pt[2]
        ) * invdenom + (
            x_nn[2]
        )))
    ]
    alt_matrix_disc_simpl1.append([x_nn[0]])

diffs = np.asarray(alt_matrix_disc_simpl1) - np.asarray(alt_steady)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by disc. simpl. pt1: RMS", rmse, "m, max", maxe, "m")

# We need to be careful here that we don't accidentally create overflow, e.g.
# when multiplying x[0] by 16. We'll take care of that when we get there.

# Originally, we simplified these expressions to reduce the number of overall
# multiplications, but we don't actually want that now; we want to reduce down
# to the minimum set of multiplications by *non-constants*. This gives us
# something vaguely looking like a sparse matrix transforming <zk, x0, x1, x2>
# to <x0', x1', x2'>; this gives us an upper bound of 12 multiplications at
# runtime, but most of the terms will end up being 0, which is good news for
# performance.

x_nn = np.zeros(3)
alt_matrix_disc_simpl2 = []
invdenom = 1 / (2*Pt[1]*ts + Pt[0] + sigsq_z)

for zk in fd:
    x_nn = [
        int(
            zk
          + x_nn[1] * (ts / 16 * invdenom * sigsq_z)
          + (x_nn[0] - zk) * (invdenom * sigsq_z)
        ),
        int(
            x_nn[2] * ts
          + x_nn[1] * (1 - Pt[1] * ts * invdenom)
          + (x_nn[0] - zk) * (-((Pt[3] + Pt[2]) * ts + Pt[1]) * 16 * invdenom)
        ),
        int(
            x_nn[2]
          + x_nn[1] * (-Pt[2] * ts * invdenom)
          + (x_nn[0] - zk) * (-(Pt[4] * ts + Pt[2]) * 16 * invdenom)
        )
    ]
    alt_matrix_disc_simpl2.append([x_nn[0]])

diffs = np.asarray(alt_matrix_disc_simpl2) - np.asarray(alt_steady)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by disc. simpl. pt2: RMS", rmse, "m, max", maxe, "m")

# Seven multiplications is a very reasonable number for us to handle on our
# limited processing power. Because each multiplication is by a constant, we
# can use the constant-division trick used in our baro approximation and avoid
# any chance of intermediate overflow.

def make_divider(d, bits):
    if d < 0:
        raise f"Divider {d} cannot be negative"
    postshift = 0
    while d < 1:
        d *= 2
        postshift += 1
    p = math.ceil(math.log2(d))
    m = math.ceil((1 << (bits + p)) / d) & ((1 << bits) - 1)
    def divider(n):
        # Correction factor since we're working with signed numbers
        if(n < 0):
            n += int(d) - 1
        q = m*n >> bits
        t = (((n - q) >> 1) + q) >> (p-1)
        return t << postshift
    return divider

invdenom = 1 / (2*Pt[1]*ts + Pt[0] + sigsq_z)
x_nn = [0, 0, 0]
alt_fixedpoint = []

div_x0_x1 = make_divider(1/(ts / 16 * invdenom * sigsq_z), 16)
div_x0_x0zk = make_divider(1/(invdenom * sigsq_z), 16)
div_x1_x2 = make_divider(1/ts, 16)
div_x1_x1 = make_divider(1/(1 - Pt[1] * ts * invdenom), 16)
div_x1_x0zk = make_divider(1/(((Pt[3] + Pt[2]) * ts + Pt[1]) * 16 * invdenom), 16)
div_x2_x1 = make_divider(1/(Pt[2] * ts * invdenom), 16)
div_x2_x0zk = make_divider(1/((Pt[4] * ts + Pt[2]) * 16 * invdenom), 16)

for zk in fd:
    zk = int(zk)
    x_nn = [
        int(
            zk
          + div_x0_x1(x_nn[1])
          + div_x0_x0zk(x_nn[0] - zk)
        ),
        int(
            div_x1_x2(x_nn[2])
          + div_x1_x1(x_nn[1])
          - div_x1_x0zk(x_nn[0] - zk)
        ),
        int(
            x_nn[2]
          - div_x2_x1(x_nn[1])
          - div_x2_x0zk(x_nn[0] - zk)
        )
    ]
    if any(abs(i) > 32767 for i in x_nn):
        print("Overflow:", x_nn)
        exit(-1)
    alt_fixedpoint.append([x_nn[0]])

diffs = np.asarray(alt_fixedpoint) - np.asarray(alt_steady)
rmse = np.sqrt(np.sum(diffs * diffs) / len(diffs))
maxe = np.max(np.abs(diffs))
print("Error introduced by constant-divide: RMS", rmse, "m, max", maxe, "m")


plt.plot(td, fd, label="Original")
plt.plot(td, alt_matrix, label="Kalman")
plt.plot(td, alt_steady, label="Kalman steady state")
plt.plot(td, alt_matrix_steady, label="approx. Kalman steady state")
plt.plot(td, alt_matrix_disc1, label="discretized Kalman steady state")
plt.plot(td, alt_fixedpoint, label="Final 7-int-mult version")
plt.legend()
plt.show()