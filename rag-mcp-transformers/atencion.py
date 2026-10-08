import numpy as np


def softmax(M):
    M = np.asarray(M, dtype=float)
    M = M - np.max(M, axis=-1, keepdims=True)
    exp_M = np.exp(M)
    return exp_M / np.sum(exp_M, axis=-1, keepdims=True)


def atencion(Q, K, V):
    dk = Q.shape[-1]

    puntajes = Q @ K.T / np.sqrt(dk)
    A = softmax(puntajes)
    salida = A @ V

    return salida, A


def autoatencion(X, WQ, WK, WV, mascara=False):
    Q = X @ WQ
    K = X @ WK
    V = X @ WV

    dk = Q.shape[-1]
    puntajes = Q @ K.T / np.sqrt(dk)

    if mascara:
        n = puntajes.shape[0]
        mask = np.triu(np.ones((n, n), dtype=bool), k=1)
        puntajes[mask] = -np.inf

    A = softmax(puntajes)
    salida = A @ V

    return salida, A


def multicabeza(X, cabezas, Wo, mascara=False):
    resultados = []

    for Wq, Wk, Wv in cabezas:
        salida, A = autoatencion(X, Wq, Wk, Wv, mascara=mascara)
        resultados.append(salida)

    concatenado = np.concatenate(resultados, axis=1)
    salida_final = concatenado @ Wo

    return salida_final


def layer_norm(x, eps=1e-5):
    x = np.asarray(x, dtype=float)

    media = np.mean(x, axis=-1, keepdims=True)
    varianza = np.var(x, axis=-1, keepdims=True)

    return (x - media) / np.sqrt(varianza + eps)
