import backtrader as bt
import numpy as np
#import matplotlib.pyplot as plt

class VolumeIndicator(bt.Indicator):
    lines = ('volume_label',)
    plotinfo = dict(subplot=True)

    def __init__(self):
        self.volume_data = []
        self.addminperiod(252 // 2)

    def next(self):
        # Append the current volume to the volume data list
        self.volume_data.append(self.data.volume[0] if self.data.volume[0] > 0 else 1)

        # Calculate mean and standard deviation of the historical volumes in log scale
        log_volumes = np.log(self.volume_data)
        mean_log_volume = np.mean(log_volumes)
        std_log_volume = np.std(log_volumes)

        # Determine if the current volume is high or low based on log-normal distribution
        current_log_volume = np.log(self.data.volume[0])
        if current_log_volume > mean_log_volume + std_log_volume:
            self.lines.volume_label[0] = 1  # "hi"
        elif current_log_volume < mean_log_volume - std_log_volume:
            self.lines.volume_label[0] = -1  # "lo"
        else:
            self.lines.volume_label[0] = 0  # "nv"
"""
    def plot(self):
        # Custom plot method to display labels
        fig, ax = plt.subplots()
        ax.plot(self.data.datetime.array, self.data.volume.array, label='Volume')
        for i, label in enumerate(self.lines.volume_label):
            if label == 1:
                ax.text(self.data.datetime.array[i], self.data.volume.array[i], 'hi', color='red' if self.data.close[i] < self.data.open[i] else 'green')
            elif label == -1:
                ax.text(self.data.datetime.array[i], self.data.volume.array[i], 'lo', color='red' if self.data.close[i] < self.data.open[i] else 'green')
            elif label == 0:
                ax.text(self.data.datetime.array[i], self.data.volume.array[i], 'nv', color='red' if self.data.close[i] < self.data.open[i] else 'green')
        plt.show()
        """