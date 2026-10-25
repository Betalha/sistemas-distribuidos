import os
import re

from locust import HttpUser, between, task

POST = os.environ.get("POST", "/")       # caminho do post do cenário, passado pelo testes.sh
HOST_DO_SITE = "localhost"               # siteurl do WordPress; evita redirecionamento
ESPERA_MIN, ESPERA_MAX = 1, 3            # segundos entre um acesso e outro
IMAGENS = re.compile(r'(/wp-content/uploads/[^"\'\s?]+)')
MINIATURA = re.compile(r"-\d+x\d+\.")    # ex.: foto-300x200.jpg


class Visitante(HttpUser):
    """Abre o post e baixa as imagens dele, como um navegador."""

    wait_time = between(ESPERA_MIN, ESPERA_MAX)

    def on_start(self):
        self.client.headers["Host"] = HOST_DO_SITE

    @task
    def ler_post(self):
        resposta = self.client.get(POST, name="post")
        for imagem in set(IMAGENS.findall(resposta.text)):
            if not MINIATURA.search(imagem):
                self.client.get(imagem, name="imagem")
