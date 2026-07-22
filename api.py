"""
Truco RL — FastAPI microservice.

Expõe um endpoint POST /action que recebe o estado do jogo
como JSON e devolve a ação escolhida pelo agente treinado.

Usage:
    pip install fastapi uvicorn
    python api.py                          # carrega models/truco_final.zip
    python api.py --model models/truco_best_vs_random
    python api.py --port 8001

Unity envia POST /action com o corpo descrito em ActionRequest.
"""
import argparse
import numpy as np
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from truco.rl.obs import OBS_DIM
from truco.rl.actions import N_ACTIONS, TrucoAction

# Labels legíveis para Unity usar no log/debug
ACTION_LABELS = {
    TrucoAction.PLAY_CARD_0:               "Jogar carta 0",
    TrucoAction.PLAY_CARD_1:               "Jogar carta 1",
    TrucoAction.PLAY_CARD_2:               "Jogar carta 2",
    TrucoAction.TRUCO_ASK_OR_RAISE:        "TRUCO / Elevar truco",
    TrucoAction.TRUCO_ACCEPT:              "Aceitar truco",
    TrucoAction.TRUCO_REFUSE:              "Recusar truco",
    TrucoAction.ENVIDO:                    "ENVIDO",
    TrucoAction.REAL_ENVIDO:               "REAL ENVIDO",
    TrucoAction.FALTA_ENVIDO:              "FALTA ENVIDO",
    TrucoAction.ENVIDO_ACCEPT:             "Aceitar envido",
    TrucoAction.ENVIDO_REFUSE:             "Recusar envido",
    TrucoAction.DECLARE_FLOR:              "FLOR",
    TrucoAction.FLOR_ME_ACHICO:            "Me achico (flor)",
    TrucoAction.FLOR_CONTRA_FLOR:          "CONTRA-FLOR",
    TrucoAction.FLOR_ACEITAR:              "Aceitar confronto de flor",
    TrucoAction.FLOR_CONTRA_FLOR_AL_RESTO: "CONTRA-FLOR AL RESTO",
}

# ── Estado global do modelo ────────────────────────────────────────────────────
_model = None
_model_path = "models/truco_final"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model
    from sb3_contrib import MaskablePPO
    print(f"Carregando modelo: {_model_path} ...")
    _model = MaskablePPO.load(_model_path)
    print("Modelo carregado. Servidor pronto.")
    yield
    _model = None


app = FastAPI(title="Truco RL API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ────────────────────────────────────────────────────────────────────

class CardSlot(BaseModel):
    """Uma carta (presente ou ausente). Se absent=True, os outros campos são ignorados."""
    present: bool = False
    strength: float = 0.0      # força no truco (1–14)
    envido_value: float = 0.0  # valor para envido (0–7)


class ActionRequest(BaseModel):
    """
    Estado completo do jogo do ponto de vista do agente.
    Unity preenche este objeto a cada turno do agente.

    Todos os valores numéricos são os valores brutos — a normalização
    é feita aqui antes de entrar no modelo.
    """

    # Mão atual do agente (até 3 cartas)
    hand: List[CardSlot] = Field(default_factory=lambda: [CardSlot()] * 3)

    # Cartas jogadas por rodada — agente e adversário (3 rodadas cada)
    played_agent: List[CardSlot] = Field(default_factory=lambda: [CardSlot()] * 3)
    played_opp:   List[CardSlot] = Field(default_factory=lambda: [CardSlot()] * 3)

    # Placar
    score_agent:   int = 0
    score_opp:     int = 0
    points_to_win: int = 24

    # Contexto da mão
    i_am_mano:    bool = False
    round_number: int = 1          # 1, 2 ou 3

    # Resultados das rodadas (1=ganhou, -1=perdeu, 0=empate/não jogada)
    round_results: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])

    # Estado do truco
    truco_value:           int  = 0    # valor atual (0=não pedido, 2=truco, 3=retruco, 4=vale4)
    truco_pending:         bool = False
    truco_i_must_respond:  bool = False

    # Estado do envido
    envido_value_accepted: int  = 0
    envido_pending:        bool = False
    envido_i_must_respond: bool = False

    # Estado da flor
    flor_over:             bool = False
    flor_waiting:          bool = False
    i_have_flor:           bool = False
    envido_cancelled:      bool = False

    # Valores de envido da mão inicial (3 cartas)
    initial_envido_values: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    computed_envido_score: float = 0.0  # pontuação total (0–33)

    # Máscara de ações legais (16 booleanos)
    action_mask: List[bool] = Field(default_factory=lambda: [True] * N_ACTIONS)


class ActionResponse(BaseModel):
    action: int
    action_name: str


# ── Obs builder ───────────────────────────────────────────────────────────────

def build_obs(req: ActionRequest) -> np.ndarray:
    """Constrói o vetor de observação (39 floats) a partir do JSON do Unity."""
    obs = np.zeros(OBS_DIM, dtype=np.float32)
    pts = float(req.points_to_win)
    idx = 0

    # [0:6] Mão do agente
    hand = (req.hand + [CardSlot()] * 3)[:3]
    for card in hand:
        obs[idx]     = 1.0 if card.present else 0.0
        obs[idx + 1] = card.strength / 14.0
        idx += 2

    # [6:12] Cartas jogadas — agente
    played_a = (req.played_agent + [CardSlot()] * 3)[:3]
    for card in played_a:
        obs[idx]     = 1.0 if card.present else 0.0
        obs[idx + 1] = card.strength / 14.0
        idx += 2

    # [12:18] Cartas jogadas — adversário
    played_o = (req.played_opp + [CardSlot()] * 3)[:3]
    for card in played_o:
        obs[idx]     = 1.0 if card.present else 0.0
        obs[idx + 1] = card.strength / 14.0
        idx += 2

    # [18:20] Placar
    obs[idx]     = req.score_agent / pts
    obs[idx + 1] = req.score_opp   / pts
    idx += 2

    # [20] Mano
    obs[idx] = 1.0 if req.i_am_mano else 0.0
    idx += 1

    # [21] Rodada
    obs[idx] = req.round_number / 3.0
    idx += 1

    # [22:25] Resultados das rodadas
    results = (list(req.round_results) + [0.0, 0.0, 0.0])[:3]
    for v in results:
        obs[idx] = float(v)
        idx += 1

    # [25:28] Truco
    obs[idx]     = req.truco_value / 4.0
    obs[idx + 1] = 1.0 if req.truco_pending        else 0.0
    obs[idx + 2] = 1.0 if req.truco_i_must_respond else 0.0
    idx += 3

    # [28:31] Envido
    obs[idx]     = req.envido_value_accepted / pts
    obs[idx + 1] = 1.0 if req.envido_pending        else 0.0
    obs[idx + 2] = 1.0 if req.envido_i_must_respond else 0.0
    idx += 3

    # [31:35] Flor
    obs[idx]     = 1.0 if req.flor_over        else 0.0
    obs[idx + 1] = 1.0 if req.flor_waiting     else 0.0
    obs[idx + 2] = 1.0 if req.i_have_flor      else 0.0
    obs[idx + 3] = 1.0 if req.envido_cancelled else 0.0
    idx += 4

    # [35:38] Envido value por carta
    env_vals = (list(req.initial_envido_values) + [0.0, 0.0, 0.0])[:3]
    for v in env_vals:
        obs[idx] = v / 7.0
        idx += 1

    # [38] Envido score total
    obs[idx] = req.computed_envido_score / 33.0
    idx += 1

    assert idx == OBS_DIM
    return obs


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": _model is not None}


@app.post("/action", response_model=ActionResponse)
def get_action(req: ActionRequest):
    if _model is None:
        raise HTTPException(status_code=503, detail="Modelo não carregado")

    obs  = build_obs(req)
    mask = np.array(req.action_mask, dtype=bool)

    if not mask.any():
        raise HTTPException(status_code=400, detail="action_mask não tem nenhuma ação legal")

    action_arr, _ = _model.predict(
        obs[np.newaxis],
        action_masks=mask[np.newaxis],
        deterministic=True,
    )
    action = int(action_arr[0])

    return ActionResponse(
        action=action,
        action_name=ACTION_LABELS.get(TrucoAction(action), f"acao_{action}"),
    )


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="models/truco_final")
    parser.add_argument("--host",  default="127.0.0.1")
    parser.add_argument("--port",  type=int, default=8000)
    args = parser.parse_args()

    _model_path = args.model
    uvicorn.run(app, host=args.host, port=args.port)
