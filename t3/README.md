# Trabalho 3: testes de carga no WordPress com Locust

Este trabalho usa a mesma arquitetura do Trabalho 2 (Nginx balanceando WordPress com um MySQL compartilhado). Foram feitas duas mudanças:

- as três instâncias `wordpress1..3` viraram um único serviço `wordpress`, escalável com `--scale wordpress=N`. O Nginx aponta para o nome `wordpress`, que o DNS do Docker resolve para todas as réplicas;
- o serviço `locust` (imagem oficial `locustio/locust`) entrou no `docker-compose.yml`, como o enunciado pede.

```
 locust ──► nginx:80 ──► wordpress (1..N réplicas) ──► db (MySQL 5.7)
 (8089)     (host:80)     ./html compartilhada
```

## Arquivos

| Arquivo | Função |
|---|---|
| `docker-compose.yml` | db, wordpress (escalável), nginx, locust e wpcli (só para o setup) |
| `nginx.conf` | `upstream wordpress { server wordpress:80; }`, em round-robin |
| `locust/locustfile.py` | Usuário que faz GET no post (`POST=/?p=ID`) e baixa as imagens dele, como faria um navegador |
| `gerar_conteudo.py` | Gera a imagem de ~1MB, o texto de ~400KB e a imagem de ~300KB em `conteudo/` |
| `setup.sh` | Sobe a stack, instala o WordPress via WP-CLI e cria os 3 posts (IDs em `locust/posts.env`) |
| `run.sh` | Roda a matriz 3 cenários × {1,2,3} instâncias × {10,100,1000} usuários |
| `graficos.py` | Lê os CSVs do Locust e gera `graficos/*.png` e `graficos/resumo.csv` |

## Pré-requisitos

- Docker com Compose v2
- Python 3 com `pillow`, `pandas` e `matplotlib` (`pip install pillow pandas matplotlib`)
- A porta 80 e a 8089 livres no host

## Passo a passo

```bash
./setup.sh      # 1. sobe tudo, instala o WP (admin/admin) e cria os posts dos cenários
./run.sh        # 2. roda os 27 testes (60s cada, ~35 min) e gera os gráficos
```

Variáveis do `run.sh`: `DURACAO=30s`, `INSTANCIAS="1 2 3"` e `USUARIOS="10 100 1000"`.
Exemplo: `DURACAO=2m USUARIOS="50 500" ./run.sh`.

Para subir só o site, sem o Locust: `docker compose up -d` (ou `docker compose up -d --scale wordpress=3`).
O Locust tem `profiles: [locust]` e só é executado quando chamado à parte:

```bash
source locust/posts.env
POST="/?p=$S1" docker compose run --rm --service-ports -e POST locust   # interface web em http://localhost:8089
POST="/?p=$S1" docker compose run --rm -e POST locust \
  -f /mnt/locust/locustfile.py -H http://nginx --headless -u 100 -r 10 -t 60s   # teste direto no terminal
```

Para conferir o balanceamento: `for i in $(seq 6); do curl -sI http://localhost/ | grep -i x-upstream; done`

Para limpar tudo: `docker compose down -v && sudo rm -rf html`

## Detalhes importantes

- **Endereço testado**: o Locust acessa `http://nginx`, que é o nome do serviço no compose, como o enunciado pede. O `siteurl` do WordPress é `http://localhost`, então o locustfile envia `Host: localhost`. Sem esse cabeçalho, o WordPress redirecionaria para `localhost`, que dentro do contêiner aponta para o próprio Locust.
- **Troca do número de instâncias**: o Nginx resolve o DNS só quando inicia, por isso o `run.sh` reinicia o Nginx depois de cada `--scale`.
- **Comportamento do usuário**: cada usuário espera de 1 a 3s entre as tarefas (`between(1, 3)`). A taxa de criação é de até 100 usuários/s.
- **API do Locust**: o enunciado usa `HttpLocust`/`TaskSet`, do Locust 0.x, que já foi removido. A versão 2.x usa `HttpUser` e `wait_time`, e o `-c/-r` virou `-u/-r`.

## Resultados

Os gráficos ficam em `graficos/`. Para cada cenário há dois:

- `cenarioN_por_usuarios.png`: eixo X com o número de usuários, uma linha por número de instâncias;
- `cenarioN_por_instancias.png`: eixo X com o número de instâncias, uma linha por número de usuários.

As métricas no eixo Y são o tempo médio de resposta, o percentil 95, as requisições por segundo e a taxa de falhas.
A tabela com todos os números fica em `graficos/resumo.csv`.
