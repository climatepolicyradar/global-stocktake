# Concept Methodology: Sectors

## Summary

References to sectors were identified based on sources published by the Intergovernmental Panel on Climate Change (IPCC). A machine learning classifier was used to assign each paragraph to zero or more sectors. For more information about our approach, please see our [methodology](../README.md)..

## Methodology

The taxonomy of sectors is based on sources published by the Intergovernmental Panel on Climate Change (IPCC). In particular, the IPCCs [AR6 Synthesis Report: Climate Change 2023](https://www.ipcc.ch/report/sixth-assessment-report-cycle/) and [AR5 Climate Change 2014: Impacts, Adaptation, and Vulnerability - Part A: Global and Sectoral Aspects (Chapter 10)](https://www.ipcc.ch/report/ar5/wg2/). This source was chosen because the IPCC is an internationally-recognised authority on climate change with widely referenced scientific assessment reports that use a sectoral approach to discuss insights and findings.

In the IPCC’s AR6 Synthesis Report, major sectors include Energy, Industry, Agriculture, Forestry and Other Land Use, Transport and Buildings. These represent key areas of economic activity with significant contribution to global GHG emissions. The report also mentions additional sectors which are “climate-exposed” including Fishery and Tourism. In Chapter 10 of the AR5 Climate Change 2014 report, the IPCC mentions additional sectors including Water Services, Recreation and Tourism, Fisheries and Aquaculture, Insurance and Financial Services and Health Services. 

Where available, IPCC sub-sectors have been used. In the absence of IPCC sector disaggregation, other internationally-recognised, sector-specific sources have been used in its place including the International Energy Agency (IEA), Food and Agriculture Organisation of the United Nations (FAO) and the International Labour Organization (ILO). [Learn more about our taxonomy methodology](../README.md).

## Performance Metrics

The performance of the classifier was evaluated using a 5-fold cross-validation approach. Statistics in the table below are the average across the 5 folds.

| Category                               | F1 score | Precision | Recall |
|--------------------------------------|----------|-----------|--------|
| Agriculture, forestry and other land use | 0.70     | 0.73      | 0.68   |
| Buildings                            | 0.71     | 0.84      | 0.63   |
| Energy                               | 0.70     | 0.73      | 0.69   |
| Fisheries & aquaculture              | 0.93     | 0.96      | 0.90   |
| Health services                      | 0.84     | 0.93      | 0.78   |
| Industry                             | 0.64     | 0.75      | 0.59   |
| Insurance & financial services       | 0.79     | 0.86      | 0.75   |
| Tourism                              | 0.94     | 0.93      | 0.95   |
| Transport                            | 0.88     | 0.97      | 0.82   |
| Water services                       | 0.76     | 0.78      | 0.80   |
