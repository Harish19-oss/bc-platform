from app import db

class Drug(db.Model):
    __tablename__ = "drug"

    drug_id         = db.Column(db.Integer, primary_key=True)
    gene_id         = db.Column(db.Integer, db.ForeignKey("gene.gene_id"), nullable=False)
    drug_name       = db.Column(db.String(200), nullable=False)
    interaction_type = db.Column(db.String(100))
    source          = db.Column(db.String(50), default="DGIdb")
    approved        = db.Column(db.Boolean, default=False)

    gene = db.relationship("Gene", backref="drugs")