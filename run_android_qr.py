import socket
import sys
import subprocess
import os
import time
from typing import Optional

import flet as ft
from app.app import main as app_main


def _get_local_ip() -> str:
    # Try to detect LAN IP reliably
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = socket.gethostbyname(socket.gethostname())
    finally:
        s.close()
    # Fallback if still localhost
    if ip.startswith("127."):
        ip = "localhost"
    return ip


def _ensure_qrcode_installed() -> Optional[object]:
    try:
        import qrcode  # type: ignore
        return qrcode
    except Exception:
        print("[info] Instalando dependência 'qrcode' para gerar QR no terminal...", flush=True)
        python_exe = sys.executable
        try:
            subprocess.check_call([python_exe, "-m", "pip", "install", "qrcode[pil]"], stdout=subprocess.DEVNULL)
            import qrcode  # type: ignore
            return qrcode
        except Exception as e:
            print(f"[aviso] Não foi possível instalar 'qrcode' automaticamente: {e}")
            return None


def _print_qr_in_terminal(data: str) -> None:
    qrcode = _ensure_qrcode_installed()
    if not qrcode:
        print("\nAbra esta URL no seu Android:")
        print(data)
        print()
        return
    qr = qrcode.QRCode(border=1, box_size=1)
    qr.add_data(data)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    # Render simples em blocos: "  " (branco) e "██" (preto)
    print("\nEscaneie o QR code abaixo com a câmera do Android para abrir o app:\n")
    for row in matrix:
        line = "".join("  " if not cell else "██" for cell in row)
        print(line)
    print(f"\nURL: {data}\n")


if __name__ == "__main__":
    # Configurações
    host = os.getenv("FLET_HOST", "0.0.0.0")
    try:
        port = int(os.getenv("FLET_PORT", "8550"))
    except ValueError:
        port = 8550

    ip = _get_local_ip()
    url = f"http://{ip}:{port}"

    # Dicas e QR no terminal
    print("============================================================")
    print(" Execução para Android via navegador (mesma rede Wi‑Fi) ")
    print("============================================================\n")
    print("1) Garanta que seu celular e este PC estão na MESMA rede Wi‑Fi.")
    print("2) Libere o firewall do Windows para conexões na porta escolhida (padrão 8550).")
    print("3) Escaneie o QR abaixo com a câmera do celular ou app de QR para abrir o app no Chrome.\n")
    _print_qr_in_terminal(url)

    # Aguarda um pouco para você posicionar o celular antes de subir o servidor
    time.sleep(0.3)

    # Inicia o app Flet como Web Server acessível na LAN
    # Observação: 'view=WEB_BROWSER' evita janela desktop; use seu navegador do PC ou do telefone.
    # Força o modo Web Server (algumas versões do Flet exigem a variável de ambiente)
    os.environ.setdefault("FLET_FORCE_WEB_SERVER", "1")
    ft.app(
        target=app_main,
        view=ft.AppView.WEB_BROWSER,
        host=host,
        port=port,
        # assets_dir pode ser configurado se você usar assets estáticos.
    )
