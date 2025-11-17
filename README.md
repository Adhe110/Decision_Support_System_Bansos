# Decision Support System Bantuan Sosial (Bansos)

## 1. Project Overview (Gambaran Proyek)  
Website ini adalah sistem pendukung keputusan (SPK) untuk memberikan **peringkat penerima bantuan sosial (bansos)** menggunakan metode **SAW (Simple Additive Weighting)** dan **TOPSIS (Technique for Order of Preference by Similarity to Ideal Solution)**.

## 2. Features (Fitur)  
- Upload file Excel data calon penerima bantuan.  
- Auto-mapping kolom berdasarkan nama yang mirip (mis. “usia”, “umur” → “Usia”).  
- Validasi data:  
  - Pastikan kolom essential ada (RW, RT, Dusun, NIK, Nama Kepala Keluarga, Jumlah Tanggungan, Usia, Pekerjaan, Status).  
  - Pastikan kolom numerik valid dan dalam rentang yang benar.  
- Proses ranking menggunakan:  
  - **SAW** → normalisasi + pembobotan  
  - **TOPSIS** → hitung jarak ideal positif/negatif → nilai ranking  
- Export hasil ranking ke file Excel.  
- Fitur filter hasil berdasarkan RW, RT, atau Dusun.  
- Download template Excel untuk data input.

## 3. Technology Stack (Tumpukan Teknologi)  
- Backend: Flask (Python)  
- Data processing: pandas, NumPy  
- Format file: Excel (.xlsx)  
- Web server: dikembangkan secara lokal, siap untuk deploy ke platform cloud.

## 4. Installation & Setup (Instalasi)  
1. Clone repository:  
   ```bash
   git clone https://github.com/Adhe110/Decision_Support_System_Bansos.git
   cd Decision_Support_System_Bansos
