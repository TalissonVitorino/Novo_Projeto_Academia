import socket
import sys
import subprocess
import os
import time
from typing import Optional

import flet as ft
from app.app import main as app_main


def _pick_port(pref_ports=(8550, 8080, 8000, 3000)) -> int:
    """Returns the first available port from pref_ports. If all busy, returns 8550."""
    for p in pref_ports:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", p))
                # If bind succeeded, it's free. Close and return this port.
                return p
        except OSError:
            continue
    return 8550


def _get_local_ip() -> str:
    """Detect best LAN IPv4 address to share via QR.
    Tries multiple strategies and avoids returning 'localhost'.
    """
    candidates = []
    # Try default route trick (most reliable)
    for target in ("8.8.8.8", "1.1.1.1", "10.255.255.255"):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect((target, 80))
            ip = s.getsockname()[0]
            candidates.append(ip)
        except Exception:
            pass
        finally:
            try:
                s.close()
            except Exception:
                pass
    # Fallback to hostname resolution
    try:
        ip = socket.gethostbyname(socket.gethostname())
        candidates.append(ip)
    except Exception:
        pass
    # Pick first private IPv4 candidate
    def _is_private(addr: str) -> bool:
        return (
            addr.startswith("10.") or
            addr.startswith("192.168.") or
            any(addr.startswith(f"172.{i}.") for i in range(16, 32))
        )
    for c in candidates:
        if _is_private(c):
            return c
    # As last resort return the first non-loopback candidate
    for c in candidates:
        if not c.startswith("127."):
            return c
    # Give up: return loopback (will be handled by caller with warning)
    return candidates[0] if candidates else "127.0.0.1"


def _parse_ipconfig_for_wifi_ipv4() -> Optional[str]:
    """Windows-only: tenta extrair o IPv4 do adaptador Wi‑Fi a partir do `ipconfig`.
    Dá preferência a seções com "Wireless" ou "Wi-Fi" e endereços 192.168.*.
    """
    if os.name != "nt":
        return None
    try:
        out = subprocess.check_output(["ipconfig"], stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="ignore")
    except Exception:
        return None
    blocks = out.split("\n\n")
    wifi_blocks = [b for b in blocks if ("Wireless" in b) or ("Wi-Fi" in b) or ("Sem Fio" in b) or ("Sem Fio (Wi-Fi)" in b)]
    def _extract_ipv4(block: str) -> Optional[str]:
        for line in block.splitlines():
            l = line.strip()
            if "IPv4" in l and ":" in l:
                try:
                    ip = l.split(":", 1)[1].strip()
                    # Remove possíveis sufixos (ex.: (Preferencial))
                    ip = ip.split(" ")[0]
                    return ip
                except Exception:
                    pass
        return None
    # Preferir blocos Wi-Fi
    for b in wifi_blocks:
        ip = _extract_ipv4(b)
        if ip and ip.startswith("192.168."):
            return ip
    for b in wifi_blocks:
        ip = _extract_ipv4(b)
        if ip and (ip.startswith("10.") or any(ip.startswith(f"172.{i}.") for i in range(16, 32))):
            return ip
    # Se não achou em Wi-Fi, tentar qualquer bloco com 192.168.* (Ethernet doméstica)
    for b in blocks:
        ip = _extract_ipv4(b)
        if ip and ip.startswith("192.168."):
            return ip
    # Último recurso: primeiro IPv4 privado em qualquer bloco
    for b in blocks:
        ip = _extract_ipv4(b)
        if ip and (ip.startswith("10.") or any(ip.startswith(f"172.{i}.") for i in range(16, 32))):
            return ip
    return None


def _env_or_best_ip() -> str:
    # 1) prioridade para override manual via ambiente
    ip = os.environ.get("FLET_LAN_IP")
    if ip:
        return ip

    # 2) tentar descobrir via ipconfig (Windows) priorizando Wi‑Fi
    ip_wifi = _parse_ipconfig_for_wifi_ipv4()
    if ip_wifi:
        return ip_wifi

    # 3) tenta heurística atual (rota padrão)
    ip = _get_local_ip()

    # 4) como ajuda, lista candidatos e tenta priorizar 192.168.* (wi-fi doméstico comum)
    try:
        infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        cands = sorted({i[4][0] for i in infos})
        pref = [x for x in cands if x.startswith("192.168.")]
        if pref:
            return pref[0]
    except Exception:
        pass
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
    # Configurações (permitem override via env)
    host = os.environ.get("FLET_HOST", "0.0.0.0")
    env_port = os.environ.get("FLET_PORT")
    if env_port:
        try:
            port = int(env_port)
        except Exception:
            port = 8550
    else:
        # Escolhe automaticamente uma porta disponível entre opções comuns
        port = _pick_port()

    # Detecta IP LAN para o QR (não usa 127.x) com possibilidade de override por FLET_LAN_IP
    ip = _env_or_best_ip()
    url = f"http://{ip}:{port}"

    # Feedback se override foi usado
    if os.environ.get("FLET_LAN_IP"):
        print(f"[INFO] IP LAN forçado via FLET_LAN_IP={os.environ.get('FLET_LAN_IP')}")

    # Ajustes de compatibilidade: força Web Server e renderer HTML
    os.environ["FLET_FORCE_WEB_SERVER"] = "1"
    os.environ["FLET_WEB_RENDERER"] = "html"
    # Evita Service Worker cachear versão antiga (splash travado)
    os.environ["FLET_DISABLE_SW"] = "1"
    # Informe ao runtime o IP LAN real, não "0.0.0.0", para o cliente construir a URL de WebSocket corretamente
    os.environ["FLET_HOST"] = ip
    os.environ["FLET_PORT"] = str(port)

    # Dicas e QR no terminal
    log_level = os.environ.get("FLET_LOG_LEVEL", "info")
    os.environ["FLET_LOG_LEVEL"] = log_level

    print("============================================================")
    print(" Execução para Android via navegador (mesma rede Wi‑Fi) ")
    print("============================================================\n")
    print("1) Garanta que seu celular e este PC estão na MESMA rede Wi‑Fi.")
    print(f"2) Libere o firewall do Windows para conexões na porta {port} (Entrada TCP).")
    print("3) Escaneie o QR abaixo com a câmera do celular ou app de QR para abrir o app no navegador.\n")
    print(f"[INFO] Renderer: HTML | ServiceWorker: desabilitado | LOG: {log_level}")

    # Aviso se IP não parecer de rede privada
    if ip.startswith("127.") or ip == "localhost":
        print("[AVISO] Não foi possível detectar um IP da rede local. O QR com '127.0.0.1' NÃO funcionará no celular.")
        print("        Descubra o IP da sua máquina (ex.: 192.168.x.x) e abra manualmente: ")
        print(f"        http://SEU_IP_LOCAL:{port}\n")
    _print_qr_in_terminal(url)

    # Aguarda um pouco para você posicionar o celular antes de subir o servidor
    time.sleep(0.5)

    print("\n[INFO] Iniciando servidor Flet...")
    # Permitir opcionalmente bind direto no IP LAN (pode ajudar em alguns ambientes)
    bind_to_ip = os.environ.get("FLET_BIND_TO_IP", "0").lower() in ("1", "true", "yes")
    bind_host = ip if bind_to_ip else host

    print(f"[INFO] Bind: host={bind_host}, port={port}")
    print(f"[INFO] URL LAN (para o celular): {url}")
    if bind_to_ip:
        print("[INFO] Bind direto no IP LAN ativado (FLET_BIND_TO_IP=1).")
    print("[INFO] Pressione Ctrl+C para parar o servidor.\n")

    # Inicia o app Flet como Web Server acessível na LAN
    try:
        ft.app(
            target=app_main,
            view=ft.AppView.WEB_BROWSER,
            host=bind_host,
            port=port,
            # Força HTML renderer para máxima compatibilidade com Android
            web_renderer=ft.WebRenderer.HTML,
        )
    except KeyboardInterrupt:
        print("\n[INFO] Servidor encerrado pelo usuário.")
    except Exception as e:
        print(f"\n[ERRO] Falha ao iniciar servidor: {e}")
