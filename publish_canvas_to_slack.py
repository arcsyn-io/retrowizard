#!/usr/bin/env python3
"""
Publica um arquivo Markdown como Canvas no Slack.

Uso:
    python publish_canvas_to_slack.py <arquivo.md> [titulo]

Exemplo:
    python publish_canvas_to_slack.py financeiro/2026-Q1/2026-01-16/report.md
    python publish_canvas_to_slack.py report.md "Retrospectiva Q1"

Pré-requisito:
    Definir SLACK_BOT_TOKEN e SLACK_USER_ID no .env
"""

import os
import re
import requests
import sys
from pathlib import Path


def load_env_file():
    """Carrega variáveis do arquivo .env se existir."""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    if key not in os.environ:
                        os.environ[key] = value


load_env_file()

SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_API = "https://slack.com/api"

if not SLACK_TOKEN:
    print("❌ Defina SLACK_BOT_TOKEN")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {SLACK_TOKEN}",
    "Content-Type": "application/json; charset=utf-8",
}


def upload_image(image_path: str) -> str:
    """Faz upload de uma imagem para o Slack e retorna o permalink"""
    # 1. Obter URL de upload
    resp = requests.post(
        f"{SLACK_API}/files.getUploadURLExternal",
        headers={"Authorization": f"Bearer {SLACK_TOKEN}"},
        data={
            "filename": Path(image_path).name,
            "length": os.path.getsize(image_path),
        },
    ).json()

    if not resp.get("ok"):
        raise RuntimeError(f"Erro ao obter URL de upload: {resp}")

    upload_url = resp["upload_url"]
    file_id = resp["file_id"]

    # 2. Fazer upload do arquivo
    with open(image_path, "rb") as f:
        upload_resp = requests.post(upload_url, files={"file": f})
        if upload_resp.status_code != 200:
            raise RuntimeError(f"Erro no upload: {upload_resp.text}")

    # 3. Completar o upload
    resp = requests.post(
        f"{SLACK_API}/files.completeUploadExternal",
        headers=HEADERS,
        json={"files": [{"id": file_id}]},
    ).json()

    if not resp.get("ok"):
        raise RuntimeError(f"Erro ao completar upload: {resp}")

    # 4. Obter informações do arquivo
    file_info = resp.get("files", [{}])[0]

    # Retorna url_private (funciona para usuários do workspace)
    return file_info.get("url_private", "")


def find_local_images(md_text: str) -> list[tuple[str, str]]:
    """Encontra todas as imagens locais no markdown. Retorna lista de (match_completo, caminho)"""
    pattern = r'!\[([^\]]*)\]\((?!http)([^\)]+)\)'
    return [(m.group(0), m.group(2)) for m in re.finditer(pattern, md_text)]


def process_images(md_text: str, base_dir: str) -> str:
    """Faz upload das imagens locais e substitui os caminhos pelas URLs do Slack"""
    images = find_local_images(md_text)

    if not images:
        return md_text

    print(f"📷 Encontradas {len(images)} imagens para upload...")

    for match, img_path in images:
        # Resolve caminho relativo
        if img_path.startswith("./"):
            img_path = img_path[2:]
        full_path = os.path.join(base_dir, img_path)

        if not os.path.exists(full_path):
            print(f"  ⚠️  Imagem não encontrada: {full_path}")
            continue

        print(f"  📤 Enviando {img_path}...")
        try:
            url = upload_image(full_path)
            if url:
                # Substitui o caminho local pela URL do Slack
                new_match = match.replace(f"({img_path})", f"({url})")
                new_match = new_match.replace(f"(./{img_path})", f"({url})")
                md_text = md_text.replace(match, new_match)
                print(f"  ✅ {img_path} -> OK")
            else:
                print(f"  ⚠️  Não foi possível obter URL para {img_path}")
        except Exception as e:
            print(f"  ❌ Erro ao enviar {img_path}: {e}")

    return md_text


def markdown_to_canvas_document(md_text: str) -> dict:
    return {
        "type": "markdown",
        "markdown": md_text,
    }



def create_canvas(md_file: str, title: str = None) -> str:
    with open(md_file, "r", encoding="utf-8") as f:
        md = f.read()

    # Usa o nome do arquivo como título se não especificado
    if not title:
        title = Path(md_file).stem

    # Processa imagens locais (upload para Slack)
    base_dir = str(Path(md_file).parent)
    md = process_images(md, base_dir)

    payload = {
        "title": title,
        "document_content": markdown_to_canvas_document(md),
    }

    resp = requests.post(
        f"{SLACK_API}/canvases.create",
        headers=HEADERS,
        json=payload,
    ).json()

    if not resp.get("ok"):
        raise RuntimeError(f"Erro ao criar canvas: {resp}")

    return resp["canvas_id"]



def share_canvas_with_user(canvas_id: str, user_id: str):
    payload = {
        "canvas_id": canvas_id,
        "user_ids": [user_id],
        "access_level": "write",
    }

    resp = requests.post(
        f"{SLACK_API}/canvases.access.set",
        headers=HEADERS,
        json=payload,
    ).json()

    if not resp.get("ok"):
        raise RuntimeError(f"Erro ao compartilhar canvas: {resp}")


def get_team_info() -> tuple[str, str]:
    """Obtém o domínio e ID do workspace"""
    resp = requests.post(
        f"{SLACK_API}/auth.test",
        headers=HEADERS,
    ).json()

    if not resp.get("ok"):
        return "app", ""

    # Extrai domínio da URL (https://domain.slack.com/)
    url = resp.get("url", "")
    domain = url.replace("https://", "").replace(".slack.com/", "") if url else "app"
    team_id = resp.get("team_id", "")

    return domain, team_id


def send_dm(user_id: str, canvas_id: str):
    domain, team_id = get_team_info()
    canvas_url = f"https://{domain}.slack.com/docs/{team_id}/{canvas_id}"

    payload = {
        "channel": user_id,
        "text": f"📄 Criei um canvas para você:\n{canvas_url}",
    }

    requests.post(
        f"{SLACK_API}/chat.postMessage",
        headers=HEADERS,
        json=payload,
    )

    return canvas_url


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python publish_canvas_to_slack.py <arquivo.md> [titulo]")
        print("Exemplo: python publish_canvas_to_slack.py report.md \"Retrospectiva Q1\"")
        sys.exit(1)

    MD_FILE = sys.argv[1]
    TITLE = sys.argv[2] if len(sys.argv) > 2 else None
    YOUR_USER_ID = os.getenv("SLACK_USER_ID")
    if not YOUR_USER_ID:
        print("❌ Defina SLACK_USER_ID (ex: no .env ou via export)")
        sys.exit(1)

    if not os.path.exists(MD_FILE):
        print(f"❌ Arquivo não encontrado: {MD_FILE}")
        sys.exit(1)

    canvas_id = create_canvas(MD_FILE, TITLE)
    print(f"✅ Canvas criado: {canvas_id}")

    share_canvas_with_user(canvas_id, YOUR_USER_ID)
    print("🔐 Canvas compartilhado no seu direct")

    canvas_url = send_dm(YOUR_USER_ID, canvas_id)
    print(f"📩 Link enviado no DM: {canvas_url}")

