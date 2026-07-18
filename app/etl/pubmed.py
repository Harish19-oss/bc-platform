import time
import requests
from app import db
from app.models.gene import Gene
from app.models.publication import Publication

NCBI_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def search_pubmed(gene_symbol, max_results=5):
    """Search PubMed for breast cancer papers mentioning this gene."""
    url = f"{NCBI_BASE}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": f"{gene_symbol}[Gene Name] AND breast cancer[MeSH Terms]",
        "retmax": max_results,
        "retmode": "json",
        "sort": "relevance"
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("esearchresult", {}).get("idlist", [])

def fetch_pubmed_details(pmids):
    """Fetch title, authors, journal, year for a list of PMIDs."""
    url = f"{NCBI_BASE}/esummary.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json"
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    result = resp.json().get("result", {})
    return [result[pmid] for pmid in pmids if pmid in result]

def run_pubmed_etl():
    """Fetch top 5 breast cancer PubMed papers per gene."""
    genes = Gene.query.all()
    total_saved = 0

    for gene in genes:
        print(f"\n[PubMed] {gene.symbol}...")
        pmids = search_pubmed(gene.symbol, max_results=5)

        if not pmids:
            print(f"  [SKIP] No results")
            time.sleep(0.4)
            continue

        details = fetch_pubmed_details(pmids)
        saved = 0

        for paper in details:
            pmid = paper.get("uid", "")
            title = paper.get("title", "")[:500]
            journal = paper.get("fulljournalname", "")[:200]
            pub_year = paper.get("pubdate", "")[:4]
            authors_list = paper.get("authors", [])
            authors = ", ".join(
                a.get("name", "") for a in authors_list[:3]
            ) + (" et al." if len(authors_list) > 3 else "")

            existing = Publication.query.filter_by(
                gene_id=gene.gene_id, pmid=pmid
            ).first()

            if not existing:
                pub = Publication(
                    gene_id=gene.gene_id,
                    pmid=pmid,
                    title=title,
                    authors=authors,
                    journal=journal,
                    pub_year=int(pub_year) if pub_year.isdigit() else None
                )
                db.session.add(pub)
                saved += 1

        print(f"  Saved {saved} papers")
        total_saved += saved
        time.sleep(0.4)

    db.session.commit()
    print(f"\n[PubMed] Done. Total publications: {Publication.query.count()}")