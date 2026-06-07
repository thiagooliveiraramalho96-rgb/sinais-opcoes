from .database import Database

class ConfigManager:
    def __init__(self, db: Database = None):
        self.db = db or Database()
    
    def get(self, key: str, default=None):
        return self.db.obter_config(key, default)
    
    def set(self, key: str, value, tipo: str = 'str'):
        self.db.salvar_config(key, value, tipo)
    
    def get_tickers(self) -> list:
        tickers_str = self.get('tickers', '')
        if tickers_str:
            return [t.strip() for t in tickers_str.split(',') if t.strip()]
        from ..analysis.data_fetcher import DataFetcher
        return DataFetcher.TICKERS_PADRAO
    
    def set_tickers(self, tickers: list):
        self.set('tickers', ','.join(tickers), 'str')
    
    def get_strategy(self):
        return {
            'formula': self.get('formula_entrada', ''),
            'timeframe': self.get('timeframe', 'D1'),
            'risco': float(self.get('risco', '1.0')),
            'stop_pct': float(self.get('stop_pct', '0.50')),
            'parcial_pct': float(self.get('parcial_pct', '1.00')),
            'saida_min_pct': float(self.get('saida_min_pct', '1.50')),
            'saida_max_pct': float(self.get('saida_max_pct', '2.00')),
        }