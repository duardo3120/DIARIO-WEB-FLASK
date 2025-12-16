from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
import calendar #Módulo para calendários


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

post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.idPost'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

 #Alterações para realizar autenticação e herdar aos usuários com UserMixin
class User(db.Model, UserMixin): #Cria a tabela de usuários no banco de dados, adicionado UserMixin para autenticação
    id = db.Column(db.Integer, primary_key=True) #ID do usuário
    username = db.Column(db.String(80), unique=True, nullable=False) #Nome do usuário
    password_hash = db.Column(db.String(128), nullable=False) #Senha do usuário (armazenada como hash) -- sempre salvar a senha em hash

    def __repr__(self):
        return f'<User {self.username}>'

class Tag(db.Model): #Criar a tabela de tags no banco de dados
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

    def __repr__(self):
        return f'<Tag {self.name}>'


class Post(db.Model): #Criar a tabela de posts no banco de dados
    idPost = db.Column(db.Integer, primary_key=True, nullable=False) #ID do post
    dataPost = db.Column(db.DateTime, default=datetime.now) #Data do post, atualizado utc para now
    content = db.Column(db.Text, nullable=False) #Conteúdo do post
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #ID do usuário que criou o post
    autor = db.relationship('User', backref ='posts')
    tags = db.relationship('Tag', secondary=post_tags, backref='posts')


# Cria a primeira pagina
@app.route('/')
def index():
    return render_template('index.html') # Renderiza o arquivo index.html e sobe para o servidor.

# - ROTA PROTEGIDA COM LOGIN REQUIRED
#Rota do dashboard (get) - pagina de sucesso pos login
@app.route('/dashboard')
@login_required
def dashboard():
    hoje = datetime.now()

    # 2. MEMÓRIAS: Posts de anos anteriores
    memorias = Post.query.filter(
        extract('month', Post.dataPost) == hoje.month,
        extract('day', Post.dataPost) == hoje.day,
        extract('year', Post.dataPost) != hoje.year, 
        Post.user_id == current_user.id
    ).all()

    # 3. CALENDÁRIO: Gerar a matriz do mês atual
    # Cria uma lista de semanas, ex: [[0,0,1,2,3...], [4,5...]]
    cal = calendar.monthcalendar(hoje.year, hoje.month)

    # 4. DIAS ATIVOS: Saber quais dias deste mês têm posts (para pintar a bolinha)
    posts_do_mes = Post.query.filter(
        extract('month', Post.dataPost) == hoje.month,
        extract('year', Post.dataPost) == hoje.year,
        Post.user_id == current_user.id
    ).all()
    # Cria uma lista simples com os dias: [14, 15, 20...]
    dias_ativos = [p.dataPost.day for p in posts_do_mes]

    data_url = request.args.get('data')  # Obtém o parâmetro 'date' da URL

    if data_url:
        data_filtro = datetime.strptime(data_url, '%Y-%m-%d')

        posts = Post.query.filter(
            extract('day', Post.dataPost) == data_filtro.day,
            extract('month', Post.dataPost) == data_filtro.month,
            extract('year', Post.dataPost) == data_filtro.year,
            Post.user_id == current_user.id).all()
        
        titulo_pagina = f'Posts de {data_filtro.strftime("%d/%m/%Y")}'

    else:
        posts = Post.query.order_by(Post.dataPost.desc()).all()
        titulo_pagina = 'Timeline'

    return render_template('dashboard.html', 
                           posts=posts, 
                           memorias=memorias,
                           calendario=cal,
                           dias_ativos=dias_ativos,
                           ano_mes=hoje.strftime('%m / %Y'),
                           title=titulo_pagina,
                           data_atual=hoje)

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
    tags_texto = request.form.get('tags')  #Obtém as tags do formulário, padrão vazio se não fornecido
    novo_post = Post(content = conteudo, autor = current_user) #Cria um novo post associado ao usuário logado

    # Lógica das Tags
    if tags_texto:
        # 1. Separa por vírgula (ex: "vida,  trabalho" vira ["vida", "  trabalho"])
        nomes_tags = tags_texto.split(',')
        
        for nome in nomes_tags:
            # 2. Limpa espaços extras e deixa minúsculo (ex: "  trabalho" vira "trabalho")
            nome = nome.strip().lower()
            
            if nome: # Se não for vazio
                # 3. Verifica se a tag já existe no banco
                tag_existente = Tag.query.filter_by(name=nome).first()
                
                if tag_existente:
                    # Se existe, usa ela
                    novo_post.tags.append(tag_existente)
                else:
                    # Se não existe, cria uma nova
                    nova_tag = Tag(name=nome)
                    novo_post.tags.append(nova_tag)

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

@app.route('/tag/<tag_name>') #Rota para ver posts por tag
@login_required
def posts_by_tag(tag_name):
    tag = Tag.query.filter_by(name=tag_name).first_or_404() #Verifica se a tag existe, se não existir retorna 404
    return render_template('dashboard.html', posts=tag.posts, title=f'Tag: {tag_name}') #Renderiza o dashboard com os posts da tag
    
@app.route('/tags')
@login_required
def all_tags():
    tags = Tag.query.all() #Consulta todas as tags do banco de dados
    return render_template('tags.html', tags=tags) #Renderiza a página de tags

@app.route('/delete_tag/<int:id>')
@login_required
def delete_tag(id):
    tag = Tag.query.get_or_404(id) #Consulta a tag pelo id, se não existir retorna 404
    db.session.delete(tag) #Deleta a tag da sessão do banco de dados
    db.session.commit() #Salva as alterações no banco de dados
    flash('Tag deletada com sucesso!', 'success') #Mensagem de sucesso
    return redirect(url_for('all_tags')) #Redireciona de volta para a página de tags

@app.route('/memories')
@login_required
def memories():
    hoje = datetime.now()
    
    # TRADUÇÃO DA QUERY:
    # Busque Posts ONDE:
    # 1. O Mês do post é igual ao mês de hoje
    # 2. E o Dia do post é igual ao dia de hoje
    # 3. E o Ano do post é DIFERENTE (!=) do ano atual (para ser lembrança, tem que ser antigo!)
    # 4. E o post pertence ao usuário logado
    
    posts = Post.query.filter(
        extract('month', Post.dataPost) == hoje.month,
        extract('day', Post.dataPost) == hoje.day,
        extract('year', Post.dataPost) != hoje.year, 
        Post.user_id == current_user.id
    ).all()

    return render_template('memories.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True)