from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.meta.form_registry import get_form_def, list_forms
from app.meta.base_form import MetaForm

router = APIRouter(prefix="/api/meta", tags=["meta"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/forms")
def meta_list_forms():
    return {"forms": list_forms()}


@router.get("/forms/{form_name}")
def meta_get_form(form_name: str):
    defn = get_form_def(form_name)
    if not defn:
        raise HTTPException(status_code=404, detail="Form not found")
    return {"form": form_name, "definition": defn}


@router.get("/forms/{form_name}/render", response_class=HTMLResponse)
def meta_render_form(request: Request, form_name: str):
    try:
        mf = MetaForm(form_name)
    except ValueError:
        raise HTTPException(status_code=404, detail="Form not found")
    ctx = mf.render_context()
    ctx["request"] = request
    return templates.TemplateResponse("meta/meta_form.html", ctx)
