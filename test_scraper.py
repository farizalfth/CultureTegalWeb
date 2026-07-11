import os
import re
import time
import hashlib
import uuid
from pymongo import MongoClient, UpdateOne
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class MockTarget:
    def __init__(self, target_id, target_type, nama_tempat, url_maps):
        self.target_id = target_id
        self.target_type = target_type
        self.nama_tempat = nama_tempat
        self.url_maps = url_maps

def load_env_manually():
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().strip('"').strip("'")
                    os.environ[key] = val

def run_standalone_test():
    print("[1/8] Memulai inisialisasi lingkungan pengujian...")
    load_env_manually()
    
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        print("[Error] MONGO_URI tidak ditemukan di file .env!")
        return

    test_target = MockTarget(
        target_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        target_type="culture",
        nama_tempat="Masjid Agung Tegal",
        url_maps="https://www.google.com/maps/place/Great+Mosque+Tegal+City/@-6.8674332,109.1342736,17z/data=!4m8!3m7!1s0x2e6fb77e2eac5133:0x74f6260003735122!8m2!3d-6.8674332!4d109.1368485!9m1!1b1!16s%2Fg%2F1yg4ltf7r?entry=ttu&hl=id"
    )

    print("[2/8] Menghubungkan ke MongoDB Atlas...")
    try:
        client = MongoClient(mongo_uri)
        mongo_db = client['review_tempat_bersejarah_tegal']
        collection = mongo_db['reviews_data']
        print(f"[Sukses] Terhubung ke MongoDB Atlas. Koleksi: {collection.name}")
    except Exception as e:
        print(f"[Error] Gagal terhubung ke MongoDB: {str(e)}")
        return

    print("[3/8] Mengonfigurasi headless Chrome...")
    opts = Options()
    opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--disable-gpu')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    opts.add_argument('--lang=id')
    opts.add_experimental_option('prefs', {'intl.accept_languages': 'id,id_ID'})

    driver = None
    try:
        driver = webdriver.Chrome(options=opts)
        
        print(f"[4/8] Membuka Google Maps URL untuk: {test_target.nama_tempat}...")
        driver.get(test_target.url_maps)
        time.sleep(5)

        print("[5/8] Memeriksa keberadaan halaman persetujuan kuki Google...")
        if "consent.google.com" in driver.current_url:
            print("[Info] Terdeteksi halaman persetujuan kuki. Melakukan bypass...")
            try:
                xpath_tombol = "//button[contains(., 'Accept all') or contains(., 'Alles accepteren') or contains(., 'Tout accepter') or contains(., 'Alle akzeptieren') or contains(., 'Terima') or contains(., 'Setuju')]"
                tombol_setuju = driver.find_element(By.XPATH, xpath_tombol)
                tombol_setuju.click()
                time.sleep(5)
                print("[Sukses] Berhasil menekan tombol setuju kuki.")
            except:
                try:
                    semua_form = driver.find_elements(By.TAG_NAME, 'form')
                    if semua_form:
                        tombol_dalam_form = semua_form[0].find_elements(By.TAG_NAME, 'button')
                        if tombol_dalam_form:
                            tombol_dalam_form[-1].click()
                            time.sleep(5)
                            print("[Sukses] Berhasil menekan tombol form setuju kuki.")
                except Exception as form_error:
                    print(f"[Info] Gagal menekan tombol kuki: {str(form_error)}")

        debug_path = os.path.join('static', 'uploads')
        if not os.path.exists(debug_path):
            os.makedirs(debug_path)
        
        screenshot_file = os.path.join(debug_path, 'test_screenshot.png')
        driver.save_screenshot(screenshot_file)
        print(f"[Sukses] Tangkapan layar pengujian disimpan di: {screenshot_file}")

        print("[6/8] Mengubah urutan ulasan menjadi Terbaru...")
        sort_js = "function clickT(a){var e=document.querySelectorAll('button,div,span');for(var i=0;i<e.length;i++){for(var j=0;j<a.length;j++){if(e[i].innerText&&e[i].innerText.trim()===a[j]){e[i].click();return true}}}return false}; clickT(['Urutkan','Sort']); setTimeout(function(){clickT(['Terbaru','Newest'])},3000);"
        driver.execute_script(sort_js)
        time.sleep(10)

        print("[7/8] Mulai menggulir halaman (Scrolling) untuk memuat ulasan...")
        try:
            ref = driver.find_element(By.CLASS_NAME, "jftiEf")
            panel = driver.execute_script("return arguments[0].closest('div[tabindex=\"-1\"]');", ref)
        except Exception as panel_err:
            print(f"[Error] Gagal menemukan panel ulasan: {str(panel_err)}")
            return

        prev_count, no_change_count = 0, 0
        for i in range(100):
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', panel)
            time.sleep(4)
            curr_count = len(driver.find_elements(By.CLASS_NAME, 'jftiEf'))
            print(f" -> Putaran gulir ke-{i+1}: Berhasil memuat {curr_count}/100 ulasan...")
            
            if curr_count >= 100:
                print(" -> [Info] Target minimal 100 ulasan terpenuhi. Menghentikan guliran.")
                break

            if curr_count == prev_count:
                no_change_count += 1
            else:
                no_change_count, prev_count = 0, curr_count
            if no_change_count >= 3:
                print(" -> [Info] Tidak ada ulasan baru terdeteksi. Menghentikan guliran.")
                break

        print("[8/8] Mulai mengekstrak kartu ulasan dan menyimpan ke MongoDB...")
        cards = driver.find_elements(By.CLASS_NAME, 'jftiEf')[:100]
        print(f" -> Mengekstrak data dari {len(cards)} kartu ulasan...")
        
        operations = []
        extracted_count = 0

        for idx, c in enumerate(cards):
            try:
                name = c.get_attribute('aria-label') or ""
                rate_text = c.find_element(By.CLASS_NAME, 'kvMYJc').get_attribute('aria-label')
                tm = c.find_element(By.CLASS_NAME, 'rsqaWe').get_attribute('textContent').strip() # type: ignore
                
                try:
                    txt = c.find_element(By.CLASS_NAME, 'wiI7pd').get_attribute('textContent').strip() # type: ignore
                except:
                    continue

                match = re.search(r'(\d+)', rate_text) # type: ignore
                rating = int(match.group()) if match else 5

                raw_string = f"{test_target.nama_tempat}_{name}_{txt}"
                unique_id = hashlib.md5(raw_string.encode('utf-8')).hexdigest()

                review_data = {
                    "_id": unique_id,
                    "target_id": str(test_target.target_id),
                    "target_type": test_target.target_type,
                    "Lokasi": test_target.nama_tempat,
                    "Nama_User": name,
                    "Rating": rating,
                    "Waktu": tm,
                    "Ulasan": txt,
                    "Tanggal_Scraping": time.strftime("%Y-%m-%d")
                }

                operations.append(
                    UpdateOne(
                        {'_id': unique_id},
                        {'$set': review_data},
                        upsert=True
                    )
                )
                extracted_count += 1
            except Exception as card_error:
                continue

        if operations:
            print(f" -> Mengunggah {len(operations)} dokumen ulasan ke MongoDB Atlas...")
            collection.bulk_write(operations)
            print(f"[Sukses] Berhasil mengamankan {extracted_count} ulasan di MongoDB Atlas!")
        else:
            print("[Warning] Tidak ada dokumen ulasan bersih yang berhasil diekstrak.")

    except Exception as run_error:
        print(f"[Error] Terjadi kesalahan fatal selama pemrosesan: {str(run_error)}")
    finally:
        if driver:
            print("[Selesai] Menutup browser Chrome secara bersih...")
            driver.quit()

if __name__ == '__main__':
    run_standalone_test()