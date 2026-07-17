# audio_describer/models/prompt_model.py
import json
import os
# from . import config_model  <- This was causing the circular import.
from ..utils.logger import app_logger

PROMPTS_FILE_NAME = "prompts.json"
PROMPTS_FILE_PATH = None # Initialize as None

DEFAULT_PROMPTS = {
    "en": [
        {
            "name": "Movie Trailer",
            "prompt": "This is a movie trailer. Focus on fast-paced, impactful, and iconic shots. Prioritize describing key action moments, dramatic character introductions, and any on-screen text like release dates or studio logos. Create a sense of excitement and hint at the plot without revealing spoilers. Descriptions must be extremely brief to fit between quick cuts."
        },
        {
            "name": "Action Movie",
            "prompt": "This is an action movie . Focus on the core choreography of the action: significant punches, kicks, dodges, and use of weapons. Describe large-scale events like explosions or car chases. Keep descriptions concise and impactful to match the high-energy pacing."
        },
        {
            "name": "Romantic Movie",
            "prompt": "This is a romantic movie. Prioritize describing the characters' proximity to each other, meaningful touches (like holding hands), and significant facial expressions that show affection, longing, or conflict. Describe the romantic atmosphere of the setting (e.g., 'candlelit dinner,' 'walk on a moonlit beach')."
        },
        {
            "name": "Comedy / Sitcom",
            "prompt": "This is a comedic content. Focus on the visual gags, physical comedy, and absurd situations. Describe exaggerated reactions and comical expressions that are key to the joke. The timing of the description is crucial to land the punchline, so be brief and place it right after the visual gag occurs."
        },
        {
            "name": "Sci-Fi / Fantasy",
            "prompt": "This is a sci-fi/fantasy . Focus on describing the unique world elements. Describe futuristic technology, fantastical creatures, magical effects, and otherworldly landscapes. Explain what makes the visual elements different from the real world (e.g., 'A ship with glowing sails flies through a purple nebula.')."
        },
        {
            "name": "Meme / Viral Video",
            "prompt": "This is a short meme or viral video. The goal is to describe the core visual joke or unexpected event as concisely as possible. Identify the key subject and the one action that makes the video funny or interesting. On-screen captions are highly important (e.g., 'A cat wearing sunglasses nods its head to a beat. Caption: Vibing.')."
        },
        {
            "name": "Documentary / Educational",
            "prompt": "This is a documentary/educational video. Prioritize describing on-screen text, labels, graphics, maps, and archival footage. For people, focus on their actions as they relate to the subject matter (e.g., 'The biologist points to a specific plant.'). Maintain a neutral, informative tone."
        },
        {
            "name": "Cooking / Recipe",
            "prompt": "This is a cooking video. Describe the specific ingredients as they are added and the cooking techniques shown (e.g., 'dicing the onion,' 'searing the steak'). Describe the visual state and texture of the food at key stages (e.g., 'The sauce thickens to a glossy consistency.')."
        },
        {
            "name": "DIY / Tutorial",
            "prompt": "This is a tutorial or DIY video. Focus on the step-by-step process. Clearly describe the specific tools and materials used. Detail the action being performed on the object, and describe the state of the object before and after the action (e.g., 'He drills a hole through the marked spot on the plank.')."
        },
        {
            "name": "Gaming / Let's Play",
            "prompt": "This is a video game recording. Prioritize describing critical on-screen UI elements (the HUD), such as health bars, ammo count, or mini-maps if they change. Describe the main character/avatar's actions within the game world (e.g., 'The character casts a fire spell,' 'They jump to the next platform.')."
        }
    ],
    "tr": [
        {
            "name": "Fragman",
            "prompt": "Bu bir film fragmanıdır. Hızlı tempolu, etkili ve ikonik çekimlere odaklan. Kilit aksiyon anlarını, dramatik karakter girişlerini ve vizyon tarihleri veya stüdyo logoları gibi ekrandaki metinleri betimlemeye öncelik ver. Spoiler  vermeden bir heyecan hissi yarat ve konuya dair ipuçları ver. Betimlemeler, hızlı kesitler arasına sığabilmesi için son derece kısa olmalıdır."
        },
        {
            "name": "Aksiyon Film",
            "prompt": "Bu bir aksiyon videosudur. Aksiyonun temel koreografisine odaklan: önemli yumruklar, tekmeler, kaçışlar ve silah kullanımı. Patlamalar veya araba kovalamacaları gibi büyük ölçekli olayları betimle. Yüksek enerjili tempoya uymak için betimlemeleri kısa ve etkili tut."
        },
        {
            "name": "Romantik Film",
            "prompt": "Bu bir romantik videodur. Karakterlerin birbirine olan yakınlığını, (el ele tutuşmak gibi) anlamlı dokunuşlarını ve sevgi, özlem veya çatışma gösteren önemli yüz ifadelerini betimlemeye öncelik ver. Mekanın romantik atmosferini betimle (örneğin, 'mum ışığında bir akşam yemeği,' 'ay ışığında bir kumsalda yürüyüş')."
        },
        {
            "name": "Komedi / Sitcom",
            "prompt": "Bu bir komedi videosudur. Görsel şakalara, fiziksel komediye ve absürt durumlara odaklan. Şakanın anahtarı olan abartılı tepkileri ve komik ifadeleri betimle. Betimlemenin zamanlaması, esprinin etkili olması için kritiktir, bu yüzden kısa ol ve görsel şaka gerçekleştikten hemen sonra yerleştir."
        },
        {
            "name": "Bilim Kurgu / Fantastik",
            "prompt": "Bu bir bilim kurgu/fantastik videosudur. Benzersiz dünya unsurlarını betimlemeye odaklan. Fütüristik teknolojiyi, fantastik yaratıkları, sihirli efektleri ve dünya dışı manzaraları betimle. Görsel unsurları gerçek dünyadan farklı kılan şeyleri açıkla (örneğin, 'Parlayan yelkenleri olan bir gemi, mor bir bulutsunun içinde uçuyor.')."
        },
        {
            "name": "Meme / Viral Video",
            "prompt": "Bu kısa bir meme veya viral videodur. Amaç, temel görsel şakayı veya beklenmedik olayı mümkün olan en kısa şekilde betimlemektir. Videoyu komik veya ilginç kılan ana özneyi ve tek eylemi belirle. Ekran üzerindeki yazılar son derece önemlidir (örneğin, 'Güneş gözlüğü takan bir kedi, bir ritme başını sallıyor. Altyazı: Modunda.')."
        },
        {
            "name": "Belgesel / Bilgilendirici",
            "prompt": "Bu bir belgesel/eğitici videodur. Ekrandaki metinleri, etiketleri, grafikleri, haritaları ve arşiv görüntülerini betimlemeye öncelik ver. İnsanlar için, konuyla ilgili eylemlerine odaklan (örneğin, \"Biyolog belirli bir bitkiyi işaret ediyor\"). Sade ve bilgilendirici bir ton kullan."},
        {
            "name": "Yemek / Tarif",
            "prompt": "Bu bir yemek pişirme videosudur. Eklenen belirli malzemeleri ve gösterilen pişirme tekniklerini (örneğin, 'soğanı küp küp doğruyor,' 'bifteği mühürlüyor') betimle. Yemeğin kilit aşamalardaki görsel durumunu ve dokusunu betimle (örneğin, 'Sos, parlak bir kıvama gelene kadar koyulaşır.')."},
        {
            "name": "Kendin Yap / Eğitici Video",
            "prompt": "Bu bir eğitici veya kendin yap videosudur. Adım adım ilerleyen sürece odaklan. Kullanılan belirli araçları ve malzemeleri net bir şekilde betimle. Nesne üzerinde gerçekleştirilen eylemi ve eylemden önceki ve sonraki durumunu detaylandır (örneğin, 'Tahtanın üzerindeki işaretli noktaya bir delik açıyor.')."},
        {
            "name": "Oyun / Oynanış Videosu Odağı",
            "prompt": "Bu bir video oyunu kaydıdır. Sağlık çubukları, mermi sayısı veya mini haritalar gibi kritik ekran arayüzü (HUD) ögelerini, değiştiklerinde betimlemeye öncelik ver. Ana karakterin/avatarın oyun dünyasındaki eylemlerini betimle (örneğin, 'Karakter bir ateş büyüsü yapıyor,' 'Bir sonraki platforma zıyplıyor)."}
    ]
}

# In-memory cache for prompts
_prompts_cache = {}

def _get_prompts_file_path():
    """Gets the prompts file path, importing config_model locally."""
    global PROMPTS_FILE_PATH
    if PROMPTS_FILE_PATH is None:
        # Import locally to break the circular dependency at startup.
        from . import config_model
        PROMPTS_FILE_PATH = os.path.join(config_model.APP_DATA_DIR, PROMPTS_FILE_NAME)
    return PROMPTS_FILE_PATH


def _get_default_prompts_for_lang(lang_code):
    """Returns a copy of the default prompts for a specific language."""
    return DEFAULT_PROMPTS.get(lang_code, []).copy()

def load_prompts():
    """Loads all prompts from the JSON file into the cache."""
    global _prompts_cache
    
    file_path = _get_prompts_file_path()

    if not os.path.exists(file_path):
        app_logger.info(f"Prompts file not found at {file_path}. Creating with defaults.")
        _prompts_cache = DEFAULT_PROMPTS.copy()
        save_prompts()
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            _prompts_cache = json.load(f)
        # Ensure all default languages are present
        updated = False
        for lang_code, default_list in DEFAULT_PROMPTS.items():
            if lang_code not in _prompts_cache:
                _prompts_cache[lang_code] = default_list.copy()
                updated = True
        if updated:
            save_prompts()
        app_logger.info(f"Prompts loaded successfully from {file_path}.")
    except (json.JSONDecodeError, IOError) as e:
        app_logger.error(f"Error loading prompts from {file_path}: {e}. Using default prompts.")
        _prompts_cache = DEFAULT_PROMPTS.copy()

def save_prompts():
    """Saves the current state of the prompts cache to the JSON file."""
    global _prompts_cache
    
    file_path = _get_prompts_file_path()

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(_prompts_cache, f, indent=4, ensure_ascii=False)
        app_logger.info(f"Prompts saved successfully to {file_path}.")
        return True
    except IOError as e:
        app_logger.error(f"Error saving prompts to {file_path}: {e}")
        return False

def get_prompts_for_language(lang_code):
    """
    Returns a list of prompt dictionaries for a given language.
    Returns a default list if the language is not found.
    """
    if not _prompts_cache:
        load_prompts()
    return _prompts_cache.get(lang_code, _get_default_prompts_for_lang(lang_code))

def set_prompts_for_language(lang_code, prompts_list):
    """
    Sets the entire list of prompts for a language and saves.
    """
    if not isinstance(prompts_list, list):
        app_logger.error(f"set_prompts_for_language: provided prompts is not a list for lang '{lang_code}'.")
        return False

    _prompts_cache[lang_code] = prompts_list
    return save_prompts()

# REMOVED the line "load_prompts()" from the end of the file.