from flask import render_template, request, redirect, url_for
from . import main_bp
from app.models.gene import Gene
from app.models.pathway import Pathway

@main_bp.route('/')
def index():
    stats = {
        "genes": Gene.query.count(),
        "pathways": Pathway.query.count(),
        "drugs": 0,        # placeholder until a Drug model/ETL exists
        "publications": 0  # placeholder until PubMed ETL is built
    }
    return render_template('main/index.html', stats=stats)


@main_bp.route('/search')
def search():
    query = request.args.get('q', '').strip()
    if not query:
        return redirect(url_for('main.index'))

    # Exact symbol match (case-insensitive) -> go straight to that gene's page
    exact = Gene.query.filter(Gene.symbol.ilike(query)).first()
    if exact:
        return redirect(url_for('genes.gene_detail', gene_id=exact.gene_id))

    # Otherwise, fall back to the full search/results list
    return redirect(url_for('genes.gene_list', q=query))