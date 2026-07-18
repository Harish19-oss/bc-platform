from app import db

class Gene(db.Model):
    __tablename__ = "gene"

    gene_id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255))
    chromosome = db.Column(db.String(10))
    start_position = db.Column(db.BigInteger)
    end_position = db.Column(db.BigInteger)
    strand = db.Column(db.String(1))
    subtype_tags = db.Column(db.ARRAY(db.String))
    ncbi_gene_id = db.Column(db.String(20))
    ensembl_id = db.Column(db.String(30))

    proteins = db.relationship("Protein", backref="gene", lazy=True)
    mutations = db.relationship("Mutation", backref="gene", lazy=True)

    def __repr__(self):
        return f"<Gene {self.symbol}>"