"""Semantic LangChain tools for the IMF evidence pipeline."""

from __future__ import annotations

from langchain_core.tools import tool

from app.v1.services import country_resolver, evidence_builder, indicator_catalog_service


@tool
def resolve_country_or_region(name: str) -> dict:
    """Resolve a plain country name, ISO code, or region name to IMF country codes.

    Args:
        name: Country name (e.g. "Vietnam", "Germany"), ISO Alpha-3 code (e.g. "VNM"),
              or region group (e.g. "asean", "brics", "g20", "gulf").

    Returns:
        Dict with keys 'type' ("country" or "region") and 'codes' (list of ISO Alpha-3).
    """
    return country_resolver.resolve(name)


@tool
def select_imf_bundle(task_type: str) -> dict:
    """Return the IMF indicator codes for a given analytical task type.

    Args:
        task_type: One of: country_profile, macro_risk, trade_potential,
                   debt_sustainability, investment_assessment.

    Returns:
        Dict with 'bundle' name and 'indicators' list of IMF codes.
    """
    indicators = indicator_catalog_service.get_indicators_for_bundle(task_type)
    return {"bundle": task_type, "indicators": indicators}


@tool
def get_imf_evidence_pack(
    task_type: str,
    country_codes: list[str],
    indicator_codes: list[str],
    start_year: int = 2015,
    end_year: int = 2027,
) -> dict:
    """Retrieve IMF economic data for the given countries and indicators and return an evidence pack.

    Args:
        task_type:       The analytical task type (e.g. "macro_risk").
        country_codes:   List of ISO Alpha-3 country codes (e.g. ["VNM", "THA"]).
        indicator_codes: List of IMF DataMapper indicator codes (e.g. ["NGDP_RPCH", "PCPIPCH"]).
        start_year:      First year to retrieve (default 2015).
        end_year:        Last year to retrieve, including IMF forecasts (default 2027).

    Returns:
        Evidence pack dict with all retrieved records and a list of any missing indicators.
    """
    pack = evidence_builder.build_evidence_pack(
        task_type=task_type,
        countries=country_codes,
        indicator_codes=indicator_codes,
        start_year=start_year,
        end_year=end_year,
    )
    return pack.model_dump()


# Exported list
IMF_TOOLS = [
    resolve_country_or_region,
    select_imf_bundle,
    get_imf_evidence_pack,
]
