from app import db

class Mutation(db.Model):
    __tablename__ = "mutation"

    mutation_id = db.Column(db.Integer, primary_key=True)
    gene_id = db.Column(db.Integer, db.ForeignKey("gene.gene_id"), nullable=False, index=True)

    hgvs_c = db.Column(db.String(255))          # coding DNA notation, e.g. c.68_69delAG
    hgvs_p = db.Column(db.String(255))          # protein notation, e.g. p.Glu23fs
    mutation_type = db.Column(db.String(50))    # missense, nonsense, frameshift, etc.
    clinical_significance = db.Column(db.String(100))  # from ClinVar: pathogenic, benign, VUS, etc.
    chromosome = db.Column(db.String(10))
    position = db.Column(db.BigInteger)
    ref_allele = db.Column(db.String(50))
    alt_allele = db.Column(db.String(50))
    clinvar_id = db.Column(db.String(30))
    cosmic_id = db.Column(db.String(30))
    source = db.Column(db.String(50))           # ClinVar / COSMIC / manual

    def __repr__(self):
        return f"<Mutation {self.hgvs_p or self.hgvs_c}>"      