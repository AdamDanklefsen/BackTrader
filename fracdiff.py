import pandas as pd
import numpy as np
from scipy.special import comb

def fracdiff(X: pd.Series, d: float, threshold: float=1e-4) -> pd.Series:
    print(f"Calculating fractional differentiation with d={d} and threshold={threshold}")

    X = pd.Series(X).squeeze().dropna()
    index = X.index
    X_vals = X.values.astype(np.float64)

    W = [1.0]
    k = 1
    while True:
        w_k = -W[-1] * (d - k + 1) / k
        W.append(w_k)
        #print(f"W[{k}] = {w_k:.6f}")
        if abs(w_k) < threshold:
            break
        k += 1
    W = np.array(W)

    K = len(W)-1

    Xd = np.zeros(len(X_vals)-K)
    for t in range(K, len(X_vals)):
        Xd[t-K] = np.dot(W, X_vals[t-K:t+1][::-1])

    result_index = index[K:]


    return pd.Series(Xd, index=result_index)


def fracint(X: pd.Series, d: float, threshold: float=1e-4) -> pd.Series:
    print(f"Calculating fractional integration with d={d} and threshold={threshold}")

    X = pd.Series(X).squeeze().dropna()
    index = X.index
    X_vals = X.values.astype(np.float64)

    W = [1.0]
    k = 1
    while True:
        w_k = W[-1] * (d + k - 1) / k
        W.append(w_k)
        #print(f"W[{k}] = {w_k:.6f}")
        if abs(w_k - W[-2]) < threshold:
            break
        k += 1
    W = np.array(W)

    K = len(W)-1

    Xi = np.zeros(len(X_vals))
    for t in range(K, len(X_vals)):
        window = X_vals[max(0, t-K):t+1]

        if len(window) < K+1:
            pad = np.zeros(K+1 - len(window))
            window = np.concatenate([pad, window])
        else:
            window = window[-K-1:][::-1]
        Xi[t] = np.dot(W, window)


    return pd.Series(Xi, index=index)