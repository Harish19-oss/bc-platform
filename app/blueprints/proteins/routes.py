from flask import render_template, request, jsonify
from . import proteins_bp
from app.models.protein import Protein

@proteins_bp.route("/")
def protein_list():
    query = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    proteins_query = Protein.query
    if query:
        proteins_query = proteins_query.filter(
            Protein.uniprot_id.ilike(f"%{query}%") | Protein.name.ilike(f"%{query}%")
        )

    pagination = proteins_query.order_by(Protein.uniprot_id).paginate(
        page=page, per_page=20, error_out=False
    )

    return render_template(
        "proteins/list.html",
        proteins=pagination.items,
        pagination=pagination,
        query=query
    )

@proteins_bp.route("/<int:protein_id>")
def protein_detail(protein_id):
    protein = Protein.query.get_or_404(protein_id)
    return render_template("proteins/detail.html", protein=protein)

@proteins_bp.route("/api/search")
def protein_search_api():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])

    proteins = Protein.query.filter(
        Protein.uniprot_id.ilike(f"%{query}%") | Protein.name.ilike(f"%{query}%")
    ).limit(10).all()

    return jsonify([
        {"protein_id": p.protein_id, "uniprot_id": p.uniprot_id, "name": p.name}
        for p in proteins
    ])