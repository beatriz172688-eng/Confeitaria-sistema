import sqlite3
import os
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

def conectar():
    return sqlite3.connect("confeitaria.db")

def inicializar_banco():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS configuracoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_loja TEXT NOT NULL,
        telefone TEXT,
        endereco TEXT,
        mensagem_rodape TEXT
    );

    CREATE TABLE IF NOT EXISTS ingredientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        unidade TEXT NOT NULL,
        preco_embalagem REAL NOT NULL,
        qtd_embalagem REAL NOT NULL
    );

    CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ingrediente_id INTEGER,
        quantidade_atual REAL NOT NULL,
        estoque_minimo REAL NOT NULL DEFAULT 50.0,
        FOREIGN KEY(ingrediente_id) REFERENCES ingredientes(id)
    );

    CREATE TABLE IF NOT EXISTS receitas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        rendimento_porcoes INTEGER NOT NULL,
        foto_url TEXT
    );

    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        telefone TEXT NOT NULL,
        endereco TEXT,
        data_nascimento TEXT
    );

    CREATE TABLE IF NOT EXISTS contas_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_nome TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor_total REAL NOT NULL,
        data_venda TEXT NOT NULL,
        data_vencimento TEXT NOT NULL,
        status TEXT DEFAULT 'PENDENTE'
    );

    CREATE TABLE IF NOT EXISTS agenda_encomendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_nome TEXT NOT NULL,
        produto TEXT NOT NULL,
        data_entrega TEXT NOT NULL,
        valor_total REAL NOT NULL,
        valor_sinal REAL NOT NULL,
        status TEXT DEFAULT 'AGUARDANDO'
    );
    """)
    
    cursor.execute("SELECT COUNT(*) FROM configuracoes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO configuracoes (nome_loja, telefone, endereco, mensagem_rodape)
        VALUES ('SweetGestão Confeitaria', '(21) 99999-9999', 'Queimados - RJ', 'Obrigado pela preferência!')
        """)
    conexao.commit()
    conexao.close()

def obter_config():
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT nome_loja, telefone, endereco FROM configuracoes LIMIT 1")
    res = cursor.fetchone()
    conexao.close()
    return res if res else ("SweetGestão", "(21) 99999-9999", "Queimados - RJ")

# HTML Template Completo com todas as abas e campo de foto
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ nome_loja }} - Sistema de Confeitaria</title>
    <style>
        :root { --primary: #d63384; --primary-light: #f8d7da; --dark: #343a40; --light: #f8f9fa; --success: #198754; --warning: #ffc107; --danger: #dc3545; }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        body { background-color: #fdf2f4; color: var(--dark); display: flex; height: 100vh; overflow: hidden; }
        aside { width: 265px; background-color: white; border-right: 1px solid #dee2e6; display: flex; flex-direction: column; }
        .logo { padding: 20px; background-color: var(--primary); color: white; text-align: center; font-size: 1.2rem; font-weight: bold; }
        .menu { list-style: none; padding: 15px; overflow-y: auto; flex: 1; }
        .menu li { padding: 12px 15px; margin-bottom: 8px; border-radius: 8px; cursor: pointer; transition: 0.2s; font-weight: 500; color: #555; }
        .menu li:hover, .menu li.active { background-color: var(--primary-light); color: var(--primary); }
        main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
        header { padding: 20px 30px; background-color: white; border-bottom: 1px solid #dee2e6; display: flex; justify-content: space-between; align-items: center; }
        header h1 { font-size: 1.5rem; color: var(--primary); }
        .content { padding: 30px; overflow-y: auto; flex: 1; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border-left: 5px solid var(--primary); }
        .card h3 { font-size: 0.9rem; color: #777; margin-bottom: 8px; }
        .card .value { font-size: 1.6rem; font-weight: bold; color: var(--dark); }
        .table-container { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-bottom: 25px; }
        .table-container h2 { font-size: 1.1rem; margin-bottom: 15px; color: var(--dark); display: flex; justify-content: space-between; align-items: center; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th, td { padding: 12px 15px; border-bottom: 1px solid #dee2e6; font-size: 0.95rem; }
        th { background-color: #f8f9fa; color: #495057; }
        .btn { background-color: var(--primary); color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-weight: 600; text-decoration: none; display: inline-block; }
        .btn:hover { opacity: 0.9; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 15px; }
        .form-group label { display: block; font-size: 0.85rem; margin-bottom: 5px; font-weight: 600; color: #555; }
        .form-group input { width: 100%; padding: 10px; border: 1px solid #ced4da; border-radius: 6px; font-size: 0.95rem; }
        .section-view { display: none; }
        .section-view.active { display: block; }
        .badge { padding: 5px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; }
        .badge-success { background-color: #d1e7dd; color: #0f5132; }
        .badge-warning { background-color: #fff3cd; color: #664d03; }
        .recipe-img { width: 50px; height: 50px; object-fit: cover; border-radius: 6px; border: 1px solid #dee2e6; }
    </style>
</head>
<body>
    <aside>
        <div class="logo">🧁 {{ nome_loja }}</div>
        <ul class="menu">
            <li class="active" onclick="mudarAba('dashboard', this)">📊 Dashboard Executivo</li>
            <li onclick="mudarAba('estoque', this)">📦 Estoque e Insumos</li>
            <li onclick="mudarAba('receitas', this)">📖 Fichas Técnicas & Preços</li>
            <li onclick="mudarAba('encomendas', this)">🎉 Agenda de Encomendas</li>
            <li onclick="mudarAba('clientes', this)">👥 Gestão de Clientes</li>
            <li onclick="mudarAba('financeiro', this)">💰 Caixa & Crediário (15d)</li>
            <li onclick="mudarAba('configuracoes', this)">⚙️ Configurações da Loja</li>
        </ul>
    </aside>
    <main>
        <header>
            <h1 id="titulo-pagina">Dashboard Executivo</h1>
            <span style="font-weight: 500; color: #666;">Painel Web Local</span>
        </header>
        <div class="content">
            <!-- DASHBOARD -->
            <div id="dashboard" class="section-view active">
                <div class="cards">
                    <div class="card">
                        <h3>Status do Sistema</h3>
                        <div class="value" style="color: green; font-size: 1.2rem;">🟢 Online & Conectado</div>
                    </div>
                </div>
                <div class="table-container">
                    <h2>Bem-vindo ao Sistema Web da {{ nome_loja }}</h2>
                    <p>Utilize o menu lateral para navegar entre todas as ferramentas operacionais da sua confeitaria.</p>
                </div>
            </div>

            <!-- ESTOQUE -->
            <div id="estoque" class="section-view">
                <div class="table-container">
                    <h2>Cadastrar Novo Insumo</h2>
                    <form action="/adicionar_ingrediente" method="POST">
                        <div class="form-grid">
                            <div class="form-group"><label>Nome do Ingrediente:</label><input type="text" name="nome" required></div>
                            <div class="form-group"><label>Unidade (ex: g, ml, un):</label><input type="text" name="unidade" required></div>
                            <div class="form-group"><label>Preço Embalagem (R$):</label><input type="number" step="0.01" name="preco" required></div>
                            <div class="form-group"><label>Qtd na Embalagem:</label><input type="number" step="0.01" name="qtd" required></div>
                        </div>
                        <button type="submit" class="btn">Salvar Insumo</button>
                    </form>
                </div>
            </div>

            <!-- RECEITAS & FOTOS -->
            <div id="receitas" class="section-view">
                <div class="table-container">
                    <h2>Fichas Técnicas & Fotos de Produtos</h2>
                    <form action="/adicionar_receita" method="POST">
                        <div class="form-grid">
                            <div class="form-group"><label>Nome da Receita / Produto:</label><input type="text" name="nome" required></div>
                            <div class="form-group"><label>Rendimento (Porções/Fatias):</label><input type="number" name="rendimento" required></div>
                            <div class="form-group" style="grid-column: span 2;"><label>Link da Foto (URL da Imagem):</label><input type="text" name="foto_url" placeholder="https://exemplo.com/foto-bolo.jpg"></div>
                        </div>
                        <button type="submit" class="btn">Cadastrar Receita com Foto</button>
                    </form>
                </div>
                <div class="table-container">
                    <h2>Receitas Cadastradas</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Foto</th>
                                <th>Produto</th>
                                <th>Rendimento</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for rec in receitas %}
                            <tr>
                                <td>
                                    {% if rec[3] %}
                                    <img src="{{ rec[3] }}" class="recipe-img" alt="Foto">
                                    {% else %}
                                    <span style="font-size: 0.8rem; color: #999;">Sem foto</span>
                                    {% endif %}
                                </td>
                                <td><strong>{{ rec[1] }}</strong></td>
                                <td>{{ rec[2] }} porções</td>
                            </tr>
                            {% else %}
                            <tr><td colspan="3" style="text-align: center; color: #777;">Nenhuma receita cadastrada ainda.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- ENCOMENDAS -->
            <div id="encomendas" class="section-view">
                <div class="table-container">
                    <h2>Agenda de Encomendas & Festas</h2>
                    <form action="/adicionar_encomenda" method="POST">
                        <div class="form-grid">
                            <div class="form-group"><label>Cliente:</label><input type="text" name="cliente" required></div>
                            <div class="form-group"><label>Produto:</label><input type="text" name="produto" required></div>
                            <div class="form-group"><label>Data Entrega:</label><input type="text" name="data" placeholder="DD/MM/AAAA" required></div>
                            <div class="form-group"><label>Valor Total (R$):</label><input type="number" step="0.01" name="total" required></div>
                            <div class="form-group"><label>Sinal Pago (R$):</label><input type="number" step="0.01" name="sinal" required></div>
                        </div>
                        <button type="submit" class="btn">Registrar Encomenda</button>
                    </form>
                </div>
            </div>

            <!-- CLIENTES -->
            <div id="clientes" class="section-view">
                <div class="table-container">
                    <h2>Cadastrar Cliente</h2>
                    <form action="/adicionar_cliente" method="POST">
                        <div class="form-grid">
                            <div class="form-group"><label>Nome Completo:</label><input type="text" name="nome" required></div>
                            <div class="form-group"><label>WhatsApp:</label><input type="text" name="telefone" required></div>
                            <div class="form-group"><label>Endereço / Bairro:</label><input type="text" name="endereco"></div>
                            <div class="form-group"><label>Aniversário (DD/MM):</label><input type="text" name="nascimento"></div>
                        </div>
                        <button type="submit" class="btn">Cadastrar Cliente</button>
                    </form>
                </div>
            </div>

            <!-- FINANCEIRO -->
            <div id="financeiro" class="section-view">
                <div class="table-container">
                    <h2>Contas a Receber (Crediário / Fiado 15d)</h2>
                    <p style="color: #666; font-size: 0.9rem;">Gerencie as vendas a prazo com vencimento configurado para 15 dias.</p>
                </div>
            </div>

            <!-- CONFIGURAÇÕES -->
            <div id="configuracoes" class="section-view">
                <div class="table-container">
                    <h2>Configurações do Estabelecimento</h2>
                    <form action="/salvar_config" method="POST">
                        <div class="form-grid">
                            <div class="form-group"><label>Nome da Confeitaria:</label><input type="text" name="nome_loja" value="{{ nome_loja }}" required></div>
                            <div class="form-group"><label>Telefone:</label><input type="text" name="telefone" value="{{ telefone }}"></div>
                            <div class="form-group"><label>Endereço:</label><input type="text" name="endereco" value="{{ endereco }}"></div>
                        </div>
                        <button type="submit" class="btn">Atualizar Configurações</button>
                    </form>
                </div>
            </div>
        </div>
    </main>
    <script>
        function mudarAba(idAba, elementoLi) {
            document.querySelectorAll('.section-view').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.menu li').forEach(el => el.classList.remove('active'));
            document.getElementById(idAba).classList.add('active');
            elementoLi.classList.add('active');
            const titulos = {
                'dashboard': 'Dashboard Executivo',
                'estoque': 'Controle de Estoque e Insumos',
                'receitas': 'Fichas Técnicas & Preços',
                'encomendas': 'Agenda de Encomendas & Festas',
                'clientes': 'Gestão de Clientes',
                'financeiro': 'Caixa & Crediário (15d)',
                'configuracoes': 'Configurações da Loja'
            };
            document.getElementById('titulo-pagina').innerText = titulos[idAba];
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    nome_loja, telefone, endereco = obter_config()
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("SELECT id, nome, rendimento_porcoes, foto_url FROM receitas")
    receitas = cursor.fetchall()
    conexao.close()
    return render_template_string(HTML_TEMPLATE, nome_loja=nome_loja, telefone=telefone, endereco=endereco, receitas=receitas)

@app.route("/salvar_config", methods=["POST"])
def salvar_config():
    novo_nome = request.form.get("nome_loja")
    novo_tel = request.form.get("telefone")
    novo_end = request.form.get("endereco")
    
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM configuracoes")
    cursor.execute("INSERT INTO configuracoes (nome_loja, telefone, endereco, mensagem_rodape) VALUES (?, ?, ?, ?)", (novo_nome, novo_tel, novo_end, "Obrigado!"))
    conexao.commit()
    conexao.close()
    return redirect(url_for('index'))

@app.route("/adicionar_ingrediente", methods=["POST"])
def adicionar_ingrediente():
    nome = request.form.get("nome")
    unidade = request.form.get("unidade")
    preco = float(request.form.get("preco"))
    qtd = float(request.form.get("qtd"))
    
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO ingredientes (nome, unidade, preco_embalagem, qtd_embalagem) VALUES (?, ?, ?, ?)", (nome, unidade, preco, qtd))
    ing_id = cursor.lastrowid
    cursor.execute("INSERT INTO estoque (ingrediente_id, quantidade_atual, estoque_minimo) VALUES (?, ?, ?)", (ing_id, qtd, qtd * 0.2))
    conexao.commit()
    conexao.close()
    return redirect(url_for('index'))

@app.route("/adicionar_receita", methods=["POST"])
def adicionar_receita():
    nome = request.form.get("nome")
    rendimento = int(request.form.get("rendimento"))
    foto_url = request.form.get("foto_url")
    
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO receitas (nome, rendimento_porcoes, foto_url) VALUES (?, ?, ?)", (nome, rendimento, foto_url))
    conexao.commit()
    conexao.close()
    return redirect(url_for('index'))

@app.route("/adicionar_cliente", methods=["POST"])
def adicionar_cliente():
    nome = request.form.get("nome")
    tel = request.form.get("telefone")
    end = request.form.get("endereco")
    nasc = request.form.get("nascimento")
    
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO clientes (nome, telefone, endereco, data_nascimento) VALUES (?, ?, ?, ?)", (nome, tel, end, nasc))
    conexao.commit()
    conexao.close()
    return redirect(url_for('index'))

@app.route("/adicionar_encomenda", methods=["POST"])
def adicionar_encomenda():
    cliente = request.form.get("cliente")
    produto = request.form.get("produto")
    data = request.form.get("data")
    total = float(request.form.get("total"))
    sinal = float(request.form.get("sinal"))
    
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("INSERT INTO agenda_encomendas (cliente_nome, produto, data_entrega, valor_total, valor_sinal) VALUES (?, ?, ?, ?, ?)", (cliente, produto, data, total, sinal))
    conexao.commit()
    conexao.close()
    return redirect(url_for('index'))

import os

if __name__ == "__main__":
    inicializar_banco()
    # Pega a porta fornecida pela nuvem ou usa a porta 5000 se estiver no seu PC
    porta = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 Servidor web iniciado na porta {porta}!")
    app.run(host="0.0.0.0", port=porta, debug=False)