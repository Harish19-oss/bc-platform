import time
import requests
from app import db
from app.models.gene import Gene
from app.models.protein import Protein
from app.models.pathway import Pathway

REACTOME_BASE = "https://reactome.org/ContentService"

def fetch_pathways_for_uniprot(uniprot_id):
    """Find Reactome pathways associated with a UniProt accession (human)."""
    url = f"{REACTOME_BASE}/data/mapping/UniProt/{uniprot_id}/pathways"
    params = {"species": "9606"}
    resp = requests.get(url, params=params, timeout=15)

    if resp.status_code == 404:
        return []

    resp.raise_for_status()
    return resp.json()

def run_reactome_etl(debug_dump=False):
    """Fetch Reactome pathways for each gene (via its protein's UniProt ID) and save them."""
    genes = Gene.query.all()
    processed, skipped = 0, 0
    dumped_once = False

    for gene in genes:
        protein = Protein.query.filter_by(gene_id=gene.gene_id).first()
        if not protein or not protein.uniprot_id:
            print(f"[SKIP] {gene.symbol}: no linked UniProt ID")
            skipped += 1
            continue

        try:
            pathways = fetch_pathways_for_uniprot(protein.uniprot_id)
        except requests.RequestException as e:
            print(f"[SKIP] {gene.symbol}: request failed ({e})")
            skipped += 1
            continue

        if debug_dump and not dumped_once and pathways:
            import json
            with open("reactome_debug.json", "w") as f:
                json.dump(pathways, f, indent=2)
            print(f"[DEBUG] Wrote raw response for {gene.symbol} to reactome_debug.json")
            dumped_once = True

        saved_count = 0
        for p in pathways:
            external_id = p.get("stId")
            name = p.get("displayName", p.get("name"))
            if not external_id:
                continue

            existing = Pathway.query.filter_by(gene_id=gene.gene_id, source="Reactome", external_id=external_id).first()
            if not existing:
                pw = Pathway(gene_id=gene.gene_id, source="Reactome", external_id=external_id, name=name)
                db.session.add(pw)
                saved_count += 1

        print(f"[OK] {gene.symbol} ({protein.uniprot_id}): {len(pathways)} pathway(s) found, {saved_count} new saved")

        processed += 1
        time.sleep(0.3)

    db.session.commit()
    print(f"\nDone. Processed: {processed}, Skipped: {skipped}")