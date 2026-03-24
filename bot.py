import discord
from discord.ext import tasks, commands
import requests
import os # Bu yeni eklendi
import feedparser

# --- AYARLAR ---
TOKEN = 'token' 
CHANNEL_ID = 1453478819490168933 # SENİN KANAL ID'N
SENT_GAMES_FILE = "free_games1" # Hafıza dosyası
# ---------------

EPIC_FREE_GAMES_URL = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions?locale=tr-TR&country=TR&allowCountries=TR"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():                                                       
    print(f'Sistem aktif! {bot.user} sunucuya giriş yaptı.')
    if not check_epic_games.is_running():
        check_epic_games.start()

@tasks.loop(minutes=1) # Her saat başı kontrol
async def check_epic_games():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel: return

    # Daha önce paylaşılanları dosyadan oku
    if os.path.exists(SENT_GAMES_FILE):
        with open(SENT_GAMES_FILE, "r", encoding="utf-8") as f:
            sent_games = f.read().splitlines()
    else:
        sent_games = []

    try:
        response = requests.get(EPIC_FREE_GAMES_URL)
        data = response.json()
        games = data['data']['Catalog']['searchStore']['elements']
        
        for game in games:
            promotions = game.get('promotions')
            if promotions and promotions.get('promotionalOffers'):
                offers = promotions['promotionalOffers'][0]['promotionalOffers']
                for offer in offers:
                    if offer.get('discountSetting', {}).get('discountPercentage') == 0:
                        title = game['title']
                        
                        # --- BU KISIMDAN İTİBAREN YENİ KODU YAPIŞTIR ---
                        if title not in sent_games:
                            slug = game.get('productSlug') or game['catalogNs']['mappings'][0]['pageSlug']
                            url = f"https://store.epicgames.com/tr/p/{slug}"
                            image = game['keyImages'][0]['url']
                            
                            embed = discord.Embed(title=f"🎁 Yeni Ücretsiz Oyun: {title}", color=0x2f3136, url=url)
                            embed.set_image(url=image)
                            embed.add_field(name="Hemen Al", value=f"[Buraya Tıkla]({url})")
                            
                            # 1. MESAJI GÖNDERİRKEN @everyone EKLE
                            sent_msg = await channel.send(content="@everyone Yeni ücretsiz oyun geldi!", embed=embed)
                            
                            # 2. EĞER KANAL DUYURU KANALIYSA OTOMATİK YAYINLA
                            try:
                                if channel.type == discord.ChannelType.news:
                                    await sent_msg.publish()
                                    print(f"{title} duyuru kanalında yayınlandı.")
                            except Exception as publish_error:
                                print(f"Yayınlama hatası: {publish_error}")

                            # Paylaşılanlar listesine ekle ve dosyaya kaydet
                            with open(SENT_GAMES_FILE, "a", encoding="utf-8") as f:
                                f.write(title + "\n")
                            print(f"{title} başarıyla paylaşıldı ve hafızaya alındı.")
                        # --- YENİ KOD BURADA BİTİYOR ---
    except Exception as e:
        print(f"Hata oluştu: {e}")

bot.run(TOKEN)
