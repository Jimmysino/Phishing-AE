import json
import re
import socket
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

try:
    import tldextract
    _USE_TLDEXTRACT = True
except ImportError:
    _USE_TLDEXTRACT = False

_FEATURES_PATH = Path(__file__).parent / "json_perfecto.json"
_SOCIAL_NETS = {"facebook.com", "twitter.com", "instagram.com", "linkedin.com",
                "youtube.com", "tiktok.com", "pinterest.com", "reddit.com"}
_BANK_KEYWORDS = {"bank", "banco", "banking", "credit", "credito", "loan",
                  "mortgage", "financial", "finance", "savings", "invest"}
_PAY_KEYWORDS = {"pay", "payment", "checkout", "billing", "invoice", "transfer",
                 "wallet", "paypal", "stripe", "venmo"}
_CRYPTO_KEYWORDS = {"crypto", "bitcoin", "btc", "ethereum", "eth", "blockchain",
                    "nft", "defi", "token", "wallet", "binance", "coinbase"}

# TLDs considerados de alta legitimidad (prob cercana a 1.0)
_HIGH_LEGIT_TLDS = {"com", "org", "net", "edu", "gov", "mil", "int",
                    "co.uk", "co.jp", "co.au", "ac.uk", "gov.uk"}
# TLDs frecuentemente asociados a phishing (prob baja)
_SUSPICIOUS_TLDS = {"tk", "ml", "ga", "cf", "gq", "pw", "top", "xyz",
                    "icu", "site", "online", "click", "link", "work"}

_OBFUSCATED_PATTERN = re.compile(r'%[0-9A-Fa-f]{2}|\\u[0-9A-Fa-f]{4}|&#\d+;|&[a-z]+;')
# Caracteres especiales relevantes para phishing (excluyendo ://. que son normales en URLs)
_SPECIAL_CHARS = set('!@#$^*[]{}|;\'",<>`~')
_REQUEST_TIMEOUT = 6

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
}


def _load_feature_keys() -> list[str]:
    with open(_FEATURES_PATH, "r") as f:
        data = json.load(f)
    return list(data["features"].keys())


def _parse_url(url: str) -> dict:
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        parsed = urllib.parse.urlparse("")

    netloc = parsed.netloc or ""
    host = netloc.split(":")[0] if ":" in netloc else netloc

    if _USE_TLDEXTRACT:
        ext = tldextract.extract(url)
        domain = ext.domain + ("." + ext.suffix if ext.suffix else "")
        tld = ext.suffix or ""
        subdomains = ext.subdomain or ""
        registered_domain = ext.registered_domain or host
    else:
        parts = host.split(".")
        tld = parts[-1] if len(parts) >= 2 else ""
        domain = ".".join(parts[-2:]) if len(parts) >= 2 else host
        subdomains = ".".join(parts[:-2]) if len(parts) > 2 else ""
        registered_domain = domain

    return {
        "url": url,
        "parsed": parsed,
        "host": host,
        "domain": domain,
        "registered_domain": registered_domain,
        "tld": tld,
        "subdomains": subdomains,
        "path": parsed.path or "",
        "query": parsed.query or "",
        "scheme": parsed.scheme or "",
    }


def _is_ip(host: str) -> bool:
    try:
        socket.inet_aton(host)
        return True
    except socket.error:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, host.strip("[]"))
        return True
    except (socket.error, OSError):
        return False


def _char_continuation_rate(url: str) -> float:
    """Ratio de pares de caracteres consecutivos iguales respecto al total de pares."""
    if len(url) < 2:
        return 0.0
    pairs = len(url) - 1
    consecutive = sum(1 for i in range(pairs) if url[i] == url[i + 1])
    return consecutive / pairs


def _tld_legitimate_prob(tld: str) -> float:
    """Heurística de probabilidad de legitimidad según el TLD."""
    tld_lower = tld.lower()
    if tld_lower in _HIGH_LEGIT_TLDS:
        return 0.9
    if tld_lower in _SUSPICIOUS_TLDS:
        return 0.1
    # TLDs de país genéricos → probabilidad media
    if len(tld_lower) == 2:
        return 0.6
    return 0.4


def _url_char_prob(url: str) -> float:
    """
    Probabilidad heurística basada en composición de caracteres de la URL.
    URLs legítimas tienen alto ratio de letras y bajo ratio de caracteres raros.
    """
    if not url:
        return 0.0
    letters = sum(1 for c in url if c.isalpha())
    digits = sum(1 for c in url if c.isdigit())
    normal = letters + digits + url.count('.') + url.count('/') + url.count(':') + url.count('-') + url.count('_')
    return min(normal / len(url), 1.0)


def _fetch_html(url: str) -> tuple[str | None, int]:
    """Retorna (html_text, redirect_count). html es None si falla."""
    try:
        session = requests.Session()
        resp = session.get(
            url,
            timeout=_REQUEST_TIMEOUT,
            headers=_HEADERS,
            allow_redirects=True,
        )
        return resp.text, len(resp.history)
    except Exception:
        return None, 0


def _check_robots(url: str) -> float:
    try:
        parsed = urllib.parse.urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        resp = requests.get(robots_url, timeout=_REQUEST_TIMEOUT, headers=_HEADERS)
        return 1.0 if resp.status_code == 200 and len(resp.text) > 0 else 0.0
    except Exception:
        return 0.0


def _extract_html_features(html: str | None, url: str, parsed_url: dict) -> dict:
    defaults = {
        "LineOfCode": 0.0, "LargestLineLength": 0.0, "HasTitle": 0.0,
        "DomainTitleMatchScore": 0.0, "URLTitleMatchScore": 0.0,
        "HasFavicon": 0.0, "IsResponsive": 0.0, "NoOfSelfRedirect": 0.0,
        "HasDescription": 0.0, "NoOfPopup": 0.0, "NoOfiFrame": 0.0,
        "HasExternalFormSubmit": 0.0, "HasSocialNet": 0.0, "HasSubmitButton": 0.0,
        "HasHiddenFields": 0.0, "HasPasswordField": 0.0, "HasCopyrightInfo": 0.0,
        "NoOfImage": 0.0, "NoOfCSS": 0.0, "NoOfJS": 0.0,
        "NoOfSelfRef": 0.0, "NoOfEmptyRef": 0.0, "NoOfExternalRef": 0.0,
    }
    if html is None:
        return defaults

    lines = html.splitlines()
    defaults["LineOfCode"] = float(len(lines))
    defaults["LargestLineLength"] = float(max((len(l) for l in lines), default=0))

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return defaults

    # Title
    title_tag = soup.find("title")
    title_text = title_tag.get_text(strip=True).lower() if title_tag else ""
    defaults["HasTitle"] = 1.0 if title_text else 0.0

    domain_lower = parsed_url["domain"].lower().replace("www.", "")
    if title_text and domain_lower:
        defaults["DomainTitleMatchScore"] = 1.0 if domain_lower in title_text else 0.0
        url_words = set(re.split(r'[\W_]+', parsed_url["url"].lower()))
        title_words = set(re.split(r'[\W_]+', title_text)) - {""}
        overlap = len(url_words & title_words)
        defaults["URLTitleMatchScore"] = min(float(overlap) / max(len(title_words), 1), 1.0)

    # Favicon
    favicon = soup.find("link", rel=lambda r: r and "icon" in " ".join(r).lower())
    defaults["HasFavicon"] = 1.0 if favicon else 0.0

    # Responsive (viewport meta)
    viewport = soup.find("meta", attrs={"name": re.compile("viewport", re.I)})
    defaults["IsResponsive"] = 1.0 if viewport else 0.0

    # Description meta
    desc = soup.find("meta", attrs={"name": re.compile("description", re.I)})
    defaults["HasDescription"] = 1.0 if desc else 0.0

    # Popups (window.open en scripts)
    scripts = soup.find_all("script")
    popup_count = 0
    for s in scripts:
        if s.string:
            popup_count += len(re.findall(r'window\.open\s*\(', s.string))
    defaults["NoOfPopup"] = float(popup_count)

    # iFrames
    defaults["NoOfiFrame"] = float(len(soup.find_all("iframe")))

    # Forms con acción externa
    base_domain = parsed_url["registered_domain"]
    forms = soup.find_all("form")
    external_form = 0
    for form in forms:
        action = form.get("action", "")
        if action and action.startswith("http") and base_domain not in action:
            external_form = 1
            break
    defaults["HasExternalFormSubmit"] = float(external_form)

    # Redes sociales en enlaces
    all_links = [a.get("href", "") for a in soup.find_all("a", href=True)]
    has_social = any(any(sn in link for sn in _SOCIAL_NETS) for link in all_links)
    defaults["HasSocialNet"] = 1.0 if has_social else 0.0

    # Submit button
    submit = (
        soup.find("input", {"type": "submit"})
        or soup.find("button", {"type": "submit"})
        or soup.find("button", {"type": lambda t: t is None})
    )
    defaults["HasSubmitButton"] = 1.0 if submit else 0.0

    # Hidden fields
    hidden = soup.find_all("input", {"type": "hidden"})
    defaults["HasHiddenFields"] = 1.0 if hidden else 0.0

    # Password field
    pwd = soup.find("input", {"type": "password"})
    defaults["HasPasswordField"] = 1.0 if pwd else 0.0

    # Copyright
    body_text = soup.get_text(separator=" ", strip=True).lower()
    defaults["HasCopyrightInfo"] = 1.0 if ("©" in body_text or "copyright" in body_text) else 0.0

    # Recursos
    defaults["NoOfImage"] = float(len(soup.find_all("img")))
    defaults["NoOfCSS"] = float(
        len(soup.find_all("link", rel=lambda r: r and "stylesheet" in " ".join(r).lower()))
        + len(soup.find_all("style"))
    )
    defaults["NoOfJS"] = float(len(soup.find_all("script")))

    # Self / empty / external refs
    self_ref = empty_ref = external_ref = 0
    for link in all_links:
        if not link or link in ("#", "javascript:void(0)", "javascript:;"):
            empty_ref += 1
        elif link.startswith("http") and base_domain not in link:
            external_ref += 1
        else:
            self_ref += 1
    defaults["NoOfSelfRef"] = float(self_ref)
    defaults["NoOfEmptyRef"] = float(empty_ref)
    defaults["NoOfExternalRef"] = float(external_ref)

    # Self-redirects vía JS
    self_redirect = 0
    if html:
        self_redirect = len(re.findall(
            rf'location\.(?:href|replace|assign)\s*=\s*["\'](?:/|{re.escape(base_domain)})',
            html, re.IGNORECASE
        ))
    defaults["NoOfSelfRedirect"] = float(self_redirect)

    return defaults


def extract_features(url: str) -> dict[str, float]:
    """Extrae exactamente 49 características de phishing a partir de una URL."""
    feature_keys = _load_feature_keys()
    result: dict[str, float] = {k: 0.0 for k in feature_keys}

    p = _parse_url(url)

    # ── Características léxicas de la URL ────────────────────────────────────

    result["URLLength"] = float(len(url))
    result["DomainLength"] = float(len(p["domain"]))
    result["IsDomainIP"] = 1.0 if _is_ip(p["host"]) else 0.0
    result["TLDLength"] = float(len(p["tld"]))

    subdomain_parts = [s for s in p["subdomains"].split(".") if s]
    result["NoOfSubDomain"] = float(len(subdomain_parts))

    result["CharContinuationRate"] = _char_continuation_rate(url)

    # Ofuscación (percent-encoding, entidades HTML en URL)
    obfuscated = _OBFUSCATED_PATTERN.findall(url)
    result["HasObfuscation"] = 1.0 if obfuscated else 0.0
    result["NoOfObfuscatedChar"] = float(len(obfuscated))
    result["ObfuscationRatio"] = len(obfuscated) / len(url) if url else 0.0

    # Composición de caracteres
    letters = [c for c in url if c.isalpha()]
    digits  = [c for c in url if c.isdigit()]
    special = [c for c in url if c in _SPECIAL_CHARS]

    result["NoOfLettersInURL"]         = float(len(letters))
    result["LetterRatioInURL"]         = len(letters) / len(url) if url else 0.0
    result["NoOfDegitsInURL"]          = float(len(digits))
    result["DegitRatioInURL"]          = len(digits) / len(url) if url else 0.0
    result["NoOfEqualsInURL"]          = float(url.count("="))
    result["NoOfQMarkInURL"]           = float(url.count("?"))
    result["NoOfAmpersandInURL"]       = float(url.count("&"))
    # Caracteres especiales que NO son =, ?, & (ya contados arriba)
    result["NoOfOtherSpecialCharsInURL"] = float(max(0, len(special)))
    result["SpacialCharRatioInURL"]    = len(special) / len(url) if url else 0.0
    result["IsHTTPS"]                  = 1.0 if p["scheme"].lower() == "https" else 0.0

    # Palabras clave en la URL
    url_lower = url.lower()
    result["Bank"]   = 1.0 if any(k in url_lower for k in _BANK_KEYWORDS)   else 0.0
    result["Pay"]    = 1.0 if any(k in url_lower for k in _PAY_KEYWORDS)    else 0.0
    result["Crypto"] = 1.0 if any(k in url_lower for k in _CRYPTO_KEYWORDS) else 0.0

    # Probabilidades heurísticas basadas en estructura léxica
    result["TLDLegitimateProb"] = _tld_legitimate_prob(p["tld"])
    result["URLCharProb"]       = _url_char_prob(url)

    # ── Fetch del HTML ───────────────────────────────────────────────────────

    html, redirect_count = _fetch_html(url)
    result["NoOfURLRedirect"] = float(redirect_count)
    result["Robots"]          = _check_robots(url)

    # ── Características estructurales del HTML ───────────────────────────────

    html_feats = _extract_html_features(html, url, p)
    for k, v in html_feats.items():
        if k in result:
            result[k] = float(v)

    # Garantiza que todas las 49 claves sean float
    for k in feature_keys:
        result[k] = float(result.get(k, 0.0))

    return result


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
    print(f"Extrayendo características de: {target}\n")
    feats = extract_features(target)
    print(json.dumps(feats, indent=2))
    print(f"\nTotal de características: {len(feats)}")
