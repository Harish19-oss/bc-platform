import time
import requests
import xml.etree.ElementTree as ET
from app import db
from app.models.gene import Gene
from app.models.mutation import Mutation

NCBI_EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Cap per gene to keep runtime sane while we're still on a small gene list.
# Raise this once we scale up and want deeper coverage.
MAX_VARIANTS_PER_GENE = 20

def fetch_variant_ids(gene_symbol):
    """Search ClinVar for variant IDs associated with a gene symbol."""
    params = {
        "db": "clinvar",
        "term": f"{gene_symbol}[gene]",
        "retmode": "json",
        "retmax": MAX_VARIANTS_PER_GENE
    }
    resp = requests.get(f"{NCBI_EUTILS_BASE}/esearch.fcgi", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("esearchresult", {}).get("idlist", [])

def fetch_variant_summaries(variant_ids, debug_dump=False):
    """Fetch summary XML for a batch of ClinVar variant IDs and parse the fields we need."""
    if not variant_ids:
        return []

    params = {
        "db": "clinvar",
        "id": ",".join(variant_ids),
        "rettype": "vcv",
        "is_variationid": "true"
    }
    resp = requests.get(f"{NCBI_EUTILS_BASE}/efetch.fcgi", params=params, timeout=30)
    resp.raise_for_status()

    if debug_dump:
        with open("clinvar_debug.xml", "wb") as f:
            f.write(resp.content)
        print("[DEBUG] Wrote raw response to clinvar_debug.xml")

    variants = []
    try:
        root = ET.fromstring(resp.content)
        for vcv in root.iter("VariationArchive"):
            variant = {
                "clinvar_id": vcv.get("VariationID"),
                "name": vcv.get("VariationName"),
            }
            classification = vcv.find(".//Description")
            variant["clinical_significance"] = classification.text if classification is not None else None

            location = vcv.find(".//SequenceLocation[@Assembly='GRCh38']")
            if location is not None:
                variant["chromosome"] = location.get("Chr")
                variant["position"] = location.get("start")
                variant["ref_allele"] = location.get("referenceAlleleVCF")
                variant["alt_allele"] = location.get("alternateAlleleVCF")
            else:
                variant["chromosome"] = variant["position"] = None
                variant["ref_allele"] = variant["alt_allele"] = None

            # Search all HGVS blocks regardless of nesting depth
            variant["hgvs_c"] = None
            variant["hgvs_p"] = None
            for hgvs in vcv.iter("HGVS"):
                nuc_expr = hgvs.find("NucleotideExpression")
                if nuc_expr is not None and variant["hgvs_c"] is None:
                    expr_el = nuc_expr.find("Expression")
                    if expr_el is not None and expr_el.text:
                        variant["hgvs_c"] = expr_el.text

                prot_expr = hgvs.find("ProteinExpression")
                if prot_expr is not None and variant["hgvs_p"] is None:
                    expr_el = prot_expr.find("Expression")
                    if expr_el is not None and expr_el.text:
                        variant["hgvs_p"] = expr_el.text

            variants.append(variant)
    except ET.ParseError as e:
        print(f"[WARN] Failed to parse ClinVar XML: {e}")

    return variants

def run_clinvar_etl():
    """Populate the mutation table with ClinVar variants for every gene already in the DB."""
    genes = Gene.query.all()
    created, updated, skipped = 0, 0, 0

    for gene in genes:
        variant_ids = fetch_variant_ids(gene.symbol)
        if not variant_ids:
            print(f"[SKIP] {gene.symbol}: no ClinVar variants found")
            skipped += 1
            time.sleep(0.4)
            continue

        variants = fetch_variant_summaries(variant_ids, debug_dump=(gene.symbol == "BRCA1"))
        gene_created = 0

        for v in variants:
            if not v.get("clinvar_id"):
                continue

            existing = Mutation.query.filter_by(clinvar_id=v["clinvar_id"]).first()

            if existing:
                existing.clinical_significance = v.get("clinical_significance")
                existing.hgvs_c = v.get("hgvs_c")
                existing.hgvs_p = v.get("hgvs_p")
                updated += 1
            else:
                mutation = Mutation(
                    gene_id=gene.gene_id,
                    hgvs_c=v.get("hgvs_c"),
                    hgvs_p=v.get("hgvs_p"),
                    clinical_significance=v.get("clinical_significance"),
                    chromosome=v.get("chromosome"),
                    position=v.get("position"),
                    ref_allele=v.get("ref_allele"),
                    alt_allele=v.get("alt_allele"),
                    clinvar_id=v["clinvar_id"],
                    source="ClinVar"
                )
                db.session.add(mutation)
                created += 1
                gene_created += 1

        print(f"[OK] {gene.symbol}: {gene_created} new variant(s) from {len(variants)} fetched")
        time.sleep(0.4)

    db.session.commit()
    print(f"\nDone. Created: {created}, Updated: {updated}, Skipped (no variants): {skipped}")