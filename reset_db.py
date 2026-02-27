from app import app, db

with app.app_context():
    db.create_all()
    print("Banco de dados recriado com sucesso!")