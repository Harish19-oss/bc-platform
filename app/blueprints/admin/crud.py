from flask import render_template, request, redirect, url_for, flash, abort
from flask_login import login_required
from sqlalchemy import inspect as sa_inspect, or_
from . import admin_bp
from app import db

from app.models.gene import Gene
from app.models.protein import Protein
from app.models.mutation import Mutation
from app.models.drug import Drug
from app.models.pathway import Pathway
from app.models.publication import Publication
from app.models.subtype import Subtype

MODEL_REGISTRY = {
    "genes": {"model": Gene, "label": "Genes"},
    "proteins": {"model": Protein, "label": "Proteins"},
    "mutations": {"model": Mutation, "label": "Mutations"},
    "drugs": {"model": Drug, "label": "Drugs"},
    "pathways": {"model": Pathway, "label": "Pathways"},
    "publications": {"model": Publication, "label": "Publications"},
    "subtypes": {"model": Subtype, "label": "GEO Records"},
}


def get_model_or_404(name):
    entry = MODEL_REGISTRY.get(name)
    if not entry:
        abort(404)
    return entry["model"], entry["label"]


def get_pk_name(model):
    mapper = sa_inspect(model)
    pk_cols = mapper.primary_key
    return pk_cols[0].name if pk_cols else "id"


def get_columns(model):
    mapper = sa_inspect(model)
    cols = []
    for col in mapper.columns:
        cols.append({
            "name": col.name,
            "type": str(col.type),
            "primary_key": col.primary_key,
        })
    return cols


@admin_bp.route("/table/<name>")
@login_required
def table_list(name):
    model, label = get_model_or_404(name)
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    columns = get_columns(model)
    pk_name = get_pk_name(model)

    query = model.query
    searchable_cols = [
        c["name"] for c in columns
        if any(t in c["type"].upper() for t in ("VARCHAR", "TEXT", "STRING"))
    ]
    if q and searchable_cols:
        filters = [getattr(model, c).ilike(f"%{q}%") for c in searchable_cols]
        query = query.filter(or_(*filters))

    pagination = query.paginate(page=page, per_page=25, error_out=False)

    return render_template(
        "admin/table_list.html",
        model_name=name, label=label, columns=columns, pk_name=pk_name,
        rows=pagination.items, pagination=pagination, q=q,
    )


@admin_bp.route("/table/<name>/add", methods=["GET", "POST"])
@login_required
def table_add(name):
    model, label = get_model_or_404(name)
    columns = [c for c in get_columns(model) if not c["primary_key"]]

    if request.method == "POST":
        obj = model()
        for c in columns:
            val = request.form.get(c["name"], "")
            setattr(obj, c["name"], val if val != "" else None)
        db.session.add(obj)
        db.session.commit()
        flash(f"{label} record added.", "success")
        return redirect(url_for("admin.table_list", name=name))

    return render_template(
        "admin/table_form.html",
        model_name=name, label=label, columns=columns, row=None, action="Add",
    )


@admin_bp.route("/table/<name>/edit/<int:row_id>", methods=["GET", "POST"])
@login_required
def table_edit(name, row_id):
    model, label = get_model_or_404(name)
    columns = get_columns(model)
    row = model.query.get_or_404(row_id)

    if request.method == "POST":
        for c in columns:
            if c["primary_key"]:
                continue
            val = request.form.get(c["name"], "")
            setattr(row, c["name"], val if val != "" else None)
        db.session.commit()
        flash(f"{label} record updated.", "success")
        return redirect(url_for("admin.table_list", name=name))

    return render_template(
        "admin/table_form.html",
        model_name=name, label=label, columns=columns, row=row, action="Edit",
    )


@admin_bp.route("/table/<name>/delete/<int:row_id>", methods=["POST"])
@login_required
def table_delete(name, row_id):
    model, label = get_model_or_404(name)
    row = model.query.get_or_404(row_id)
    db.session.delete(row)
    db.session.commit()
    flash(f"Deleted from {label}.", "success")
    return redirect(url_for("admin.table_list", name=name))