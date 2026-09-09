# Exercício 1.2: como n, k e p afetam a disponibilidade

Implementação em [`disponibilidade.py`](disponibilidade.py), tabela completa em
`resultados.csv`, gráficos em `grafico_analitico.png` e `grafico_comparativo.png`.
Fórmula deduzida no [Exercício 1.1](../e1.1/RESOLUCAO.md).

Varredura de `n ∈ {1, 3, 5, 10}`, `k ∈ {1, ⌈n/2⌉, n}` e `p` de 0 a 1 em passos de
0,05. Recorte dos valores analíticos:

| n | k | caso | p=0,50 | p=0,70 | p=0,90 | p=0,95 |
|---|---|------|--------|--------|--------|--------|
| 1 | 1 | k=1=n | 0,5000 | 0,7000 | 0,9000 | 0,9500 |
| 3 | 1 | k=1 | 0,8750 | 0,9730 | 0,9990 | 0,9999 |
| 3 | 2 | k=n/2 | 0,5000 | 0,7840 | 0,9720 | 0,9928 |
| 3 | 3 | k=n | 0,1250 | 0,3430 | 0,7290 | 0,8574 |
| 5 | 1 | k=1 | 0,9688 | 0,9976 | 1,0000 | 1,0000 |
| 5 | 3 | k=n/2 | 0,5000 | 0,8369 | 0,9914 | 0,9988 |
| 5 | 5 | k=n | 0,0313 | 0,1681 | 0,5905 | 0,7738 |
| 10 | 1 | k=1 | 0,9990 | 1,0000 | 1,0000 | 1,0000 |
| 10 | 5 | k=n/2 | 0,6230 | 0,9527 | 0,9999 | 1,0000 |
| 10 | 10 | k=n | 0,0010 | 0,0282 | 0,3487 | 0,5987 |

## Efeito de n

Depende inteiramente do `k`. Com `k = 1`, mais réplicas sempre ajudam, e rápido: com
`p = 0,9`, ir de 1 para 3 servidores leva de 0,900 a 0,999 (um nove para três noves);
da quarta em diante o ganho é desprezível, porque o teto é 1.

Com `k = n`, mais réplicas sempre atrapalham. Ainda com `p = 0,9`, exigir as 10 no ar
dá 0,349, bem pior do que um servidor sozinho. Cada réplica adicionada vira mais um
ponto único de falha.

## Efeito de k

Fixando `n` e `p`, aumentar `k` sempre reduz a disponibilidade, e a queda é acentuada:
em `n = 10`, `p = 0,9`, ela vai de 1,000 (`k = 1`) para 0,9999 (`k = 5`) e despenca
para 0,349 (`k = 10`).

O quórum `k = ⌈n/2⌉` é o meio-termo que ainda escala: com `p = 0,7` vai de 0,784
(n=3) a 0,953 (n=10). O ponto de virada é `p = 0,5`, onde ele trava em torno de 0,5
independentemente de `n`; abaixo disso, mais réplicas passam a piorar o quórum.

## Efeito de p

Todas as curvas crescem monotonicamente de `A = 0` em `p = 0` até `A = 1` em `p = 1`.
O que muda com `k` é o formato: `k = 1` sobe quase imediatamente e satura cedo,
enquanto `k = n` fica colado no eixo e só sobe quando `p` já está alto. O `p` também
determina se replicar compensa — para `k = ⌈n/2⌉` e `k = n`, servidores ruins
(`p` baixo) fazem a replicação trabalhar contra a disponibilidade.

Ver `grafico_analitico.png`: um painel por `n`, uma curva por caso de `k`.
