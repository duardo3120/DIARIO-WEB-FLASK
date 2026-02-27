# 📒 Chronicle Clone - Diário Web com Flask

Um aplicativo de diário pessoal completo, seguro e com design moderno, desenvolvido em Python e Flask.

![Status do Projeto](https://img.shields.io/badge/Status-Concluído-green)

## ✨ Funcionalidades

* **🔐 Autenticação Completa:** Registro, Login e Logout seguros com hash de senhas.
* **📝 CRUD de Postagens:** Criar, Ler, Editar e Apagar entradas do diário.
* **🎨 Interface Moderna:** Design responsivo inspirado no estilo "Chronicle", usando CSS Grid e Flexbox.
* **🛡️ Segurança:** Proteção de rotas (apenas usuários logados acessam o painel) e validação de autoria (usuários só editam seus próprios posts).
* **📅 Formatação de Dados:** Datas e horários ajustados para leitura humana.

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-Login.
* **Frontend:** HTML5, CSS3 (Grid/Flexbox), Jinja2 Templates.
* **Banco de Dados:** SQLite.

## 🚀 Como Rodar o Projeto

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/SeuUsuario/DIARIO-WEB-FLASK.git](https://github.com/SeuUsuario/DIARIO-WEB-FLASK.git)
    cd DIARIO-WEB-FLASK
    ```

2.  **Crie e ative o ambiente virtual:**
    ```bash
    python -m venv venv
    .\venv\Scripts\Activate  # No Windows
    ```

3.  **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure o ambiente:**
    * Crie um arquivo `.env` na raiz.
    * Adicione: `SECRET_KEY='sua-chave-secreta-aqui'`

5.  **Inicialize o Banco de Dados:**
    ```bash
    flask --app app shell
    >>> from app import db
    >>> db.create_all()
    >>> exit()
    ```

6.  **Execute:**
    ```bash
    flask --app app run --debug
    ```
    Acesse `http://127.0.0.1:5000` no seu navegador.

---
Desenvolvido por Eduardo (Duardo)
