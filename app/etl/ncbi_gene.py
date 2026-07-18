import time
import requests
from app import db
from app.models.gene import Gene

NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Curated starter list of well-known breast-cancer-relevant genes.
# Expand this list later or replace with a file/DB-driven list.
BC_GENE_SYMBOLS = [
    # Original 15
    "BRCA1", "BRCA2", "TP53", "PIK3CA", "ERBB2",
    "ESR1", "PTEN", "CDH1", "ATM", "PALB2",
    "CHEK2", "RB1", "MYC", "CCND1", "AKT1",
    # New 35
    "GATA3", "MAP3K1", "MAP2K4", "TBX3", "RUNX1",
    "SF3B1", "CBFB", "PIK3R1", "ARID1A", "NCOR1",
    "AKT2", "AKT3", "MTOR", "EGFR", "FGFR1",
    "FGFR2", "IGF1R", "VEGFA", "MDM2", "BCL2",
    "BAX", "CCNE1", "CDK4", "CDK6", "CDKN2A",
    "BRIP1", "RAD51", "RAD51C", "RAD51D", "NBN",
    "MLH1", "MSH2", "MSH6", "PMS2", "STK11"
]

def fetch_gene_id(symbol):
    """Look up the NCBI Gene ID for a gene symbol (human)."""
    params = {
        "db": "gene",
        "term": f"{symbol}[sym] AND Homo sapiens[orgn]",
        "retmode": "json"
    }
    resp = requests.get(f"{NCBI_EUTILS_BASE}/esearch.fcgi", params=params, timeout=15)
    resp.raise_for_status()
    ids = resp.json().get("esearchresult", {}).get("idlist", [])
    return ids[0] if ids else None

def fetch_gene_summary(gene_id):
    """Fetch gene details (name, location) for a given NCBI Gene ID."""
    params = {"db": "gene", "id": gene_id, "retmode": "json"}
    resp = requests.get(f"{NCBI_EUTILS_BASE}/esummary.fcgi", params=params, timeout=15)
    resp.raise_for_status()
    result = resp.json().get("result", {})
    return result.get(gene_id)

def run_ncbi_gene_etl():
    """Populate the gene table from NCBI for the curated BC gene list."""
    created, updated, skipped = 0, 0, 0

    for symbol in BC_GENE_SYMBOLS:
        existing = Gene.query.filter_by(symbol=symbol).first()

        gene_id = fetch_gene_id(symbol)
        if not gene_id:
            print(f"[SKIP] {symbol}: not found on NCBI")
            skipped += 1
            continue

        summary = fetch_gene_summary(gene_id)
        if not summary:
            print(f"[SKIP] {symbol}: no summary data")
            skipped += 1
            continue

        chrom = summary.get("chromosome", "")
        name = summary.get("description", "")

        genomic_info = summary.get("genomicinfo", [])
        strand = None
        if genomic_info:
            raw_start = genomic_info[0].get("chrstart")
            raw_stop = genomic_info[0].get("chrstop")
            if raw_start is not None and raw_stop is not None:
                if raw_start > raw_stop:
                    start_pos, end_pos = raw_stop, raw_start
                    strand = "-"
                else:
                    start_pos, end_pos = raw_start, raw_stop
                    strand = "+"
            else:
                start_pos = end_pos = None
        else:
            start_pos = end_pos = None

        if existing:
            existing.name = name
            existing.chromosome = chrom
            existing.start_position = start_pos
            existing.end_position = end_pos
            existing.strand = strand
            existing.ncbi_gene_id = gene_id
            updated += 1
        else:
            gene = Gene(
                symbol=symbol,
                name=name,
                chromosome=chrom,
                start_position=start_pos,
                end_position=end_pos,
                strand=strand,
                ncbi_gene_id=gene_id
            )
            db.session.add(gene)
            created += 1

        print(f"[OK] {symbol} -> NCBI Gene ID {gene_id}")
        time.sleep(0.4)  # be polite to NCBI's rate limits (max ~3 req/sec without an API key)

    db.session.commit()
    print(f"\nDone. Created: {created}, Updated: {updated}, Skipped: {skipped}")