import matplotlib.pyplot as plt
import numpy as np

def h1d(data, bins=50, title="Histogram", xlabel="Value", ylabel="Frequency"):
    """
    Create a histogram of a 1D numeric sequence.
    
    Args:
        data: Array-like sequence of numbers
        bins: Number of bins for histogram (default: 50)
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
"""
    data = np.asarray(data).flatten()
    
    plt.figure(figsize=(10, 6))
    plt.hist(data, bins=bins, edgecolor='black', alpha=0.7)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    
    # Add statistics
    stats_text = f'Mean: {np.mean(data):.3f}\nStd: {np.std(data):.3f}\nMin: {np.min(data):.3f}\nMax: {np.max(data):.3f}'
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.show()


def p1d(data, title="plotted samples (no explicit abscissa)", xlabel="sample number", ylabel="value"):
    """
    Create a simple plot of a sequence of 1D numeric values.
    
    Args:
        data: Array-like sequence of numbers
        bins: Number of bins for histogram (default: 50)
        title: Plot title
        xlabel: X-axis label
        ylabel: Y-axis label
"""
    data = np.asarray(data).flatten()
    
    plt.figure(figsize=(10, 6))
    plt.plot(np.arange(len(data)), data, edgecolor='black', alpha=0.7)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    
    # Add statistics
    stats_text = f'Mean: {np.mean(data):.3f}\nStd: {np.std(data):.3f}\nMin: {np.min(data):.3f}\nMax: {np.max(data):.3f}'
    plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
             verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.show()

