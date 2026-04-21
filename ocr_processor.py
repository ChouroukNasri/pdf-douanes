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

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

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
    Extrait les 5 champs pour Avis Tarifaires :
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

    m = re.search(r'\b(\d{7})\b', text)
    if m:
        fields["numero_avis"] = m.group(1)

    patterns_desig = [
        r'[Dd][ée]signation\s+[Cc]ommerciale?\s*:\s*(.+?)(?:\n\n|\n-|\n[A-Z]|\Z)',
        r'[Dd][ée]signation\s*:\s*(.+?)(?:\n\n|\n-|\n[A-Z]|\Z)',
    ]
    for pat in patterns_desig:
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            fields["designation"] = _clean(m.group(1))
            break

    m = re.search(
        r'[Uu]sage\s*:\s*(.+?)(?:\n\n|\n-|\nEMET|\ZEMET|\Z)',
        text, re.IGNORECASE | re.DOTALL
    )
    if m:
        fields["usage_text"] = _clean(m.group(1))

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
    """
    import re
    if filename is None:
        filename = Path(pdf_path).name

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

    for marker in ["Liste A", "Liste B", "List A", "List B"]:
        if marker in full_text:
            full_text = full_text[:full_text.index(marker)]

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

        hs_m = re.search(r'\b(\d{2,4}\.\d{2,3})\b', rest)
        if not hs_m:
            continue

        classement = hs_m.group(1)
        before = re.sub(r'\s+', ' ', rest[:hs_m.start()]).strip()
        after  = re.sub(r'\s+', ' ', rest[hs_m.end():]).strip()

        motif_markers = ['RGI', 'Note ', 'Chapitre ', 'Exclusion', 'Section ']

        if len(before) >= 5 and len(after) >= 5:
            desc  = before
            motif = after[:500]
        elif len(before) >= 5:
            desc  = before
            motif = ''
        elif len(after) >= 5:
            motif_pos = None
            for mk in motif_markers:
                pos = after.find(mk)
                if pos > 10 and (motif_pos is None or pos < motif_pos):
                    motif_pos = pos
            if motif_pos:
                desc  = after[:motif_pos].strip()
                motif = after[motif_pos:].strip()[:500]
            else:
                desc  = after
                motif = ''
        else:
            desc  = re.sub(r'\s+', ' ', rest).replace(classement, '').strip()[:800]
            motif = ''

        if not desc or len(desc) < 3:
            desc = re.sub(r'\s+', ' ', rest).strip()[:800]

        if desc:
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


# ══════════════════════════════════════════════════════════════════════════════
#  PARSER SPECIAL : AVIS TARÉS (format kap_XX_f.pdf)
# ══════════════════════════════════════════════════════════════════════════════
def parse_kap_pdf(pdf_path, filename=None):
    """
    Parse un PDF de type kap_XX_f.pdf (recueil tarifaire par chapitre).

    Structure d'une entrée typique :
    ┌──────────────────────────────────────────────────────────┐
    │  Nom du produit (bold, 1ère ligne)                        │
    │  Description (plusieurs lignes)                           │
    │  [Référence numérique ex: 304.64.2004.2]                 │
    │  Mots-clés: mot1 / mot2 / mot3          CODE.XXXX        │
    └──────────────────────────────────────────────────────────┘

    Le code HS (ex: 0402.9910) apparaît aligné à droite sur la ligne
    des mots-clés ou juste après.
    """
    if filename is None:
        filename = Path(pdf_path).name

    # ── 1. Extraction texte brut ──────────────────────────────────────────────
    if HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages_text = []
                for page in pdf.pages:
                    t = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
                    pages_text.append(t)
                full_text = "\n".join(pages_text)
        except Exception:
            full_text = extract_text_from_pdf(pdf_path)
    else:
        full_text = extract_text_from_pdf(pdf_path)

    # Supprimer les en-têtes de pages (ex: "0402 - 0405\n1/5 (Etat: 1.10.2022)")
    full_text = re.sub(r'\d{4}\s*-\s*\d{4}\s*\n\d+/\d+\s*\(Etat[^\n]*\)\n?', '', full_text)
    full_text = re.sub(r'\d+/\d+\s*\(Etat[^\n]*\)\n?', '', full_text)

    print("[KAP] Texte extrait (" + str(len(full_text)) + " chars) depuis " + filename)

    # ── 2. Regex pour parser chaque produit ───────────────────────────────────
    #
    # Pattern de détection d'un code HS en fin de ligne :
    #   "Mots-clés: ..." suivi du code HS, ex: 0402.9910
    #   OU le code HS seul sur sa propre ligne
    #
    # On split sur les occurrences de "Mots-clés:" pour isoler les blocs
    # puis on récupère le code HS qui suit chaque bloc.

    products = []

    # Stratégie : découper le texte en blocs délimités par "Mots-clés:"
    # Chaque bloc contient :  [nom + description + ref] AVANT "Mots-clés:"
    # Et [mots-clés + code HS] APRÈS "Mots-clés:"

    # Regex pour trouver toutes les occurrences de "Mots-clés:"
    splits = list(re.finditer(r'Mots-cl[eé]s\s*:', full_text, re.IGNORECASE))

    if not splits:
        print("[KAP] Aucun 'Mots-clés' trouvé — tentative alternative")
        return _parse_kap_fallback(full_text, filename)

    for i, match in enumerate(splits):
        # Texte AVANT ce Mots-clés (corps du produit)
        start = splits[i-1].end() if i > 0 else 0
        body_text = full_text[start:match.start()].strip()

        # Texte APRÈS ce Mots-clés jusqu'au prochain Mots-clés
        after_start = match.end()
        after_end   = splits[i+1].start() if i+1 < len(splits) else len(full_text)
        after_text  = full_text[after_start:after_end].strip()

        # ── Extraire le code HS depuis after_text ────────────────────────────
        # Le code HS est du type: 0402.9910  ou  0403.2011/ 2029  ou  0405.2011,\n0405.2091
        hs_match = re.search(
            r'\b(\d{4}\.\d{4}(?:/\s*\d{4})?(?:,\s*\n?\s*\d{4}\.\d{4}(?:/\s*\d{4})?)*)\b',
            after_text
        )
        if not hs_match:
            # Code HS simple (4 chiffres point 2-4 chiffres)
            hs_match = re.search(r'\b(\d{4}\.\d{2,4}(?:[/,]\s*\d{2,4})?)\b', after_text)

        hs_code = ""
        if hs_match:
            raw_hs = hs_match.group(1)
            # Extraire TOUS les codes HS individuels (ex: "0405.2011,\n0405.2091")
            all_codes = re.findall(r'\d{4}\.\d{2,4}', raw_hs)
            hs_code = ", ".join(c for c in all_codes if c)  # stocker tous séparés par ", "

        # ── Extraire les mots-clés (avant le code HS dans after_text) ────────
        mots_cles_raw = after_text
        if hs_match:
            mots_cles_raw = after_text[:hs_match.start()]
        mots_cles = re.sub(r'\s+', ' ', mots_cles_raw).strip().strip('/')

        # ── Parser le body_text : nom + description + ref ────────────────────
        # Référence numérique type: 304.64.2004.2 ou 3101.56.2014.4
        ref_match = re.search(r'\b(\d{3,10}\.\d{1,10}\.\d{4}\.\d{1,3})\b', body_text)
        ref_numero = ref_match.group(1) if ref_match else ""

        # Supprimer la référence du body
        clean_body = body_text
        if ref_match:
            clean_body = body_text[:ref_match.start()] + body_text[ref_match.end():]
        clean_body = clean_body.strip()

        # Supprimer boilerplate
        clean_body = re.sub(
            r'Application des R[eè]gles g[eé]n[eé]rales[^\n]*\n?',
            '', clean_body, flags=re.IGNORECASE
        )
        clean_body = re.sub(r'Voir aussi[^\n]*\n?', '', clean_body, flags=re.IGNORECASE)
        # Supprimer les codes HS parasites qui trainent dans le body (ex: "0405.2011, 0405.2091")
        clean_body = re.sub(r'\b\d{4}\.\d{2,4}(?:[,/\s]+\d{4}\.\d{2,4})*', '', clean_body)
        clean_body = clean_body.strip()

        # ── Identifier le NOM : chercher un titre court (ligne sans virgule ni point final)
        # Dans le format kap_XX_f.pdf, le nom est en GRAS sur la 1ère ligne du bloc
        # et la description commence par une minuscule ou "sous forme", "constitué", etc.
        lines = [l.strip() for l in clean_body.split('\n') if l.strip()]
        if not lines:
            continue

        # Trouver la dernière ligne "titre" = ligne courte (≤120 cars) qui ne commence
        # pas par une minuscule et n'est pas du texte courant (pas de virgule au milieu)
        nom = ""
        desc_start = 0
        for idx, line in enumerate(lines):
            # Critères d'un nom de produit :
            # - commence par une majuscule ou un chiffre
            # - relativement courte (≤ 120 chars)
            # - ne ressemble pas à une phrase descriptive (pas de "sous forme", "constitué", etc.)
            is_title = (
                len(line) <= 120
                and (line[0].isupper() or line[0].isdigit())
                and not re.match(r'^(sous|constitué|contenant|utilisé|liquide|masse|produit|poudre|mélange de)', line, re.IGNORECASE)
            )
            if is_title and idx == 0:
                nom = line
                desc_start = 1
                break
            elif is_title and idx > 0:
                # Vérifier que la ligne précédente était aussi un titre (titre multi-ligne rare)
                nom = line
                desc_start = idx + 1
                break

        if not nom:
            # Fallback : première ligne
            nom = lines[0]
            desc_start = 1

        description = ' '.join(lines[desc_start:]).strip()
        description = re.sub(r'\s+', ' ', description).strip()

        # Ignorer les blocs trop courts ou sans code HS
        if not nom or len(nom) < 3:
            continue

        products.append({
            "filename":    filename,
            "hs_code":     hs_code,
            "nom":         nom[:200],
            "description": description[:1500],
            "mots_cles":   mots_cles[:500],
            "ref_numero":  ref_numero,
        })

    print("[KAP] " + str(len(products)) + " produits extraits depuis " + filename)
    return products


def _parse_kap_fallback(full_text, filename):
    """
    Fallback si pas de 'Mots-clés:' trouvé.
    Tente de détecter des blocs par présence de code HS en fin de ligne.
    """
    products = []
    lines = full_text.split('\n')
    hs_pattern = re.compile(r'\b(\d{4}\.\d{2,4}(?:[/,]\s*\d{2,4})?)\b')

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        hs_m = hs_pattern.search(line)
        if hs_m and len(line) < 30:  # code HS seul ou presque
            hs_code = hs_m.group(1)
            # Remonter pour trouver le nom/description
            block_lines = []
            j = i - 1
            while j >= 0 and j >= i - 15:
                prev = lines[j].strip()
                if not prev or hs_pattern.search(prev):
                    break
                block_lines.insert(0, prev)
                j -= 1

            if block_lines:
                nom = block_lines[0][:200]
                desc = ' '.join(block_lines[1:])[:1000]
                products.append({
                    "filename":    filename,
                    "hs_code":     hs_code,
                    "nom":         nom,
                    "description": desc,
                    "mots_cles":   "",
                    "ref_numero":  "",
                })
        i += 1

    print("[KAP fallback] " + str(len(products)) + " produits extraits")
    return products