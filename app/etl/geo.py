import time
import requests
from app import db
from app.models.gene import Gene
from app.models.subtype import Subtype

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Curated breast cancer GEO datasets
BC_GEO_SERIES = ["GSE2034", "GSE7390", "GSE11121", "GSE20685"]

def search_geo_series(series_id):
    """Search for a GEO series and return its UID."""
    url = f"{NCBI_BASE}/esearch.fcgi"
    params = {
        "db": "gds",
        "term": f"{series_id}[Accession]",
        "retmode": "json"
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    ids = resp.json().get("esearchresult", {}).get("idlist", [])
    return ids[0] if ids else None

def fetch_geo_summary(uid):
    """Fetch summary metadata for a GEO series UID."""
    url = f"{NCBI_BASE}/esummary.fcgi"
    params = {"db": "gds", "id": uid, "retmode": "json"}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    result = resp.json().get("result", {})
    return result.get(uid, {})

def run_geo_etl():
    """Fetch GEO breast cancer series metadata and link to subtypes."""
    genes = Gene.query.all()
    gene_map = {g.symbol.upper(): g for g in genes}

    for series_id in BC_GEO_SERIES:
        print(f"\n[GEO] Fetching {series_id}...")
        uid = search_geo_series(series_id)
        if not uid:
            print(f"  [SKIP] No UID found for {series_id}")
            time.sleep(0.5)
            continue

        summary = fetch_geo_summary(uid)
        title = summary.get("title", "")
        samples = summary.get("n_samples", "N/A")
        organism = summary.get("taxon", "")
        print(f"  Title: {title}")
        print(f"  Samples: {samples}, Organism: {organism}")

        # Map to known BC subtypes and link to genes
        subtype_keywords = {
            "Luminal A": ["luminal a", "luminal-a", "er+", "er positive"],
            "Luminal B": ["luminal b", "luminal-b", "her2+"],
            "HER2-enriched": ["her2", "erbb2"],
            "Basal-like": ["basal", "tnbc", "triple negative"],
        }

        title_lower = title.lower()
        matched_subtype = None
        for subtype_name, keywords in subtype_keywords.items():
            if any(kw in title_lower for kw in keywords):
                matched_subtype = subtype_name
                break

        for gene in genes:
            existing = Subtype.query.filter_by(
                gene_id=gene.gene_id,
                subtype_name=matched_subtype or "General BC",
                source=series_id
            ).first()

            if not existing:
                st = Subtype(
                    gene_id=gene.gene_id,
                    subtype_name=matched_subtype or "General BC",
                    source=series_id,
                    n_samples=int(samples) if str(samples).isdigit() else None,
                    notes=title[:200] if title else None
                )
                db.session.add(st)

        time.sleep(0.5)

    db.session.commit()
    print(f"\n[GEO] Done. Total subtype records: {Subtype.query.count()}")