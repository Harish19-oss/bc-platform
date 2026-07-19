from flask import render_template, request, jsonify
from . import genes_bp
from app.models.gene import Gene
from app import db

@genes_bp.route("/")
def gene_list():
    print("Total genes:", Gene.query.count(), flush=True)

    genes = Gene.query.all()
    print("Genes:", genes, flush=True)

    return render_template(
        "genes/list.html",
        genes=genes,
        pagination=None,
        query="",
        chrom_filter="",
        sort="symbol",
        chromosomes=[]
    )