# Concept Methodology: Policy instruments

## Summary

References to policy instruments were identified based on taxonomies created by the NewClimate Institute and the Grantham Research Institute at the London School of Economics and Political Science. For more information about our approach, please see our [methodology](../README.md).

## Methodology

The taxonomy of policy instruments is adapted from the taxonomies created for the [Climate Policy Database](https://climatepolicydatabase.org/methodology) (CPD), maintained by the NewClimate Institute, and for [Climate Change Laws of the World](https://climate-laws.org/methodology) (CCLW) database maintained by the Grantham Research Institute at the London School of Economics and Political Science and Climate Policy Radar. These sources were selected for their renowned expertise on policy research.

The four high-level categories of policy instruments — Economic, Regulatory, Information & Education and Governance — are based on those used in the CCLW taxonomy. All instrument sub-categories across the CCLW and CPD taxonomies were merged with these four high-level categories: for example, ‘Institutional creation’ and ‘Strategic planning’, under ‘Policy support’ in the CPD taxonomy, were merged into the ‘Governance’ instrument category.

We excluded certain values from the instrument taxonomy. For example, ‘Targets’ was not included in the instruments taxonomy because we are developing a separate, dedicated machine learning classifier to detect references to targets. [Learn more about our taxonomy methodology](../README.md).

## Performance Metrics

The performance of the classifier was evaluated using a 5-fold cross-validation approach. Statistics in the table below are the average across the 5 folds.

| Category                    | F1 score | Precision | Recall |
|-----------------------------|----------|-----------|--------|
| Economic instruments        | 0.91     | 0.88      | 0.95   |
| Governance                  | 0.84     | 0.84      | 0.84   |
| Information and education   | 0.76     | 0.82      | 0.71   |
| Regulatory instruments      | 0.85     | 0.82      | 0.89   |