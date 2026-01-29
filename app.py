from flask import Flask, render_template, request, redirect, url_for, make_response
from fpdf import FPDF
import mysql.connector

app = Flask(__name__, template_folder='templates')

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

@app.route('/cetak/<nis>/<semester>', methods=['GET'])
def cetak(nis, semester):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT a.nama, a.nis, d.nama_kelas, b.id_mapel, b.nama_mapel, c.deskripsi, c.semester, (c.nilai_tugas+c.nilai_uts+c.nilai_uas)/3 as nilai_akhir FROM siswa_revita a, nilai_revita c , mapel_revita b, kelas_revita d WHERE b.id_mapel=c.id_mapel AND a.nis=c.nis AND a.id_kelas=d.id_kelas AND a.nis=%s AND c.semester=%s ORDER BY b.id_mapel;", (nis, semester,))
    revitaNilai = cursor.fetchall()
    cursor.execute("SELECT absensi, COUNT(absensi) AS jumlah FROM absensi_revita WHERE nis = %s AND semester = %s GROUP BY absensi;", (nis, semester,))
    revitaAbsensi = cursor.fetchall()
    cursor.close()
    conn.close()

    revitaPDF = FPDF()
    revitaPDF.add_page()
    
    revitaPDF.add_font('DejaVu', '', 'static/DejaVuSans.ttf', uni=True)
    revitaPDF.set_font('DejaVu', '', 11)

    revitaPDF.set_font_size(14)
    revitaPDF.cell(0, 10, 'Laporan Hasil Belajar', new_x='LMARGIN', new_y='NEXT', align='C')
    revitaPDF.ln(5)

    revitaPDF.set_font_size(11)
    revitaPDF.set_fill_color(220, 220, 220)
    revitaPDF.cell(40, 8, 'Nama:', 0, 0, 'L', False)
    revitaPDF.cell(55, 8, revitaNilai[0]['nama'], 0, 0, 'L', False)
    revitaPDF.cell(40, 8, 'Kelas:', 0, 0, 'L', False)
    revitaPDF.cell(55, 8, revitaNilai[0]['nama_kelas'], 0, 0, 'L', False)
    revitaPDF.ln()

    revitaPDF.cell(40, 8, 'NIS:', 0, 0, 'L', False)
    revitaPDF.cell(55, 8, revitaNilai[0]['nis'], 0, 0, 'L', False)
    revitaPDF.cell(40, 8, 'Semester:', 0, 0, 'L', False)
    revitaPDF.cell(55, 8, str(revitaNilai[0]['semester']), 0, 0, 'L', False)
    revitaPDF.ln()

    revitaPDF.cell(40, 8, 'Sekolah:', 0, 0, 'L', False)
    revitaPDF.cell(55, 8, 'SMK Negeri 2 Cimahi', 0, 0, 'L', False)
    revitaPDF.cell(40, 8, 'Tahun Ajaran:', 0, 0, 'L', False)
    revitaPDF.cell(55, 8, '2025-2026', 0, 0, 'L', False)
    revitaPDF.ln(20)
    
    revitaPDF.cell(10, 8, 'No', 1, 0, 'C', True)
    revitaPDF.cell(60, 8, 'Mata Pelajaran', 1, 0, 'C', True)
    revitaPDF.cell(40, 8, 'Nilai Akhir', 1, 0, 'C', True)
    revitaPDF.cell(80, 8, 'Capaian Kompetensi', 1, 0, 'C', True)
    revitaPDF.ln()

    for revitaLoop in revitaNilai:
        revitaPDF.cell(10, 8, str(revitaLoop['id_mapel']), 1, 0, 'L', False)
        revitaPDF.cell(60, 8, str(revitaLoop['nama_mapel']), 1, 0, 'L', False)
        revitaPDF.cell(40, 8, str(revitaLoop['nilai_akhir']), 1, 0, 'L', False)
        revitaPDF.cell(80, 8, str(revitaLoop['deskripsi']), 1, 0, 'L', False)
        revitaPDF.ln()
    revitaPDF.ln(20)

    revitaPDF.cell(100, 8, 'Kehadiran', 1, 0, 'C', True)
    revitaPDF.ln()
    for revitaLoop in revitaAbsensi:
        revitaPDF.cell(50, 8, str(revitaLoop['absensi']), 1, 0, 'L', False)
        revitaPDF.cell(50, 8, str(revitaLoop['jumlah']), 1, 0, 'L', False)
        revitaPDF.ln()
    revitaPDF.ln(20)

    revitaPDF.cell(100, 8, 'TTD Orang Tua Peserta Didik', align='C')
    revitaPDF.cell(0, 8, 'TTD Wali Kelas', new_x='LMARGIN', new_y='NEXT', align='C')
    revitaPDF.ln(30)
    revitaPDF.cell(0, 8, 'TTD Kepala Sekolah', new_x='LMARGIN', new_y='NEXT', align='C')

    revitaPDFTampil = bytes(revitaPDF.output(dest='S'))
    revitaResponse = make_response(revitaPDFTampil)
    revitaResponse.headers['Content-Type'] = 'application/pdf'
    revitaResponse.headers['Content-Disposition'] = (f'inline; filename=RAPORT_{nis}.pdf')

    return revitaResponse