import time
import requests
from app import db
from app.models.gene import Gene
from app.models.tcga_stats import TcgaStats

GDC_API_BASE = "https://api.gdc.cancer.gov"

def fetch_gene_mutation_frequency(gene_symbol):
    """
    Query GDC for the number of TCGA-BRCA cases with a simple somatic mutation
    in the given gene, plus total cases in the cohort, to compute frequency.
    """
    # Total cases in the TCGA-BRCA cohort
    total_filters = {
        "op": "and",
        "content": [
            {"op": "in", "content": {"field": "cases.project.project_id", "value": ["TCGA-BRCA"]}}
        ]
    }
    total_params = {
        "filters": str(total_filters).replace("'", '"'),
        "size": "0"
    }
    total_resp = requests.get(f"{GDC_API_BASE}/cases", params=total_params, timeout=20)
    total_resp.raise_for_status()
    total_cases = total_resp.json().get("data", {}).get("pagination", {}).get("total", 0)

    # Cases with a mutation in this gene, within TCGA-BRCA
    mutation_filters = {
        "op": "and",
        "content": [
            {"op": "in", "content": {"field": "cases.project.project_id", "value": ["TCGA-BRCA"]}},
            {"op": "in", "content": {"field": "genes.symbol", "value": [gene_symbol]}}
        ]
    }
    mutation_params = {
        "filters": str(mutation_filters).replace("'", '"'),
        "size": "0"
    }
    mut_resp = requests.get(f"{GDC_API_BASE}/ssm_occurrences", params=mutation_params, timeout=20)
    mut_resp.raise_for_status()
    mutated_cases = mut_resp.json().get("data", {}).get("pagination", {}).get("total", 0)

    return mutated_cases, total_cases

def run_tcga_gdc_etl():
    """Fetch TCGA-BRCA mutation frequency for every gene in the DB and store it on the Gene record."""
    genes = Gene.query.all()
    updated, skipped = 0, 0

    for gene in genes:
        try:
            mutated_cases, total_cases = fetch_gene_mutation_frequency(gene.symbol)
        except requests.RequestException as e:
            print(f"[SKIP] {gene.symbol}: request failed ({e})")
            skipped += 1
            continue

        if total_cases == 0:
            print(f"[SKIP] {gene.symbol}: no TCGA-BRCA case data returned")
            skipped += 1
            continue

        frequency_pct = round((mutated_cases / total_cases) * 100, 2)
        print(f"[OK] {gene.symbol}: {mutated_cases}/{total_cases} TCGA-BRCA cases mutated ({frequency_pct}%)")

        existing = TcgaStats.query.filter_by(gene_id=gene.gene_id, project_id="TCGA-BRCA").first()
        if existing:
            existing.mutated_cases = mutated_cases
            existing.total_cases = total_cases
            existing.frequency_pct = frequency_pct
        else:
            stat = TcgaStats(
                gene_id=gene.gene_id,
                project_id="TCGA-BRCA",
                mutated_cases=mutated_cases,
                total_cases=total_cases,
                frequency_pct=frequency_pct
            )
            db.session.add(stat)

        updated += 1
        time.sleep(0.3)

    db.session.commit()
    print(f"\nDone. Processed: {updated}, Skipped: {skipped}")