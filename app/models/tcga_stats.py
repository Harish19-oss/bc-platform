from app import db

class TcgaStats(db.Model):
    __tablename__ = "tcga_stats"

    stat_id = db.Column(db.Integer, primary_key=True)
    gene_id = db.Column(db.Integer, db.ForeignKey("gene.gene_id"), nullable=False, index=True)

    project_id = db.Column(db.String(50), default="TCGA-BRCA")  # cohort identifier
    mutated_cases = db.Column(db.Integer)
    total_cases = db.Column(db.Integer)
    frequency_pct = db.Column(db.Float)

    gene = db.relationship("Gene", backref="tcga_stats")

    def __repr__(self):
        return f"<TcgaStats {self.project_id} gene={self.gene_id} {self.frequency_pct}%>"