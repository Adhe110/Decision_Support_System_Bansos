from flask import Flask, render_template, request, send_file
import pandas as pd
import numpy as np
import os
from datetime import datetime

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

hasil_global = None
last_output_file = None


# =========================================================
#   🔹 SAW NORMALISASI + PEMBOBOTAN
# =========================================================
def saw_normalisasi_berbobot(df):
    X = df[["Jumlah Tanggungan", "Usia", "Pekerjaan", "Status"]].astype(float)

    weights = np.array([0.30, 0.20, 0.30, 0.20])
    benefit_mask = np.array([True, True, False, True])

    R = X.copy()

    # Normalisasi Min-Max
    for i, col in enumerate(X.columns):
        if benefit_mask[i]:
            R[col] = (X[col] - X[col].min()) / (X[col].max() - X[col].min())
        else:
            R[col] = (X[col].max() - X[col]) / (X[col].max() - X[col].min())

    # Pembobotan
    return R * weights


# =========================================================
#   🔹 TOPSIS
# =========================================================
def topsis_ranking(Rb):
    Rb_np = Rb.values
    benefit_mask = np.array([True, True, False, True])

    Aplus = np.where(benefit_mask, Rb_np.max(axis=0), Rb_np.min(axis=0))
    Aminus = np.where(benefit_mask, Rb_np.min(axis=0), Rb_np.max(axis=0))

    Dplus = np.sqrt(((Aplus - Rb_np)**2).sum(axis=1))
    Dminus = np.sqrt(((Rb_np - Aminus)**2).sum(axis=1))

    return Dminus / (Dplus + Dminus)


@app.route('/')
def home():
    return render_template('home.html')


# =========================================================
#   🔹 ROUTE INDEX
# =========================================================
@app.route('/index', methods=['GET','POST'])
def index():
    global hasil_global, last_output_file

    if request.method == 'POST':
        file = request.files['file']
        if file.filename == '':
            return render_template("index.html", tableshow=False,
                                   error_msg="❌ File tidak valid atau kosong.")

        path_input = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(path_input)

        try:
            df = pd.read_excel(path_input)
        except:
            return render_template("index.html", tableshow=False,
                                   error_msg="❌ File tidak dapat dibaca sebagai Excel.")

        # ===================== AUTO MAP =====================
        map_patterns = {
            "RW": ["rw"],
            "RT": ["rt"],
            "Dusun": ["dusun","dusun/desa","desa"],
            "NIK": ["nik","no nik","nomor nik"],
            "Nama Kepala Keluarga": ["nama","nama kk","nama kepala keluarga"],
            "Jumlah Tanggungan": ["tanggungan","jumlah tanggungan","jml tanggungan"],
            "Usia": ["usia","umur"],
            "Pekerjaan": ["pekerjaan","job","kerja"],
            "Status": ["status","perkawinan","status kawin"]
        }

        df.columns = df.columns.str.lower().str.strip()
        col_map = {}

        for std_name, keys in map_patterns.items():
            for pattern in keys:
                for real_col in df.columns:
                    if pattern in real_col:
                        col_map[std_name] = real_col
                        break

        required = ["RW","RT","Dusun","NIK","Nama Kepala Keluarga",
                    "Jumlah Tanggungan","Usia","Pekerjaan","Status"]

        missing = [x for x in required if x not in col_map]
        if missing:
            msg = "❌ Kolom berikut tidak ditemukan:<br><ul>"
            for m in missing:
                msg += f"<li>{m}</li>"
            msg += "</ul>Periksa kembali file Excel Anda."
            return render_template("index.html", tableshow=False, error_msg=msg)

        df = df[[ col_map[c] for c in required ]]
        df.columns = required

        # =====================================================
        #   VALIDASI NUMERIK
        # =====================================================
        numeric_cols = ["Jumlah Tanggungan", "Usia", "Pekerjaan", "Status"]

        bad_cols = []
        reason = {}

        for col in numeric_cols:
            if df[col].isnull().any():
                bad_cols.append(col)
                reason[col] = "Ada nilai kosong."
                continue
            try:
                df[col].astype(float)
            except:
                bad_cols.append(col)
                reason[col] = "Berisi nilai non-numerik."
        
        if bad_cols:
            msg = "❌ Kesalahan data pada kolom berikut:<br><ul>"
            for c in bad_cols:
                msg += f"<li><b>{c}</b> → {reason[c]}</li>"
            msg += "</ul>Perbaiki file Excel Anda."
            return render_template("index.html", tableshow=False, error_msg=msg)
        
                # =====================================================
        # 🔍 VALIDASI RANGE PEKERJAAN & STATUS
        # =====================================================
        invalid_pekerjaan = df[ (df["Pekerjaan"] < 1) | (df["Pekerjaan"] > 5) ]
        invalid_status   = df[ (df["Status"] < 1) | (df["Status"] > 3) ]

        if not invalid_pekerjaan.empty or not invalid_status.empty:
            msg = "❌ Nilai kategori tidak valid:<br><ul>"

            if not invalid_pekerjaan.empty:
                msg += "<li><b>Pekerjaan</b> harus 1–5. Terdapat nilai invalid.</li>"

            if not invalid_status.empty:
                msg += "<li><b>Status</b> harus 1–3. Terdapat nilai invalid.</li>"

            msg += "</ul>Perbaiki file Excel Anda."
            return render_template("index.html", tableshow=False, error_msg=msg)


        # =====================================================
        #   NIK LAST 4 DIGIT
        # =====================================================
        df["NIK"] = df["NIK"].astype(str).str.replace(r"\.0$","",regex=True)
        df["NIK"] = df["NIK"].str.zfill(16).str[-4:]

        # =====================================================
        #   SAW + TOPSIS
        # =====================================================
        df[numeric_cols] = df[numeric_cols].astype(float)

        Rb = saw_normalisasi_berbobot(df)
        nilai_topsis = topsis_ranking(Rb)

        # =====================================================
        #   HASIL AKHIR
        # =====================================================
        hasil = pd.DataFrame({
            "RW": df["RW"].astype(str),
            "RT": df["RT"].astype(str),
            "Dusun": df["Dusun"].astype(str),
            "NIK": df["NIK"],
            "Nama": df["Nama Kepala Keluarga"],
            "SAW_Normalisasi_Berbobot": Rb.sum(axis=1),
            "Nilai_TOPSIS": nilai_topsis
        })

        hasil["Ranking"] = hasil["Nilai_TOPSIS"].rank(ascending=False, method="min")
        hasil = hasil.sort_values("Ranking")

        hasil_global = hasil.copy()

        nama_out = "Hasil_Ranking_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".xlsx"
        last_output_file = os.path.join(app.config['OUTPUT_FOLDER'], nama_out)
        hasil.to_excel(last_output_file, index=False)

        return render_template("index.html",
                               data=hasil.to_dict(orient='records'),
                               file_download="/download_all",
                               tableshow=True)

    return render_template("index.html", tableshow=False)


# =========================================================
#   DOWNLOAD SEMUA
# =========================================================
@app.route('/download_all')
def download_all():
    global last_output_file
    if last_output_file is None:
        return "❌ Belum ada hasil"
    return send_file(last_output_file, as_attachment=True)


# =========================================================
#   DOWNLOAD FILTER
# =========================================================
@app.route('/download_filter')
def download_filter():
    global hasil_global

    if hasil_global is None:
        return "❌ Belum ada proses ranking"

    rw = request.args.get("rw", "")
    rt = request.args.get("rt", "")
    dusun = request.args.get("dusun", "")

    df = hasil_global.copy()

    if rw: df = df[df["RW"] == rw]
    if rt: df = df[df["RT"] == rt]
    if dusun: df = df[df["Dusun"] == dusun]

    nama_out = f"Hasil_Filter_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    out = os.path.join(app.config['OUTPUT_FOLDER'], nama_out)
    df.to_excel(out, index=False)

    return send_file(out, as_attachment=True)


# =========================================================
#   DOWNLOAD TEMPLATE
# =========================================================
@app.route('/download_template')
def download_template():
    template_path = "template/template_excel.xlsx"  # lokasi file template kamu
    return send_file(template_path, as_attachment=True)


# =========================================================
#   RUN APP
# =========================================================
if __name__ == "__main__":
    app.run(debug=True)
