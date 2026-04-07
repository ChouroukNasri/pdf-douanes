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
    Retourne une liste de dicts prets pour db.insert_omd().
    Format attendu : N°, Description, Classement, Motif, Session.
    """
    import re
    if filename is None:
        filename = Path(pdf_path).name

    text = extract_text_from_pdf(pdf_path)
    # Supprimer separateurs de pages
    text = re.sub(r'--- Page \d+ ---\n', '', text)

    decisions = []

    # 1. Extraire la session
    s = re.search(r'(\d+.?[ee]me?\s+[Ss]ession[^)\n]*)', text)
    session = re.sub(r'\s+', ' ', s.group(1)).strip() if s else ""

    # 2. Couper apres Liste A / Liste B
    for marker in ["Liste A", "Liste B", "List A", "List B"]:
        if marker in text:
            text = text[:text.index(marker)]

    # 3. Splitter par entrees numerotees
    entries = re.split(r'\n(?=\d{1,2}\.\s)', text)

    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue

        num_match = re.match(r'^(\d{1,2})\.\s+(.+)', entry, re.DOTALL)
        if not num_match:
            continue

        num  = num_match.group(1)
        rest = num_match.group(2)

        # Chercher code HS (ex: 17.04, 1901.90, 8471.90)
        hs_pattern = r'\b(\d{2,4}\.\d{2,3})\b'
        hs_matches = list(re.finditer(hs_pattern, rest))
        if not hs_matches:
            continue

        hs_match   = hs_matches[0]
        classement = hs_match.group(1)
        hs_pos     = hs_match.start()

        # Description = tout avant le code HS, nettoyee
        desc = re.sub(r'\s+', ' ', rest[:hs_pos]).strip()
        # Ajouter le texte apres le code HS qui fait partie de la description
        # (le motif est souvent interleave avec la description dans les PDFs)
        after_hs = rest[hs_match.end():].strip()

        # Heuristique : si apres le HS il y a du texte court avant une majuscule,
        # c'est probablement le motif
        motif_match = re.search(r'\b(RGI\s*\d+[a-z]?|Note\s+\d|Chapitre\s+\d+)', after_hs, re.IGNORECASE)
        motif = after_hs.strip()

        # Nettoyer motif
        motif = re.sub(r'\s+', ' ', motif)[:600]
        desc  = desc[:800]

        if desc and classement and len(desc) > 5:
            decisions.append({
                "filename":    filename,
                "numero":      num,
                "description": desc,
                "classement":  classement,
                "motif":       motif,
                "session":     session,
            })

    print(f"[OMD] {len(decisions)} decisions extraites de {filename}")
    return decisions