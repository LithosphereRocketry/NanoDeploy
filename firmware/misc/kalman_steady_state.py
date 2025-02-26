import numpy as np

# Compute a steady state covariance (P) matrix for the given parameters.
# Computes iteratively; stops computation when the error in every cell is less
# than thresh * the cell value. E.g., a threshold of 1/1000 will make sure all
# values are stable within 0.1% per iteration.
def steady_state_P(F: np.ndarray, H: np.ndarray, R: np.ndarray, Q: np.ndarray, thresh: float) -> np.ndarray:
    def P_step(P_nn: np.ndarray) -> np.ndarray:
        P_npred = F @ P_nn @ F.T + Q
        S_n = H @ P_npred @ H.T + R
        K_n = P_npred @ H.T @ np.linalg.inv(S_n)
        return (np.eye(3) - K_n @ H) @ P_npred
    P_nn = np.zeros_like(F)
    while True:
        P_new = P_step(P_nn)
        if not np.any(P_nn == 0):
            maxe = np.max((P_new - P_nn) / P_nn)
            if maxe < thresh:
                return P_nn
        P_nn = P_new