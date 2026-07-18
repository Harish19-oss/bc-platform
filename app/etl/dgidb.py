import time
import requests
from app import db
from app.models.gene import Gene
from app.models.drug import Drug

DGIDB_GRAPHQL = "https://dgidb.org/api/graphql"

def fetch_drug_interactions(gene_symbol):
    """Fetch drug-gene interactions via DGIdb GraphQL API."""
    query = """
    {
      genes(names: ["%s"]) {
        nodes {
          name
          interactions {
            drug {
              name
              approved
            }
            interactionTypes {
              type
            }
          }
        }
      }
    }
    """ % gene_symbol

    try:
        resp = requests.post(
            DGIDB_GRAPHQL,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        resp.raise_for_status()
        data = resp.json()
        nodes = data.get("data", {}).get("genes", {}).get("nodes", [])
        if not nodes:
            return []
        return nodes[0].get("interactions", [])
    except requests.RequestException as e:
        print(f"  [ERROR] {gene_symbol}: {e}")
        return []

def run_dgidb_etl():
    """Fetch drug interactions for all genes and save to drug table."""
    genes = Gene.query.all()
    total_saved = 0

    for gene in genes:
        print(f"\n[DGIdb] {gene.symbol}...")
        interactions = fetch_drug_interactions(gene.symbol)

        if not interactions:
            print(f"  [SKIP] No interactions found")
            time.sleep(0.3)
            continue

        saved = 0
        for item in interactions[:10]:
            drug_info = item.get("drug", {})
            drug_name = drug_info.get("name", "").strip()
            approved = drug_info.get("approved", False)
            types = item.get("interactionTypes", [])
            interaction_type = types[0].get("type", "") if types else ""

            if not drug_name:
                continue

            existing = Drug.query.filter_by(
                gene_id=gene.gene_id,
                drug_name=drug_name
            ).first()

            if not existing:
                drug = Drug(
                    gene_id=gene.gene_id,
                    drug_name=drug_name,
                    interaction_type=interaction_type,
                    source="DGIdb",
                    approved=approved
                )
                db.session.add(drug)
                saved += 1

        print(f"  Saved {saved} drugs (of {len(interactions)} found)")
        total_saved += saved
        time.sleep(0.3)

    db.session.commit()
    print(f"\n[DGIdb] Done. Total drug records: {Drug.query.count()}")