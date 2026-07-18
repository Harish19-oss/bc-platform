from app import db

class Subtype(db.Model):
    __tablename__ = "subtype"

    subtype_id   = db.Column(db.Integer, primary_key=True)
    gene_id      = db.Column(db.Integer, db.ForeignKey("gene.gene_id"), nullable=False)
    subtype_name = db.Column(db.String(100), nullable=False)  # Luminal A, Basal-like, etc.
    source       = db.Column(db.String(50))                   # GSE2034, GSE7390, etc.
    n_samples    = db.Column(db.Integer)
    notes        = db.Column(db.Text)

    gene = db.relationship("Gene", backref="subtypes")