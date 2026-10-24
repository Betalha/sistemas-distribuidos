"""Gera os arquivos dos 3 cenários: imagem de ~1MB, texto de ~400KB e imagem de ~300KB."""
import os
import random

from PIL import Image

PASTA = "conteudo"
IMAGENS = {"imagem_1mb.jpg": 1_000_000, "imagem_300kb.jpg": 300_000}  # nome -> tamanho mínimo em bytes
TEXTO = "texto_400kb.html"
TAMANHO_TEXTO = 400_000
PALAVRAS = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor".split()
PALAVRAS_POR_PARAGRAFO = 120


def gerar_imagem(caminho, tamanho_minimo):
    """Ruído aleatório não comprime bem: aumenta a imagem até passar do tamanho desejado."""
    lado = 100
    while True:
        Image.effect_noise((lado, lado), 64).convert("RGB").save(caminho, quality=85)
        if os.path.getsize(caminho) >= tamanho_minimo:
            return
        lado += 20


def gerar_texto(caminho, tamanho_minimo):
    random.seed(1)
    with open(caminho, "w") as f:
        while f.tell() < tamanho_minimo:
            f.write("<p>" + " ".join(random.choices(PALAVRAS, k=PALAVRAS_POR_PARAGRAFO)) + ".</p>\n")


if __name__ == "__main__":
    os.makedirs(PASTA, exist_ok=True)
    for nome, tamanho in IMAGENS.items():
        gerar_imagem(os.path.join(PASTA, nome), tamanho)
    gerar_texto(os.path.join(PASTA, TEXTO), TAMANHO_TEXTO)

    for nome in sorted(os.listdir(PASTA)):
        print(f"{nome}: {os.path.getsize(os.path.join(PASTA, nome))} bytes")
