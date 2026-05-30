from flask import Flask, render_template, request, redirect, url_for, flash
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clinica-saludpro-secret-2025')

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL no está configurada en las variables de entorno")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

# Inicializar base de datos
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id SERIAL PRIMARY KEY,
            numero_identidad TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            edad INTEGER,
            ciudad TEXT,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS medicos (
            id SERIAL PRIMARY KEY,
            numero_identidad TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            especialidad TEXT NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS citas (
            id SERIAL PRIMARY KEY,
            paciente_id INTEGER REFERENCES pacientes(id) ON DELETE CASCADE,
            medico_id INTEGER REFERENCES medicos(id) ON DELETE CASCADE,
            fecha DATE NOT NULL,
            estado TEXT DEFAULT 'Pendiente',
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS recomendaciones (
            id SERIAL PRIMARY KEY,
            cita_id INTEGER REFERENCES citas(id) ON DELETE CASCADE,
            texto TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    conn.commit()
    cur.close()
    conn.close()

with app.app_context():
    init_db()

# ==================== DASHBOARD PRINCIPAL ====================

@app.route('/')
def index():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT c.id, c.fecha, c.estado, 
               p.nombre as paciente, p.numero_identidad as paciente_identidad,
               m.nombre as medico, m.numero_identidad as medico_identidad, 
               m.especialidad 
        FROM citas c
        JOIN pacientes p ON c.paciente_id = p.id
        JOIN medicos m ON c.medico_id = m.id
        ORDER BY c.fecha DESC
    ''')
    citas = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('index.html', citas=citas)

# ==================== PACIENTES CRUD ====================

@app.route('/patients')
def patients():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pacientes ORDER BY nombre")
    pacientes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('patients.html', pacientes=pacientes)

@app.route('/register_patient', methods=['GET', 'POST'])
def register_patient():
    if request.method == 'POST':
        numero_identidad = request.form['numero_identidad'].strip()
        nombre = request.form['nombre'].strip()
        edad = int(request.form['edad'])
        ciudad = request.form['ciudad'].strip()
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO pacientes (numero_identidad, nombre, edad, ciudad) 
                VALUES (%s, %s, %s, %s)
            ''', (numero_identidad, nombre, edad, ciudad))
            conn.commit()
            flash('✅ Paciente registrado con éxito', 'success')
            return redirect(url_for('patients'))
        except psycopg2.IntegrityError:
            flash('⚠️ Ya existe un paciente con ese número de identidad', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    return render_template('register_patient.html')

@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        numero_identidad = request.form['numero_identidad'].strip()
        nombre = request.form['nombre'].strip()
        edad = int(request.form['edad'])
        ciudad = request.form['ciudad'].strip()
        
        try:
            cur.execute('''
                UPDATE pacientes 
                SET numero_identidad=%s, nombre=%s, edad=%s, ciudad=%s
                WHERE id=%s
            ''', (numero_identidad, nombre, edad, ciudad, id))
            conn.commit()
            flash('✅ Paciente actualizado con éxito', 'success')
            return redirect(url_for('patients'))
        except psycopg2.IntegrityError:
            flash('⚠️ Número de identidad ya existe', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    cur.execute("SELECT * FROM pacientes WHERE id = %s", (id,))
    paciente = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_patient.html', paciente=paciente)

@app.route('/delete_patient/<int:id>')
def delete_patient(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM pacientes WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('🗑️ Paciente eliminado correctamente', 'danger')
    return redirect(url_for('patients'))

# ==================== MÉDICOS CRUD ====================

@app.route('/doctors')
def doctors():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM medicos ORDER BY nombre")
    medicos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('doctors.html', medicos=medicos)

@app.route('/register_doctor', methods=['GET', 'POST'])
def register_doctor():
    if request.method == 'POST':
        numero_identidad = request.form['numero_identidad'].strip()
        nombre = request.form['nombre'].strip()
        especialidad = request.form['especialidad'].strip()
        
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            cur.execute('''
                INSERT INTO medicos (numero_identidad, nombre, especialidad) 
                VALUES (%s, %s, %s)
            ''', (numero_identidad, nombre, especialidad))
            conn.commit()
            flash('✅ Médico registrado con éxito', 'success')
            return redirect(url_for('doctors'))
        except psycopg2.IntegrityError:
            flash('⚠️ Ya existe un médico con ese número de identidad', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    return render_template('register_doctor.html')

@app.route('/edit_doctor/<int:id>', methods=['GET', 'POST'])
def edit_doctor(id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        numero_identidad = request.form['numero_identidad'].strip()
        nombre = request.form['nombre'].strip()
        especialidad = request.form['especialidad'].strip()
        
        try:
            cur.execute('''
                UPDATE medicos 
                SET numero_identidad=%s, nombre=%s, especialidad=%s
                WHERE id=%s
            ''', (numero_identidad, nombre, especialidad, id))
            conn.commit()
            flash('✅ Médico actualizado con éxito', 'success')
            return redirect(url_for('doctors'))
        except psycopg2.IntegrityError:
            flash('⚠️ Número de identidad ya existe', 'danger')
            conn.rollback()
        finally:
            cur.close()
            conn.close()
    
    cur.execute("SELECT * FROM medicos WHERE id = %s", (id,))
    medico = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('edit_doctor.html', medico=medico)

@app.route('/delete_doctor/<int:id>')
def delete_doctor(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM medicos WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('🗑️ Médico eliminado correctamente', 'danger')
    return redirect(url_for('doctors'))

# ==================== CITAS ====================

@app.route('/new_appointment', methods=['GET', 'POST'])
def new_appointment():
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        paciente_id = request.form['paciente_id']
        medico_id = request.form['medico_id']
        fecha = request.form['fecha']
        
        cur.execute('INSERT INTO citas (paciente_id, medico_id, fecha) VALUES (%s, %s, %s)',
                    (paciente_id, medico_id, fecha))
        conn.commit()
        flash('✅ Cita agendada correctamente', 'success')
        return redirect(url_for('index'))

    cur.execute("SELECT id, nombre, numero_identidad FROM pacientes ORDER BY nombre")
    pacientes = cur.fetchall()
    cur.execute("SELECT id, nombre, numero_identidad, especialidad FROM medicos ORDER BY nombre")
    medicos = cur.fetchall()
    
    cur.close()
    conn.close()
    return render_template('new_appointment.html', pacientes=pacientes, medicos=medicos)

@app.route('/finish_appointment/<int:cita_id>', methods=['GET', 'POST'])
def finish_appointment(cita_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    if request.method == 'POST':
        texto = request.form['recomendaciones']
        cur.execute('INSERT INTO recomendaciones (cita_id, texto) VALUES (%s, %s)', (cita_id, texto))
        cur.execute("UPDATE citas SET estado = 'Completada' WHERE id = %s", (cita_id,))
        conn.commit()
        flash('✅ Recomendaciones guardadas y cita finalizada', 'success')
        return redirect(url_for('index'))

    cur.execute('''
        SELECT c.*, p.nombre as paciente, p.numero_identidad as paciente_identidad,
               m.nombre as medico, m.numero_identidad as medico_identidad 
        FROM citas c
        JOIN pacientes p ON c.paciente_id = p.id
        JOIN medicos m ON c.medico_id = m.id
        WHERE c.id = %s
    ''', (cita_id,))
    cita = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('recommendations.html', cita=cita)

if __name__ == '__main__':
    app.run(debug=True)