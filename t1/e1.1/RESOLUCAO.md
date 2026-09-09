# Exercício 1.1: dedução da fórmula de disponibilidade

Parâmetros: `n` servidores (`n > 0`), `k` servidores no ar necessários para acesso
consistente (`0 < k ≤ n`), `p` a probabilidade de um servidor estar disponível
(`0 ≤ p ≤ 1`).

Assumo que os servidores falham de forma independente e todos com a mesma
probabilidade `p`. O serviço está disponível quando pelo menos `k` deles estão no ar.

## Casos extremos

**k = 1 (consulta).** Basta um servidor. É mais curto calcular o complemento: o
serviço só cai se todos caírem, o que por independência vale `(1−p)^n`. Logo:

```
A(n, 1, p) = 1 − (1 − p)^n
```

**k = n (atualização).** Todos precisam estar no ar ao mesmo tempo, e as
probabilidades multiplicam:

```
A(n, n, p) = p^n
```

As duas apontam para lados opostos: com `n` crescendo, a primeira sobe para 1 e a
segunda desce para 0. Replicar ajuda a leitura e atrapalha a escrita síncrona.

## Caso geral

Seja `X` o número de servidores no ar. Cada servidor é um ensaio de Bernoulli
independente, então `X ~ Binomial(n, p)`:

```
P[X = i] = C(n, i) · p^i · (1 − p)^(n − i)
```

`p^i` é a chance de `i` servidores específicos estarem no ar, `(1−p)^(n−i)` a dos
outros estarem fora, e `C(n, i)` conta as escolhas possíveis desse grupo, já que só
importa *quantos* estão no ar. O serviço funciona quando `X ≥ k`, e como os eventos
`X = i` são mutuamente exclusivos, basta somar:

```
                n
A(n, k, p) =    Σ   C(n, i) · p^i · (1 − p)^(n − i)
              i = k
```

## Conferindo

- `k = n`: sobra só o termo `i = n`, que é `p^n`.
- `k = 1`: a soma de `i = 0` a `n` vale 1 (binômio de Newton); tirando o termo
  `i = 0`, sobra `1 − (1−p)^n`.
- `p = 0` dá 0 e `p = 1` dá 1, para qualquer `k`.

## Interpretação

A fórmula é a cauda superior da binomial. Aumentar `n` com `k` fixo sempre melhora a
disponibilidade; aumentar `k` sempre piora.

O caso interessante é o quórum `k = ⌈n/2⌉`, usado por Paxos e Raft (maioria estrita
quando `n` é ímpar; para `n` par a maioria seria `n/2 + 1`). Ao contrário de `k = n`,
ele continua melhorando com mais réplicas, desde que `p > 0,5` — daí os algoritmos de
consenso pedirem maioria e não unanimidade. Abaixo de `p = 0,5` isso se inverte:
mais réplicas pioram o quórum, porque a fração de máquinas no ar converge para `p`.

Vale lembrar que a hipótese de independência torna o resultado otimista. Falhas
correlacionadas (uma zona inteira, um deploy ruim) derrubam várias réplicas de uma
vez, então o número calculado aqui é um teto, não uma previsão de SLA.

