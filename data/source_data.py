class SourceData:
    def __init__(self, max_years=5):
        self.max_years = max_years

    def download_and_save_csv(self, ticker, exchange, start, end, filename, savefile=False):
        pass

    def load_data_from_csv(self, ticker):
        pass

    def refresh_data(self, ticker, exchange):
        pass