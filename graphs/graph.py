
import matplotlib.pyplot as plt
import matplotlib.dates as dates


def print_graph(title: str, x: list, y1: list, y2: list = [], y3: list = []):

    ax=plt.gca()
    xfmt = dates.DateFormatter('%m-%d')
    ax.xaxis.set_major_formatter(xfmt)

    plt.figure(figsize=(12,2))

    plt.grid(True)
    plt.plot(x, y1)
    plt.plot(x, y2)
    plt.plot(x, y3)
    plt.ylabel(title)
    plt.show()
