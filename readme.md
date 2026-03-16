# ⏳ Chronos - Diário Web

Um aplicativo web de diário digital construído em Python com Flask. O Chronos permite que os usuários guardem memórias, organizem pensamentos por tags e revivam momentos do passado através de um sistema inteligente de "lembranças".

## 🚀 Funcionalidades

* **Autenticação Segura:** Criação de conta, login e recuperação de senha com senhas criptografadas (hash).
* **Comunicação Integrada:** Envio de e-mails para ativação de conta e redefinição de senha utilizando a API do Brevo.
* **Privacidade de Dados:** Dashboard isolado, garantindo que cada usuário tenha acesso estrito apenas às suas próprias memórias.
* **Organização e Filtros:** Sistema de criação e edição de tags personalizadas para categorizar postagens.
* **Máquina do Tempo:** Destaque automático de postagens realizadas na mesma data em anos anteriores.

## 🛠️ Tecnologias Utilizadas

* **Back-end:** Python, Flask, Flask-Login
* **Banco de Dados:** SQLite gerenciado via SQLAlchemy
* **Front-end:** HTML, CSS, Jinja2
* **Integração de API:** `requests` para comunicação REST com o Brevo
* **Hospedagem / Deploy:** Render (com integração contínua via GitHub)

## 🧠 Desafios e Aprendizados

Durante a construção e o deploy deste projeto, solucionei problemas reais de ambiente de produção:
* **Infraestrutura e Redes:** Adaptação da arquitetura de envio de e-mails. Substituí o uso de portas SMTP tradicionais (bloqueadas no plano gratuito da nuvem) por requisições HTTP via API REST do Brevo.
* **Segurança da Informação:** Identificação e correção de um *Data Leak* (vazamento de dados) na visualização da timeline, ajustando as consultas do banco de dados para validar o `current_user.id` em todas as rotas.

## ⚙️ Como rodar o projeto localmente

1. **Clone este repositório:**
   ```bash
   git clone [https://github.com/duardo3120/DIARIO-WEB-FLASK.git](https://github.com/duardo3120/DIARIO-WEB-FLASK.git)
   cd DIARIO-WEB-FLASK

2. **Crie e ative um ambiente virtual**
python -m venv venv
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

3. **Instale as dependências**
pip install -r requirements.txt

4. **Configure as variaveis de ambiente**
SECRET_KEY=sua_chave_secreta_aqui
BREVO_API_KEY=sua_chave_api_do_brevo_aqui
EMAIL_USER=seu_email_cadastrado_no_brevo@gmail.com

5. **Executar a aplicação**
python app.py

