import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SECRET_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not supabase_url or not supabase_key:
    print("[Error] Harap periksa SUPABASE_URL dan SUPABASE_SECRET_KEY di file .env!")
    exit()

supabase = create_client(supabase_url, supabase_key)

email = ""
password = "123456"

try:
    print(f"Mencoba melakukan sign-in untuk {email}...")
    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    print("\n--- LOGIN SUKSES! BERIKUT ADALAH TOKEN JWT-MU ---")
    print(response.session.access_token) # type: ignore
    print("------------------------------------------------\n")
except Exception as login_err:
    print(f"[Info] Gagal sign-in, mencoba mendaftarkan akun baru terlebih dahulu...")
    try:
        signup_response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        print("\n--- REGISTRASI BERHASIL! ---")
        print("Akun baru telah dibuat. Silakan periksa email kamu untuk konfirmasi (jika email confirmation aktif),")
        if signup_response.session:
            print("Berikut adalah Token JWT-mu:")
            print(signup_response.session.access_token)
        else:
            print("Sesi belum terbentuk. Harap lakukan sign-in kembali setelah konfirmasi email.")
        print("----------------------------\n")
    except Exception as signup_err:
        print(f"[Error] Gagal mendaftarkan akun: {signup_err}")