const BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem("anapec_token") || "";
}

export function setSession(token, user) {
  localStorage.setItem("anapec_token", token);
  localStorage.setItem("anapec_user", JSON.stringify(user));
}

export function clearSession() {
  localStorage.removeItem("anapec_token");
  localStorage.removeItem("anapec_user");
}

export function currentUser() {
  const raw = localStorage.getItem("anapec_user");
  return raw ? JSON.parse(raw) : null;
}

export async function downloadFile(path, filename) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  const response = await fetch(`${BASE}${path}`, { headers });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || "Téléchargement impossible");
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function downloadText(filename, text) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

const WIN1252 = { "€": 0x80, "‚": 0x82, "„": 0x84, "…": 0x85, "†": 0x86, "‡": 0x87, "‰": 0x89, "Š": 0x8a, "‹": 0x8b, "Œ": 0x8c, "Ž": 0x8e, "‘": 0x91, "’": 0x92, "“": 0x93, "”": 0x94, "•": 0x95, "–": 0x96, "—": 0x97, "˜": 0x98, "™": 0x99, "š": 0x9a, "›": 0x9b, "œ": 0x9c, "ž": 0x9e, "Ÿ": 0x9f };

function pdfByte(char) {
  const code = char.codePointAt(0);
  if (code <= 0x7f) return code;
  if (code >= 0xa0 && code <= 0xff) return code;
  return WIN1252[char] ?? 0x3f;
}

function pdfEscape(text) {
  let out = "";
  for (const char of text) {
    const byte = pdfByte(char);
    if (byte === 0x28 || byte === 0x29 || byte === 0x5c) out += `\\${String.fromCharCode(byte)}`;
    else if (byte < 32 || byte > 126) out += `\\${byte.toString(8).padStart(3, "0")}`;
    else out += String.fromCharCode(byte);
  }
  return out;
}

function wrapLetter(text) {
  const lines = [];
  for (const paragraph of String(text || "").replace(/\r/g, "").split("\n")) {
    const words = paragraph.split(/\s+/).filter(Boolean);
    if (words.length === 0) {
      lines.push("");
      continue;
    }
    let current = "";
    for (const word of words) {
      const next = current ? `${current} ${word}` : word;
      if (next.length > 88 && current) {
        lines.push(current);
        current = word;
      } else current = next;
    }
    if (current) lines.push(current);
  }
  return lines;
}

export function letterPdf(text) {
  const lines = wrapLetter(text);
  const pages = [];
  for (let index = 0; index < lines.length; index += 46) pages.push(lines.slice(index, index + 46));
  if (pages.length === 0) pages.push([""]);
  const fontId = 3 + pages.length * 2;
  const objects = new Array(fontId);
  objects[0] = "<< /Type /Catalog /Pages 2 0 R >>";
  objects[1] = `<< /Type /Pages /Kids [${pages.map((_, index) => `${3 + index * 2} 0 R`).join(" ")}] /Count ${pages.length} >>`;
  pages.forEach((pageLines, index) => {
    const stream = ["BT", "/F1 12 Tf", "50 790 Td", "16 TL", ...pageLines.flatMap((line) => [`(${pdfEscape(line)}) Tj`, "T*"]), "ET"].join("\n");
    objects[2 + index * 2] = `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents ${4 + index * 2} 0 R /Resources << /Font << /F1 ${fontId} 0 R >> >> >>`;
    objects[3 + index * 2] = `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`;
  });
  objects[fontId - 1] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>";
  let body = "%PDF-1.4\n";
  const offsets = [0];
  objects.forEach((object, index) => {
    offsets.push(body.length);
    body += `${index + 1} 0 obj\n${object}\nendobj\n`;
  });
  const xref = body.length;
  body += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  offsets.slice(1).forEach((offset) => { body += `${String(offset).padStart(10, "0")} 00000 n \n`; });
  body += `trailer << /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF`;
  return body;
}

export function downloadPdf(filename, text) {
  const blob = new Blob([letterPdf(text)], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(options.body);
  }
  const response = await fetch(`${BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "Une erreur est survenue");
  }
  return data;
}
