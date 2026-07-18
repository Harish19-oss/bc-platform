import time
import requests
from app import db
from app.models.gene import Gene
from app.models.protein import Protein

UNIPROT_BASE = "https://rest.uniprot.org/uniprotkb/search"

def fetch_uniprot_entry(gene_symbol):
    """Find the reviewed (Swiss-Prot) human UniProt entry for a gene symbol."""
    params = {
        "query": f"gene:{gene_symbol} AND organism_id:9606 AND reviewed:true",
        "fields": "accession,protein_name,length,cc_function",
        "format": "json",
        "size": 1
    }
    resp = requests.get(UNIPROT_BASE, params=params, timeout=15)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    return results[0] if results else None

def extract_function_summary(entry):
    """Pull the FUNCTION comment text, if present."""
    for comment in entry.get("comments", []):
        if comment.get("commentType") == "FUNCTION":
            texts = comment.get("texts", [])
            if texts:
                return texts[0].get("value", "")
    return None

def run_uniprot_etl():
    """Populate the protein table for every gene already in the DB."""
    genes = Gene.query.all()
    created, updated, skipped = 0, 0, 0

    for gene in genes:
        entry = fetch_uniprot_entry(gene.symbol)
        if not entry:
            print(f"[SKIP] {gene.symbol}: not found on UniProt")
            skipped += 1
            continue

        accession = entry.get("primaryAccession")
        protein_desc = entry.get("proteinDescription", {})
        full_name = (
            protein_desc.get("recommendedName", {})
            .get("fullName", {})
            .get("value", "")
        )
        length = entry.get("sequence", {}).get("length")
        function_summary = extract_function_summary(entry)

        existing = Protein.query.filter_by(uniprot_id=accession).first()

        if existing:
            existing.name = full_name
            existing.sequence_length = length
            existing.function_summary = function_summary
            existing.gene_id = gene.gene_id
            updated += 1
        else:
            protein = Protein(
                uniprot_id=accession,
                name=full_name,
                sequence_length=length,
                function_summary=function_summary,
                gene_id=gene.gene_id
            )
            db.session.add(protein)
            created += 1

        print(f"[OK] {gene.symbol} -> UniProt {accession} ({length} aa)")
        time.sleep(0.4)

    db.session.commit()
    print(f"\nDone. Created: {created}, Updated: {updated}, Skipped: {skipped}")