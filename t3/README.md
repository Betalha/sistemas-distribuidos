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
| `docker-compose.yml` | db, wordpress (escalável), nginx e locust (perfil `locust`) |
| `nginx.conf` | `upstream wordpress { server wordpress:80; }` em round-robin |
| `locust/posts.env` | Caminho dos 3 posts dos cenários (`S1`, `S2`, `S3`) |
| `locust/locustfile.py` | Visitante que abre o post (`POST`) e baixa as imagens dele, como um navegador |
| `testes.sh` | Roda a matriz 3 cenários × {1,2,3} instâncias × {100,1000,10000} usuários e chama o `graficos.py` |
| `graficos.py` | Lê os CSVs do Locust e gera `graficos/*.png` e `graficos/resumo.csv` |

Os parâmetros de cada arquivo (duração, quantidades, espera) ficam declarados no topo dele.

## Pré-requisitos

- Docker com Compose v2
- Python 3 com `pandas` e `matplotlib` (`pip install pandas matplotlib`)
- Portas 80 e 8089 livres no host

## Passo a passo

A aplicação e os testes são executados separadamente.

**1. Aplicação**

```bash
docker compose up -d                       # db + 1 WordPress + nginx (o Locust não sobe)
docker compose up -d --scale wordpress=3   # com 3 instâncias
```

Na primeira vez, instale o WordPress em http://localhost e crie os 3 posts dos cenários
(imagem de ~1MB, texto de ~400KB, imagem de ~300KB). Grave o caminho de cada post em `locust/posts.env`:

```
S1=/2026/10/24/cenario-1-imagem-de-1mb/
S2=/2026/10/24/cenario-2-texto-de-400kb/
S3=/2026/10/24/cenario-3-imagem-de-300kb/
```

**2. Testes de carga** (comando próprio)

```bash
./testes.sh         # 27 execuções de 60s (~35 min) + gráficos
DURACAO=30s USUARIOS="100 1000" INSTANCIAS="1 3" CENARIOS="2" ./testes.sh   # subconjunto
```

O `testes.sh` muda a escala do serviço `wordpress` e reinicia o nginx a cada quantidade de instâncias.

**Locust avulso**, pela interface web em http://localhost:8089:

```bash
source locust/posts.env
POST="$S1" docker compose run --rm --service-ports -e POST locust
```

Para conferir o balanceamento: `for i in $(seq 6); do curl -sI http://localhost/ | grep -i x-upstream; done`

Para parar: `docker compose down` (com `-v` apaga também o banco e os posts).

## Detalhes importantes

- **Links permanentes**: o `posts.env` guarda o caminho do post (ex.: `/2026/10/24/cenario-1-.../`) e não `?p=ID`, porque o `?p=ID` gera um redirecionamento para `http://localhost`.
- **Endereço testado**: o Locust acessa `http://nginx`, que é o nome do serviço no compose, como o enunciado pede. O `siteurl` do WordPress é `http://localhost`, então o locustfile envia `Host: localhost`. Sem esse cabeçalho, o WordPress redirecionaria para `localhost`, que dentro do contêiner aponta para o próprio Locust.
- **Troca do número de instâncias**: o Nginx resolve o DNS só quando inicia, por isso o `testes.sh` reinicia o Nginx depois de cada `--scale`.
- **Comportamento do usuário**: cada usuário espera de 1 a 3s entre as tarefas (`between(1, 3)`). A taxa de criação é de até 100 usuários/s.
- **API do Locust**: o enunciado usa `HttpLocust`/`TaskSet`, do Locust 0.x, que já foi removido. A versão 2.x usa `HttpUser` e `wait_time`, e o `-c/-r` virou `-u/-r`.

## Resultados

Os gráficos ficam em `graficos/`. Para cada cenário há dois:

- `cenarioN_por_usuarios.png`: eixo X com o número de usuários, uma linha por número de instâncias;
- `cenarioN_por_instancias.png`: eixo X com o número de instâncias, uma linha por número de usuários.

As métricas no eixo Y são o tempo médio de resposta, o percentil 95, as requisições por segundo e a taxa de falhas.
A tabela com todos os números fica em `graficos/resumo.csv`.
