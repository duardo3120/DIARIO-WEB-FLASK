# 📝 Projeto Diário Web em Flask

Este é um projeto de um diário web simples, desenvolvido em Python usando o framework Flask. O foco principal é um sistema de autenticação e sessão de usuários completo e seguro, construído do zero.

---

## 🚀 Funcionalidades

* **Registro de Novos Usuários:** Permite que novos usuários criem uma conta.
* **Login de Usuários:** Autenticação de usuários existentes.
* **Armazenamento Seguro de Senhas:** As senhas são "hasheadas" (usando `werkzeug.security`) antes de serem salvas no banco de dados.
* **Gestão de Sessão:** "Lembra" o usuário que fez login (usando `Flask-Login`).
* **Rotas Protegidas:** A página `/dashboard` só pode ser acessada por usuários autenticados.
* **Funcionalidade de Logout:** Permite que o usuário encerre sua sessão com segurança.
* **Banco de Dados:** Usa SQLite e `Flask-SQLAlchemy` para gerenciar os dados dos usuários.

---

## 🛠️ Tecnologias Utilizadas

* **Python 3**
* **Flask** (Framework web principal)
* **Flask-SQLAlchemy** (ORM para interagir com o banco de dados)
* **Flask-Login** (Gerenciamento de sessão de usuário)
* **python-dotenv** (Para carregar variáveis de ambiente)
* **SQLite** (Banco de dados)
* **HTML** (Estrutura das páginas)

---

## ⚙️ Como Executar o Projeto

Siga estes passos para rodar o projeto localmente:

1.  **Clone o repositório:**
    ```bash
    git clone [URL-DO-SEU-REPOSITORIO-AQUI]
    cd [NOME-DA-PASTA-DO-PROJETO]
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Criar o ambiente
    python -m venv venv
    
    # Ativar (Windows PowerShell)
    .\venv\Scripts\Activate
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure as Variáveis de Ambiente:**
    * Crie um arquivo chamado `.env` na raiz do projeto.
    * Adicione sua chave secreta dentro dele:
    ```text
    SECRET_KEY='sua-chave-secreta-aleatoria-e-longa-aqui'
    ```

5.  **Crie o Banco de Dados:**
    * Execute o shell interativo do Flask:
    ```bash
    flask --app app shell
    ```
    * Dentro do shell, digite os seguintes comandos para criar as tabelas e seu primeiro usuário "admin" (senha: "123"):
    ```python
    from app import db, User, generate_password_hash
    
    # Cria as tabelas
    db.create_all()
    
    # Cria o hash da senha
    hash_admin = generate_password_hash('123')
    
    # Cria o usuário admin
    admin = User(username='admin', password_hash=hash_admin)
    
    # Salva no banco
    db.session.add(admin)
    db.session.commit()
    
    # Saia do shell
    exit()
    ```

6.  **Execute a Aplicação:**
    ```bash
    flask --app app run --debug
    ```

7.  **Acesse no navegador:**
    Abra `http://127.0.0.1:5000/` no seu navegador.