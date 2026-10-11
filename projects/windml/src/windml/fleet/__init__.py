"""Repeatable fleet condition report: any ingested fleet (a windml.ingest mapping) -> condition report (md/html/pdf).

Stages (each cached in a work directory, per turbine, memory-bounded):
  prepare  raw export -> per-turbine canonical, cleaned, labelled 10-min parquet   (fleet.prepare)
  health   normal-behaviour models -> residual z-scores per turbine                (fleet.health)
  metrics  data quality, availability, stops, trips, oil trends, drift, NBM health (fleet.metrics)
  score    RAG flag, plain-language reasons, confidence                            (fleet.scoring)
  render   markdown -> html -> pdf, executive summary first                        (fleet.render)
Entry point: `windml report --mapping mappings/<farm>.yaml --out reports/<farm>/` (fleet.cli).
"""
