import time
import json
import requests
from app import db
from app.models.gene import Gene
from app.models.mutation import Mutation

COSMIC_SEARCH_URL = "https://clinicaltables.nlm.nih.gov/api/cosmic/v4/search"

def fetch_cosmic_entries(gene_symbol, max_results=20):
    """Query the NLM Clinical Table Search Service for COSMIC entries matching a gene symbol."""
    params = {
        "terms": gene_symbol,
        "maxList": max_results
    }
    resp = requests.get(COSMIC_SEARCH_URL, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()

def run_cosmic_etl(debug_dump=True):
    """Populate/supplement the mutation table with COSMIC entries for every gene in the DB."""
    genes = Gene.query.all()
    created, updated, skipped = 0, 0, 0
    dumped_once = False

    for gene in genes:
        data = fetch_cosmic_entries(gene.symbol)

        if debug_dump and not dumped_once:
            with open("cosmic_debug.json", "w") as f:
                json.dump(data, f, indent=2)
            print(f"[DEBUG] Wrote raw response for {gene.symbol} to cosmic_debug.json")
            dumped_once = True

        # data format from this API is: [total_count, codes_list, extra_data_dict, display_strings_list]
        total_count = data[0] if len(data) > 0 else 0
        codes = data[1] if len(data) > 1 else []
        display_strings = data[3] if len(data) > 3 else []

        if not codes:
            print(f"[SKIP] {gene.symbol}: no COSMIC entries found")
            skipped += 1
            time.sleep(0.3)
            continue

        gene_created = 0
        for code, display in zip(codes, display_strings):
            existing = Mutation.query.filter_by(cosmic_id=code).first()
            display_text = display[0] if isinstance(display, list) and display else str(display)

            if existing:
                updated += 1
            else:
                mutation = Mutation(
                    gene_id=gene.gene_id,
                    hgvs_c=None,
                    hgvs_p=None,
                    mutation_type=None,
                    clinical_significance=None,
                    cosmic_id=code,
                    source="COSMIC"
                )
                db.session.add(mutation)
                created += 1
                gene_created += 1

        print(f"[OK] {gene.symbol}: {gene_created} new COSMIC entr{'y' if gene_created==1 else 'ies'} (total available: {total_count})")
        time.sleep(0.3)

    db.session.commit()
    print(f"\nDone. Created: {created}, Updated: {updated}, Skipped: {skipped}")