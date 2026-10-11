"""windml.ingest: map an operator's SCADA export onto the canonical windml format.

Workflow for a new operator (see README "Onboarding a new operator's data" and mappings/README.md):

    windml ingest suggest  <sample file>  --out mappings/acme.yaml     # draft mapping with confidence scores
    (review the YAML: every CHECK line, units, timezone, interval label, turbine ids)
    windml ingest validate --mapping mappings/acme.yaml                 # strict mapping check + day-1 data-quality report
    windml ingest load     --mapping mappings/acme.yaml --out data/ingest/acme [--export]

Modules: schema (canonical signals and units), units (conversion and unit detection), mapping (YAML format and
validation), readers (CSV/Excel/parquet), loader (mapping -> canonical frame + event table), quality (data-quality
report), suggest (draft mappings), pipeline (hand-off to clean_wind / labeling / NBM file layout), cli.
"""
