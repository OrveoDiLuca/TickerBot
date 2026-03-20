import os
import re
from pathlib import Path
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup

FILINGS_DIR = Path(__file__).parent.parent

#Instala el archivo de 10k segun el ticker de la empresa que pida el usuario
def download_10k(ticker:str) -> bool:
    company_name = os.getenv("SEC_COMPANY_NAME", "TickerBot")
    email = os.getenv("SEC_EMAIL","orveo841@gmail.com")
    
    dl = Downloader(company_name,email,FILINGS_DIR)
    try: 
        dl.get("10-K",ticker,limit=1)
        return True
    except Exception:
        return False

def find_10k_file(ticker: str) -> Path | None:
    ticker_dir = FILINGS_DIR / "sec-edgar-filings" / ticker / "10-K"
    if not ticker_dir.exists():
        return None

    for accession_dir in sorted(ticker_dir.iterdir()):
        for filename in ["primary-document.html", "full-submission.txt"]:
            f = accession_dir / filename
            if f.exists():
                return f

    return None

def parse_10k(ticker: str) -> str | None:
    filing_file = find_10k_file(ticker)
    if not filing_file:
        return None

    raw = filing_file.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "lxml")

    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()

    text = soup.get_text(separator="\n")
    # Elimina cualquier tag HTML residual que BeautifulSoup no haya limpiado
    text = re.sub(r"<[^>]+>", " ", text)
    # Colapsa espacios multiples
    text = re.sub(r" {2,}", " ", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)

def get_10k_accession(ticker: str) -> str | None:
    """Devuelve el número de accesión del 10-K más reciente (ej: 0000320193-24-000123)."""
    ticker_dir = FILINGS_DIR / "sec-edgar-filings" / ticker.upper() / "10-K"
    if not ticker_dir.exists():
        return None
    dirs = sorted(ticker_dir.iterdir())
    if not dirs:
        return None
    return dirs[-1].name  # El directorio más reciente es el número de accesión


def get_10k_text(ticker: str) -> str | None:
    """Descarga (si no existe) y devuelve el texto del 10-K."""
    ticker = ticker.upper()

    if not find_10k_file(ticker):
        success = download_10k(ticker)
        if not success:
            return None

    return parse_10k(ticker)