#!/bin/bash
# Script de configuração automática para build do APK
# Execute dentro do WSL Ubuntu após: chmod +x setup_wsl.sh && ./setup_wsl.sh

echo "=========================================="
echo "  📱 Setup APK - Sinais Opções B3"
echo "=========================================="
echo ""

# Configurar locale
sudo locale-gen pt_BR.UTF-8

# Atualizar pacotes
echo "🔄 Atualizando pacotes..."
sudo apt update -qq && sudo apt upgrade -y -qq

# Instalar dependências
echo "📦 Instalando dependências..."
sudo apt install -y -qq \
    python3-pip \
    python3-dev \
    python3-virtualenv \
    libssl-dev \
    libffi-dev \
    build-essential \
    libltdl-dev \
    libncurses5 \
    libncurses5-dev \
    curl \
    git \
    unzip \
    wget \
    zip \
    openjdk-17-jdk \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev

# Instalar Buildozer e Cython
echo "🐍 Instalando Buildozer..."
pip3 install --quiet --upgrade pip
pip3 install --quiet buildozer cython 2>&1 | tail -3

# Navegar para o diretório do projeto
echo "📁 Acessando o projeto..."
cd /mnt/c/Users/Usuário/sinais-opcoes

# Verificar arquivos
echo ""
echo "✅ Arquivos do projeto:"
ls -la *.py *.spec *.txt requirements.txt 2>/dev/null
echo ""

# Iniciar build
echo "🚀 INICIANDO BUILD DO APK..."
echo "   Isso pode levar de 30 a 60 minutos."
echo "   O APK será gerado em: bin/"
echo ""

# Executar build
buildozer android debug 2>&1 | tee build_log.txt

# Verificar resultado
echo ""
echo "=========================================="
if ls -la bin/*.apk 2>/dev/null; then
    echo "✅ APK GERADO COM SUCESSO!"
    echo "   Arquivo: bin/*.apk"
    echo ""
    echo "   Para copiar para o Windows:"
    echo "   cp bin/*.apk /mnt/c/Users/Usuário/Desktop/"
else
    echo "❌ ERRO: APK não foi gerado."
    echo "   Verifique o arquivo build_log.txt"
fi
echo "=========================================="