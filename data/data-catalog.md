# Data Catalog

## OECD-WTO_BATIS_BPM6_December2025_CH.csv

- Source File: ./economics/OECD-WTO_BATIS_BPM6_December2025_CH.csv
- Upstream Raw File: ./economics/OECD-WTO_BATIS_BPM6_December2025_bulk.csv
- Transformation Notebook: ../datapreparation/wto-trade.ipynb
- Topic: International trade in services (BPM6), Switzerland-focused extract

### Description
This dataset is a transformed subset of the OECD-WTO Balanced Trade in Services (BaTIS) BPM6 release (December 2025).

It contains bilateral trade in services records where Switzerland is involved, with additional filtering applied in the transformation notebook.

### Source
- WTO trade datasets page: https://www.wto.org/english/res_e/statis_e/trade_datasets_e.htm

### Transformation Notes
- Derived from the bulk BaTIS extract.
- Switzerland scope filter: rows were kept when Reporter == CH or Partner == CH.
- Partner type filter: only country partners were kept (excluding aggregates/groups in the notebook workflow).
- Item filter: only selected service categories were retained in Item_code.

### Kept Item_code Values
| Item code | Description |
|---|---|
| S | Total services (sum of the others) |
| SA | Manufacturing services on physical inputs owned by others |
| SB | Maintenance and repair services n.i.e. |
| SC | Transport |
| SD | Travel |
| SE | Construction |
| SF | Insurance and pension services |
| SG | Financial services |
| SH | Charges for the use of intellectual property n.i.e. |
| SI | Telecommunications, computer, and information services |
| SJ | Other business services |
| SK | Personal, cultural, and recreational services |
| SL | Government goods and services n.i.e. |

### What Can Be Found In This File
- Bilateral service-trade observations with yearly values.
- Data coverage includes years 2005 to 2024.
- Flow direction includes exports (X) and imports (M).
- Core value fields include Reported_value, Final_value, and Balanced_value.

### Column Dictionary
| Column | Description |
|---|---|
| Reporter | Reporting economy code. |
| type_Reporter | Reporter type code (country-level marker in this transformed file). |
| Partner | Partner economy code. |
| Flow | Trade flow direction (X = exports, M = imports). |
| Item_code | Services category code (filtered list above). |
| type_Item | Item type code for the services classification. |
| Year | Reference year. |
| Reported_value | Reported trade value from source reporting when available. |
| Final_value | Final modeled/harmonized trade value in BaTIS. |
| Final_value_methodology | Methodology flag/code used to derive Final_value. |
| Balanced_value | Balanced bilateral value used in BaTIS balancing framework. |



