# 📊 Sinais Opções B3

Aplicativo para geração de sinais de compra de **opções CALL ATM** com análise técnica, 
suporte para **fórmulas matemáticas personalizadas**, **backtest de estratégias** e **notificações push**.

---

## 🚀 Funcionalidades

### 1. Motor de Fórmulas Matemáticas
Crie suas próprias regras de entrada usando uma linguagem simples:

| Variável | Descrição | Exemplo |
|---|---|---|
| `AC[N]` | Média do fechamento dos últimos N candles | `AC[10]` |
| `H[N]` | High do candle N (0 = atual) | `H[0]` |
| `L[N]` | Low do candle N | `L[5]` |
| `C[N]` | Close do candle N | `C[0]` |
| `HH[N]` | Maior máxima dos últimos N | `HH[20]` |
| `LL[N]` | Menor mínima dos últimos N | `LL[20]` |
| `MM[N]` | Média móvel de N períodos | `MM[20]` |
| `ADX` | ADX atual | `ADX > 25` |
| `IFR` | IFR/RSI atual | `IFR > 45 && IFR < 75` |
| `VOLMEAN[N]` | Volume médio N períodos | `VOLMEAN[20]` |
| `BODY` | Corpo do candle | `BODY` |
| `WICK` | Sombra do candle | `WICK` |
| `GAP` | Gap percentual | `GAP < 3` |
| `STD[N]` | Desvio padrão | `STD[20]` |
| `SHIFT[N]` | Deslocamento | `MM[20].SHIFT[5]` |

Exemplo de fórmula:
```
AC[10] > AC[20] && AC[20] > AC[30] && H[0] == HH[20] && IFR < 75 && IFR > 45
```

### 2. Estratégia Padrão (Filtros + Gatilhos)
- ✅ Preço > MM200, Preço > MM50
- ✅ MM20 > MM50, MM50 subindo
- ✅ ADX > 25, ADX subindo
- ✅ IFR entre 45 e 75
- ✅ Distância MM20 ≤ 8%
- ✅ Gatilho A: Pullback MM20
- ✅ Gatilho B: Rompimento de Topo

### 3. Backtest de Estratégia
Teste sua estratégia em dados históricos:
- ✅ Simulação de trades CALL ATM
- ✅ Win rate, fator de lucro, drawdown, Sharpe
- ✅ Configuração de saída (stop, parcial, total)
- ✅ Curva de capital

### 4. Notificações
- ✅ Notificações push quando sinal verde encontrado
- ✅ Monitoramento automático a cada 15 min
- ✅ Histórico de sinais

---

## 📦 Instalação

### Requisitos
- Python 3.10+
- WSL (Ubuntu) para build do APK

### Instalação Local

```bash
# Clonar o repositório
cd sinais-opcoes

# Instalar dependências
pip install -r requirements.txt

# Executar
python main.py
```

### Build APK (Android)

```bash
# No WSL/Ubuntu:
sudo apt update && sudo apt install -y buildozer
buildozer init
buildozer android debug
```

O APK será gerado em `bin/sinais_opcoes-1.0-*-debug.apk`

---

## 🎮 Como Usar

### 1. Tela de Sinais ao Vivo
- Mostra análise em tempo real dos ativos
- Botão Refresh para atualizar manualmente
- Switch para ativar/desativar monitoramento automático

### 2. Criar Estratégia
- Nomeie sua estratégia
- Escreva a fórmula de entrada
- Configure stop, realização parcial e saída total
- Valide a fórmula antes de salvar

### 3. Backtest
- Selecione a estratégia
- Defina período e capital
- Execute e veja métricas detalhadas

### 4. Configurações
- Adicione/remova ativos para monitorar
- Ative/desative notificações
- Configure intervalo de verificação

---

## 📁 Estrutura do Projeto

```
sinais-opcoes/
├── main.py                    # Ponto de entrada
├── requirements.txt           # Dependências
│
├── engine/                    # Motor de fórmulas
│   ├── tokenizer.py           # Tokenizador
│   ├── parser.py              # Parser → AST
│   ├── interpreter.py         # Avaliador
│   └── formula_validator.py   # Validador
│
├── analysis/                  # Análise técnica
│   ├── data_fetcher.py        # yfinance
│   ├── indicators.py          # Indicadores
│   ├── filters.py             # Filtros
│   ├── triggers.py            # Gatilhos
│   └── signal_engine.py       # Motor de sinais
│
├── backtest/                  # Backtest
│   ├── backtest_engine.py     # Motor
│   ├── trade_simulator.py     # Simulador
│   ├── option_pricing.py      # Black-Scholes
│   ├── metrics.py             # Métricas
│   └── report.py              # Relatórios
│
├── storage/                   # Persistência
│   ├── database.py            # SQLite
│   └── config_manager.py      # Configs
│
└── ui/                        # Interface
    ├── app.py                 # App KivyMD
    └── kv/sinais.kv           # Layout
```

---

## ⚙️ Personalização

### Exemplos de Fórmulas

**Pullback Personalizado:**
```
H[0] <= MM[20] * 1.01 && C[0] > MM[20] && C[0] > H[1] && V[0] >= VOLMEAN[20]
```

**Rompimento de Canal:**
```
C[0] >= HH[20] * 1.01 && V[0] >= VOLMEAN[20] * 1.2
```

**Estratégia de Tendência:**
```
AC[10] > AC[20] && AC[20] > AC[30] && H[0] == HH[20] && (H[0] - L[0]) < STD[20] * 0.5
```

**Suporte e Resistência:**
```
C[0] > MM[50] && L[0] >= LL[20] * 0.99 && V[0] > VOLMEAN[20] * 1.5
```

---

## 🛠 Tecnologias

- **Python 3.12** — Linguagem principal
- **KivyMD** — Interface Material Design
- **yfinance** — Dados financeiros
- **pandas_ta** — Indicadores técnicos
- **SQLite** — Banco de dados local
- **plyer** — Notificações nativas
- **Buildozer** — Build do APK Android
- **Black-Scholes** — Precificação de opções

---

## 📝 Licença

Este projeto é para fins educacionais. Use por sua conta e risco em operações reais.

---

## 👨‍💻 Autor

Desenvolvido sob demanda para análise de opções CALL ATM na B3.