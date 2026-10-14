# Benchmark source

AutoSTAIR's first case study uses:

> World Bank. 2024. *World Development Report 2024: The Middle-Income Trap.*
> Washington, DC: World Bank. doi:10.1596/978-1-4648-2078-6. License:
> Creative Commons Attribution CC BY 3.0 IGO.

- [Publication page](https://www.worldbank.org/en/publication/wdr2024)
- [Official full PDF](https://openknowledge.worldbank.org/bitstreams/8dca4aff-e0f5-4865-b245-ec9c4583aa60/download)
- [CC BY 3.0 IGO license](https://creativecommons.org/licenses/by/3.0/igo/)

The report PDF is an evaluation input and is ignored by Git. AutoSTAIR does not
modify its headings or generate a replacement hierarchy. It reads the embedded
PDF outline and maps authored leaf sections to their page ranges.

The PDF also exposes separate bookmark indexes for boxes, figures, maps, and
tables. Those auxiliary indexes point back into pages already covered by the main
chapter hierarchy, so the default configuration excludes them to prevent duplicate
evidence. Notes, references, and other navigation-only entries are also excluded.

The World Bank does not necessarily own every third-party component in the
report. Avoid redistributing extracted figures, photographs, or other third-party
content unless their reuse rights have been checked separately.
