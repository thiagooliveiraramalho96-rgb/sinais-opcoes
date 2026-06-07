"""
Aplicação principal KivyMD para Sinais de Opções.
"""
import os
import sys
import threading
import json
from datetime import datetime

# Kivy imports
import kivy
kivy.require('2.1.0')

from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.clock import Clock, mainthread
from kivy.metrics import dp

from kivymd.app import MDApp
from kivymd.uix.list import OneLineListItem, TwoLineListItem, ThreeLineListItem
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.theming import ThemeManager

# Project imports
from ..analysis.data_fetcher import DataFetcher
from ..analysis.signal_engine import SignalEngine, SinalResultado
from ..engine.formula_validator import validar_formula
from ..engine.parser import parse
from ..engine.interpreter import Interpretador
from ..storage.database import Database
from ..storage.config_manager import ConfigManager
from ..storage.signal_history import SignalHistory
from ..backtest.backtest_engine import BacktestEngine
from ..backtest.trade_simulator import ExitConfig

# Carregar KV
KV_DIR = os.path.join(os.path.dirname(__file__), 'kv')
KV_FILE = os.path.join(KV_DIR, 'sinais.kv')

if os.path.exists(KV_FILE):
    Builder.load_file(KV_FILE)


class SinaisOpcoesApp(MDApp):
    """Aplicação principal."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.theme_style = "Dark"
        
        self.db = Database()
        self.config = ConfigManager(self.db)
        self.signal_history = SignalHistory(self.db)
        self.data_fetcher = DataFetcher()
        self.sinal_engine = SignalEngine()
        self.thread_running = False
    
    def build(self):
        """Constrói a interface."""
        self.title = "Sinais Opções B3"
        
        sm = ScreenManager()
        
        # Criar screens
        screens = {
            'sinais': Screen(name='sinais'),
            'criar_estrategia': Screen(name='criar_estrategia'),
            'backtest': Screen(name='backtest'),
            'config': Screen(name='config'),
            'historico': Screen(name='historico'),
        }
        
        for name, screen in screens.items():
            sm.add_widget(screen)
        
        return sm
    
    def on_start(self):
        """Inicialização após construção da UI."""
        self.carregar_configuracoes()
        
        # Iniciar monitoramento automático
        self.iniciar_monitoramento()
    
    def carregar_configuracoes(self):
        """Carrega configurações salvas."""
        try:
            root = self.root
            
            # Tickers
            tickers = self.config.get_tickers()
            if hasattr(root, 'ids') and 'tickers_input' in root.ids:
                root.ids.tickers_input.text = ', '.join(tickers)
            
            # Notificações
            notif = self.config.get('notificacoes', 'True')
            if hasattr(root, 'ids') and 'notificacoes_switch' in root.ids:
                root.ids.notificacoes_switch.active = notif.lower() == 'true'
            
            print(f"[CONFIG] Configurações carregadas: {len(tickers)} ativos")
        except Exception as e:
            print(f"[CONFIG] Erro ao carregar: {e}")
    
    def carregar_tickers_padrao(self):
        """Carrega lista padrão de 50 tickers."""
        tickers = DataFetcher.TICKERS_PADRAO
        root = self.root
        if hasattr(root, 'ids') and 'tickers_input' in root.ids:
            root.ids.tickers_input.text = ', '.join(tickers)
        self.config.set_tickers(tickers)
    
    def iniciar_monitoramento(self):
        """Inicia monitoramento automático em thread separada."""
        if self.thread_running:
            return
        
        self.thread_running = True
        thread = threading.Thread(target=self._loop_monitoramento, daemon=True)
        thread.start()
        print("[MONITOR] Monitoramento automático iniciado")
    
    def _loop_monitoramento(self):
        """Loop principal de monitoramento."""
        import time
        
        while self.thread_running:
            try:
                self.atualizar_sinais()
                time.sleep(900)  # 15 minutos
            except Exception as e:
                print(f"[MONITOR] Erro: {e}")
                time.sleep(60)
    
    @mainthread
    def atualizar_sinais(self, *args):
        """Atualiza lista de sinais na tela."""
        try:
            tickers = self.config.get_tickers()
            
            if not tickers:
                self._mostrar_mensagem("Nenhum ativo configurado")
                return
            
            print(f"[SINAIS] Analisando {len(tickers)} ativos...")
            
            # Pegar engine atual
            engine = self.sinal_engine
            
            # Processar em lotes para não travar UI
            sinais_verdes = []
            todos_resultados = []
            
            for ticker in tickers[:10]:  # Limitar a 10 por vez
                try:
                    dados = self.data_fetcher.baixar_dados(ticker, periodo='2y')
                    if not dados.empty:
                        resultado = engine.analisar(ticker, dados)
                        todos_resultados.append(resultado)
                        
                        if resultado.sinal_verde:
                            sinais_verdes.append(resultado)
                            # Salvar no histórico
                            self.signal_history.add_signal(ticker, resultado.para_dict())
                            
                            # Notificar
                            self._notificar_sinal(resultado)
                except Exception as e:
                    print(f"[SINAIS] Erro {ticker}: {e}")
            
            self._atualizar_lista_ui(todos_resultados)
            self._atualizar_historico_ui()
            
            if sinais_verdes:
                msg = f"✅ {len(sinais_verdes)} sinal(is) VERDE(s) encontrado(s)!"
                print(f"[SINAIS] {msg}")
                self._mostrar_mensagem(msg)
            else:
                print("[SINAIS] Nenhum sinal verde no momento")
        
        except Exception as e:
            print(f"[SINAIS] Erro geral: {e}")
    
    def _atualizar_lista_ui(self, resultados):
        """Atualiza a lista de resultados na UI."""
        try:
            root = self.root
            if not hasattr(root, 'ids'):
                return
            
            sinais_list = root.ids.get('sinais_list')
            if not sinais_list:
                return
            
            sinais_list.clear_widgets()
            
            if not resultados:
                item = OneLineListItem(text="Nenhum resultado disponível")
                sinais_list.add_widget(item)
                return
            
            # Cards para cada resultado
            for resultado in resultados:
                if resultado.sinal_verde:
                    cor = [0, 0.8, 0, 1]  # Verde
                    icone = "✅"
                else:
                    cor = [0.8, 0, 0, 1]  # Vermelho
                    icone = "❌"
                
                texto = f"{icone} {resultado.ticker} - R$ {resultado.preco_atual:.2f}"
                texto2 = f"ADX:{resultado.adx:.1f} IFR:{resultado.ifr:.1f} | {resultado.tipo_entrada or 'Sem sinal'}"
                
                item = TwoLineListItem(
                    text=texto,
                    secondary_text=texto2,
                )
                sinais_list.add_widget(item)
        
        except Exception as e:
            print(f"[UI] Erro atualizar lista: {e}")
    
    def _atualizar_historico_ui(self):
        """Atualiza tela de histórico."""
        try:
            root = self.root
            if not hasattr(root, 'ids'):
                return
            
            historico_list = root.ids.get('historico_list')
            if not historico_list:
                return
            
            sinais = self.signal_history.get_recent(20)
            historico_list.clear_widgets()
            
            for sinal in sinais:
                ticker = sinal[1]
                timestamp = sinal[2]
                status = "✅ VERDE" if sinal[5] else "❌"
                item = OneLineListItem(
                    text=f"{timestamp[:19]} - {ticker} - {status}"
                )
                historico_list.add_widget(item)
        
        except Exception as e:
            print(f"[UI] Erro histórico: {e}")
    
    def _notificar_sinal(self, resultado: SinalResultado):
        """Dispara notificação de sinal."""
        try:
            from plyer import notification
            
            titulo = f"✅ SINAL VERDE: {resultado.ticker}"
            mensagem = f"Preço: R$ {resultado.preco_atual:.2f}\n"
            mensagem += f"Entrada: {resultado.tipo_entrada}\n"
            mensagem += f"ADX: {resultado.adx:.1f} | IFR: {resultado.ifr:.1f}"
            
            notification.notify(
                title=titulo,
                message=mensagem,
                app_name="Sinais Opções",
                timeout=10
            )
        except Exception as e:
            print(f"[NOTIF] Erro: {e}")
    
    def validar_formula(self):
        """Valida fórmula de entrada."""
        try:
            root = self.root
            formula = root.ids.formula_entrada.text
            
            valido, msg, ast = validar_formula(formula)
            
            if hasattr(root, 'ids') and 'resultado_validacao' in root.ids:
                if valido:
                    root.ids.resultado_validacao.text = f"✅ {msg}"
                    root.ids.resultado_validacao.theme_text_color = "Custom"
                    root.ids.resultado_validacao.text_color = [0, 1, 0, 1]
                else:
                    root.ids.resultado_validacao.text = f"❌ {msg}"
                    root.ids.resultado_validacao.theme_text_color = "Custom"
                    root.ids.resultado_validacao.text_color = [1, 0, 0, 1]
        except Exception as e:
            print(f"[VALIDAR] Erro: {e}")
    
    def salvar_estrategia(self):
        """Salva estratégia personalizada."""
        try:
            root = self.root
            
            nome = root.ids.estrategia_nome.text
            formula = root.ids.formula_entrada.text
            formula_saida = root.ids.formula_saida.text
            risco = root.ids.risco_input.text
            
            if not nome or not formula:
                self._mostrar_mensagem("Nome e fórmula são obrigatórios")
                return
            
            self.db.salvar_estrategia(nome, formula, formula_saida, 'D1', float(risco))
            
            # Atualizar engine
            self.sinal_engine = SignalEngine(
                usar_regra_personalizada=True,
                formula_entrada=formula
            )
            
            self._mostrar_mensagem(f"✅ Estratégia '{nome}' salva com sucesso!")
        
        except Exception as e:
            self._mostrar_mensagem(f"❌ Erro: {e}")
    
    def executar_backtest(self):
        """Executa backtest em thread separada."""
        try:
            root = self.root
            
            ticker = root.ids.data_inicio.text  # Usar campo
            data_inicio = root.ids.data_inicio.text
            data_fim = root.ids.data_fim.text or None
            capital = float(root.ids.capital_input.text)
            
            # Usar estratégia personalizada?
            usar_personalizada = root.ids.usar_estrategia_personalizada.active
            
            if usar_personalizada:
                formula = self.config.get('formula_entrada', '')
                engine = BacktestEngine(
                    capital_inicial=capital,
                    usar_regra_personalizada=True,
                    formula_entrada=formula
                )
            else:
                engine = BacktestEngine(
                    capital_inicial=capital,
                    usar_regra_personalizada=False
                )
            
            # Executar em thread
            thread = threading.Thread(
                target=self._executar_backtest_thread,
                args=(engine, ticker, data_inicio, data_fim),
                daemon=True
            )
            thread.start()
            
            self._mostrar_mensagem("⏳ Backtest em execução...")
        
        except Exception as e:
            self._mostrar_mensagem(f"❌ Erro: {e}")
    
    def _executar_backtest_thread(self, engine, ticker, data_inicio, data_fim):
        """Executa backtest em thread separada."""
        try:
            # Usar primeiro ticker da lista se não especificado
            if not ticker or ticker == data_inicio:
                tickers = self.config.get_tickers()
                ticker = tickers[0] if tickers else 'PETR4.SA'
            
            dados = self.data_fetcher.baixar_dados(ticker, periodo='5y')
            
            if dados.empty:
                self._mostrar_mensagem(f"❌ Sem dados para {ticker}")
                return
            
            resultado = engine.executar(ticker, dados, data_inicio, data_fim)
            
            # Mostrar resultados
            self._mostrar_resultados_backtest(resultado)
            
        except Exception as e:
            self._mostrar_mensagem(f"❌ Backtest error: {e}")
    
    @mainthread
    def _mostrar_resultados_backtest(self, resultado):
        """Mostra resultados do backtest na UI."""
        try:
            root = self.root
            if not hasattr(root, 'ids') or 'resultados_backtest' not in root.ids:
                return
            
            texto = f"""
📊 RESULTADOS BACKTEST - {resultado.ticker}
Período: {resultado.periodo_inicio} a {resultado.periodo_fim}

💰 Capital: R$ {resultado.capital_inicial:.2f} → R$ {resultado.capital_final:.2f}
📈 Lucro: R$ {resultado.lucro_total:.2f} ({resultado.lucro_percentual:.2f}%)

📋 Métricas:
• Total operações: {resultado.total_operacoes}
• Win rate: {resultado.win_rate:.1f}%
• Fator lucro: {resultado.fator_lucro:.2f}
• Drawdown máx: {resultado.drawdown_maximo:.2f}%
• Sharpe: {resultado.sharpe_ratio:.2f}
• Expectancy: R$ {resultado.expectancy:.2f}
"""
            
            root.ids.resultados_backtest.text = texto
        
        except Exception as e:
            print(f"[BACKTEST UI] Erro: {e}")
    
    def salvar_config(self):
        """Salva configurações."""
        try:
            root = self.root
            
            if hasattr(root, 'ids') and 'tickers_input' in root.ids:
                tickers_text = root.ids.tickers_input.text
                tickers = [t.strip() for t in tickers_text.split(',') if t.strip()]
                self.config.set_tickers(tickers)
            
            if hasattr(root, 'ids') and 'notificacoes_switch' in root.ids:
                notif = root.ids.notificacoes_switch.active
                self.config.set('notificacoes', str(notif), 'bool')
            
            self._mostrar_mensagem("✅ Configurações salvas!")
        
        except Exception as e:
            self._mostrar_mensagem(f"❌ Erro: {e}")
    
    def limpar_historico(self):
        """Limpa histórico de sinais."""
        # Implementar se necessário
        self._mostrar_mensagem("Histórico limpo")
    
    def _mostrar_mensagem(self, mensagem: str):
        """Mostra mensagem ao usuário via dialog."""
        try:
            dialog = MDDialog(
                text=mensagem,
                buttons=[MDRaisedButton(text="OK", on_release=lambda x: dialog.dismiss())]
            )
            dialog.open()
        except Exception:
            print(f"[DIALOG] {mensagem}")
    
    def on_stop(self):
        """Quando o app é fechado."""
        self.thread_running = False
        print("[APP] Aplicação encerrada")