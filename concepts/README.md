# Centralised Store For Explorer Outputs

This directory is a centralised store for version controlled inputs and outputs from the explorer tool
for concepts identified as relevant. 

## Process

- We identify interesting concepts and define linguistic rules for extracting them in an Excel sheet;
- Then we extract matches using the explorer tool, storing artifacts here in the following format:

    ```
    |-- input_spec_1
       |-- README.md
       |-- input.xlsx
       |-- output.xlsx
       |-- output_with_metadata.xlsx
       |-- spans.csv
    ```

input_spec_1 is a concept (fossil fuels, for example);
input.xlsx is a file containing the patterns used to extract the relevant concepts from global-stocktake data, finding the exact rules
is an iterative process depending on phrasing in the GST corpus;
output.xlsx is a file containing the extracted concepts;
output_with_metadata.xlsx is a file containing the extracted concepts as well as metadata from UNFCCC;

# Utility 

This unified structure of this concept store will allow us to analyse the quality of extracted data in a scalable way. For example, we will
be able to write data quality assessment scripts or notebooks in a manner that is agnostic to the concept being analysed. This way, we can
automatically check if the extracted data is of sufficient quality or if it needs to be improved when we add or update a concept. This will
tell us whether we need to update the rules. The aim is for such data quality assessment scripts to be run automatically whenever a new concept
is added and for their outputs to have an interface that is interpretable by non-technical users.

Git will allow us to leverage version control facilities. In particular, if we update the rules for a concept, we can check if the data quality checks
just alluded to lead to a degradation, and if not we can merge them into the main branch here for everyone to access.