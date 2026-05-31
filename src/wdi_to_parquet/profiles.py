"""Predefined indicator profiles and year granularities.

Two indicator profiles:
  minimum  — 6 core indicators for basic population/economic queries
  basic    — 16 indicators adding social, health, and environment dimensions

Two year granularities:
  quinquennial — 5-year steps from 1990, plus 2024 (current)
  annual       — every year 1990-2024

Sizes (approximate, ZSTD-compressed Parquet):
  minimum × quinquennial  ~  83 KB   (baseline)
  minimum × annual        ~ 250 KB
  basic × quinquennial    ~ 200 KB
  basic × annual          ~ 650 KB
"""

from __future__ import annotations

INDICATORS_MINIMUM: list[str] = [
    "SP.POP.TOTL",       # Population, total
    "SP.POP.GROW",       # Population growth (annual %)
    "NY.GDP.MKTP.CD",    # GDP (current US$)
    "NY.GDP.PCAP.CD",    # GDP per capita (current US$)
    "AG.SRF.TOTL.K2",    # Surface area (sq. km)
    "SP.URB.TOTL.IN.ZS", # Urban population (% of total)
]

INDICATORS_BASIC: list[str] = INDICATORS_MINIMUM + [
    # Demographics & health
    "SP.DYN.LE00.IN",    # Life expectancy at birth (years)
    "SP.DYN.TFRT.IN",    # Fertility rate (births per woman)
    "SH.DYN.MORT",       # Mortality rate, under-5 (per 1,000 live births)
    "SE.ADT.LITR.ZS",    # Literacy rate, adult total (% of people 15+)
    # Economy
    "NY.GNP.PCAP.CD",    # GNI per capita, Atlas method (current US$)
    "SI.POV.GINI",       # Gini index (income inequality)
    "SL.UEM.TOTL.ZS",    # Unemployment, total (% of total labor force)
    # Environment
    "EN.ATM.CO2E.PC",    # CO2 emissions (metric tons per capita)
    "AG.LND.FRST.ZS",    # Forest area (% of land area)
    # Connectivity
    "IT.NET.USER.ZS",    # Individuals using the Internet (% of population)
]

YEARS_QUINQUENNIAL: list[int] = [
    1990, 1995, 2000, 2005, 2010, 2015, 2020, 2024,
]

YEARS_ANNUAL: list[int] = list(range(1990, 2025))


def years_for_granularity(granularity: str) -> list[int]:
    if granularity == "quinquennial":
        return YEARS_QUINQUENNIAL
    if granularity == "annual":
        return YEARS_ANNUAL
    raise ValueError(f"unknown granularity {granularity!r}; choose 'quinquennial' or 'annual'")


def indicators_for_profile(profile: str) -> list[str]:
    if profile == "minimum":
        return INDICATORS_MINIMUM
    if profile == "basic":
        return INDICATORS_BASIC
    raise ValueError(f"unknown profile {profile!r}; choose 'minimum' or 'basic'")
