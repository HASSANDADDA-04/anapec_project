import os
import re
import shutil
import subprocess
import tempfile
import unicodedata
from io import BytesIO
from pathlib import Path

from docx import Document
from PIL import Image, ImageEnhance, ImageOps
from pypdf import PdfReader

MIN_TEXT = 40
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".webp"}
_HEADINGS = {
    "competences", "competence", "certificats", "certificat",
    "langues", "langue", "formation", "formations", "etudes",
    "experiences professionnelles", "experience professionnelle", "experiences",
    "parcours professionnel", "projets realises", "profil", "profil professionnel",
    "centres d'interet", "centres d'interets", "contact",
}


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = _pdf_text(path)
        if len(text) < MIN_TEXT:
            text = _ocr_pdf(path)
    elif suffix == ".docx":
        document = Document(str(path))
        text = "\n".join(p.text for p in document.paragraphs).strip()
    else:
        raise ValueError("Format accepté : PDF ou DOCX")
    if len(text) < MIN_TEXT:
        raise ValueError("Le fichier ne contient pas assez de texte lisible. Un scan image ne peut pas être analysé.")
    return text


def _pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    parts = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(parts).strip()


def _tesseract_exe() -> str | None:
    candidates = [
        os.environ.get("TESSERACT_CMD", ""),
        shutil.which("tesseract") or "",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    return None


def _tessdata_dir() -> Path | None:
    bundled = Path(__file__).resolve().parents[2] / "tessdata"
    if (bundled / "fra.traineddata").is_file() and (bundled / "eng.traineddata").is_file():
        return bundled
    system = Path(r"C:\Program Files\Tesseract-OCR\tessdata")
    if (system / "fra.traineddata").is_file():
        return system
    return None


def _heading(line: str) -> str:
    value = unicodedata.normalize("NFD", line.lower())
    value = "".join(char for char in value if unicodedata.category(char) != "Mn")
    value = value.replace("’", "'").replace("`", "'")
    return value.strip(" .:-|")


def _ocr_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        for image in page.images:
            text = _ocr_embedded(image.data)
            if text:
                parts.append(text)
    return "\n".join(parts).strip()


def _ocr_embedded(data: bytes) -> str:
    try:
        image = Image.open(BytesIO(data)).convert("RGB")
    except Exception:
        return ""
    pieces = _split_sidebar(image)
    texts = [_read_piece(piece) for piece in pieces]
    return "\n".join(part for part in texts if part).strip()


def _split_sidebar(image: Image.Image) -> list[Image.Image]:
    gray = ImageOps.grayscale(image)
    width, height = gray.size
    if width < 400 or height < 400:
        return [image]
    step = max(1, height // 80)
    columns = []
    for x in range(width):
        columns.append(sum(gray.getpixel((x, y)) for y in range(0, height, step)) / (height / step))
    boundary = None
    for x in range(int(width * 0.18), int(width * 0.46)):
        if columns[x] > 170 and columns[x - 12] < 90:
            boundary = x
            break
    if boundary is None:
        return [image]
    left_mean = sum(columns[:boundary]) / boundary
    right_mean = sum(columns[boundary:]) / (width - boundary)
    if left_mean > 100 or right_mean < 150:
        return [image]
    left = ImageOps.invert(image.crop((0, 0, boundary - 2, height)).convert("L"))
    right = image.crop((boundary + 2, 0, width, height))
    return [left, right]


def _prepare(image: Image.Image) -> Image.Image:
    prepared = ImageOps.autocontrast(image.convert("L"))
    if prepared.width < 1700:
        scale = 1700 / prepared.width
        prepared = prepared.resize((int(prepared.width * scale), int(prepared.height * scale)), Image.Resampling.LANCZOS)
    return ImageEnhance.Sharpness(prepared).enhance(1.4)


def _run_tesseract(image: Image.Image, tsv: bool) -> str:
    exe = _tesseract_exe()
    data = _tessdata_dir()
    if exe is None or data is None:
        return ""
    with tempfile.TemporaryDirectory() as folder:
        target = Path(folder) / "page.png"
        image.save(target)
        command = [exe, str(target), "stdout", "-l", "fra+eng", "--tessdata-dir", str(data), "--psm", "4"]
        if tsv:
            command.extend(["-c", "tessedit_create_tsv=1"])
        completed = subprocess.run(command, capture_output=True, timeout=90, check=False)
    return completed.stdout.decode("utf-8", "replace")


def _read_piece(image: Image.Image) -> str:
    prepared = _prepare(image)
    plain = _run_tesseract(prepared, tsv=False).strip()
    if not plain:
        return ""
    skills = _skill_lines(_run_tesseract(prepared, tsv=True))
    if len(skills) < 2:
        return plain
    return _replace_skill_block(plain, skills)


def _skill_lines(tsv: str) -> list[str]:
    words = []
    for row in tsv.splitlines()[1:]:
        parts = row.split("\t")
        if len(parts) < 12 or not parts[11].strip():
            continue
        text = parts[11].strip()
        if sum(char.isalpha() for char in text) < 2:
            continue
        words.append({"x": int(parts[6]), "y": int(parts[7]), "w": int(parts[8]), "text": text})
    start = next((word["y"] for word in words if _heading(word["text"]) in {"competences", "competence"}), None)
    if start is None:
        return []
    end = next((word["y"] for word in words if word["y"] > start + 10 and _heading(word["text"]) in _HEADINGS), 10**9)
    selected = [word for word in words if start + 10 < word["y"] < end]
    if not selected:
        return []
    selected.sort(key=lambda word: (word["y"], word["x"]))
    rows: list[list[dict]] = []
    for word in selected:
        if not rows or word["y"] - rows[-1][0]["y"] > 28:
            rows.append([word])
        else:
            rows[-1].append(word)
    table = []
    for row in rows:
        row.sort(key=lambda word: word["x"])
        cells = [[row[0]]]
        for word in row[1:]:
            previous = cells[-1][-1]
            gap = word["x"] - (previous["x"] + previous["w"])
            if gap > 80:
                cells.append([word])
            else:
                cells[-1].append(word)
        table.append([(cell[0]["x"], " ".join(item["text"] for item in cell)) for cell in cells])
    columns: list[list[str]] = []
    for row in table:
        for origin, text in row:
            column = next((item for item in columns if abs(item[0] - origin) < 120), None)
            if column is None:
                columns.append([origin, [text]])
            else:
                column[1].append(text)
    skills = []
    for _, cells in sorted(columns, key=lambda item: item[0]):
        skills.extend(_join_wrapped(cells))
    cleaned = []
    for skill in skills:
        skill = skill.replace("hételiers", "hôteliers").replace("problémes", "problèmes")
        if sum(char.isalpha() for char in skill) >= 4:
            cleaned.append(skill)
    return cleaned


def _join_wrapped(cells: list[str]) -> list[str]:
    joined: list[str] = []
    for text in cells:
        text = re.sub(r"^Y(?=[a-zà-ÿ])", "l'", text)
        if joined and (joined[-1].endswith((" de", " et", " d'", " d’")) or text.startswith(("de ", "et ", "d'", "l'"))):
            joined[-1] = f"{joined[-1]} {text}"
        else:
            joined.append(text)
    return joined


def _replace_skill_block(plain: str, skills: list[str]) -> str:
    lines = plain.splitlines()
    start = None
    end = None
    for index, line in enumerate(lines):
        heading = _heading(line)
        if heading in {"competences", "competence"}:
            start = index
        elif start is not None and heading in _HEADINGS:
            end = index
            break
    if start is None:
        return plain
    if end is None:
        end = len(lines)
    return "\n".join([*lines[: start + 1], *skills, *lines[end:]]).strip()
