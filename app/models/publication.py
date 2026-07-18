from app import db

class Publication(db.Model):
    __tablename__ = "publication"

    pub_id   = db.Column(db.Integer, primary_key=True)
    gene_id  = db.Column(db.Integer, db.ForeignKey("gene.gene_id"), nullable=False)
    pmid     = db.Column(db.String(20), nullable=False)
    title    = db.Column(db.Text)
    authors  = db.Column(db.String(500))
    journal  = db.Column(db.String(200))
    pub_year = db.Column(db.Integer)

    gene = db.relationship("Gene", backref="publications")