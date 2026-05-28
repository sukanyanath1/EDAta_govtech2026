# Data Catalog

## WPP2024_Demographic_Indicators_Medium.csv

Source File: ./demographic/WPP2024_Demographic_Indicators_Medium.csv
Topic: Demographic Indicators from 1950-2100

### Description
This file contains demographic indicators from the United Nations World Population Prospects (WPP) 2024, Medium Variant scenario.

It is designed for population and demographic analysis across countries/areas and years, including:
- population size and growth
- fertility patterns
- mortality and life expectancy
- net migration

### Source
- UN WPP download page (CSV, Standard Projections): https://population.un.org/wpp/downloads?folder=Standard%20Projections&group=CSV%20format

### What Can Be Found In This File
- A standardized indicator model with fields:
	- IndicatorNo
	- Topic
	- Indicator
	- IndicatorName
	- Unit
- Indicators grouped into core themes:
	- Population
	- Fertility
	- Mortality
	- Migration

### Indicator Dictionary

#### Population
| IndicatorNo | Indicator | IndicatorName | Unit |
|---:|---|---|---|
| 1 | TPopulation1Jan | Total Population, as of 1 January | thousands |
| 2 | TPopulation1July | Total Population, as of 1 July | thousands |
| 3 | TPopulationMale1July | Male Population, as of 1 July | thousands |
| 4 | TPopulationFemale1July | Female Population, as of 1 July | thousands |
| 5 | PopDensity | Population Density, as of 1 July | persons per square km |
| 6 | PopSexRatio | Population Sex Ratio, as of 1 July | males per 100 females |
| 7 | MedianAgePop | Median Age, as of 1 July | years |
| 8 | NatChange | Natural Change, Births minus Deaths | thousands |
| 9 | NatChangeRT | Rate of Natural Change | per 1,000 population |
| 10 | PopChange | Population Change | thousands |
| 11 | PopGrowthRate | Population Growth Rate | percentage |
| 12 | DoublingTime | Population Annual Doubling Time | years |

#### Fertility
| IndicatorNo | Indicator | IndicatorName | Unit |
|---:|---|---|---|
| 13 | Births | Births | thousands |
| 58 | BirthsMale | Male Births | thousands |
| 59 | BirthsFemale | Females Births | thousands |
| 14 | Births1519 | Births by women aged 15 to 19 | thousands |
| 15 | CBR | Crude Birth Rate | births per 1,000 population |
| 16 | TFR | Total Fertility Rate | live births per woman |
| 17 | NRR | Net Reproduction Rate | surviving daughters per woman |
| 18 | MAC | Mean Age Childbearing | years |
| 19 | SRB | Sex Ratio at Birth | males per 100 female births |

#### Mortality
| IndicatorNo | Indicator | IndicatorName | Unit |
|---:|---|---|---|
| 20 | Deaths | Total Deaths | thousands |
| 21 | DeathsMale | Male Deaths | thousands |
| 22 | DeathsFemale | Female Deaths | thousands |
| 23 | CDR | Crude Death Rate | deaths per 1,000 population |
| 24 | LEx | Life Expectancy at Birth, both sexes | years |
| 25 | LExMale | Male Life Expectancy at Birth | years |
| 26 | LExFemale | Female Life Expectancy at Birth | years |
| 27 | LE15 | Life Expectancy at Age 15, both sexes | years |
| 28 | LE15Male | Male Life Expectancy at Age 15 | years |
| 29 | LE15Female | Female Life Expectancy at Age 15 | years |
| 55 | LE60 | Life Expectancy at Age 60, both sexes | years |
| 56 | LE60Male | Male Life Expectancy at Age 60 | years |
| 57 | LE60Female | Female Life Expectancy at Age 60 | years |
| 30 | LE65 | Life Expectancy at Age 65, both sexes | years |
| 31 | LE65Male | Male Life Expectancy at Age 65 | years |
| 32 | LE65Female | Female Life Expectancy at Age 65 | years |
| 33 | LE80 | Life Expectancy at Age 80, both sexes | years |
| 34 | LE80Male | Male Life Expectancy at Age 80 | years |
| 35 | LE80Female | Female Life Expectancy at Age 80 | years |
| 36 | InfantDeaths | Infant Deaths, under age 1 | thousands |
| 37 | IMR | Infant Mortality Rate | infant deaths per 1,000 live births |
| 38 | LBsurvivingAge1 | Live births Surviving to Age 1 | thousands |
| 39 | Under5Deaths | Deaths under age 5 | thousands |
| 40 | Q5 | Under-five Mortality Rate | deaths under age 5 per 1,000 live births |
| 41 | Q0040 | Mortality before Age 40, both sexes | deaths under age 40 per 1,000 live births |
| 42 | Q0040Male | Male mortality before Age 40 | deaths under age 40 per 1,000 male live births |
| 43 | Q0040Female | Female mortality before Age 40 | deaths under age 40 per 1,000 female live births |
| 44 | Q0060 | Mortality before Age 60, both sexes | deaths under age 60 per 1,000 live births |
| 45 | Q0060Male | Male mortality before Age 60 | deaths under age 60 per 1,000 male live births |
| 46 | Q0060Female | Female mortality before Age 60 | deaths under age 60 per 1,000 female live births |
| 47 | Q1550 | Mortality between Age 15 and 50, both sexes | deaths under age 50 per 1,000 alive at age 15 |
| 48 | Q1550Male | Male mortality between Age 15 and 50 | deaths under age 50 per 1,000 males alive at age 15 |
| 49 | Q1550Female | Female mortality between Age 15 and 50 | deaths under age 50 per 1,000 females alive at age 15 |
| 50 | Q1560 | Mortality between Age 15 and 60, both sexes | deaths under age 60 per 1,000 alive at age 15 |
| 51 | Q1560Male | Male mortality between Age 15 and 60 | deaths under age 60 per 1,000 males alive at age 15 |
| 52 | Q1560Female | Female mortality between Age 15 and 60 | deaths under age 60 per 1,000 females alive at age 15 |

#### Migration
| IndicatorNo | Indicator | IndicatorName | Unit |
|---:|---|---|---|
| 53 | NetMigrations | Net Number of Migrants | thousands |
| 54 | CNMR | Net Migration Rate | per 1,000 population |

