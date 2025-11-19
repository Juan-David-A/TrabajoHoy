from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from config import Config
import os
from datetime import date
from datetime import datetime
from sqlalchemy.orm import joinedload



BASE_DIR = os.path.abspath(os.path.dirname(__file__)) 
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, 'static'),  
    static_url_path='/static'  
)
app.config.from_object(Config)
app.secret_key = os.urandom(24)
db = SQLAlchemy(app)

# Modelos
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    habilidades = db.Column(db.String(255), nullable=True)
    experiencia = db.Column(db.String(255), nullable=True)
    cv_url = db.Column(db.String(255), nullable=True)
    rol = db.Column(db.String(20), nullable=False, default='usuario')
    postulaciones = db.relationship('Postulacion', back_populates='usuario', lazy=True)
    foto_url = db.Column(db.String(255))  

class Empresa(db.Model):
    id_empresa = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(255), nullable=False)
    direccion = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20), nullable=True)
    nit = db.Column(db.String(50), unique=True, nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    ofertas = db.relationship('Oferta', back_populates='empresa', lazy=True)
    postulantes = db.relationship('Postulacion', back_populates='empresa', lazy=True)

class Oferta(db.Model):
    id_oferta = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(255), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(db.Date, nullable=False)
    estado = db.Column(db.String(20), default='Activa')
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id_empresa'), nullable=False)
    empresa = db.relationship('Empresa', back_populates='ofertas')
    postulaciones = db.relationship('Postulacion', back_populates='oferta', lazy=True)

class Postulacion(db.Model):
    id_postulacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    id_oferta = db.Column(db.Integer, db.ForeignKey('oferta.id_oferta'), nullable=False)
    id_empresa = db.Column(db.Integer, db.ForeignKey('empresa.id_empresa'), nullable=False)
    fecha_postulacion = db.Column(db.Date, default=date.today)
    usuario = db.relationship('Usuario', back_populates='postulaciones')
    oferta = db.relationship('Oferta', back_populates='postulaciones')
    empresa = db.relationship('Empresa', back_populates='postulantes')


# Rutas generales
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/informacion")
def info():
    return render_template("informacion.html")

@app.route("/recuperar")
def recuperar():
    return render_template("recuperar_contrasena.html")

@app.route("/inicio")
def inicio():
    if 'usuario_id' not in session and 'empresa_id_empresa' not in session:
        flash("Debes iniciar sesión primero.", "warning")
        return redirect(url_for("login"))

    empresas = Empresa.query.all()
    ofertas = Oferta.query.filter_by(estado='Activa').all() 
    postulaciones = []
    usuario_nombre = "Invitado" 

    if 'usuario_id' in session:
        usuario_id = session['usuario_id']
        usuario = Usuario.query.get(usuario_id)
        if usuario:
            usuario_nombre = usuario.nombre
            # Cargar postulaciones del usuario
            postulaciones = Postulacion.query.filter_by(id_usuario=usuario_id).all()

    elif 'empresa_id_empresa' in session:
        empresa_id = session['empresa_id_empresa']
        empresa = Empresa.query.get(empresa_id)
        if empresa:
            usuario_nombre = empresa.nombre
    
    return render_template(
        "inicio.html",
        empresas=empresas,
        ofertas=ofertas,
        postulaciones=postulaciones,
        usuario_nombre=usuario_nombre
    )

@app.route("/logout")
def logout():
    session.clear()
    flash("Has cerrado sesión correctamente.", "success")
    return redirect(url_for("home"))

@app.route("/registro_elegir")
def registro_elegir():
    return render_template("registro_elegir.html")

# Registro de usuarios
@app.route("/registro", methods=["POST", "GET"])
def registro():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        habilidades = request.form["habilidades"]
        experiencia = request.form["experiencia"]
        try:
            nuevo_usuario = Usuario(
                nombre=nombre,
                email=email,
                password=generate_password_hash(password),
                habilidades=habilidades,
                experiencia=experiencia
            )
            db.session.add(nuevo_usuario)
            db.session.commit()
            flash("¡Registro exitoso! Ahora puedes iniciar sesión.", 'success')
            return redirect(url_for('login'))
        except IntegrityError as e:
            db.session.rollback()
            if 'email' in str(e.orig):
                flash("El correo electrónico ya está registrado.", 'danger')
            else:
                flash("Error al registrar el usuario.", 'danger')
        return redirect(url_for('registro'))
    return render_template("registro.html")

# Login de usuarios
@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        session.clear()
        email = request.form["email"]
        password = request.form["password"]
        usuario = Usuario.query.filter_by(email=email).first()
        
        if usuario and check_password_hash(usuario.password, password):
            session['usuario_id'] = usuario.id
            session['usuario_nombre'] = usuario.nombre
            session['tipo_usuario'] = usuario.rol
            session['foto_usuario'] = usuario.foto_url if usuario.foto_url else None

            flash("¡Inicio de sesión exitoso!", "success")
            return redirect(url_for('inicio'))
        
        flash("Credenciales incorrectas.", "danger")
        return redirect(url_for("login"))
    
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if 'usuario_id' not in session or session.get('tipo_usuario') != 'admin':
        flash("No tienes permisos para acceder a esta página.", "danger")
        return redirect(url_for("login"))

    usuarios = Usuario.query.all()
    empresas = Empresa.query.all()
    return render_template("dashboard.html", usuarios=usuarios, empresas=empresas)

@app.route("/editar_usuario/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):
    if 'usuario_id' not in session or session.get('tipo_usuario') != 'admin':
        flash("No tienes permisos para editar usuarios.", "danger")
        return redirect(url_for("login"))

    usuario = Usuario.query.get_or_404(id)

    if request.method == "POST":
        usuario.nombre = request.form["nombre"]
        usuario.habilidades = request.form["habilidades"]
        usuario.experiencia = request.form["experiencia"]
        password = request.form.get("password")
        if password:
            usuario.password = generate_password_hash(password)
        db.session.commit()
        flash("Usuario actualizado con éxito", "success")
        return redirect(url_for("dashboard"))

    return render_template("editar_usuario.html", usuario=usuario)

@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):
    if 'usuario_id' not in session or session.get('tipo_usuario') != 'admin':
        flash("No tienes permisos para eliminar usuarios.", "danger")
        return redirect(url_for("login"))

    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()

    flash("¡Usuario eliminado con éxito!", 'success')
    return redirect(url_for("dashboard"))

# Registro y login de empresas
@app.route("/registro_empresa", methods=["POST", "GET"])
def registro_empresa():
    if request.method == "POST":
        nombre = request.form["nombre"]
        direccion = request.form["direccion"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        telefono = request.form["telefono"]
        nit = request.form["nit"]

        try:
            nueva_empresa = Empresa(
                nombre=nombre,
                direccion=direccion,
                email=email,
                password=password,
                telefono=telefono,
                nit=nit
            )
            db.session.add(nueva_empresa)
            db.session.commit()
            flash("¡Registro exitoso!", 'success')
            return redirect(url_for("login_empresa"))
        except IntegrityError as e:
            db.session.rollback()
            if 'email' in str(e.orig):
                flash("El correo electrónico ya está registrado. Intenta con otro.", 'danger')
            else:
                flash("Error al registrar la empresa. Verifica los datos.", 'danger')
        except Exception as e:
            flash("Ocurrió un error inesperado al registrar la empresa.", 'danger')

        return redirect(url_for('registro_empresa'))

    return render_template("registro_empresa.html")

@app.route('/login_empresa', methods=['GET', 'POST'])
def login_empresa():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        empresa = Empresa.query.filter_by(email=email).first()

        if empresa and check_password_hash(empresa.password, password):
            
            session['empresa_id_empresa'] = empresa.id_empresa
            session['usuario_nombre'] = empresa.nombre
            session['tipo_usuario'] = 'empresa'

            flash("Has iniciado sesión exitosamente.", "success")
            return redirect(url_for('dashboard_emp'))  

        else:
            flash("Correo o contraseña incorrectos.", "danger")

    return render_template('login_empresa.html')

@app.route("/dashboard_emp")
def dashboard_emp():
    if 'empresa_id_empresa' not in session or session.get('tipo_usuario') != 'empresa':
        flash("Debes iniciar sesión primero.", "warning")
        return redirect(url_for("login_empresa"))
    
    empresa_id_empresa = session['empresa_id_empresa']
    empresa = Empresa.query.get(empresa_id_empresa)
    ofertas = Oferta.query.filter_by(id_empresa=empresa_id_empresa).all()
    return render_template("dashboard_emp.html", empresa=empresa, ofertas=ofertas)

from werkzeug.security import generate_password_hash

@app.route('/editar_empresa', methods=['GET', 'POST'])
def editar_emp():
    if 'empresa_id_empresa' not in session:
        flash('Debes iniciar sesión para editar la empresa.', 'warning')
        return redirect(url_for('login'))

    empresa_id = session['empresa_id_empresa']
    empresa = Empresa.query.get(empresa_id)

    if not empresa:
        flash('Empresa no encontrada.', 'danger')
        return redirect(url_for('dashboard_emp'))

    if request.method == 'POST':
        empresa.nombre = request.form.get('nombre')
        empresa.direccion = request.form.get('direccion')
        empresa.telefono = request.form.get('telefono')
        empresa.nit = request.form.get('nit')
        empresa.descripcion = request.form.get('descripcion')

        password_nueva = request.form.get('password')
        if password_nueva:
            empresa.password = generate_password_hash(password_nueva)

        try:
            db.session.commit()
            flash('Perfil de empresa actualizado correctamente.', 'success')
            return redirect(url_for('dashboard_emp'))
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar la empresa.', 'danger')

    return render_template('editar_emp.html', empresa=empresa)


@app.route("/eliminar_empresa/<int:id>")
def eliminar_empresa(id):
    empresa = Empresa.query.get_or_404(id)

    if session.get('empresa_id') == empresa.id:
        flash("No puedes eliminar tu propio usuario.", "warning")
        return redirect(url_for("dashboard_emp"))

    try:
        db.session.delete(empresa)
        db.session.commit()
        flash("¡Empresa eliminada con éxito!", 'success')
    except Exception:
        flash("Hubo un error al eliminar la empresa.", 'danger')

    return redirect(url_for("dashboard_emp"))

# Página 404
def pagina_no_encontrada(error):
    return render_template('404.html'), 404

@app.route('/crear_oferta', methods=['GET', 'POST'])
def crear_oferta():
    if 'empresa_id_empresa' not in session:
        flash('Debes iniciar sesión como empresa para crear una oferta.', 'warning')
        return redirect(url_for('crear_oferta'))  # o login

    if request.method == 'POST':
        titulo = request.form.get('titulo')
        descripcion = request.form.get('descripcion')

        if not titulo or not descripcion:
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(url_for('crear_oferta'))

        nueva_oferta = Oferta(
            titulo=titulo,
            descripcion=descripcion,
            fecha_publicacion=date.today(),
            estado='Activa',
            id_empresa=session['empresa_id_empresa']
        )
        db.session.add(nueva_oferta)
        db.session.commit()

        flash('Oferta creada exitosamente.', 'success')
        return redirect(url_for('dashboard_emp'))

    return render_template('crear_oferta.html')

@app.route('/editar_oferta/<int:id_oferta>', methods=['GET', 'POST'])
def editar_oferta(id_oferta):
    if 'empresa_id_empresa' not in session:
        flash('Debes iniciar sesión para editar ofertas.', 'warning')
        return redirect(url_for('registro_empresa'))  # o tu login de empresa

    oferta = Oferta.query.filter_by(id_oferta=id_oferta, id_empresa=session['empresa_id_empresa']).first()

    if not oferta:
        flash('Oferta no encontrada o no te pertenece.', 'danger')
        return redirect(url_for('dashboard_emp'))  # o donde quieras redirigir

    if request.method == 'POST':
        oferta.titulo = request.form.get('titulo')
        oferta.descripcion = request.form.get('descripcion')
        db.session.commit()
        flash('Oferta actualizada correctamente.', 'success')
        return redirect(url_for('dashboard_emp')
)

    return render_template('editar_oferta.html', oferta=oferta)

@app.route('/eliminar_oferta/<int:id_oferta>', methods=['POST'])
def eliminar_oferta(id_oferta):
    if 'empresa_id_empresa' not in session:
        flash('Debes iniciar sesión para eliminar ofertas.', 'warning')
        return redirect(url_for('registro_empresa'))  # o login

    oferta = Oferta.query.filter_by(id_oferta=id_oferta, id_empresa=session['empresa_id_empresa']).first()

    if not oferta:
        flash('Oferta no encontrada o no te pertenece.', 'danger')
        return redirect(url_for('dashboard_emp'))

    db.session.delete(oferta)
    db.session.commit()
    flash('Oferta eliminada correctamente.', 'success')
    return redirect(url_for('dashboard_emp'))

@app.route('/postular/<int:id_oferta>', methods=['POST'])
def postular(id_oferta):
    if 'usuario_id' not in session:
        flash('Debes iniciar sesión para postular.', 'warning')
        return redirect(url_for('login'))

    oferta = Oferta.query.get(id_oferta)
    if not oferta:
        flash("La oferta no existe.", "danger")
        return redirect(url_for('ofertas_disponibles'))

    # Validar que no se postule dos veces a la misma oferta
    ya_postulado = Postulacion.query.filter_by(id_usuario=session['usuario_id'], id_oferta=id_oferta).first()
    if ya_postulado:
        flash('Ya te has postulado a esta oferta.', 'info')
        return redirect(url_for('ofertas_empresa', id_empresa=oferta.id_empresa))

    postulacion = Postulacion(
        id_usuario=session['usuario_id'],
        id_oferta=id_oferta,
        id_empresa=oferta.id_empresa,
        fecha_postulacion=datetime.utcnow()
    )
    db.session.add(postulacion)
    db.session.commit()

    flash('Postulación realizada con éxito.', 'success')
    return redirect(url_for('ofertas_empresa', id_empresa=oferta.id_empresa))


@app.route('/ofertas_empresa/<int:id_empresa>')
def ofertas_empresa(id_empresa):
    empresa = Empresa.query.get_or_404(id_empresa)
    ofertas = Oferta.query.filter_by(id_empresa=id_empresa, estado='Activa').all()
    return render_template('ofertas_empresa.html', empresa=empresa, ofertas=ofertas)

@app.route("/perfil")
def perfil():
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return redirect("/login")

    usuario = Usuario.query.get(usuario_id)

    if not usuario:
        flash("Usuario no encontrado", "danger")
        return redirect("/login")

    return render_template("perfil.html", usuario=usuario)

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

@app.route("/actualizar_perfil", methods=["GET", "POST"])
def actualizar_perfil():
    if "usuario_id" not in session:
        return redirect("/login")

    usuario_id = session["usuario_id"]
    usuario = Usuario.query.get(usuario_id)

    if request.method == "POST":
        experiencia = request.form.get("experiencia")
        habilidades = request.form.get("habilidades")
        cv_archivo = request.files.get("cv_archivo")
        foto_perfil = request.files.get("foto_perfil")

        if experiencia is not None:
            usuario.experiencia = experiencia

        if habilidades is not None:
            usuario.habilidades = habilidades

        # Guardar archivo CV PDF
        if cv_archivo and cv_archivo.filename != "" and allowed_file(cv_archivo.filename, Config.ALLOWED_EXTENSIONS_CV):
            filename_cv = f"cv_usuario_{usuario_id}.pdf"
            filepath_cv = os.path.join(Config.UPLOAD_FOLDER_CV, filename_cv)
            os.makedirs(os.path.dirname(filepath_cv), exist_ok=True)
            cv_archivo.save(filepath_cv)
            usuario.cv_url = filename_cv

        # Guardar foto de perfil (jpg/png)
        if foto_perfil and foto_perfil.filename != "" and allowed_file(foto_perfil.filename, Config.ALLOWED_EXTENSIONS_IMG):
            ext = foto_perfil.filename.rsplit('.', 1)[1].lower()
            filename_foto = f"foto_usuario_{usuario_id}.{ext}"
            filepath_foto = os.path.join(Config.UPLOAD_FOLDER_FOTOS, filename_foto)
            os.makedirs(os.path.dirname(filepath_foto), exist_ok=True)
            foto_perfil.save(filepath_foto)
            usuario.foto_url = filename_foto
            session['usuario_foto'] = filename_foto

        db.session.commit()
        flash("Perfil actualizado correctamente", "success")
        return redirect("/perfil")

    return render_template("actualizar_perfil.html", usuario=usuario)

@app.route('/empresa/candidatos')
def ver_candidatos():
    if 'empresa_id_empresa' not in session:
        return redirect(url_for('login'))

    empresa_id_empresa = session['empresa_id_empresa']
    ofertas = Oferta.query.filter_by(id_empresa=empresa_id_empresa).all()

    postulaciones = []
    for oferta in ofertas:
        for postulacion in oferta.postulaciones:
            postulaciones.append(postulacion)
    
    return render_template('empresa_candidatos.html', postulaciones=postulaciones, )

@app.route('/empresa/candidato/<int:candidato_id>')
def ver_perfil_candidato(candidato_id):
    if 'empresa_id_empresa' not in session:
        return redirect(url_for('login'))

    usuario = Usuario.query.get_or_404(candidato_id)
    return render_template('perfil.html', usuario=usuario)

# Ejecutar aplicación
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Esta línea crea las tablas en la base de datos
    app.register_error_handler(404, pagina_no_encontrada)
    app.run(debug=True)
