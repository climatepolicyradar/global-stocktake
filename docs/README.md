# Climate Policy Radar Global Stocktake Explorer methodology

> **Note**
> We are continuing to update and refine our methodology as we develop our tool and its capabilities. This is the methodology for our approach to detecting concepts in the text of documents. For information about the research methods and taxonomies used to identify references to specific concepts, please refer to our [concept-specific methodologies](./concept-specific-methodologies/).

## 1. Overview

The text labels and filter tools in our Global Stocktake search tool are based on data collected using Explorer, an internal text analysis tools developed by Climate Policy Radar. Explorer enables search for references to a number of concepts simultaneously across a large number of documents, using keywords. This section documents how Explorer works, and the methodology we follow to develop keyword lists to identify references to concepts within documents related to the Global Stocktake.

## 2. How Explorer works

To search a set of documents for references to a concept using Explorer, we create bespoke CSV input files for each concept, containing keywords organised across a three-tier hierarchy. For example, for fossil fuels:

| Tier 1 concept | Tier 2 concept | Tier 3 concept |
| --- | --- | --- |
| Fossil fuels | Oil | Crude oil |
| Fossil fuels | Oil | Petroleum oil |
| Fossil fuels | Oil | Gasoline |
| Fossil fuels | Gas | Natural gas |
| Fossil fuels | Gas | Petroleum gas |

In our input files, we indicate where a certain keyword may have multiple synonyms or different linguistic expressions, such a present/past tense and singular/plural. These variations are then searched for automatically. This enables us to perform a precise and comprehensive search for each concept without exhaustively listing all its possible variations or linguistic expressions.

## 3. How we develop keyword lists

### 3.1 Using existing resources

Wherever possible, we use existing taxonomies developed by expert third-party sources as the basis for our keyword lists. For example, our keyword list for technologies is based on the UN Climate Technology Centre and Network’s [Taxonomy of Climate Technologies](https://www.ctc-n.org/resources/ctcn-taxonomy-0), while our keyword list for climate-related hazards is based on the UN Office for Disaster Risk Reduction’s [Hazard Definition and Classification Review](https://www.undrr.org/publication/hazard-definition-and-classification-review-technical-report).

Where such resources are available, we take the following steps to develop a keyword list:

1. We evaluate existing resources to assess whether they are developed by **credible sources** (for example, a UN agency) and whether they are **widely used and referenced**.
2. We use the taxonomy to create keyword lists following the process described in Section 2 above.
3. We use desk research to expand these keyword lists and ensure ~~that~~ they include as many relevant terms as possible.

### 3.2 Creating keyword lists based on desk research

Where we are not able to identify an existing credible source providing a taxonomy for a given concept, we create keyword lists based on desk research.

To do this, we review literature from sources such as Wikidata, as well as academic journals and reports and publications by international agencies, to identify the relevant key terms for a given concept.

We then create keyword lists following the process described in Section 2 above.

## 4. How this work is reflected in the search tool

When you search using the filters on the left side of the page, phrases in the text of a document that represent or express a concept will be tagged and labelled.

Use these labels to find instances of your chosen concept, and read the surrounding text to understand its context in the document.
