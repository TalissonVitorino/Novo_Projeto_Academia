import flet as ft
from datetime import datetime


def validar_data_brasil(data_str: str):
    try:
        if not data_str or len(data_str) != 10:
            return False, ""
        dia, mes, ano = data_str.split("/")
        dt = datetime(int(ano), int(mes), int(dia))
        # SQLite date format
        if dt.year < 1900 or dt.year > 2100:
            return False, ""
        return True, dt.strftime("%Y-%m-%d")
    except Exception:
        return False, ""


def sqlite_para_brasileiro(data_sqlite: str):
    try:
        dt = datetime.strptime(data_sqlite, "%Y-%m-%d")
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return data_sqlite


def calcular_imc(peso, altura):
    try:
        if not peso or not altura or peso <= 0 or altura <= 0:
            return "-", "Dados incompletos", ft.Colors.GREY_400
        imc = peso / (altura * altura)
        if imc <= 18.5:
            return f"{imc:.2f}", "Magreza", ft.Colors.BLUE_300
        if imc <= 24.9:
            return f"{imc:.2f}", "Saudável", ft.Colors.GREEN_400
        if imc <= 29.9:
            return f"{imc:.2f}", "Sobrepeso", ft.Colors.ORANGE_400
        if imc <= 34.9:
            return f"{imc:.2f}", "Obesidade I", ft.Colors.RED_400
        if imc <= 39.9:
            return f"{imc:.2f}", "Obesidade II", ft.Colors.RED_600
        return f"{imc:.2f}", "Obesidade III", ft.Colors.RED_800
    except Exception:
        return "-", "Erro", ft.Colors.GREY_400
