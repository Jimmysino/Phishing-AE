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
_OBFUSCATED_PATTERN = re.compile(r'%[0-9A-Fa-f]{2}|\\u[0-9A-Fa-f]{4}|&#\d+;|&[a-z]+;')
_SPECIAL_CHARS = set('!@#$%^&*()-_=+[]{}|;:\'",.<>?/\\`~')
_REQUEST_TIMEOUT = 8


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
    # Strip port from host
    host = netloc.split(":")[0] if ":" in netloc else netloc

    if _USE_TLDEXTRACT:
        ext = tldextract.extract(url)
        domain = ext.domain + ("." + ext.suffix if ext.suffix else "")
        tld = ext.suffix or ""
        subdomains = ext.subdomain or ""
    else:
        parts = host.split(".")
        tld = parts[-1] if len(parts) >= 2 else ""
        domain = ".".join(parts[-2:]) if len(parts) >= 2 else host
        subdomains = ".".join(parts[:-2]) if len(parts) > 2 else ""

    return {
        "url": url,
        "parsed": parsed,
        "host": host,
        "domain": domain,
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
    # IPv6
    try:
        socket.inet_pton(socket.AF_INET6, host.strip("[]"))
        return True
    except (socket.error, OSError):
        return False


def _count_special(text: str) -> int:
    return sum(1 for c in text if c in _SPECIAL_CHARS)


def _char_continuation_rate(url: str) -> float:
    """Ratio of consecutive same-character pairs to total pairs."""
    if len(url) < 2:
        return 0.0
    pairs = len(url) - 1
    consecutive = sum(1 for i in range(pairs) if url[i] == url[i + 1])
    return consecutive / pairs


def _fetch_html(url: str) -> tuple[str | None, int]:
    """Returns (html_text, redirect_count). html is None on failure."""
    headers_falsos = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8"
}
    try:
        session = requests.Session()
        resp = session.get(
            url,
            timeout=3,
            headers=headers_falsos,
            allow_redirects=True,
        )
        redirects = len(resp.history)
        return resp.text, redirects
    except Exception:
        return None, 0


def _check_robots(url: str) -> float:
    try:
        parsed = urllib.parse.urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        resp = requests.get(robots_url, timeout=_REQUEST_TIMEOUT,
                            headers={"User-Agent": "Mozilla/5.0"})
        return 1.0 if resp.status_code == 200 and len(resp.text) > 0 else 0.0
    except Exception:
        return 0.0


def _extract_html_features(html: str, url: str, parsed_url: dict) -> dict:
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
        domain_in_title = 1.0 if domain_lower in title_text else 0.0
        defaults["DomainTitleMatchScore"] = domain_in_title
        url_words = set(re.split(r'[\W_]+', parsed_url["url"].lower()))
        title_words = set(re.split(r'[\W_]+', title_text))
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

    # Popups (window.open in scripts)
    scripts = soup.find_all("script")
    popup_count = 0
    for s in scripts:
        if s.string:
            popup_count += len(re.findall(r'window\.open\s*\(', s.string))
    defaults["NoOfPopup"] = float(popup_count)

    # iFrames
    defaults["NoOfiFrame"] = float(len(soup.find_all("iframe")))

    # Forms
    base_domain = parsed_url["domain"]
    forms = soup.find_all("form")
    external_form = 0
    for form in forms:
        action = form.get("action", "")
        if action and action.startswith("http") and base_domain not in action:
            external_form = 1
            break
    defaults["HasExternalFormSubmit"] = float(external_form)

    # Social networks in links
    all_links = [a.get("href", "") for a in soup.find_all("a", href=True)]
    has_social = any(
        any(sn in link for sn in _SOCIAL_NETS) for link in all_links
    )
    defaults["HasSocialNet"] = 1.0 if has_social else 0.0

    # Submit button
    submit = soup.find("input", {"type": "submit"}) or soup.find("button", {"type": "submit"})
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

    # Images, CSS, JS
    defaults["NoOfImage"] = float(len(soup.find_all("img")))
    defaults["NoOfCSS"] = float(
        len(soup.find_all("link", rel=lambda r: r and "stylesheet" in " ".join(r).lower()))
        + len(soup.find_all("style"))
    )
    defaults["NoOfJS"] = float(len(soup.find_all("script")))

    # Self / empty / external refs
    self_ref = empty_ref = external_ref = 0
    for link in all_links:
        if not link or link == "#":
            empty_ref += 1
        elif link.startswith("http") and base_domain not in link:
            external_ref += 1
        else:
            self_ref += 1
    defaults["NoOfSelfRef"] = float(self_ref)
    defaults["NoOfEmptyRef"] = float(empty_ref)
    defaults["NoOfExternalRef"] = float(external_ref)

    return defaults


def extract_features(url: str) -> dict[str, float]:
    """Extract 49 phishing-detection features from a URL."""
    feature_keys = _load_feature_keys()
    result: dict[str, float] = {k: 0.0 for k in feature_keys}

    p = _parse_url(url)
    full_url = url

    # --- Lexical / URL features ---
    result["URLLength"] = float(len(full_url))
    result["DomainLength"] = float(len(p["domain"]))
    result["IsDomainIP"] = 1.0 if _is_ip(p["host"]) else 0.0
    result["TLDLength"] = float(len(p["tld"]))

    subdomain_parts = [s for s in p["subdomains"].split(".") if s]
    result["NoOfSubDomain"] = float(len(subdomain_parts))

    result["CharContinuationRate"] = _char_continuation_rate(full_url)

    # Obfuscation (percent-encoding and HTML entities in URL)
    obfuscated_matches = _OBFUSCATED_PATTERN.findall(full_url)
    result["HasObfuscation"] = 1.0 if obfuscated_matches else 0.0
    result["NoOfObfuscatedChar"] = float(len(obfuscated_matches))
    result["ObfuscationRatio"] = (
        len(obfuscated_matches) / len(full_url) if full_url else 0.0
    )

    letters = [c for c in full_url if c.isalpha()]
    digits = [c for c in full_url if c.isdigit()]
    special = [c for c in full_url if c in _SPECIAL_CHARS]

    result["NoOfLettersInURL"] = float(len(letters))
    result["LetterRatioInURL"] = len(letters) / len(full_url) if full_url else 0.0
    result["NoOfDegitsInURL"] = float(len(digits))
    result["DegitRatioInURL"] = len(digits) / len(full_url) if full_url else 0.0
    result["NoOfEqualsInURL"] = float(full_url.count("="))
    result["NoOfQMarkInURL"] = float(full_url.count("?"))
    result["NoOfAmpersandInURL"] = float(full_url.count("&"))
    result["NoOfOtherSpecialCharsInURL"] = float(
        len(special) - full_url.count("=") - full_url.count("?") - full_url.count("&")
    )
    result["SpacialCharRatioInURL"] = len(special) / len(full_url) if full_url else 0.0
    result["IsHTTPS"] = 1.0 if p["scheme"].lower() == "https" else 0.0

    # Keyword features (check full URL)
    url_lower = full_url.lower()
    result["Bank"] = 1.0 if any(k in url_lower for k in _BANK_KEYWORDS) else 0.0
    result["Pay"] = 1.0 if any(k in url_lower for k in _PAY_KEYWORDS) else 0.0
    result["Crypto"] = 1.0 if any(k in url_lower for k in _CRYPTO_KEYWORDS) else 0.0

    # Probabilistic / external-DB features — default 0.0 (no external DB)
    result["TLDLegitimateProb"] = 0.0
    result["URLCharProb"] = 0.0

    # --- Fetch HTML ---
    html, redirect_count = _fetch_html(full_url)
    result["NoOfURLRedirect"] = float(redirect_count)

    # robots.txt (parallel-ish but kept simple)
    result["Robots"] = _check_robots(full_url)

    # --- HTML features ---
    html_feats = _extract_html_features(html, full_url, p)
    for k, v in html_feats.items():
        if k in result:
            result[k] = float(v)

    # Self-redirects: JS location.href pointing to same domain
    self_redirect = 0
    if html:
        self_redirect = len(re.findall(
            rf'location\.(?:href|replace|assign)\s*=\s*["\'](?:/|{re.escape(p["domain"])})',
            html, re.IGNORECASE
        ))
    result["NoOfSelfRedirect"] = float(self_redirect)

    # Guarantee all 49 keys exist and are float
    for k in feature_keys:
        result[k] = float(result.get(k, 0.0))

    return result


if __name__ == "__main__":
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "https://www.google.com"
    print(f"Extrayendo características de: {target}")
    feats = extract_features(target)
    print(json.dumps(feats, indent=2))
    print(f"\nTotal de características: {len(feats)}")
