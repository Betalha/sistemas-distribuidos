# Trabalho 6 - SOAP x REST x GraphQL x gRPC

Comparamos 4 tecnologias de comunicação entre sistemas implementando **o mesmo serviço** nas quatro, em **duas linguagens (Python e Java)**, e medindo o desempenho das 8 implementações com teste de carga.

O serviço é um streaming de músicas: usuários, músicas e playlists (relação usuário 1..N playlist N..M música), com CRUD e 5 consultas do enunciado.

## 1. O que o enunciado pede
1. Pesquisar origem, características, vantagens e desvantagens de SOAP, REST, GraphQL e gRPC.
2. Implementar o mesmo serviço nas 4 tecnologias (8 entregas: 4 em Python e 4 em Java).
3. Rodar testes de carga e comparar.
4. Fazer uma análise crítica com gráficos.

Esclarecimentos do professor (21/11/2026):
- Cada tecnologia é uma entrega completa, sem misturar (por exemplo, nada de `/users` em GraphQL e `/playlists` em REST). Resposta: opção B, 8 entregas (4 tecnologias em Python e as mesmas 4 em Java).
- São 3 entidades por API (usuários, músicas, playlists), e o código de tratamento pode ser reaproveitado entre as APIs da mesma linguagem (aqui, `app/data.py`).

## 2. Como foi feito

### Escolhas
- **Python**: FastAPI, Strawberry, grpcio e Locust cobrem as 4 tecnologias.
- **Java 21**: JDK `HttpServer` (REST, GraphQL e SOAP), graphql-java e grpc-java. Um projeto Maven, um jar, e o argumento `rest|graphql|soap|grpc` escolhe o serviço. Compila dentro do Docker (não precisa de Maven na máquina).
- **Dados em memória, num módulo só por linguagem** (`app/data.py` e `java/.../Data.java`), usado pelas 4 implementações da linguagem. Assim a diferença medida vem da tecnologia, não da lógica. Semente: 50 usuários, 200 músicas, 150 playlists com 10 músicas cada. O Java não reproduz o sorteio do Python, então carrega o mesmo estado exportado em `java/src/main/resources/seed.json`.
- **Isolamento**: cada serviço roda num contêiner com 1 CPU (`docker-compose.yml`), então a comparação é justa.

### As 4 implementações em Python (`app/`)
| Tecnologia | Arquivo | Como funciona |
|---|---|---|
| REST | `rest_server.py` (FastAPI) | URLs de recurso + verbos HTTP, JSON. Ex.: `GET /users/7/playlists` |
| GraphQL | `graphql_server.py` (Strawberry) | Um endpoint `/graphql`, esquema tipado, relações aninhadas. Ex.: `user { playlists { songs } }` |
| SOAP | `soap_server.py` | Envelope XML em `POST /soap`; a operação é o primeiro filho do Body (ex.: `ListPlaylistsByUser`). Escrito à mão, sem WSDL, porque as libs de servidor SOAP em Python estão abandonadas |
| gRPC | `music.proto` + `grpc_server.py` | Contrato `.proto`, protobuf binário sobre HTTP/2; stubs gerados no build do Docker |

### As 4 implementações em Java (`java/src/main/java/music/`)
Mesmo contrato do Python, então o mesmo `locustfile.py` mede as duas linguagens.

| Tecnologia | Arquivo | Observação |
|---|---|---|
| REST | `Rest.java` | Mesmas rotas, JSON (Jackson), 201 no POST, 204 no DELETE, 404 se não existe |
| GraphQL | `GraphQl.java` | graphql-java com o `schema.graphqls`, que é o SDL gerado pelo Strawberry |
| SOAP | `Soap.java` | Escrito à mão, XML do JDK, mesmo envelope e mesmas operações do Python |
| gRPC | `Grpc.java` | Compilado do mesmo `music.proto` |

### O teste de carga (`app/locustfile.py`)
- Mesma carga nas 8: listar usuários, listar músicas, playlists de um usuário (peso 3), músicas de uma playlist (peso 3), playlists de uma música (peso 2) e um ciclo criar/alterar/remover usuário.
- Espera de 50 a 150 ms entre requisições.
- 10, 50, 200 e 500 usuários simultâneos, 30 s cada, 2 processos Locust.
- Antes da bateria, cada serviço Java recebe 15 s de aquecimento (JIT da JVM), descartado.
- Um teste de 10 s por serviço Java, com 0 falhas, antecedeu a bateria.
- Um teste curto antes da bateria achou dois bugs, já corrigidos: o Locust não coletava as tarefas do mixin e o gRPC falhava ao converter mensagem em dicionário.

### A análise
`graficos.py` lê a linha `Aggregated` de cada CSV do Locust e gera `tabela.csv` e os gráficos em `graficos/`: vazão, tempo médio, p95 e bytes por operação.

## 3. Estrutura
- `app/`: serviços Python, `.proto`, `Dockerfile`, `locustfile.py`
- `java/`: serviços Java (`pom.xml`, `Dockerfile`, `src/`)
- `docker-compose.yml`: 8 serviços (Python nas portas 8001 a 8004, Java de 8011 a 8014); `locust` no perfil `tools`
- `testes.sh`: bateria completa (8 serviços x usuários)
- `graficos.py`: tabela e gráficos
- `resultados/`: CSVs do Locust; `graficos/` e `tabela.csv`: saída da análise

## 4. Como reproduzir
```bash
./testes.sh                  # ~25 min, gera resultados/*.csv
                             # variar: DURACAO=60s USUARIOS="10 100" ./testes.sh
python3 graficos.py          # tabela.csv e graficos/*.png
python3 graficos.py --test   # checagem rápida do script
```

## 5. Resultados
Vazão em req/s, entre parênteses o p95 em ms. Execução única, 30 s, 0 falhas nas 32 execuções.

| usuários | REST py | REST java | GraphQL py | GraphQL java | SOAP py | SOAP java | gRPC py | gRPC java |
|---|---|---|---|---|---|---|---|---|
| 10 | 112 (5) | 108 (42) | 105 (18) | 105 (43) | 115 (4) | 105 (43) | 113 (3) | 114 (2) |
| 50 | 559 (6) | 547 (42) | 247 (190) | 529 (43) | 567 (4) | 531 (43) | 571 (2) | 569 (2) |
| 200 | 1774 (39) | 2151 (43) | 232 (860) | 2069 (45) | 2152 (12) | 2080 (44) | 2288 (1) | 2306 (1) |
| 500 | 1596 (260) | 2367 (650) | 223 (2300) | 2144 (710) | 2300 (150) | 2259 (700) | 4593 (61) | 5669 (2) |

Tamanho médio da resposta: gRPC ~700 B, REST ~1500 B, GraphQL ~1500-1900 B, SOAP ~2600-3000 B. Python e Java retornam praticamente o mesmo tamanho, o que confirma que o contrato é o mesmo.

Os números do Python mudaram um pouco em relação à bateria anterior (por exemplo REST com 200 usuários foi de 1364 para 1774 req/s). É a variação de uma execução única, não uma diferença de código.

## 6. Como ler os resultados

**10 usuários: todas empatam (~105 a 115 req/s).** A demanda é que limita: 10 usuários com ~0,1 s de espera geram poucas requisições e o sistema tem folga. Só o tempo de resposta diferencia.

**Entre tecnologias (dentro de cada linguagem):**
- **GraphQL em Python** trava em ~230 req/s e o tempo explode (média de 2 s com 500 usuários). Cada requisição gasta muita CPU resolvendo campos e relações no Strawberry.
- **gRPC** é o mais rápido nas duas linguagens e o único que passa de ~2300 req/s. Protobuf binário e HTTP/2 são mais baratos e a resposta é menor.
- **REST e SOAP** ficam entre os dois. O SOAP escrito à mão tem tamanho de resposta ~1,8x maior que o REST, mas o servidor faz menos trabalho que o FastAPI com validação.

**Entre linguagens (o achado novo):**
- **O GraphQL é o que mais muda.** Em Java ele fica junto de REST e SOAP (~2100 req/s com 200 usuários), contra 232 em Python. Boa parte do custo do GraphQL em Python é da biblioteca (Strawberry), não da ideia de GraphQL.
- **gRPC em Java** chega a 5669 req/s com 500 usuários e média de 1,9 ms, contra 4593 req/s e 22 ms em Python.
- **REST, SOAP e GraphQL em Java parecem bater num teto comum (~2100 a 2400 req/s).** Como esse teto é quase igual para três tecnologias diferentes e também aparece no SOAP e gRPC em Python, a hipótese é que o limite seja o gerador de carga (Locust, 2 processos) e não os serviços. Não foi verificado.
- **O p95 do Java HTTP é ~42 ms mesmo com 10 usuários**, enquanto a média é de 5 a 8 ms. É um degrau fixo, que sugere um atraso de ~40 ms de ACK do TCP no servidor HTTP do JDK em parte das respostas. Também não foi verificado; o gRPC em Java não tem esse degrau.

**Média x p95.** O p95 mostra a cauda que a média esconde. Com 500 usuários, o p95 do GraphQL em Python é 2300 ms e o do gRPC em Java é 2 ms.

## 7. As tecnologias (origem, prós, contras e código)

**REST** (Fielding, 2000). Recursos identificados por URL e manipulados com verbos HTTP, em JSON.
- Prós: simples, cacheável, universal. Contras: over/under-fetching, vários round-trips para dados relacionados.
```python
@app.get("/users/{id}/playlists")
async def pu(id: int): return data.playlists_of_user(id)
```

**GraphQL** (Facebook, aberto em 2015). Um endpoint; o cliente descreve os campos que quer e navega pelas relações.
- Prós: sem over-fetching, uma consulta traz o aninhado. Contras: resolvers caros no servidor, cache mais difícil.
```python
@strawberry.type
class Playlist:
    id: int
    name: str
    @strawberry.field
    def songs(self) -> list[Song]:
        return [Song(**s) for s in data.songs_of_playlist(self.id)]
```

**SOAP** (W3C, fim dos anos 1990). Mensagens em envelope XML, normalmente com contrato WSDL e extensões WS-*.
- Prós: contrato formal, padrões corporativos (segurança, transação). Contras: verboso, mais lento, ferramental pesado.
```python
OPS["ListPlaylistsByUser"] = lambda p: data.playlists_of_user(p["user_id"])
```

**gRPC** (Google, aberto em 2015). Contrato em `.proto`, protobuf binário sobre HTTP/2, com streaming.
- Prós: rápido, payload pequeno, contrato fortemente tipado e geração de código. Contras: difícil de depurar e de usar direto do navegador.
```proto
service Music {
  rpc ListPlaylistsByUser(Id) returns (Playlists);
}
```

## 8. Conclusão por tecnologia
- **gRPC**: melhor desempenho e menor payload, contrato forte. Pior de depurar e difícil de usar direto do navegador. Bom para comunicação entre serviços internos.
- **REST**: bom equilíbrio entre simplicidade e desempenho. Bom para APIs públicas.
- **GraphQL**: o mais flexível para o cliente (pede só os campos que precisa, aninha relações), mas o mais caro no servidor. Faz sentido com clientes variados ou móveis.
- **SOAP**: o mais verboso. Só se justifica por legado ou exigência de contrato WS-*.

## 9. Limitações
- Gerador de carga e serviços na mesma máquina; com 500 usuários o gerador pode limitar os resultados (ver seção 6).
- Os serviços Java HTTP usam o servidor embutido do JDK, enquanto o Python usa o uvicorn. Parte da diferença entre linguagens é do servidor HTTP, não da linguagem. O gRPC usa a stack própria de cada lado.
- Execução única de 30 s, sem repetição, então não há dispersão medida.
- Dados pequenos e em memória, sem banco.
- O SOAP escrito à mão (nas duas linguagens) favorece o SOAP frente a uma stack real com WSDL. Parte da diferença REST/SOAP é do FastAPI, não da tecnologia.
- O mix de carga usa a granularidade de chamadas do REST. O ganho do GraphQL (uma consulta aninhada no lugar de várias chamadas) não foi medido.

## 10. Falta fazer
- Prints da máquina dos testes (16 CPUs, 11 GB RAM, Fedora).
- Opcional: repetir a bateria 3x para mostrar dispersão.
