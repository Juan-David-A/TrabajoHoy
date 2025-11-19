import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # TrabajoHoy/TrabajoHoy
PROJECT_ROOT = os.path.dirname(BASE_DIR)               # TrabajoHoy/

class Config:
    # Configuración de la base de datos
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:@localhost:3306/db"
    
    # Carpeta para subir CV y fotos
    UPLOAD_FOLDER_CV = os.path.join(PROJECT_ROOT,'Pagina', 'static', 'cv')
    UPLOAD_FOLDER_FOTOS = os.path.join(PROJECT_ROOT,'Pagina', 'static', 'fotos')
    
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB límite global

    # Extensiones permitidas
    ALLOWED_EXTENSIONS_CV = {'pdf', 'doc', 'docx'}
    ALLOWED_EXTENSIONS_IMG = {'png', 'jpg', 'jpeg'}
