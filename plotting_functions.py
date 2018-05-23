import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import string

def plot_with_predict(X_values, y_values, model):
    y_predict = model.predict(X_values)

    plt.plot(y_values,y_predict, 'o', alpha = 0.5)
    plt.xlabel('actual y')
    plt.ylabel('predicted y')
    plt.grid()
    return

def plot_residuals(X, y_predict,y_actual,var_to_check):
    col_size = 3
    row_size = round(len(var_to_check)/col_size,0)+1
    fig=plt.figure(figsize=(10,2.5*row_size),dpi=100)
    for i, var in enumerate(var_to_check):
        ax=fig.add_subplot(row_size,col_size,i+1)
        # use the unscaled X against the y that is predicted from the scaled X - scaling doesn't affect output
        # also, plotting the scaled X values is not helpful in understanding the affect of X on y prediction
        ax.plot(X[var], y_predict - y_actual,'o', alpha=0.25)
        ax.set_title(var+" residuals (train)")
        ax.axhline(+1,color='r',lw=1,ls='-');
        ax.axhline(-1,color='r',lw=1,ls='-');
        ax.set_xlabel(var)
        ax.set_ylabel('rating prediction error')
        ax.grid()
    fig.tight_layout()
    return