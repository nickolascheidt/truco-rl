# truco-rl

[![ci](https://github.com/nickolascheidt/truco-rl/actions/workflows/ci.yml/badge.svg)](https://github.com/nickolascheidt/truco-rl/actions/workflows/ci.yml)

*[Read in English](README.md)*

Um motor de regras para **Truco Gaúcho** 1x1 e um agente de aprendizado por reforço que aprende
a jogar por *self-play*, sem partidas humanas e sem estratégia escrita à mão.

É um projeto de portfólio. O interessante está em transformar um jogo cheio de blefe e aposta
num ambiente de RL limpo, e em medir o agente com honestidade.

## Resultados

O agente treinou por 5 milhões de passos jogando contra cópias de si mesmo e depois foi
avaliado em 2.000 partidas contra dois adversários **contra os quais nunca treinou**:

- **Aleatório** escolhe uma ação legal qualquer.
- **Heurístico** é um bot de regras que joga como um iniciante cauteloso: pede envido só com
  pontuação boa, pede truco com carta forte ou rodada ganha e joga a carta mais barata que
  ganha cada rodada. Ele vence o aleatório em 89% das partidas.

| Checkpoint | vs Aleatório | vs Heurístico |
|---:|---:|---:|
| 250 mil passos | 89,6% | 38,0% |
| 750 mil | 88,4% | 54,1% |
| 1,25 milhão | 83,5% | 63,9% |
| **2,25 milhões** | **83,9%** | **73,1%** |
| 3,0 milhões | 81,5% | 60,1% |
| 3,5 milhões | 79,0% | 52,6% |
| 5,0 milhões (final) | 80,2% | 62,8% |

As taxas têm margem de cerca de ±2 pontos (95%). Para comparar: aleatório contra aleatório
vence 51%, e heurístico contra heurístico, 50,5%.

**O que a curva mostra.** O agente passa o bot heurístico por volta de 750 mil passos e chega
ao pico de 73% em 2,25 milhões. Depois disso ele *piora*, caindo até 53% antes de voltar a
uns 60%. É a falha clássica do *self-play* ingênuo: o adversário é sempre a cópia mais
recente, então o agente se especializa contra si mesmo e esquece estratégias que venciam
versões anteriores. A correção usual é um *pool* de adversários (uma liga com cópias antigas e
bots fixos), que é o próximo passo óbvio e não está implementado aqui.

Para reproduzir: `python train.py` (cerca de uma hora na CPU de um notebook, sem GPU) e
`python evaluate.py models/truco_2250000_steps`. Os modelos treinados não vão para o repo.

## Como funciona

- **Ambiente** (`truco/rl/env.py`): um env [Gymnasium](https://gymnasium.farama.org/) em que o
  agente é sempre um dos jogadores e a política do adversário roda dentro do `step()`. A
  partida vai a 24 pontos. A recompensa é +1/−1 no fim da partida, mais um pequeno termo
  proporcional aos pontos ganhos ou perdidos a cada passo, para que as apostas de envido e
  truco tenham sinal antes do fim do jogo.
- **Observação** (`truco/rl/obs.py`): 39 números com as cartas do agente, as cartas jogadas em
  cada rodada, o placar, quem é mano, o resultado das rodadas, o estado de cada aposta e a
  pontuação de envido. A mão do adversário fica escondida, como na mesa.
- **Ações** (`truco/rl/actions.py`): 16 ações discretas (jogar uma das três cartas, pedir ou
  responder cada aposta). Uma máscara marca as legais a cada passo, e o
  [MaskablePPO](https://sb3-contrib.readthedocs.io/) do sb3-contrib só sorteia entre elas.
- **Self-play** (`truco/rl/self_play.py`): a cada 20 mil passos os pesos atuais são copiados
  para o adversário.

## Regras implementadas

O motor cobre partidas 1x1. Ele segue as regras gaúchas mais comuns até onde eu as conheço;
há variações regionais, e onde foi preciso escolher, a escolha está listada aqui.

- **Cartas**: baralho espanhol de 40 cartas. As manilhas fixas são o 1 de espadas, o 1 de paus,
  o 7 de espadas e o 7 de ouros; depois vêm 3, 2, os outros ases, 12, 11, 10, os outros 7, 6, 5, 4.
- **Mão**: melhor de três rodadas. Rodada empatada é decidida pelas outras (empate depois de uma
  rodada ganha mantém quem ganhou a primeira); se as três empatarem, ganha o mano.
- **Truco**: Truco (2) → Retruco (3) → Vale Quatro (4). Quem recusa dá a quem pediu o valor
  anterior ao aumento.
- **Envido**: só na primeira rodada, antes de quem pede jogar carta. A cadeia só sobe: Envido
  no máximo duas vezes, Real Envido uma vez e depois Falta Envido, que encerra. Envido vale 2 e
  Real Envido 3, somados ao que já está na mesa; Falta Envido vale o que o lado perdedor ainda
  precisa para ganhar a partida. Empate vai para o mano.
- **Flor** (três cartas do mesmo naipe): cancela o envido. Responder *me achico* dá 4 a quem
  cantou e 2 ao outro lado; *contra flor* leva a um confronto que vale 6 ou a
  *contra flor al resto*.

Simplificações: não há duplas nem trios, nem sinais (señas) entre parceiros.

## Estrutura

```
truco/entities/   Card, Deck, Player, Team, Round, Hand, Game
truco/states/     máquinas de estado das apostas: Truco, Envido, Flor
truco/rl/         ambiente, codificação de observação e ações, self-play, bot heurístico
tests/            testes pytest do motor e do bot heurístico
train.py          treino com MaskablePPO + self-play
evaluate.py       taxa de vitória contra os baselines, com intervalo de 95%
play.py           jogar contra o agente no terminal
watch.py          assistir o agente jogar uma partida inteira
```

## Uso

Requer Python 3.11+.

```bash
pip install -e ".[rl,dev]"

pytest                                             # testes do motor e do bot

python train.py                                    # 5 milhões de passos, checkpoint a cada 250 mil
python train.py --steps 20000                      # teste rápido
python train.py --load models/truco_1000000_steps  # continuar um treino

python evaluate.py models/truco_final              # contra aleatório e heurístico
python evaluate.py heuristic                       # avaliar um baseline do mesmo jeito

python play.py models/truco_final                  # você contra o agente
python watch.py models/truco_final --opponent heuristic
```

## Licença

[MIT](LICENSE)
