# coding=utf-8
# Bing Images Domain Scraper - Menggunakan cloudscraper (anti-deteksi)
import os
import re
import json
import html
import time
import random
from urllib.parse import urlparse, quote
import cloudscraper  # pip install cloudscraper

# Warna manual (opsional)
GREEN = '\033[92m'
CYAN = '\033[96m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def log(msg, color=RESET):
    print(f"{color}{msg}{RESET}")

def extract_domains(html_content):
    """Ekstrak domain dari atribut m (JSON) di tag a.iusc"""
    domains = set()
    pattern = r'<a[^>]+class="iusc"[^>]+m="([^"]+)"'
    for match in re.finditer(pattern, html_content):
        m_val = html.unescape(match.group(1))
        try:
            data = json.loads(m_val)
            purl = data.get('purl')
            if purl:
                domain = urlparse(purl).netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
                domains.add(domain)
        except:
            continue
    return domains

def search_keyword(keyword, max_pages=2, retries=2):
    """Cari keyword dengan cloudscraper, otomatis retry jika gagal"""
    scraper = cloudscraper.create_scraper()
    base_url = "https://www.bing.com/images/search"
    found_domains = set()
    
    for page in range(max_pages):
        first = page * 36 + 1
        params = {'q': keyword, 'first': first, 'form': 'HDRSC3'}
        url = base_url
        
        for attempt in range(retries):
            try:
                resp = scraper.get(url, params=params, timeout=30)
                if resp.status_code == 200:
                    domains = extract_domains(resp.text)
                    found_domains.update(domains)
                    log(f"      Halaman {page+1}: {len(domains)} domain", GREEN)
                    break
                else:
                    log(f"      Halaman {page+1}: HTTP {resp.status_code} (percobaan {attempt+1}/{retries})", RED)
                    time.sleep(5)
            except Exception as e:
                log(f"      Halaman {page+1} error: {str(e)[:60]} (percobaan {attempt+1}/{retries})", RED)
                time.sleep(5)
        else:
            log(f"      Gagal mengambil halaman {page+1}", RED)
        
        time.sleep(random.uniform(1.5, 3))
    
    return found_domains

def main():
    log("=== Bing Images Domain Scraper (cloudscraper) ===", CYAN)
    log("Mendukung daftar keyword besar, otomatis retry jika koneksi tertutup\n", CYAN)
    
    keyword_file = input("[+] File daftar keyword (.txt): ").strip()
    try:
        with open(keyword_file, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip()]
    except Exception as e:
        log(f"Error membaca file: {e}", RED)
        return
    
    if not keywords:
        log("Tidak ada keyword.", RED)
        return
    
    try:
        pages = int(input("[+] Halaman per keyword (1-3, default 2): ") or 2)
        pages = max(1, min(pages, 3))
    except:
        pages = 2
    
    output_file = input("[+] Nama file output (default: bing_domains.txt): ").strip()
    if not output_file:
        output_file = "bing_domains.txt"
    
    if os.path.exists(output_file):
        os.remove(output_file)
    
    all_domains = set()
    total = len(keywords)
    
    log(f"\nMemulai {total} keyword, masing-masing {pages} halaman\n", CYAN)
    print("-" * 60)
    
    for idx, kw in enumerate(keywords, 1):
        log(f"[{idx}/{total}] Keyword: {kw[:50]}", CYAN)
        try:
            domains = search_keyword(kw, pages)
            new_domains = domains - all_domains
            all_domains.update(domains)
            
            if new_domains:
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write('\n'.join(new_domains) + '\n')
                log(f"  ✓ {len(new_domains)} domain baru (total {len(all_domains)})", GREEN)
            else:
                log("  ℹ️  Tidak ada domain baru", RESET)
        except Exception as e:
            log(f"  ✗ Error: {e}", RED)
        
        # Jeda antar keyword (sangat penting untuk menghindari blokir)
        delay = random.uniform(5, 10)
        log(f"  Menunggu {delay:.1f} detik sebelum keyword berikutnya...", YELLOW)
        time.sleep(delay)
        print()
    
    print("-" * 60)
    log(f"\nSelesai. Total domain unik: {len(all_domains)}", GREEN)
    log(f"Disimpan di: {output_file}", GREEN)
    
    if all_domains:
        print("\n20 domain pertama:")
        for d in sorted(all_domains)[:20]:
            print(f"  {d}")

if __name__ == "__main__":
    main()
