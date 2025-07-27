#!/bin/bash

# Install script para XadrezPython no CODDUO
# Autor: CODDUO Team
# Versão: 1.0

echo "======================================"
echo "  CODDUO - Instalador XadrezPython"
echo "======================================"
echo

# Verificar se está executando como root/sudo
if [[ $EUID -eq 0 ]]; then
   echo "⚠️  AVISO: Este script não deve ser executado como root!"
   echo "Execute sem sudo: ./install.sh"
   exit 1
fi

# Função para verificar dependências
check_dependencies() {
    echo "🔍 Verificando dependências..."
    
    # Verificar Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python3 não encontrado!"
        echo "Instalando Python3..."
        sudo pacman -S python --noconfirm
    else
        echo "✅ Python3 encontrado: $(python3 --version)"
    fi
    
    # Verificar pip
    if ! command -v pip3 &> /dev/null; then
        echo "❌ pip3 não encontrado!"
        echo "Instalando pip..."
        sudo pacman -S python-pip --noconfirm
    else
        echo "✅ pip3 encontrado"
    fi
    
    # Verificar pygame via pacman (recomendado no Arch Linux)
    if ! pacman -Qi python-pygame &> /dev/null; then
        echo "📦 Instalando pygame via pacman..."
        sudo pacman -S python-pygame --noconfirm
        if [ $? -eq 0 ]; then
            echo "✅ pygame instalado via pacman"
        else
            echo "⚠️  Falha na instalação via pacman, tentando via pip..."
            pip3 install pygame==2.1.2 --user
        fi
    else
        echo "✅ pygame já está instalado via pacman"
    fi
    
    echo
}

# Função para configurar o ambiente
setup_environment() {
    echo "⚙️  Configurando ambiente..."
    
    # Criar diretório de aplicações se não existir
    APPS_DIR="/opt/codduo/apps"
    if [ ! -d "$APPS_DIR" ]; then
        echo "📁 Criando diretório de aplicações CODDUO..."
        sudo mkdir -p "$APPS_DIR"
        sudo chown $USER:$USER "$APPS_DIR"
    fi
    
    # Criar diretório específico para XadrezPython
    XADREZ_DIR="$APPS_DIR/XadrezPython"
    if [ ! -d "$XADREZ_DIR" ]; then
        echo "📁 Criando diretório para XadrezPython..."
        mkdir -p "$XADREZ_DIR"
    fi
    
    echo "✅ Ambiente configurado"
    echo
}

# Função para copiar arquivos
install_files() {
    echo "📋 Instalando arquivos do XadrezPython..."
    
    XADREZ_DIR="/opt/codduo/apps/XadrezPython"
    
    # Copiar arquivos principais
    cp -r chess/ "$XADREZ_DIR/"
    cp -r images1/ "$XADREZ_DIR/"
    cp -r sounds/ "$XADREZ_DIR/"
    cp config.json "$XADREZ_DIR/"
    cp requirements.txt "$XADREZ_DIR/"
    cp Logo.png "$XADREZ_DIR/" 2>/dev/null || echo "⚠️  Logo.png não encontrado (opcional)"
    cp install.sh "$XADREZ_DIR/"
    
    # Criar arquivo principal de inicialização
    cat > "$XADREZ_DIR/xadrez.py" << 'EOF'
#!/usr/bin/env python3
"""
CODDUO - XadrezPython
Jogo de Xadrez integrado ao sistema CODDUO
"""

import os
import sys

# Adicionar diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mudar para o diretório do jogo
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Importar e executar o jogo
from chess import main

if __name__ == "__main__":
    main.main()
EOF
    
    # Tornar executável
    chmod +x "$XADREZ_DIR/xadrez.py"
    
    echo "✅ Arquivos instalados em $XADREZ_DIR"
    echo
}

# Função para criar launcher
create_launcher() {
    echo "🚀 Criando launcher para CODDUO..."
    
    # Criar arquivo de configuração para o CODDUO
    cat > "/opt/codduo/apps/XadrezPython/codduo-app.json" << EOF
{
    "name": "XadrezPython",
    "version": "2.0",
    "description": "Jogo de Xadrez desenvolvido em Python com Pygame",
    "author": "CODDUO Team",
    "category": "games",
    "executable": "xadrez.py",
    "icon": "Logo.png",
    "requirements": {
        "python": ">=3.8",
        "pygame": ">=2.1.0"
    },
    "window": {
        "resizable": true,
        "min_width": 800,
        "min_height": 600
    },
    "features": [
        "Jogo de xadrez completo",
        "Interface gráfica elegante",
        "Sistema de timer configurável",
        "Rotação automática do tabuleiro",
        "Animações suaves",
        "Histórico de peças capturadas"
    ]
}
EOF
    
    # Criar script de execução para PATH
    sudo cat > "/usr/local/bin/xadrez" << 'EOF'
#!/bin/bash
cd /opt/codduo/apps/XadrezPython
python3 xadrez.py "$@"
EOF
    
    sudo chmod +x "/usr/local/bin/xadrez"
    
    echo "✅ Launcher criado (execute 'xadrez' de qualquer lugar)"
    echo
}

# Função para verificar instalação
verify_installation() {
    echo "🔍 Verificando instalação..."
    
    XADREZ_DIR="/opt/codduo/apps/XadrezPython"
    
    if [ -f "$XADREZ_DIR/xadrez.py" ] && [ -f "$XADREZ_DIR/codduo-app.json" ]; then
        echo "✅ XadrezPython instalado com sucesso!"
        echo
        echo "📍 Localização: $XADREZ_DIR"
        echo "🎮 Para jogar, execute: xadrez"
        echo "📁 Ou navegue até: $XADREZ_DIR"
        echo
        echo "🎯 Recursos disponíveis:"
        echo "   • Jogo de xadrez completo"
        echo "   • Interface moderna e elegante"
        echo "   • Timer configurável"
        echo "   • Rotação automática do tabuleiro"
        echo "   • Animações e efeitos sonoros"
        echo
    else
        echo "❌ Falha na instalação!"
        exit 1
    fi
}

# Função principal
main() {
    echo "🏁 Iniciando instalação do XadrezPython para CODDUO..."
    echo
    
    # Verificar se estamos no diretório correto
    if [ ! -f "chess/main.py" ]; then
        echo "❌ Erro: Execute este script no diretório do XadrezPython!"
        echo "Certifique-se de que os arquivos chess/main.py existem."
        exit 1
    fi
    
    check_dependencies
    setup_environment
    install_files
    create_launcher
    verify_installation
    
    echo "🎉 Instalação concluída com sucesso!"
    echo "🎮 Digite 'xadrez' para começar a jogar!"
    echo
}

# Executar instalação
main