import time
import requests
from app import db
from app.models.gene import Gene
from app.models.pathway import Pathway

KEGG_BASE = "https://rest.kegg.jp"

def fetch_kegg_gene_id(gene_symbol):
    """Look up the KEGG gene ID (hsa:####) for a human gene symbol."""
    url = f"{KEGG_BASE}/find/genes/{gene_symbol}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    for line in resp.text.strip().split("\n"):
        if not line:
            continue
        kegg_id, description = line.split("\t", 1)
        # Only accept human entries (hsa:) and reasonably exact symbol matches
        if kegg_id.startswith("hsa:") and gene_symbol.upper() in description.upper().split(",")[0]:
            return kegg_id
    return None

def fetch_kegg_pathways(kegg_gene_id):
    """Fetch pathway IDs/names linked to a KEGG gene ID."""
    url = f"{KEGG_BASE}/link/pathway/{kegg_gene_id}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    pathway_ids = []
    for line in resp.text.strip().split("\n"):
        if not line:
            continue
        _, pathway_id = line.split("\t")
        pathway_ids.append(pathway_id)
    return pathway_ids

def fetch_pathway_name(pathway_id):
    """Fetch the human-readable name for a KEGG pathway ID."""
    url = f"{KEGG_BASE}/get/{pathway_id}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()

    for line in resp.text.split("\n"):
        if line.startswith("NAME"):
            return line.replace("NAME", "").strip()
    return pathway_id

def run_kegg_etl():
    """Fetch KEGG pathway names for each gene and save them."""
    genes = Gene.query.all()
    processed, skipped = 0, 0

    for gene in genes:
        kegg_id = fetch_kegg_gene_id(gene.symbol)
        if not kegg_id:
            print(f"[SKIP] {gene.symbol}: no KEGG gene ID found")
            skipped += 1
            time.sleep(0.3)
            continue

        pathway_ids = fetch_kegg_pathways(kegg_id)
        if not pathway_ids:
            print(f"[OK] {gene.symbol} ({kegg_id}): 0 pathways")
            processed += 1
            time.sleep(0.3)
            continue

        # Fetch names for up to 5 pathways to keep this run quick
        pathway_names = []
        for pid in pathway_ids[:5]:
            pathway_names.append(fetch_pathway_name(pid))
            time.sleep(0.2)

        saved_count = 0
        for pid, name in zip(pathway_ids[:5], pathway_names):
            existing = Pathway.query.filter_by(gene_id=gene.gene_id, source="KEGG", external_id=pid).first()
            if not existing:
                pw = Pathway(gene_id=gene.gene_id, source="KEGG", external_id=pid, name=name)
                db.session.add(pw)
                saved_count += 1

        print(f"[OK] {gene.symbol} ({kegg_id}): {len(pathway_ids)} pathway(s) found, {saved_count} new saved (top 5 fetched)")
        processed += 1
        time.sleep(0.3)

    db.session.commit()
    print(f"\nDone. Processed: {processed}, Skipped: {skipped}")