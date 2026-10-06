# WordPress com múltiplas instâncias (Nginx + Docker Compose)

Três instâncias do WordPress rodam atrás de um Nginx, que funciona como balanceador de carga. Todas usam o mesmo banco MySQL, então qualquer uma delas entrega o mesmo conteúdo.

## Arquitetura

```
              host:80
                 │
            ┌────▼────┐
            │  nginx  │  balanceador (único com porta exposta)
            └────┬────┘
     ┌───────────┼───────────┐
┌────▼─────┐┌────▼─────┐┌────▼─────┐
│wordpress1││wordpress2││wordpress3│  ← ./html compartilhada (/var/www/html)
└────┬─────┘└────┬─────┘└────┬─────┘
     └───────────┼───────────┘
            ┌────▼────┐
            │   db    │  MySQL 5.7 (acessível só pela rede interna)
            └─────────┘
```

| Serviço | Imagem | Papel |
|---|---|---|
| `nginx` | `nginx:1.19.0` | Recebe as requisições na porta 80 e as distribui entre os WordPress |
| `wordpress1..3` | `wordpress:5.4.2-php7.2-apache` | Executam a aplicação |
| `db` | `mysql:5.7` | Banco de dados único, compartilhado pelas três instâncias |

## Como funciona

1. **Rede**: o Compose cria uma rede interna e cada contêiner pode ser encontrado pelo nome do serviço (`db`, `wordpress1`...). Só o `nginx` publica porta no host. O WordPress e o MySQL não ficam acessíveis de fora, apenas pela rede interna.
2. **Balanceamento** (`nginx.conf`): o bloco `upstream wordpress` lista as três instâncias e o `proxy_pass http://wordpress` reparte as requisições entre elas em *round-robin*, que é o padrão do Nginx. O cabeçalho `X-Upstream $upstream_addr` informa qual instância atendeu cada requisição.
3. **Estado compartilhado**:
   - **Banco**: as três instâncias usam as mesmas variáveis `WORDPRESS_DB_*` e se conectam ao mesmo `db`. Posts, usuários e configurações ficam iguais em todas.
   - **Arquivos**: a pasta `./html` do host é montada em `/var/www/html` nos três WordPress, então temas, plugins e uploads são os mesmos. O Nginx monta essa mesma pasta em `/usr/share/nginx/html`.
   - **Persistência**: os dados do MySQL ficam no volume nomeado `db_data` e não se perdem quando os contêineres são recriados.
4. **Configuração enxuta**: os três serviços WordPress usam uma âncora YAML (`x-wordpress: &wordpress`), o que evita repetir a mesma configuração três vezes.

## Executando

```bash
docker compose up -d        # sobe os 5 contêineres
docker compose ps           # confere o estado
docker compose down         # para tudo (adicione -v para apagar o banco)
```

Depois de subir, abra `http://localhost` no navegador para concluir a instalação do WordPress.

## Testando o balanceamento

```bash
for i in $(seq 6); do curl -sI http://localhost/ | grep -i x-upstream; done
```

A saída mostra três IPs diferentes se alternando, um para cada contêiner WordPress:

```
X-Upstream: 172.23.0.4:80
X-Upstream: 172.23.0.5:80
X-Upstream: 172.23.0.3:80
```

Para ver o mesmo pelo navegador, abra as ferramentas de desenvolvedor (F12), vá na aba **Rede** e confira o cabeçalho `X-Upstream` das respostas.
