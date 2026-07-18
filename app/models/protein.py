from app import db

class Protein(db.Model):
    __tablename__ = "protein"

    protein_id = db.Column(db.Integer, primary_key=True)
    gene_id = db.Column(db.Integer, db.ForeignKey("gene.gene_id"), nullable=False)
    uniprot_id = db.Column(db.String(20), unique=True, index=True)
    name = db.Column(db.String(255))
    sequence_length = db.Column(db.Integer)
    function_summary = db.Column(db.Text)

    def __repr__(self):
        return f"<Protein {self.uniprot_id}>"