"""
Banco de dados SQLite local para persistência.
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import Optional


DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'sinais_opcoes.db')


class Database:
    """Gerenciador do banco SQLite."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = os.path.abspath(db_path)
        self._inicializar_tabelas()
    
    def _conectar(self):
        return sqlite3.connect(self.db_path)
    
    def _inicializar_tabelas(self):
        conn = self._conectar()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sinais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                preco REAL,
                tipo_entrada TEXT,
                sinal_verde INTEGER,
                detalhes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                valor TEXT NOT NULL,
                tipo TEXT DEFAULT 'str'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS estrategias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                formula_entrada TEXT,
                formula_saida TEXT,
                timeframe TEXT DEFAULT 'D1',
                risco REAL DEFAULT 1.0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backtest_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estrategia_id INTEGER,
                ticker TEXT,
                periodo_inicio TEXT,
                periodo_fim TEXT,
                capital_inicial REAL,
                capital_final REAL,
                total_operacoes INTEGER,
                win_rate REAL,
                resultado_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def salvar_sinal(self, ticker: str, sinal_dict: dict):
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sinais (ticker, timestamp, preco, tipo_entrada, sinal_verde, detalhes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            ticker,
            datetime.now().isoformat(),
            sinal_dict.get('Preço atual', 0),
            sinal_dict.get('Tipo de entrada'),
            1 if 'VERDE' in str(sinal_dict.get('Status', '')) else 0,
            json.dumps(sinal_dict)
        ))
        conn.commit()
        conn.close()
    
    def salvar_config(self, nome: str, valor, tipo: str = 'str'):
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO configs (nome, valor, tipo)
            VALUES (?, ?, ?)
        """, (nome, str(valor), tipo))
        conn.commit()
        conn.close()
    
    def obter_config(self, nome: str, default=None):
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT valor, tipo FROM configs WHERE nome = ?", (nome,))
        row = cursor.fetchone()
        conn.close()
        if row:
            valor, tipo = row
            if tipo == 'float':
                return float(valor)
            elif tipo == 'int':
                return int(valor)
            elif tipo == 'bool':
                return valor.lower() == 'true'
            return valor
        return default
    
    def listar_estrategias(self) -> list:
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM estrategias ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    def salvar_estrategia(self, nome: str, formula_entrada: str, formula_saida: str = '',
                          timeframe: str = 'D1', risco: float = 1.0):
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO estrategias (nome, formula_entrada, formula_saida, timeframe, risco)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, formula_entrada, formula_saida, timeframe, risco))
        conn.commit()
        conn.close()
    
    def obter_ultimos_sinais(self, limite: int = 50) -> list:
        conn = self._conectar()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM sinais ORDER BY timestamp DESC LIMIT ?
        """, (limite,))
        rows = cursor.fetchall()
        conn.close()
        return rows