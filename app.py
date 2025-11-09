from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
#NOVO UPDATE
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user


# Cria a aplicação web
app = Flask(__name__)

#Configura a chave secreta para sessões e flash messages
app.config['SECRET_KEY'] = '' #Chave secreta para sessões escolhidas por mim

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diario.db' #Configuração do banco de dados SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #Desativa o rastreamento de modificações para economizar recursos
db = SQLAlchemy(app) #Inicializa o banco de dados com a aplicação Flask

# NOVO - INICIALIZAÇÃO DO GER5ENCIAOR DE LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

#NOVO - CONFIGURAÇÕES DO FLASK-LOGIN
#Informar qual a pagina de login
login_manager.login_view = 'index'

#Caso tentar acessar pagina protegida
login_manager.login_message = "Não autorizado"
login_manager.login_message_category = "error"

#NOVO - Função User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) #Convertendo id string para int

#MODIFICADO - Alterações para realizar autenticação e herdar aos usuários com UserMixin
class User(db.Model, UserMixin): #Cria a tabela de usuários no banco de dados, adicionado UserMixin para autenticação
    id = db.Column(db.Integer, primary_key=True) #ID do usuário
    username = db.Column(db.String(80), unique=True, nullable=False) #Nome do usuário
    password_hash = db.Column(db.String(128), nullable=False) #Senha do usuário (armazenada como hash) -- sempre salvar a senha em hash

    def __repr__(self):
        return f'<User {self.username}>'


# Cria a primeira pagina
@app.route('/')
def index():
    return render_template('index.html') # Renderiza o arquivo index.html e sobe para o servidor.

#MODIFICADO - ROTA PROTEGIDA COM LOGIN REQUIRED
#Rota do dashboard (get) - pagina de sucesso pos login
@app.route('/dashboard')
@login_required #novo - Nosso guarda para a rota
def dashboard():
    return (
        f"<h1>Bem-vindo, {current_user.username}!</h1>" #Usa current_user para pegar o usuário logado
        f"<p>Login foi um sucesso.</p>"
        f"<p><a href='{url_for('logout')}'>Sair (Logout)</a></p>" # Link para logout
    )

# MODIFICADO - A rota lembra o usuário
@app.route('/login', methods=['POST']) #Rota para o login com metodo post
def login():

    #Obtém dados do formulário
    usuario = request.form['username'] #Baseado no name do input
    senha = request.form['password'] #Baseado no name do input

    user = User.query.filter_by(username=usuario).first() #Consulta o banco de dados para achar o usuário

    if user and check_password_hash(user.password_hash, senha): #Verifica se o usuário existe e se a senha está correta
        login_user(user) #NOVO  O FLASK lembra dele 
        # Login bem-sucedido
        return redirect(url_for('dashboard')) #Redireciona para o dashboard
    else:
        # Login falhou
        flash('Nome de usuário ou senha incorretos.', 'error') #Mensagem de erro
        return redirect(url_for('index')) #Redireciona de volta para a página inicial

#NOVO - ROTA DE LOGOUT    
@app.route('/logout') #Rota para logout
@login_required #Protege a rota de logout
def logout():
    logout_user() #NOVO - Desloga o usuário
    flash('Você saiu com sucesso.', 'success') #Mensagem de sucesso
    return redirect(url_for('index')) #Redireciona para a página inicial
    
@app.route('/register') #Rota para a página de registro (get)
def mostra_register():
    return render_template('register.html') # Renderiza o arquivo register.html

@app.route('/register', methods=['POST']) #Rota para o registro com metodo post
def register():
    #Obtém dados do formulário
    usuario = request.form['username'] #Baseado no name do input
    senha = request.form['password'] #Baseado no name do input
    confirm_password = request.form['confirm_password'] #Baseado no name do input

    if senha != confirm_password:
        flash('As senhas não coincidem.', 'error')
        return redirect(url_for('mostra_register')) #Redireciona de volta para a página de registro
    
    user_exists = User.query.filter_by(username=usuario).first() #Verifica se o usuário já existe
    if user_exists:
        flash('Nome de usuário já existe. Escolha outro.', 'error')
        return redirect(url_for('mostra_register')) #Redireciona de volta para a página de registro
    
    password_hash = generate_password_hash(senha)    #Gera o hash da senha

    new_user = User(username=usuario, password_hash=password_hash) #Cria um novo usuário

    db.session.add(new_user) #Adiciona o novo usuário à sessão do banco de dados
    db.session.commit() #Salva as alterações no banco de dados

    flash('Conta criada com sucesso! Você já pode fazer login.', 'success')
    return redirect(url_for('index'))
    
if __name__ == '__main__':
    app.run(debug=True)