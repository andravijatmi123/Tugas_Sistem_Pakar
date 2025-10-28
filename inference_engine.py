import json
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__)

# Memuat knowledge base saat aplikasi dimulai
with open('rule.json', 'r') as f: #
    kb = json.load(f) #

def combine_cf(cf1, cf2): #
    """
    Fungsi untuk mengkombinasikan dua nilai Certainty Factor (CF).
    Ini adalah rumus standar kombinasi CF yang lebih lengkap
    daripada contoh di jurnal yang hanya mencakup kasus positif.
    """
    if cf1 >= 0 and cf2 >= 0: #
        return cf1 + cf2 * (1 - cf1) #
    elif cf1 < 0 and cf2 < 0: #
        return cf1 + cf2 * (1 + cf1) #
    else: #
        return (cf1 + cf2) / (1 - min(abs(cf1), abs(cf2))) #

@app.route('/')
def index(): #
    """Menyajikan halaman web utama (ui.html)."""
    # MODIFIKASI: Menyajikan 'ui.html'
    return send_from_directory('.', 'ui.html') #

@app.route('/get_symptoms')
def get_symptoms(): #
    """Menyediakan daftar gejala untuk ditampilkan di frontend."""
    return jsonify(kb['symptoms']) #

@app.route('/diagnose', methods=['POST'])
def diagnose(): #
    """
    Mesin inferensi utama.
    Menerima daftar gejala, menghitung CF untuk setiap penyakit.
    """
    data = request.get_json() #
    selected_symptom_ids = data.get('symptoms', []) #
    
    if not selected_symptom_ids: #
        return jsonify({"error": "Tidak ada gejala yang dipilih"}), 400 #

    results = [] #

    # Iterasi melalui setiap penyakit di knowledge base
    for disease in kb['diseases']: #
        cf_combined = 0.0 #
        matched_symptoms_details = [] #

        # Iterasi melalui gejala yang dipilih pengguna
        for symptom_id in selected_symptom_ids: #
            # Periksa apakah gejala ini ada dalam 'rules' penyakit saat ini
            if symptom_id in disease['rules']: #
                rule = disease['rules'][symptom_id] #
                mb = rule['mb'] #
                md = rule['md'] #
                
                # Hitung CF untuk gejala ini (CF evidence)
                cf_evidence = mb - md #
                
                # Kombinasikan CF evidence dengan CF gabungan sebelumnya
                cf_combined = combine_cf(cf_combined, cf_evidence) #
                
                # Simpan detail gejala yang cocok
                symptom_name = next((s['name'] for s in kb['symptoms'] if s['id'] == symptom_id), symptom_id) #
                matched_symptoms_details.append(f"{symptom_name} (CF: {cf_evidence:.2f})") #

        # Jika ada gejala yang cocok (CF > 0), tambahkan ke hasil
        if cf_combined > 0: #
            results.append({ #
                "disease_id": disease['id'], #
                "disease_name": disease['name'], #
                "solution": disease['solution'], #
                "matched_symptoms": matched_symptoms_details, #
                "confidence": cf_combined * 100,  # Ubah ke persentase
                "cf_value": cf_combined # Tambahkan nilai CF mentah
            })

    # Urutkan hasil dari keyakinan tertinggi ke terendah
    sorted_results = sorted(results, key=lambda x: x['confidence'], reverse=True) #
    
    return jsonify(sorted_results) #

if __name__ == '__main__': #
    app.run(debug=True) #