from flask import Flask, render_template, request, redirect, url_for, make_response
from fpdf import FPDF
import mysql.connector
import os

app = Flask(__name__, template_folder='templates')

PDF_FOLDER = "raport_output"

if not os.path.exists(PDF_FOLDER):
    os.makedirs(PDF_FOLDER)

def get_db_connection():
    try:
        db = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='raport_revita'
        )                                                                               
        return db
    except mysql.connector.Error as e:
        print('gk nyambung', e)
        return None
    
@app.route('/')
def nilai():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT a.nis, c.id_nilai, a.nama, b.nama_mapel, c.nilai_tugas, c.nilai_uts, c.nilai_uas, c.deskripsi, c.semester, (c.nilai_tugas+c.nilai_uts+c.nilai_uas)/3 as nilai_akhir FROM siswa_revita a, nilai_revita c , mapel_revita b WHERE b.id_mapel=c.id_mapel AND a.nis=c.nis;")
    revitaNilai = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', revitaNilai=revitaNilai)

@app.route('/siswa', methods=['GET', 'POST'])
def siswa():
    revitaNIS = request.form.get('revitaNIS')
    revitaSemester = request.form.get('revitaSemester')
    revitaTahunAjar = request.form.get('revitaTahunAjar')

    if revitaNIS == 'None':
        revitaNIS = None
    if revitaSemester == 'None':
        revitaSemester = None
    if revitaTahunAjar == 'None':
        revitaTahunAjar = None

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT nis, nama FROM siswa_revita")
    revitaListsis = cursor.fetchall()

    cursor.execute("SELECT DISTINCT semester FROM nilai_revita")
    revitaListsem = cursor.fetchall()

    cursor.execute("SELECT DISTINCT tahun_ajar FROM nilai_revita")
    revitaListtahun = cursor.fetchall()

    revitaQuery = """
    SELECT DISTINCT a.nis, a.nama, a.alamat, a.jk, b.semester, b.tahun_ajar
    FROM siswa_revita a
    JOIN nilai_revita b ON a.nis = b.nis
    WHERE (%s IS NULL OR a.nis = %s)
      AND (%s IS NULL OR b.semester = %s)
      AND (%s IS NULL OR b.tahun_ajar = %s)
    ORDER BY a.nis, b.semester
    """
    cursor.execute(revitaQuery, (
        revitaNIS, revitaNIS,
        revitaSemester, revitaSemester,
        revitaTahunAjar, revitaTahunAjar
    ))

    revitaData = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('siswa.html',revitaData=revitaData, revitaListsis=revitaListsis, revitaListsem=revitaListsem, revitaListtahun=revitaListtahun)

    
@app.route('/tambah_nilai')
def tambah_nilai():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT nama, nis FROM siswa_revita")
    revitaSiswa = cursor.fetchall()
    cursor.execute("SELECT id_mapel, nama_mapel FROM mapel_revita")
    revitaNilai= cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('tambah_nilai.html', revitaNilai=revitaNilai, revitaSiswa=revitaSiswa )
    
@app.route('/tambah_nilai1',methods=['GET','POST'])
def tambah_nilai1():
    revitaNama= request.form['revitaNama']
    revitaMapel= request.form['revitaMapel']
    revitaTugas= request.form['revitaTugas']
    revitaUTS= request.form['revitaUTS']
    revitaUAS= request.form['revitaUAS']
    revitaDeskripsi= request.form['revitaDeskripsi']
    revitaSemester= request.form['revitaSemester']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id_nilai FROM nilai_revita ORDER BY id_nilai DESC LIMIT 1")
    revitaDataIDNilai = cursor.fetchone()
    revitaID = revitaDataIDNilai['id_nilai'] 
    if revitaID :
        revitaNumber = int(revitaID[2:])+1
    else:
        revitaNumber = 1
    
    revitaIDNilai= f"NP{revitaNumber:03d}"

    cursor.execute(f"INSERT INTO nilai_revita (id_nilai, nis, id_mapel, nilai_tugas, nilai_uts, nilai_uas, deskripsi, semester) VALUES ('{revitaIDNilai}', '{revitaNama}', '{revitaMapel}', '{revitaTugas}', '{revitaUTS}', '{revitaUAS}', '{revitaDeskripsi}', '{revitaSemester}')")
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('nilai'))
    
@app.route('/edit_nilai/<id_nilai>', methods=['GET'])
def edit_nilai(id_nilai):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM nilai_revita WHERE id_nilai=%s", (id_nilai,))
    revitaEdit = cursor.fetchone()
    cursor.execute("SELECT nama, nis FROM siswa_revita")
    revitaSiswa = cursor.fetchall()
    cursor.execute("SELECT id_mapel, nama_mapel FROM mapel_revita")
    revitaMapel= cursor.fetchall()
    cursor.close()
    conn.close()
    
    if revitaEdit:
        return render_template('update_nilai.html', revitaEdit=revitaEdit,revitaSiswa=revitaSiswa, revitaMapel=revitaMapel )
    return redirect(url_for('nilai'))


@app.route('/update_nilai', methods=['POST'])
def update_nilai():
    revitaNama = request.form['revitaNama']
    revitaMapel= request.form['revitaMapel']
    revitaTugas= request.form['revitaTugas']
    revitaUTS= request.form['revitaUTS']
    revitaUAS= request.form['revitaUAS']
    revitaDeskripsi= request.form['revitaDeskripsi']
    revitaSemester= request.form['revitaSemester']
    revitaID= request.form['revitaID']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE nilai_revita SET nis=%s, id_mapel=%s, nilai_tugas=%s, nilai_uts=%s, nilai_uas=%s, deskripsi=%s, semester=%s WHERE id_nilai=%s", (revitaNama, revitaMapel, revitaTugas, revitaUTS, revitaUAS, revitaDeskripsi, revitaSemester, revitaID))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('nilai'))

@app.route('/delete_nilai/<id_nilai>', methods=['GET'])
def delete_nilai(id_nilai):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM nilai_revita WHERE id_nilai=%s", (id_nilai,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('nilai'))

@app.route('/cetak', methods=['GET'])
def cetak():
    semester = request.args.get('semester')
    tahun_ajar = request.args.get('tahun_ajar')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ambil semua kelas
    cursor.execute("SELECT id_kelas,nama_kelas FROM kelas_revita")
    kelas_list = cursor.fetchall()

    for kelas in kelas_list:

        kelas_id = kelas['id_kelas']
        nama_kelas = kelas['nama_kelas']

        folder_kelas = os.path.join(PDF_FOLDER, nama_kelas)
        os.makedirs(folder_kelas, exist_ok=True)

        pdf = FPDF()
        pdf.add_font('DejaVu','', 'static/DejaVuSans.ttf', uni=True)

        # ambil siswa per kelas
        cursor.execute("""
            SELECT DISTINCT a.nis
            FROM siswa_revita a
            JOIN nilai_revita b ON a.nis=b.nis
            WHERE a.id_kelas=%s
            AND (%s IS NULL OR b.semester=%s)
            AND (%s IS NULL OR b.tahun_ajar=%s)
        """,(kelas_id,semester,semester,tahun_ajar,tahun_ajar))

        siswa_list = cursor.fetchall()

        if not siswa_list:
            continue

        for siswa in siswa_list:

            nis = siswa['nis']

            cursor.execute("""
                SELECT a.nama,a.nis,d.nama_kelas,
                       b.nama_mapel,c.deskripsi,c.semester,
                       (c.nilai_tugas+c.nilai_uts+c.nilai_uas)/3 nilai_akhir
                FROM siswa_revita a
                JOIN nilai_revita c ON a.nis=c.nis
                JOIN mapel_revita b ON b.id_mapel=c.id_mapel
                JOIN kelas_revita d ON a.id_kelas=d.id_kelas
                WHERE a.nis=%s
                AND (%s IS NULL OR c.semester=%s)
                AND (%s IS NULL OR c.tahun_ajar=%s)
            """,(nis,semester,semester,tahun_ajar,tahun_ajar))

            nilai = cursor.fetchall()

            if not nilai:
                continue

            cursor.execute("""
                SELECT absensi,COUNT(*) jumlah
                FROM absensi_revita
                WHERE nis=%s
                GROUP BY absensi
            """,(nis,))

            absensi = cursor.fetchall()

            pdf.add_page()
            pdf.set_font('DejaVu','',11)

            pdf.cell(0,10,'LAPORAN HASIL BELAJAR',ln=1,align='C')

            pdf.cell(40,8,'Nama')
            pdf.cell(60,8,nilai[0]['nama'])
            pdf.cell(30,8,'Kelas')
            pdf.cell(0,8,nama_kelas,ln=1)

            pdf.cell(40,8,'NIS')
            pdf.cell(60,8,nilai[0]['nis'])
            pdf.cell(30,8,'Semester')
            pdf.cell(0,8,str(nilai[0]['semester']),ln=1)

            pdf.ln(5)

            pdf.set_fill_color(220,220,220)
            pdf.cell(10,8,'No',1,0,'C',True)
            pdf.cell(60,8,'Mapel',1,0,'C',True)
            pdf.cell(30,8,'Nilai',1,0,'C',True)
            pdf.cell(90,8,'Deskripsi',1,1,'C',True)

            no=1
            for n in nilai:
                pdf.cell(10,8,str(no),1)
                pdf.cell(60,8,n['nama_mapel'],1)
                pdf.cell(30,8,f"{n['nilai_akhir']:.2f}",1)
                pdf.cell(90,8,n['deskripsi'],1,1)
                no+=1

            pdf.ln(5)
            pdf.cell(0,8,'Kehadiran',ln=1)

            for a in absensi:
                pdf.cell(50,8,a['absensi'],1)
                pdf.cell(50,8,str(a['jumlah']),1,ln=1)

        file_pdf = os.path.join(folder_kelas,f"RAPORT_{nama_kelas}.pdf")
        pdf.output(file_pdf)

    cursor.close()
    conn.close()

    return "SEMUA RAPORT PER KELAS BERHASIL DIBUAT"
