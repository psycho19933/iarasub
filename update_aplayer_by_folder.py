#!/usr/bin/env python3
# update_aplayer_by_folder.py
import re
from pathlib import Path

# Ajustá si tu archivo HTML es otro (puede ser una lista)
HTML_FILES = [Path("index.html")]
AUDIO_ROOT = Path("audios")
LRC_ROOT = Path("subtitulos")
COVERS_ROOT = Path("covers")

AUDIO_EXTS = {".mp3", ".opus", ".ogg", ".wav", ".m4a", ".flac"}
LRC_EXTS = [".lrc", ".srt", ".txt"]

# Regex para localizar bloques: <!-- AUDIO_LIST_START:RJ... --> ... <!-- AUDIO_LIST_END:RJ... -->
BLOCK_RE = re.compile(
    r"<!--\s*AUDIO_LIST_START:([A-Za-z0-9_\-]+)\s*-->(.*?)<!--\s*AUDIO_LIST_END:\1\s*-->",
    re.DOTALL | re.IGNORECASE
)

def find_audio_files(post_id):
    folder = AUDIO_ROOT / post_id
    if not folder.exists():
        return []
    return sorted([p.name for p in folder.iterdir() if p.suffix.lower() in AUDIO_EXTS and p.is_file()])

def find_subtitle(post_id, base):
    folder = LRC_ROOT / post_id
    if not folder.exists():
        return None
    for ext in LRC_EXTS:
        candidate = folder / (base + ext)
        if candidate.exists():
            return str(candidate).replace("\\", "/")
    return None

def find_cover(post_id):
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        c = COVERS_ROOT / f"{post_id}{ext}"
        if c.exists():
            return str(c).replace("\\", "/")
    # fallback: buscar por prefijo post_id en la carpeta
    if COVERS_ROOT.exists():
        for p in sorted(COVERS_ROOT.iterdir()):
            if p.is_file() and p.name.startswith(post_id):
                return str(p).replace("\\", "/")
    return None

def js_escape(s):
    s = str(s)
    s = s.replace("\\", "\\\\").replace("'", "\\'")
    return s

def build_audio_item(idx, fname, post_id, cover):
    base = Path(fname).stem
    title = f"{idx}. {base}"
    url = f"audios/{post_id}/{fname}"
    lrc = find_subtitle(post_id, base)
    parts = ["{",
             f"    name: '{js_escape(title)}',",
             f"    artist: '{js_escape(post_id)}',",
             f"    url: '{js_escape(url)}',"]
    if lrc:
        parts.append(f"    lrc: '{js_escape(lrc)}',")
    if cover:
        parts.append(f"    cover: '{js_escape(cover)}',")
    parts.append("}")
    return "\n".join(parts)

def build_audio_block(post_id):
    files = find_audio_files(post_id)
    if not files:
        return "audio: []"
    cover = find_cover(post_id)
    items = [build_audio_item(i+1, f, post_id, cover) for i, f in enumerate(files)]
    return "audio: [\n" + ",\n".join(items) + "\n]"

def process_file(path: Path):
    text = path.read_text(encoding="utf-8")
    matches = list(BLOCK_RE.finditer(text))
    if not matches:
        print(f"No se encontraron marcadores en {path}")
        return
    new_text = text
    for m in reversed(matches):
        post_id = m.group(1)
        start, end = m.span()
        new_block = f"<!-- AUDIO_LIST_START:{post_id} -->\n{build_audio_block(post_id)}\n<!-- AUDIO_LIST_END:{post_id} -->"
        new_text = new_text[:start] + new_block + new_text[end:]
        print(f"Bloque actualizado para: {post_id}")
    path.write_text(new_text, encoding="utf-8")
    print(f"{path} guardado.")

def main():
    for f in HTML_FILES:
        if f.exists():
            process_file(f)
        else:
            print(f"Archivo no encontrado: {f}")

if __name__ == "__main__":
    main()