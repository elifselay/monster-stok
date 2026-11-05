"""
Monster High stok takip botu
Ürünler stoğa girince Telegram'dan mesaj atar.
"""
import json
import os
import re
import requests

# Takip etmek istediğin ürünleri buraya ekle (isim: link)
URUNLER = {
    "Draculaura JMG89 (Armağan)": "https://www.armaganoyuncak.com.tr/monster-high-dawn-of-the-dance-draculaura-bebek-jmg89-p-010101matjmg89",
    "Lagoona Blue JKM48 (Toyzz)": "https://www.toyzzshop.com/monster-high-dawn-of-the-dance-lagoona-blue-bebek-jkm48?serial=108958",
    "Cleo JKM47 (Toyzz)": "https://www.toyzzshop.com/monster-high-dawn-of-the-dance-cleo-bebek-jkm47?serial=108957",
    "Frankie Stein JKM46 (Toyzz)": "https://www.toyzzshop.com/monster-high-dawn-of-the-dance-frankie-stein-bebek-jkm46?serial=108956",
}

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
DURUM_DOSYASI = "durum.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept-Language": "tr-TR,tr;q=0.9",
}


def stokta_mi(html: str) -> bool:
    # 1) Sayfadaki ürün verisine bak (en güvenilir yol)
    m = re.search(r'"availability"\s*:\s*"https?://schema\.org/(\w+)"', html)
    if m:
        return m.group(1) == "InStock"
    # 2) Yedek: buton yazılarına bak
    kucuk = html.lower()
    for ifade in ["stokta olduğunda bana bildir", "gelince haber ver", "stokta yok", "tükendi"]:
        if ifade in kucuk:
            return False
    return "sepete ekle" in kucuk


def telegram_gonder(mesaj: str):
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={"chat_id": TELEGRAM_CHAT_ID, "text": mesaj},
        timeout=15,
    )


def main():
    try:
        with open(DURUM_DOSYASI) as f:
            onceki = json.load(f)
    except FileNotFoundError:
        onceki = {}

    yeni = {}
    for isim, link in URUNLER.items():
        try:
            r = requests.get(link, headers=HEADERS, timeout=20)
            simdi = stokta_mi(r.text)
        except Exception as e:
            print(f"{isim}: hata ({e})")
            yeni[isim] = onceki.get(isim, False)
            continue

        print(f"{isim}: {'STOKTA ✅' if simdi else 'yok ❌'}")
        # Sadece "yok -> var" olunca haber ver (sürekli mesaj atmasın)
        if simdi and not onceki.get(isim, False):
            telegram_gonder(f"🚨 STOK GELDİ!\n{isim}\n{link}")
        yeni[isim] = simdi

    with open(DURUM_DOSYASI, "w") as f:
        json.dump(yeni, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
