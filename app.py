from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
import os
from datetime import datetime
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer
load_dotenv()
import calendar #Módulo para calendários


# Cria a aplicação web
app = Flask(__name__)

#Configurações do e-mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER') #E-mail do remetente (definido no .env)
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS') #Senha do e-mail do remetente (definida no .env)

mail = Mail(app) #Inicializa o Flask-Mail com a aplicação Flask

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
    email = db.Column(db.String(120), unique=True, nullable=False)
    email_ativo = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Tag(db.Model): #Criar a tabela de tags no banco de dados
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #ID do usuário que criou a tag

    def __repr__(self):
        return f'<Tag {self.name}>'


class Post(db.Model): #Criar a tabela de posts no banco de dados
    idPost = db.Column(db.Integer, primary_key=True, nullable=False) #ID do post
    dataPost = db.Column(db.DateTime, default=datetime.now) #Data do post, atualizado utc para now
    content = db.Column(db.Text, nullable=False) #Conteúdo do post
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) #ID do usuário que criou o post
    autor = db.relationship('User', backref ='posts')
    tags = db.relationship('Tag', secondary=post_tags, backref='posts')
    imagem = db.Column(db.String(200), nullable=True)


# Cria a primeira pagina
@app.route('/')
def index():
    return render_template('index.html') # Renderiza o arquivo index.html e sobe para o servidor.

# - ROTA PROTEGIDA COM LOGIN REQUIRED
#Rota do dashboard (get) - pagina de sucesso pos login
# Rota do dashboard (get) - pagina de sucesso pos login
@app.route('/dashboard')
@login_required
def dashboard():

    page = request.args.get('page', 1, type=int)  # Pega o número da página da URL, padrão 1

    hoje = datetime.now()

    # --- 1. MEMÓRIAS E CALENDÁRIO (Mantemos isto igual) ---
    memorias = Post.query.filter(
        extract('month', Post.dataPost) == hoje.month,
        extract('day', Post.dataPost) == hoje.day,
        extract('year', Post.dataPost) != hoje.year, 
        Post.user_id == current_user.id
    ).all()

    cal = calendar.monthcalendar(hoje.year, hoje.month)

    posts_do_mes = Post.query.filter(
        extract('month', Post.dataPost) == hoje.month,
        extract('year', Post.dataPost) == hoje.year,
        Post.user_id == current_user.id
    ).all()
    dias_ativos = [p.dataPost.day for p in posts_do_mes]

    # --- 2. LÓGICA DE FILTRAGEM  ---
    
    # Tenta obter o termo de pesquisa 'q' e a data 'data'
    busca = request.args.get('q')
    data_url = request.args.get('data') 

    if busca:
        # SE houver pesquisa: filtra pelo conteúdo
        posts = Post.query.filter(
            Post.content.contains(busca), # Procura o termo dentro do conteúdo
            Post.user_id == current_user.id
        ).order_by(Post.dataPost.desc()).paginate(page=page, per_page=5)
        
        titulo_pagina = f'Resultados para "{busca}"'

    elif data_url:
        # SE houver data selecionada no calendário
        data_filtro = datetime.strptime(data_url, '%Y-%m-%d')
        posts = Post.query.filter(
            extract('day', Post.dataPost) == data_filtro.day,
            extract('month', Post.dataPost) == data_filtro.month,
            extract('year', Post.dataPost) == data_filtro.year,
            Post.user_id == current_user.id
        ).order_by(Post.dataPost.desc()).paginate(page=page, per_page=5)
        titulo_pagina = f'Posts de {data_filtro.strftime("%d/%m/%Y")}'

    else:
        # SE NÃO houver nada: mostra tudo
        posts = Post.query.order_by(Post.dataPost.desc()).paginate(page=page, per_page=5)
        titulo_pagina = 'Timeline'

    # Retorna tudo para o template
    return render_template('dashboard.html', 
                           posts=posts, 
                           memorias=memorias,
                           calendario=cal,
                           dias_ativos=dias_ativos,
                           ano_mes=hoje.strftime('%m / %Y'),
                           title=titulo_pagina,
                           data_atual=hoje,
                           mes_atual=hoje.month,
                           ano_atual=hoje.year)

#  - A rota lembra o usuário
@app.route('/login', methods=['POST'])
def login():
    # Obtém dados do formulário (agora buscamos por 'email')
    email = request.form['email'] 
    senha = request.form['password']

    # Busca o usuário pelo e-mail em vez do nome de usuário
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password_hash, senha):
        # 1. VERIFICA SE A CONTA ESTÁ ATIVA
        if not user.email_ativo:
            flash('Sua conta ainda não foi ativada. Por favor, verifique seu e-mail.', 'warning')
            return redirect(url_for('index'))
        
        # 2. SE ESTIVER ATIVA, FAZ O LOGIN
        login_user(user)
        return redirect(url_for('dashboard'))
    else:
        flash('E-mail ou senha incorretos.', 'error')
        return redirect(url_for('index'))

# - Rota para adicionar post    
@app.route('/add_post', methods=['POST'])
@login_required
def add_post():
    conteudo = request.form['content']
    tags_texto = request.form.get('tags')
    
    # 1. PEGAR O ARQUIVO
    arquivo = request.files['imagem'] # 'imagem' deve ser igual ao name no HTML
    nome_imagem = None # Começa vazio caso não tenha foto

    # 2. VERIFICAR SE TEM ARQUIVO E SE ELE TEM NOME
    if arquivo and arquivo.filename != '':
        # Limpa o nome para segurança (ex: "Minha Foto!.jpg" vira "Minha_Foto.jpg")
        nome_seguro = secure_filename(arquivo.filename)
        
        # Salva o arquivo na pasta do projeto
        # Certifique-se de que a pasta 'static/uploads' existe!
        caminho_salvar = os.path.join('static/uploads', nome_seguro)
        arquivo.save(caminho_salvar)
        
        # Guarda apenas o nome limpo para salvar no banco
        nome_imagem = nome_seguro

    # 3. CRIAR O POST (Agora passando a imagem também)
    novo_post = Post(content=conteudo, imagem=nome_imagem, autor=current_user)

    # Lógica das Tags (igual ao que você já tinha)
    if tags_texto:
        nomes_tags = tags_texto.split(',')
        for nome in nomes_tags:
            nome = nome.strip().lower()
            if nome:
                tag_existente = Tag.query.filter_by(name=nome, user_id=current_user.id).first()
                if tag_existente:
                    novo_post.tags.append(tag_existente)
                else:
                    nova_tag = Tag(name=nome, user_id=current_user.id)
                    novo_post.tags.append(nova_tag)

    db.session.add(novo_post)
    db.session.commit()
    flash('Post adicionado com sucesso!', 'success')
    return redirect(url_for('dashboard'))

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
    
@app.route('/register')
def mostra_register():
    return render_template('register.html')

# --- ROTA DE REGISTRO ATUALIZADA (Salva E-mail e pede confirmação) ---
@app.route('/register', methods=['POST'])
def register():
    usuario = request.form['username']
    email = request.form['email'] # <--- NOVO: Pegando o e-mail do HTML
    senha = request.form['password']
    confirm_password = request.form['confirm_password']

    # Verificações básicas
    if senha != confirm_password:
        flash('As senhas não coincidem.', 'error')
        return redirect(url_for('mostra_register'))
    
    if User.query.filter_by(username=usuario).first():
        flash('Nome de usuário já existe. Escolha outro.', 'error')
        return redirect(url_for('mostra_register'))

    # VERIFICAÇÃO NOVA: Se o e-mail já existe
    if User.query.filter_by(email=email).first():
        flash('Este e-mail já está cadastrado.', 'error')
        return redirect(url_for('mostra_register'))
    
    # Criação do Usuário
    password_hash = generate_password_hash(senha)
    # email_ativo começa como False (definido no modelo)
    new_user = User(username=usuario, email=email, password_hash=password_hash)

    db.session.add(new_user)
    db.session.commit()

    # GERAR TOKEN DE CONFIRMAÇÃO
    token = gerar_token_confirmacao(email)

    link_confirmacao = url_for('confirmar_email', token=token, _external=True) #Gera o link de confirmação com o token

    msg = Message('Confirme sua conta no Chronos',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=[email])
    
    msg.body = f'''Olá {usuario}! Bem-vindo ao Chronos. Para ativar sua conta e começar a guardar suas memórias, clique no link abaixo: {link_confirmacao}
    Se você não se cadastrou no Chronos, ignore este e-mail.'''

    mail.send(msg) #Envia o e-mail de confirmação (ainda sem configuração real do Flask-Mail, isso é só um placeholder)

    # MENSAGEM DE SUCESSO (Ainda sem o envio real do e-mail)
    flash('Conta criada com sucesso! Verifique seu e-mail para ativar a conta antes de logar.', 'info')
    
    # Redireciona para o login (index), não entra direto!
    return redirect(url_for('index'))

def gerar_token_confirmacao(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='email-confirmacao-salt')

# Função para gerar token de recuperação
def gerar_token_recuperacao(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='recuperacao-senha-salt')

@app.route('/recuperar_senha', methods=['GET', 'POST'])
def recuperar_senha():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            token = gerar_token_recuperacao(email)
            link_recuperacao = url_for('resetar_senha', token=token, _external=True)

            msg = Message('Recuperação de senha do Chronos',
                          sender=app.config['MAIL_USERNAME'],
                          recipients=[email])
            msg.body = f'''Olá {user.username}!
            
Você solicitou a redefinição da sua senha no Chronos.
Clique no link abaixo para criar uma nova senha (este link expira em 15 minutos):

{link_recuperacao}

Se você não solicitou essa mudança, por favor, ignore este e-mail. Nenhuma alteração será feita na sua conta.
'''
            mail.send(msg)

            flash('Um link de recuperação foi enviado para seu e-mail.')
            return redirect(url_for('index'))
    return render_template('recuperar_senha.html')

@app.route('/tag/<tag_name>') #Rota para ver posts por tag
@login_required
def posts_by_tag(tag_name):
    tag = Tag.query.filter_by(name=tag_name).first_or_404() #Verifica se a tag existe, se não existir retorna 404
    return render_template('dashboard.html', posts=tag.posts, title=f'Tag: {tag_name}') #Renderiza o dashboard com os posts da tag
    
@app.route('/tags')
@login_required
def all_tags():
    tags = Tag.query.filter_by(user_id=current_user.id).all() #Consulta todas as tags do banco de dados

    #Captura o ID que queremos editar
    edit_id = request.args.get('edit_id', type=int)

    return render_template('tags.html', tags=tags, edit_id=edit_id) #Renderiza a página de tags

@app.route('/delete_tag/<int:id>')
@login_required
def delete_tag(id):
    tag = Tag.query.get_or_404(id) #Consulta a tag pelo id, se não existir retorna 404
    db.session.delete(tag) #Deleta a tag da sessão do banco de dados
    db.session.commit() #Salva as alterações no banco de dados
    flash('Tag deletada com sucesso!', 'success') #Mensagem de sucesso
    return redirect(url_for('all_tags')) #Redireciona de volta para a página de tags

@app.route('/edit_tag/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_tag(id):
    tag = Tag.query.get_or_404(id) #Consulta a tag pelo id, se não existir retorna 404

    if request.method == 'POST':
        novo_nome = request.form['name'].strip().lower() #Obtém o novo nome da tag do formulário

        if novo_nome:
            tag.name = novo_nome
            db.session.commit() #Salva as alterações no banco de dados
            flash('Tag atualizada com sucesso!', 'success') #Mensagem de sucesso
            return redirect(url_for('all_tags')) #Redireciona de volta para a página de tags
        else:
            flash('O nome da tag não pode ser vazio.', 'error') #Mensagem de erro

            return redirect(url_for('all_tags'))
    return render_template('edit_tag.html', tag=tag) #Renderiza a página de edição de tag

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

@app.errorhandler(404) #Rota para erro 404
def page_not_found(e):
    return render_template('404.html'), 404

def confirmar_token_email(token, expiracao=3600):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirmacao-salt', max_age=expiracao)
        return email
    except:
        return False
    
@app.route('/confirmar/<token>')
def confirmar_email(token):
    #descobrir de quem é o token
    email = confirmar_token_email(token)

    #Se o token for invalido ou expirado
    if not email:
        flash('O link de confirmação é inválido ou expirou.', 'error')
        return redirect(url_for('index'))
    
    # Se o token for valido, acha o usuario no banco de dados
    user = User.query.filter_by(email=email).first_or_404()

    #Verifica se ele ja estava ativo
    if user.email_ativo:
        flash('Sua conta já está ativa. Faça login.', 'info')
    else:
        user.email_ativo = True
        db.session.commit()
        flash('Conta ativada com sucesso! Agora você pode fazer login.', 'success')
    return redirect(url_for('index'))

# 1. Função que "desfaz" o token de recuperação e verifica o tempo
def confirmar_token_recuperacao(token, expiracao=900): # 900 segundos = 15 minutos
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        # Tenta descobrir o e-mail, usando o MESMO salt que usamos para gerar
        email = serializer.loads(token, salt='recuperacao-senha-salt', max_age=expiracao)
        return email
    except:
        return False # Retorna Falso se expirou ou foi alterado

# 2. A rota que recebe o clique do usuário no e-mail
@app.route('/resetar_senha/<token>', methods=['GET', 'POST'])
def resetar_senha(token):
    # Verifica se o token é válido e descobre de qual e-mail ele é
    email = confirmar_token_recuperacao(token)
    
    # Se o token for falso (passou de 15 min ou foi mexido)
    if not email:
        flash('O link de redefinição é inválido ou expirou. Solicite um novo link.', 'error')
        return redirect(url_for('recuperar_senha'))
        
    # Acha o usuário no banco de dados
    user = User.query.filter_by(email=email).first_or_404()
    
    # Se o usuário preencheu o formulário com a nova senha (POST)
    if request.method == 'POST':
        senha = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if senha != confirm_password:
            flash('As senhas não coincidem. Tente novamente.', 'error')
            # Redireciona de volta para a mesma página, mantendo o token na URL
            return redirect(url_for('resetar_senha', token=token))
            
        # O momento mais importante: Troca a senha antiga pela nova (em hash!)
        user.password_hash = generate_password_hash(senha)
        db.session.commit()
        
        flash('Sua senha foi redefinida com sucesso! Você já pode entrar.', 'success')
        return redirect(url_for('index'))
        
    # Se ele apenas clicou no link e está acessando a página (GET)
    return render_template('resetar_senha.html', token=token)

if __name__ == '__main__':
    app.run(debug=True)