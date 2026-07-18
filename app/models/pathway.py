from app import db

class Pathway(db.Model):
    __tablename__ = "pathway"

    pathway_id = db.Column(db.Integer, primary_key=True)
    gene_id = db.Column(db.Integer, db.ForeignKey("gene.gene_id"), nullable=False, index=True)

    source = db.Column(db.String(20))          # "Reactome" or "KEGG"
    external_id = db.Column(db.String(50))      # e.g. R-HSA-1234 or hsa04151
    name = db.Column(db.String(255))

    gene = db.relationship("Gene", backref="pathways")

    def __repr__(self):
        return f"<Pathway {self.source}:{self.external_id} gene={self.gene_id}>"