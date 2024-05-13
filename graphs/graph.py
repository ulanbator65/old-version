
import matplotlib.pyplot as plt


def print_graph(title: str, x: list, y: list):
    plt.plot(x, y)
    plt.ylabel(title)
    plt.show()
