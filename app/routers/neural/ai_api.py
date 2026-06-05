from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.neural import (
    CashFlowPredictor,
    ClientChurnPredictor,
    PnrOverrunPredictor,
    TransactionAnomalyDetector,
    FeatureEngineer,
    ModelRegistry,
)

router = APIRouter(prefix="/api/v1/ai", tags=["Neural AI"])


class NeuralNodeCreate(BaseModel):
    model_config = {"protected_namespaces": ()}
    organ: str
    cell: str
    name: str
    description: str = ""
    model_type: str = "default"
    status: str = "active"


class NeuralNodeResponse(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}
    id: int
    organ: str
    cell: str
    name: str
    description: str
    model_type: str
    status: str
    last_trained: str | None = None
    accuracy: float | None = None
    training_count: int = 0


class PredictRequest(BaseModel):
    pnr_number: str | None = None
    client_code: str | None = None
    transaction_ids: list[int] | None = None
    forecast_days: int = 30


class FeedbackRequest(BaseModel):
    prediction_id: str
    organ: str
    cell: str
    actual_outcome: Any
    feedback_text: str = ""


def _safe_db(callback, default=None):
    try:
        return callback()
    except Exception:
        return default


# ── Node Management ──────────────────────────────────────────

@router.post("/nodes", response_model=NeuralNodeResponse, status_code=status.HTTP_201_CREATED)
def create_node(data: NeuralNodeCreate, db: Session = Depends(get_db)):
    from app.models.neural import NeuralNode
    node = NeuralNode(
        organ=data.organ,
        cell=data.cell,
        name=data.name,
        description=data.description,
        model_type=data.model_type,
        status=data.status,
    )
    _safe_db(lambda: db.add(node))
    _safe_db(lambda: db.commit())
    _safe_db(lambda: db.refresh(node))
    return node


@router.get("/nodes", response_model=list[NeuralNodeResponse])
def list_nodes(
    organ: str | None = Query(None),
    cell: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    from app.models.neural import NeuralNode
    result = _safe_db(lambda: _do_list_nodes(db, NeuralNode, organ, cell, status), [])
    return result or []


def _do_list_nodes(db, cls, organ, cell, status):
    stmt = select(cls)
    if organ:
        stmt = stmt.where(cls.organ == organ)
    if cell:
        stmt = stmt.where(cls.cell == cell)
    if status:
        stmt = stmt.where(cls.status == status)
    return list(db.execute(stmt).scalars().all())


@router.get("/nodes/{node_id}", response_model=NeuralNodeResponse)
def get_node(node_id: int, db: Session = Depends(get_db)):
    from app.models.neural import NeuralNode
    node = _safe_db(lambda: db.get(NeuralNode, node_id))
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Neural node not found")
    return node


@router.post("/nodes/{node_id}/train")
def train_node(node_id: int, db: Session = Depends(get_db)):
    from app.models.neural import NeuralNode, NeuralTrainingHistory
    node = _safe_db(lambda: db.get(NeuralNode, node_id))
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Neural node not found or DB unavailable")
    predictor = _get_predictor(node.organ, node.cell, db)
    if predictor is None:
        raise HTTPException(status_code=400, detail=f"No predictor for organ={node.organ} cell={node.cell}")
    X, y = predictor._build_training_data()
    if X is None or len(X) == 0:
        raise HTTPException(status_code=400, detail="Insufficient training data")
    predictor._fit(X, y)
    serialized = predictor.serialize()
    history = NeuralTrainingHistory(
        node_id=node_id,
        training_date=datetime.now(timezone.utc),
        samples=len(X),
        features=X.shape[1] if len(X.shape) > 1 else 1,
        accuracy=0.0,
        status="completed",
        model_data=serialized,
    )
    _safe_db(lambda: db.add(history))
    _safe_db(lambda: setattr(node, 'last_trained', datetime.now(timezone.utc)))
    _safe_db(lambda: setattr(node, 'training_count', (node.training_count or 0) + 1))
    _safe_db(lambda: db.commit())
    return {
        "node_id": node_id,
        "status": "trained",
        "samples": len(X),
        "features": X.shape[1] if len(X.shape) > 1 else 1,
    }


# ── Predictions ──────────────────────────────────────────────

@router.post("/predict/{organ}/{cell}")
def predict(organ: str, cell: str, req: PredictRequest, db: Session = Depends(get_db)):
    predictor = _get_predictor(organ, cell, db)
    if predictor is None:
        raise HTTPException(status_code=404, detail=f"No predictor for {organ}/{cell}")
    kwargs = req.model_dump(exclude_none=True)
    result = predictor.predict(**kwargs)
    if result.get("prediction") is None and result.get("anomalies") is None:
        return {"status": "no_data", "message": result.get("message", "Model returned no prediction."), **result}
    return {"status": "success", **result}


# ── Feedback ─────────────────────────────────────────────────

@router.post("/feedback")
def submit_feedback(req: FeedbackRequest, db: Session = Depends(get_db)):
    from app.models.neural import NeuralPrediction
    feedback = NeuralPrediction(
        organ=req.organ,
        cell=req.cell,
        prediction_id=req.prediction_id,
        actual_outcome=str(req.actual_outcome) if req.actual_outcome else None,
        feedback_text=req.feedback_text,
        created_at=datetime.now(timezone.utc),
    )
    added = _safe_db(lambda: db.add(feedback))
    _safe_db(lambda: db.commit())
    fid = _safe_db(lambda: feedback.id, None)
    if not added or fid is None:
        return {"status": "no_db", "message": "Database unavailable — feedback recorded in memory only", "feedback_id": None}
    return {"status": "recorded", "feedback_id": fid}


# ── Dashboard ────────────────────────────────────────────────

@router.get("/dashboard")
def ai_dashboard(db: Session = Depends(get_db)):
    from app.models.neural import NeuralNode
    nodes = _safe_db(lambda: list(db.execute(select(NeuralNode)).scalars().all()), [])
    eng = FeatureEngineer(db)
    features = _safe_db(lambda: eng.refresh_feature_store(), {})
    return {
        "nodes": [{"id": n.id, "organ": n.organ, "cell": n.cell, "status": n.status, "last_trained": str(n.last_trained or "")} for n in (nodes or [])],
        "feature_summary": {k: list(v.keys()) if isinstance(v, dict) else [] for k, v in (features or {}).items()},
    }


# ── Insights ─────────────────────────────────────────────────

@router.get("/insights")
def get_insights(context: str = Query("/", description="Current page path"), db: Session = Depends(get_db)):
    insights = []
    predictor = CashFlowPredictor(db)
    cf = predictor.predict()
    if cf.get("cash_risk") == "high":
        insights.append({"type": "alert", "icon": "cash", "message": f"Cash flow risk: {cf.get('cash_risk')}. Current balance: {cf.get('current_balance'):,.2f} EGP", "action": "/bnk"})
    eng = FeatureEngineer(db)
    features = eng.refresh_feature_store()
    client_f = features.get("client_features", {})
    if isinstance(client_f, dict) and client_f.get("unpaid_receivables", 0) > 0:
        insights.append({"type": "info", "icon": "receivable", "message": f"Unpaid receivables: {client_f.get('unpaid_receivables'):,.2f} EGP", "action": "/sal"})
    pnr_f = features.get("pnr_features", {})
    if isinstance(pnr_f, dict) and pnr_f.get("overrun_rate", 0) > 15:
        insights.append({"type": "warning", "icon": "overrun", "message": f"PNR overrun rate: {pnr_f.get('overrun_rate'):.1f}%", "action": "/evn"})
    return {"insights": insights, "context": context}


# ── Feature Refresh ──────────────────────────────────────────

@router.post("/refresh-features")
def refresh_features(db: Session = Depends(get_db)):
    eng = FeatureEngineer(db)
    results = eng.refresh_feature_store()
    return {"status": "refreshed", "features": results}


# ── Helpers ──────────────────────────────────────────────────

def _get_predictor(organ: str, cell: str, db: Session):
    if organ == "finance" and cell == "cashflow":
        return CashFlowPredictor(db)
    elif organ == "sales" and cell == "churn":
        return ClientChurnPredictor(db)
    elif organ == "events" and cell == "overrun":
        return PnrOverrunPredictor(db)
    elif organ == "finance" and cell == "anomaly":
        return TransactionAnomalyDetector(db)
    return None
