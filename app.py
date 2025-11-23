from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os, datetime
from dotenv import load_dotenv
load_dotenv()


# Cria a aplicação web
app = Flask(__name__)

#Configura a chave secreta para sessões e flash messages
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') #Chave secreta para sessões escolhidas por mim

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diario.db' #Configuração do banco de dados SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #Desativa o rastreamento de modificações para economizar recursos
db = SQLAlchemy(app) #Inicializa o banco de dados com a aplicação Flask

#  - INICIALIZAÇÃO DO GERENCIADOR DE LOGIN
login_manager = LoginManager()
login_manager.init_app(app)

# - CONFIGURAÇÕES DO FLASK-LOGIN
#Informar qual a pagina de login
login_manager.login_view = 'index'

#Caso tentar acessar pagina protegida
login_manager.login_message = "Não autorizado"
login_manager.login_message_category = "error"

# Função User Loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) #Convertendo id string para int

 #Alterações para realizar autenticação e herdar aos usuários com UserMixin
class User(db.Model, UserMixin): #Cria a tabela de usuários no banco de dados, adicionado UserMixin para autenticação
    id = db.Column(db.Integer, primary_key=True) #ID do usuário
    username = db.Column(db.String(80), unique=True, nullable=False) #Nome do usuário
    password_hash = db.Column(db.String(128), nullable=False) #Senha do usuário (armazenada como hash) -- sempre salvar a senha em hash

    def __repr__(self):
        return f'<User {self.username}>'
    
class Post(db.Model): #Criar a tabela de posts no banco de dados
    idPost = db.Column(db.Integer, primary_key=True, nullable=False) #ID do post
    dataPost = db.Column(db.DateTime, default=datetime.datetime.now) #Data do post, atualizado utc para now
    content = db.Column(db.Text, nullable=False) #Conteúdo do post
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #ID do usuário que criou o post
    autor = db.relationship('User', backref ='posts')
    pass #temporario


# Cria a primeira pagina
@app.route('/')
def index():
    return render_template('index.html') # Renderiza o arquivo index.html e sobe para o servidor.

# - ROTA PROTEGIDA COM LOGIN REQUIRED
#Rota do dashboard (get) - pagina de sucesso pos login
@app.route('/dashboard')
@login_required # - Nosso guarda para a rota
def dashboard():
    posts_user = current_user.posts #Consulta todos os posts do usuário logado, usando referencia de relacionamento feito em Post.
    return render_template('dashboard.html', posts=posts_user) # Renderiza o arquivo dashboard.html

#  - A rota lembra o usuário
@app.route('/login', methods=['POST']) #Rota para o login com metodo post
def login():

    #Obtém dados do formulário
    usuario = request.form['username'] #Baseado no name do input
    senha = request.form['password'] #Baseado no name do input

    user = User.query.filter_by(username=usuario).first() #Consulta o banco de dados para achar o usuário

    if user and check_password_hash(user.password_hash, senha): #Verifica se o usuário existe e se a senha está correta
        login_user(user) #  O FLASK lembra dele 
        # Login bem-sucedido
        return redirect(url_for('dashboard')) #Redireciona para o dashboard
    else:
        # Login falhou
        flash('Nome de usuário ou senha incorretos.', 'error') #Mensagem de erro
        return redirect(url_for('index')) #Redireciona de volta para a página inicial

# - Rota para adicionar post    
@app.route('/add_post', methods=['POST']) #Rota para adicionar post com metodo post
@login_required #Protege a rota de adicionar post
def add_post():
    conteudo = request.form['content'] #Obtém o conteúdo do post do formulário
    novo_post = Post(content = conteudo, autor = current_user) #Cria um novo post associado ao usuário logado
    db.session.add(novo_post) #Adiciona o novo post à sessão do banco de dados
    db.session.commit() #Salva as alterações no banco de dados
    flash('Post adicionado com sucesso!', 'success') #Mensagem de sucesso
    return redirect(url_for('dashboard')) #Redireciona de volta para o dashboard

@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST']) #Rota para editar post com metodo get
@login_required #Protege a rota de editar post
def edit_post(post_id): #O end-point precisa pegar o id, então usamos como parametro o post_id
    post = Post.query.get(post_id) #Consulta o banco de dados para achar o post pelo id
    # Verificação de segurança
    if not post or post.autor != current_user:
        flash('Post não encontrado ou sem permissão.', 'error')
        return redirect(url_for('dashboard'))

    #  O SALVAMENTO (POST) ===
    if request.method == 'POST':
        # Pegamos o texto novo do formulário
        post.content = request.form['content'] # 'conteudo' será o name no HTML
        
        # Não precisamos de db.session.add() porque o post já existe!
        # O SQLAlchemy monitora mudanças automaticamente.
        db.session.commit()
        
        flash('Post atualizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    # === PARTE ANTIGA: A VISUALIZAÇÃO (GET) ===
    # Se não for POST, só mostramos a página com os dados atuais
    return render_template('edit_post.html', post=post)

@app.route('/delete_post/<int:post_id>', methods=['POST']) #Rota para deletar post com metodo post
@login_required #Protege a rota de deletar post
def delete_post(post_id): #O end-point precisa pegar o id, então usamos como parametro o post_id
    post = Post.query.get(post_id) #Consulta o banco de dados para achar o post pelo id
    
    if post and post.autor == current_user: #Verifica se o post existe e se o autor é o usuário logado
        db.session.delete(post) #Deleta o post da sessão do banco de dados
        db.session.commit() #Salva as alterações no banco de dados
        flash('Post deletado com sucesso!', 'success') #Mensagem de sucessos
    else:
        flash('Post não encontrado ou você não tem permissão para deletá-lo.', 'error') #Mensagem de erro
    
    return redirect(url_for('dashboard')) #Redireciona de volta para o dashboard
    


# - ROTA DE LOGOUT    
@app.route('/logout') #Rota para logout
@login_required #Protege a rota de logout
def logout():
    logout_user() # - Desloga o usuário
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

    new_user = User(username=usuario, password_hash=password_hash) #Cria um  usuário

    db.session.add(new_user) #Adiciona o  usuário à sessão do banco de dados
    db.session.commit() #Salva as alterações no banco de dados

    flash('Conta criada com sucesso! Você já pode fazer login.', 'success')
    return redirect(url_for('index'))
    
if __name__ == '__main__':
    app.run(debug=True)