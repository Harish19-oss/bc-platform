from flask import render_template, request, jsonify
from . import genes_bp
from app.models.gene import Gene
from app import db

@genes_bp.route("/")
def gene_list():
    query  = request.args.get("q", "").strip()
    chrom  = request.args.get("chrom", "").strip()
    sort   = request.args.get("sort", "symbol")
    page   = request.args.get("page", 1, type=int)

    q = Gene.query

    if query:
        q = q.filter(
            db.or_(
                Gene.symbol.ilike(f"%{query}%"),
                Gene.name.ilike(f"%{query}%")
            )
        )
    if chrom:
        q = q.filter(Gene.chromosome == chrom)

    if sort == "name":
        q = q.order_by(Gene.name)
    elif sort == "chromosome":
        q = q.order_by(Gene.chromosome)
    else:
        q = q.order_by(Gene.symbol)

    pagination = q.paginate(page=page, per_page=20, error_out=False)

    chromosomes = sorted(set(
        g.chromosome for g in Gene.query.all() if g.chromosome
    ))

    return render_template(
        "genes/list.html",
        genes=pagination.items,
        pagination=pagination,
        query=query,
        chrom_filter=chrom,
        sort=sort,
        chromosomes=chromosomes
    )

@genes_bp.route("/<int:gene_id>")
def gene_detail(gene_id):
    gene = Gene.query.get_or_404(gene_id)
    return render_template("genes/detail.html", gene=gene)

@genes_bp.route("/api/search")
def gene_search_api():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])

    genes = Gene.query.filter(
        Gene.symbol.ilike(f"%{query}%")
    ).limit(10).all()

    return jsonify([
        {"gene_id": g.gene_id, "symbol": g.symbol, "name": g.name}
        for g in genes
    ])