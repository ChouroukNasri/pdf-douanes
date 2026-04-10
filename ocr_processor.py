import os
import re
import tempfile
from pathlib import Path

try:
    import pytesseract
    from PIL import Image
    TESSERACT_OK = True
except ImportError:
    TESSERACT_OK = False

try:
    import fitz
    PYMUPDF_OK = True
except ImportError:
    PYMUPDF_OK = False

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_OK = True
except ImportError:
    PDF2IMAGE_OK = False

# Si Tesseract n'est pas dans le PATH, decommenter :
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def _detect_best_lang():
    if not TESSERACT_OK:
        return "eng"
    try:
        available = pytesseract.get_languages(config="")
        print("[OCR] Langues disponibles : " + str(available))
        has_fra = "fra" in available
        has_ara = "ara" in available
        has_eng = "eng" in available
        if has_fra and has_ara:
            lang = "fra+ara"
        elif has_fra:
            lang = "fra"
        elif has_eng:
            lang = "eng"
        else:
            langs = [l for l in available if l != "osd"]
            lang = langs[0] if langs else "eng"
        print("[OCR] Langue selectionnee : " + lang)
        return lang
    except Exception as e:
        print("[OCR] Fallback eng (" + str(e) + ")")
        return "eng"

OCR_LANG = _detect_best_lang() if TESSERACT_OK else "eng"
OCR_LANG_FALLBACK = "eng"


def extract_text_from_pdf(pdf_path):
    text = ""
    if PYMUPDF_OK:
        try:
            doc = fitz.open(pdf_path)
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            print("[PyMuPDF] Erreur : " + str(e))
    if len(text.strip()) < 50:
        text = _ocr_pdf(pdf_path)
    return text.strip()


def _ocr_pdf(pdf_path):
    if not TESSERACT_OK:
        return "[ERREUR] pytesseract non installe."
    if not PDF2IMAGE_OK:
        return "[ERREUR] pdf2image non installe."
    full_text = ""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            images = convert_from_path(pdf_path, dpi=300, output_folder=tmpdir)
            for i, img in enumerate(images):
                page_text = ""
                try:
                    page_text = pytesseract.image_to_string(img, lang=OCR_LANG)
                except pytesseract.TesseractError:
                    try:
                        page_text = pytesseract.image_to_string(img, lang=OCR_LANG_FALLBACK)
                    except Exception:
                        try:
                            page_text = pytesseract.image_to_string(img)
                        except Exception as e3:
                            page_text = "[ERREUR PAGE " + str(i+1) + "] " + str(e3)
                full_text += "\n--- Page " + str(i+1) + " ---\n" + page_text
    except Exception as e:
        full_text = "[ERREUR OCR] " + str(e)
    return full_text


def parse_fields(text):
    """
    Extrait les 5 champs :
      - numero_avis
      - designation
      - usage_text
      - tarif_number
      - ndp
    """
    fields = {
        "numero_avis":  "",
        "designation":  "",
        "usage_text":   "",
        "tarif_number": "",
        "ndp":          "",
    }

    if not text:
        return fields

    # N° Avis (7 chiffres)
    m = re.search(r'\b(\d{7})\b', text)
    if m:
        fields["numero_avis"] = m.group(1)

    # Designation commerciale
    patterns_desig = [
        r'[Dd][ée]signation\s+[Cc]ommerciale?\s*:\s*(.+?)(?:\n\n|\n-|\n[A-Z]|\Z)',
        r'[Dd][ée]signation\s*:\s*(.+?)(?:\n\n|\n-|\n[A-Z]|\Z)',
    ]
    for pat in patterns_desig:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            fields["designation"] = _clean(m.group(1))
            break

    # Usage — toute la phrase
    m = re.search(
        r'[Uu]sage\s*:\s*(.+?)(?:\n\n|\n-|\nEMET|\ZEMET|\Z)',
        text, re.IGNORECASE | re.DOTALL
    )
    if m:
        fields["usage_text"] = _clean(m.group(1))

    # Numero tarifaire
    patterns_tarif = [
        r'classer\s+au\s+n[o0O][^\d]*(\d{9,10})',
        r'n[o0O][^\d\w]*(\d{9,10})\b',
        r'classement\s*[:\-]\s*(\d{9,10})',
        r'\b(\d{4}[.\s]\d{2}[.\s]\d{2,4})\b',
        r'\b(94\d{7,8})\b',
        r'\b(85\d{7,8})\b',
        r'\b(39\d{7,8})\b',
        r'\b(73\d{7,8})\b',
    ]
    for pat in patterns_tarif:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw = m.group(1).replace(".", "").replace(" ", "")
            fields["tarif_number"] = raw
            break

    # NDP — detecte NDP, N.D.P, N.D.P.
    patterns_ndp = [
        r'N\.?D\.?P\.?\s*[:\s]+(\d{10,15})',
        r'\(\s*N\.?D\.?P\.?\s*[:\s]*(\d{10,15})\s*\)',
    ]
    for pat in patterns_ndp:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            fields["ndp"] = m.group(1).strip()
            break

    return fields


def _clean(s):
    s = re.sub(r'\s+', ' ', s)
    s = s.strip(" \t\n\r-")
    return s


def process_pdf(pdf_path, filename=None):
    if filename is None:
        filename = Path(pdf_path).name
    print("[OCR] Traitement : " + filename)
    text = extract_text_from_pdf(pdf_path)
    fields = parse_fields(text)
    return {
        "filename":  filename,
        "filepath":  pdf_path,
        "full_text": text,
        **fields,
    }




# ══════════════════════════════════════════════════════════════════════════════
#  PARSER SPECIAL : DECISIONS OMD
# ══════════════════════════════════════════════════════════════════════════════
def parse_omd_pdf(pdf_path, filename=None):
    """
    Parse un PDF de decisions OMD (Comite du Systeme Harmonise).
    Utilise pdfplumber (texte natif) pour capturer la session correctement.
    La session detectee (ex: 22eme Session - Novembre 1998) est diffusee
    a TOUTES les decisions du meme PDF.
    """
    import re
    try:
        import pdfplumber
        HAS_PDFPLUMBER = True
    except ImportError:
        HAS_PDFPLUMBER = False

    if filename is None:
        filename = Path(pdf_path).name

    # 1. Extraction texte
    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                full_text = "\n".join(
                    p.extract_text() or "" for p in pdf.pages
                )
        except Exception:
            full_text = extract_text_from_pdf(pdf_path)
            full_text = re.sub(r'--- Page \d+ ---\n', '', full_text)
    else:
        full_text = extract_text_from_pdf(pdf_path)
        full_text = re.sub(r'--- Page \d+ ---\n', '', full_text)

    # 2. Detecter la session UNIQUE du PDF et la diffuser a tous
    session = ""
    m_num  = re.search(r'(\d+).?[eèê]me?\s+session', full_text, re.IGNORECASE)
    m_date = re.search(
        r'(janvier|f[eé]vrier|mars|avril|mai|juin|juillet|ao[uû]t|'
        r'septembre|octobre|novembre|d[eé]cembre)\s+(\d{4})',
        full_text[:500], re.IGNORECASE
    )
    if m_num:
        num = m_num.group(1)
        if m_date:
            mois  = m_date.group(1).capitalize()
            annee = m_date.group(2)
            session = num + "ème Session (" + mois + " " + annee + ")"
        else:
            m_year = re.search(r'\b(19|20)\d{2}\b', full_text[:500])
            session = num + "ème Session (" + (m_year.group(0) if m_year else "?") + ")"

    print("[OMD] Session detectee : " + repr(session))

    # 3. Couper avant Liste A / Liste B
    for marker in ["Liste A", "Liste B", "List A", "List B"]:
        if marker in full_text:
            full_text = full_text[:full_text.index(marker)]

    # 4. Splitter par entrees numerotees "N. texte"
    entries = re.split(r'\n(?=\d{1,2}\.\s)', full_text)

    decisions = []
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        num_m = re.match(r'^(\d{1,2})\.\s+(.+)', entry, re.DOTALL)
        if not num_m:
            continue

        num  = num_m.group(1)
        rest = num_m.group(2)

        # Code HS (ex: 17.04, 1901.90)
        hs_m = re.search(r'\b(\d{2,4}\.\d{2,3})\b', rest)
        if not hs_m:
            continue

        classement = hs_m.group(1)
        desc  = re.sub(r'\s+', ' ', rest[:hs_m.start()]).strip()
        motif = re.sub(r'\s+', ' ', rest[hs_m.end():]).strip()[:500]

        if desc and len(desc) > 5:
            decisions.append({
                "filename":    filename,
                "numero":      num,
                "description": desc[:800],
                "classement":  classement,
                "motif":       motif,
                "session":     session,
            })

    print("[OMD] " + str(len(decisions)) + " decisions extraites — session=" + repr(session))
    return decisions