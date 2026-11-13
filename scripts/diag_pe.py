import io, re, urllib.request
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "text/html,application/xhtml+xml,application/pdf,*/*", "Accept-Language": "en-US,en;q=0.9"}
URLS = {
 "SPYM_ind": "https://www.ssga.com/us/en/individual/etfs/funds/spdr-portfolio-sp-500-etf-spym",
 "SPYM_int": "https://www.ssga.com/us/en/intermediary/etfs/spdr-portfolio-sp-500-etf-spym",
 "SPSM_ind": "https://www.ssga.com/us/en/individual/etfs/funds/spdr-portfolio-sp-600-small-cap-etf-spsm",
 "SPSM_int": "https://www.ssga.com/us/en/intermediary/etfs/spdr-portfolio-sp-600-small-cap-etf-spsm",
 "EAFE": "https://www.msci.com/documents/10199/822e3d18-16fb-4d23-9295-11bc9e07b8ba",
 "EM": "https://www.msci.com/documents/10199/c0db0a48-01f2-4ba9-ad01-226fd5678111",
}
for k, u in URLS.items():
    try:
        req = urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            b = r.read(); ct = r.headers.get("Content-Type"); fu = r.geturl()
        print(f"== {k} {len(b)} bytes {ct} final={fu}")
        if b[:4] == b"%PDF":
            from pypdf import PdfReader
            t = "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(b)).pages[:2])
            i = t.find("FUNDAMENTALS"); print(t[i:i+200] if i >= 0 else t[:300])
        else:
            t = b.decode("utf-8", "ignore")
            for m in re.finditer(r"Index Characteristics as of[^<]{0,40}|Price/Earnings Ratio FY1|Price/Earnings<", t):
                s = re.sub(r"<[^>]+>", " ", t[m.start():m.start()+600]); print("  ...", re.sub(r"\s+", " ", s)[:250])
                break
            for m in list(re.finditer(r"Price/Earnings", t))[:6]:
                s = re.sub(r"<[^>]+>", " ", t[m.start():m.start()+400]); print("  >>", re.sub(r"\s+", " ", s)[:160])
    except Exception as e:
        print(f"== {k} ERROR {e!r}")
