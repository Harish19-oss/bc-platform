# Breast Cancer Integrated Bioinformatics Platform

A Flask-based web platform for exploring breast cancer gene data, integrating multiple bioinformatics databases.

## Features
- 50 breast cancer genes with full annotations
- Mutation data from ClinVar (1,000 records)
- TCGA-BRCA mutation frequency data
- Pathway data from Reactome and KEGG (1,000+ records)
- GEO expression context (200 records)
- Drug repurposing data from DGIdb (406 records)
- PubMed publications (250 records)
- Interactive charts (pathway donut, TCGA bar chart)
- Gene search and filter by chromosome

## Tech Stack
- Python 3.11, Flask, SQLAlchemy
- PostgreSQL
- Bootstrap 5, Chart.js
- APIs: NCBI, UniProt, Ensembl, Reactome, KEGG, GEO, DGIdb, PubMed

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
createdb bc_platform
flask db upgrade
flask run
```

## Project Structure

## Developed by
Harish Siva Balaji M (44738010) — B.Sc. Bioinformatics and Data Science, Sathyabama University