from .database import Database

class SignalHistory:
    def __init__(self, db: Database = None):
        self.db = db or Database()
    
    def add_signal(self, ticker: str, sinal_dict: dict):
        self.db.salvar_sinal(ticker, sinal_dict)
    
    def get_recent(self, limit: int = 50) -> list:
        return self.db.obter_ultimos_sinais(limit)