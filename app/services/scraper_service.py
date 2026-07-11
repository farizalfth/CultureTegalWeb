import os
import threading
import uuid
import time
import hashlib
import re
from datetime import datetime, timedelta
from app.models import db, ScrapeTarget
from pymongo import MongoClient, UpdateOne
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class ScraperService:
    progress = {
        "running": False,
        "current": 0,
        "total": 0,
        "status": "Idle",
        "last_run": None
    }

    @staticmethod
    def validate_url(url):
        if not url:
            return False
        pattern = re.compile(
            r'^https?://([a-zA-Z0-9-]+\.)*(google\.[a-z]+|maps\.app\.goo\.gl|goo\.gl)/maps.*', 
            re.IGNORECASE
        )
        return bool(pattern.match(url))

    @staticmethod
    def clean_text(text):
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        words = text.split()
        
        custom_stopwords = {
            'dan', 'di', 'yang', 'ke', 'dari', 'ini', 'itu', 'ada', 'adalah', 
            'bisa', 'sangat', 'untuk', 'juga', 'dengan', 'pada', 'saya', 
            'kita', 'kami', 'mereka', 'dia', 'akan', 'telah', 'sudah', 'oleh',
            'atau', 'jika', 'karena', 'namun', 'tetapi', 'bahwa', 'secara', 
            'tersebut', 'banyak', 'beberapa', 'maupun', 'dalam', 'tentang'
        }
        
        try:
            import nltk
            from nltk.corpus import stopwords
            try:
                indonesian_stopwords = set(stopwords.words('indonesian'))
            except LookupError:
                nltk.download('stopwords', quiet=True)
                indonesian_stopwords = set(stopwords.words('indonesian'))
            indonesian_stopwords.update(custom_stopwords)
        except ImportError:
            indonesian_stopwords = custom_stopwords
            
        filtered_words = [w for w in words if w not in indonesian_stopwords and len(w) > 2]
        return " ".join(filtered_words)

    @staticmethod
    def calculate_absolute_date(waktu_str):
        text = waktu_str.lower()
        text = re.sub(r'(diedit|edited)\s+', '', text).strip()
        
        match = re.search(r'\d+', text)
        number = int(match.group()) if match else 1
        
        now = datetime.now()
        
        if 'tahun' in text or 'year' in text:
            dt = now - timedelta(days=number * 365)
        elif 'bulan' in text or 'month' in text:
            dt = now - timedelta(days=number * 30)
        elif 'minggu' in text or 'week' in text:
            dt = now - timedelta(days=number * 7)
        elif 'hari' in text or 'day' in text:
            dt = now - timedelta(days=number)
        elif 'jam' in text or 'hour' in text:
            dt = now - timedelta(hours=number)
        elif 'menit' in text or 'minute' in text:
            dt = now - timedelta(minutes=number)
        else:
            dt = now
            
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def get_word_frequencies(location_name, mongo_uri):
        client = MongoClient(mongo_uri)
        db_mongo = client['review_tempat_bersejarah_tegal']
        collection = db_mongo['reviews_data']
        reviews = collection.find({"Lokasi": location_name})
        word_counts = {}
        for r in reviews:
            cleaned = ScraperService.clean_text(r.get("Ulasan", "")) # type: ignore
            for word in cleaned.split():
                word_counts[word] = word_counts.get(word, 0) + 1
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:50]
        return [{"text": k, "value": v} for k, v in sorted_words]

    @staticmethod
    def run_scraping_job(mongo_uri):
        if ScraperService.progress["running"]:
            return
        
        ScraperService.progress["running"] = True
        ScraperService.progress["current"] = 0
        ScraperService.progress["status"] = "Initializing scraper..."
        
        from flask import current_app
        app = current_app._get_current_object() # type: ignore
        
        thread = threading.Thread(target=ScraperService._execute_scrape, args=(app, mongo_uri))
        thread.start()

    @staticmethod
    def _execute_scrape(app, mongo_uri):
        with app.app_context():
            try:
                targets = ScrapeTarget.query.all()
                total_targets = len(targets)
                ScraperService.progress["total"] = total_targets
                
                if total_targets == 0:
                    ScraperService.progress["running"] = False
                    ScraperService.progress["status"] = "No targets configured."
                    return

                opts = Options()
                opts.add_argument('--headless')
                opts.add_argument('--no-sandbox')
                opts.add_argument('--disable-dev-shm-usage')
                opts.add_argument('--disable-gpu')
                opts.add_argument('--window-size=1920,1080')
                opts.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                opts.add_argument('--lang=id')
                opts.add_experimental_option('prefs', {'intl.accept_languages': 'id,id_ID'})
                
                driver = webdriver.Chrome(options=opts)
                
                if not mongo_uri:
                    mongo_uri = os.getenv("MONGO_URI")

                if not mongo_uri:
                    raise Exception("MONGO_URI connection string is missing in .env")

                client = MongoClient(mongo_uri)
                mongo_db = client['review_tempat_bersejarah_tegal']
                collection = mongo_db['reviews_data']

                for index, target in enumerate(targets):
                    ScraperService.progress["current"] = index + 1
                    ScraperService.progress["status"] = f"Scraping {target.nama_tempat} (Memulai...)"
                    
                    url = target.url_maps
                    if "hl=id" not in url:
                        url += "&hl=id" if "?" in url else "?hl=id"

                    driver.get(url)
                    time.sleep(5)

                    if "consent.google.com" in driver.current_url:
                        try:
                            xpath_tombol = "//button[contains(., 'Accept all') or contains(., 'Alles accepteren') or contains(., 'Tout accepter') or contains(., 'Alle akzeptieren') or contains(., 'Terima') or contains(., 'Setuju')]"
                            tombol_setuju = driver.find_element(By.XPATH, xpath_tombol)
                            tombol_setuju.click()
                            time.sleep(5)
                        except:
                            try:
                                semua_form = driver.find_elements(By.TAG_NAME, 'form')
                                if semua_form:
                                    tombol_dalam_form = semua_form[0].find_elements(By.TAG_NAME, 'button')
                                    if tombol_dalam_form:
                                        tombol_dalam_form[-1].click()
                                        time.sleep(5)
                            except:
                                pass

                    debug_path = os.path.join(app.root_path, 'static', 'uploads')
                    if not os.path.exists(debug_path):
                        os.makedirs(debug_path)
                    driver.save_screenshot(os.path.join(debug_path, 'debug_screenshot.png'))

                    sort_js = "function clickT(a){var e=document.querySelectorAll('button,div,span');for(var i=0;i<e.length;i++){for(var j=0;j<a.length;j++){if(e[i].innerText&&e[i].innerText.trim()===a[j]){e[i].click();return true}}}return false}; clickT(['Urutkan','Sort']); setTimeout(function(){clickT(['Terbaru','Newest'])},3000);"
                    driver.execute_script(sort_js)
                    time.sleep(10)

                    try:
                        ref = driver.find_element(By.CLASS_NAME, "jftiEf")
                        panel = driver.execute_script("return arguments[0].closest('div[tabindex=\"-1\"]');", ref) # type: ignore
                    except:
                        continue

                    limit_count = target.max_reviews if getattr(target, 'max_reviews', None) else 100

                    prev_count, no_change_count = 0, 0
                    for _ in range(100):
                        driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', panel) # type: ignore
                        time.sleep(4)
                        
                        text_elements = driver.find_elements(By.CLASS_NAME, 'wiI7pd')
                        curr_text_count = sum(1 for el in text_elements if el.get_attribute('textContent').strip()) # type: ignore
                        
                        ScraperService.progress["status"] = f"Scraping {target.nama_tempat} (Memuat {curr_text_count}/{limit_count} ulasan berteks...)"
                        
                        if curr_text_count >= limit_count:
                            break

                        curr_total_count = len(driver.find_elements(By.CLASS_NAME, 'jftiEf'))
                        if curr_total_count == prev_count:
                            no_change_count += 1
                        else:
                            no_change_count, prev_count = 0, curr_total_count
                        if no_change_count >= 3:
                            break

                    cards = driver.find_elements(By.CLASS_NAME, 'jftiEf')
                    ScraperService.progress["status"] = f"Mengekstrak ulasan dari {target.nama_tempat}..."
                    operations = []
                    text_count = 0
                    
                    for c in cards:
                        try:
                            name = c.get_attribute('aria-label') or ""
                            rate_text = c.find_element(By.CLASS_NAME, 'kvMYJc').get_attribute('aria-label') # type: ignore
                            tm = c.find_element(By.CLASS_NAME, 'rsqaWe').get_attribute('textContent').strip() # type: ignore
                            
                            try:
                                txt = c.find_element(By.CLASS_NAME, 'wiI7pd').get_attribute('textContent').strip() # type: ignore
                            except:
                                txt = ""

                            if txt != "":
                                if text_count >= limit_count:
                                    continue
                                text_count += 1

                            match = re.search(r'(\d+)', rate_text) # type: ignore
                            rating = int(match.group()) if match else 5

                            waktu_bersih = re.sub(r'(diedit|edited)\s+', '', tm.lower()).strip()
                            tanggal_review = ScraperService.calculate_absolute_date(tm)

                            raw_string = f"{target.nama_tempat}_{name}_{txt}"
                            unique_id = hashlib.md5(raw_string.encode('utf-8')).hexdigest()

                            review_data = {
                                "_id": unique_id,
                                "target_id": str(target.target_id),
                                "target_type": target.target_type,
                                "Lokasi": target.nama_tempat,
                                "Nama_User": name,
                                "Rating": rating,
                                "Waktu": waktu_bersih,
                                "Tanggal_Review": tanggal_review,
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
                        except Exception as card_error:
                            print(f"Error parsing card: {str(card_error)}")
                            continue

                    if operations:
                        collection.bulk_write(operations)

                driver.quit()
                ScraperService.progress["status"] = "Success"
            except Exception as e:
                ScraperService.progress["status"] = f"Failed: {str(e)}"
            finally:
                ScraperService.progress["running"] = False
                ScraperService.progress["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")