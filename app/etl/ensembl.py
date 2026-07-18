import time
import requests
from app import db
from app.models.gene import Gene

ENSEMBL_REST_BASE = "https://rest.ensembl.org"

def fetch_with_retry(url, headers, params=None, timeout=30, retries=3):
    """GET with retry on timeout."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.Timeout:
            print(f"  [TIMEOUT] attempt {attempt+1}/{retries}, retrying...")
            time.sleep(3)
        except requests.exceptions.RequestException as e:
            print(f"  [ERROR] {e}")
            return None
    return None

def fetch_ensembl_id(gene_symbol):
    url = f"{ENSEMBL_REST_BASE}/xrefs/symbol/homo_sapiens/{gene_symbol}"
    headers = {"Content-Type": "application/json"}
    results = fetch_with_retry(url, headers)
    if not results:
        return None
    for entry in results:
        if entry.get("type") == "gene":
            return entry.get("id")
    return None

def fetch_ensembl_details(ensembl_gene_id):
    url = f"{ENSEMBL_REST_BASE}/lookup/id/{ensembl_gene_id}"
    headers = {"Content-Type": "application/json"}
    return fetch_with_retry(url, headers, params={"expand": "1"})

def run_ensembl_etl():
    genes = Gene.query.all()
    updated, skipped = 0, 0

    for gene in genes:
        # Skip genes already processed
        if gene.ensembl_id:
            print(f"[SKIP] {gene.symbol}: already has {gene.ensembl_id}")
            skipped += 1
            continue

        ensembl_id = fetch_ensembl_id(gene.symbol)
        if not ensembl_id:
            print(f"[SKIP] {gene.symbol}: no Ensembl ID found")
            skipped += 1
            time.sleep(0.5)
            continue

        gene.ensembl_id = ensembl_id

        details = fetch_ensembl_details(ensembl_id)
        if details:
            transcript_count = len(details.get("Transcript", []))
            print(f"[OK] {gene.symbol} -> {ensembl_id} ({transcript_count} transcripts)")
        else:
            print(f"[OK] {gene.symbol} -> {ensembl_id} (details unavailable)")

        updated += 1
        time.sleep(0.5)

    db.session.commit()
    print(f"\nDone. Updated: {updated}, Skipped: {skipped}")