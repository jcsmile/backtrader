class VolumeIndicator(bt.Indicator):
    lines = ('volume_label',)
    plotinfo = dict(subplot=False)

    def __init__(self, period=20):
        self.period = period
        self.volume_data = []

    def next(self):
        # Append the current volume to the volume data list
        self.volume_data.append(self.data.volume[0])

        # Keep only the last 'period' volumes for analysis
        if len(self.volume_data) > self.period:
            self.volume_data.pop(0)

        # Calculate mean and standard deviation of the historical volumes
        if len(self.volume_data) == self.period:
            mean_volume = sum(self.volume_data) / self.period
            std_volume = (sum((x - mean_volume) ** 2 for x in self.volume_data) / self.period) ** 0.5

            # Determine if the current volume is high or low
            if self.data.volume[0] > mean_volume + std_volume:
                self.lines.volume_label[0] = "high vol"
            elif self.data.volume[0] < mean_volume - std_volume:
                self.lines.volume_label[0] = "low vol"
            else:
                self.lines.volume_label[0] = "normal vol"
        else:
            self.lines.volume_label[0] = "loading"  # Not enough data yet