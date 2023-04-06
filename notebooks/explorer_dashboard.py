import altair as alt
import numpy as np
import pandas as pd
import pycountry
import re
from pathlib import Path
from typing import List
from wbgapi import economy



def find_country(text):
    # Check for uppercase and lowercase country name
    for country in pycountry.countries:
        if country.name.upper() in text.upper():
            return country.name
        elif country.name.lower() in text.lower():
            return country.name

    # Check for common name
    for country in pycountry.countries:
        if country.name in text:
            return country.name
        if hasattr(country, 'common_name') and country.common_name in text:
            return country.common_name

        # Check for official name
        if hasattr(country, 'official_name') and country.official_name in text:
            return country.official_name

        # Check for alpha_2 code (e.g., "US" for United States)
        if country.alpha_2 in re.findall(r'\b[A-Z]{2}\b', text):
            return country.name

        # Check for alpha_3 code (e.g., "USA" for United States)
        if country.alpha_3 in re.findall(r'\b[A-Z]{3}\b', text):
            return country.name

    return None

def get_country_code(x):
    try:
        return pycountry.countries.get(name=x).alpha_3
    except (AttributeError, LookupError):
        return None

def create_docs_table(df_concepts):

    # First, create a new column that categorizes each row as 'Party' or 'Non-party'
    df_concepts['category'] = np.where(df_concepts['party'].notna(), 'Party', 'Non-party')

    # Use groupby to count the unique document_id's for each category and for the total dataset
    docs_analysed = df_concepts.groupby('category')['document_id'].nunique()
    docs_analysed.loc['Total'] = df_concepts['document_id'].nunique()

    # Convert the resulting Series into a DataFrame with a single row and a custom index
    docs_analysed_table = pd.DataFrame(docs_analysed.values.reshape(1, -1),
                                       columns=docs_analysed.index,
                                       index=["Documents"])

    return docs_analysed_table

from typing import Iterable

def get_cols_between(df: pd.DataFrame, start_col_name: str = "text", end_col_name: str = "document_id") -> Iterable[str]:
    """
    Get the names of the columns between two named columns in a dataframe.
    """
    start_col = df.columns.get_loc(start_col_name)
    end_col = df.columns.get_loc(end_col_name)
    assert start_col < end_col, "start_col must be before end_col"
    indicator_columns = df.columns[start_col + 1:end_col]
    return indicator_columns

def get_indicator_data(df: pd.DataFrame, indicator_col: str, value_col: str, category_col: str) -> List:
    """
    Get unique and total counts of a specific indicator column grouped by a category column.

    :param df: DataFrame containing the data.
    :param indicator_col: Column with the indicator values (1 or 0).
    :param value_col: Column used to count unique values.
    :param category_col: Column used to group the data.
    :return: List containing the indicator column and unique and total counts for each category and in total.
    """
    df_filtered = df[df[indicator_col] == 1]
    data_grouped = df_filtered.groupby(category_col)[value_col].agg(['nunique','count'])

    data_grouped.loc['Total'] = df_filtered[value_col].agg(['nunique', 'count'])


    result = [indicator_col, *data_grouped['nunique'], *data_grouped['count']]
    return result

def create_indicator_tables(df: pd.DataFrame, start_col_name, end_col_name: str, category_col: str, value_col: str) -> pd.DataFrame:
    """
    Create a table with unique and total counts for a range of indicator columns, grouped by a category column.

    :param df: DataFrame containing the data.
    :param category_col: Column used to group the data.
    :param start_col_name: Name of the last column before the indicator columns.
    :param end_col_name: Name of the first column after the indicator columns.
    :param value_col: Column used to count unique values.
    :return: DataFrame with unique and total counts for each indicator column and category.
    """
    indicator_cols = get_cols_between(df_concepts, start_col_name=start_col_name, end_col_name=end_col_name)
    data_list = [get_indicator_data(df, col, value_col, category_col) for col in indicator_cols]
    columns = ['Concept', 'Num Docs Mentioned (party)', 'Num Docs Mentioned (non-party)', 'Num Docs Mentioned (Total)', 'Num Concept Mentions (Parties)', 'Num Concept Mentions (Non-parties)', 'All Concept Mentions']
    return pd.DataFrame(data_list, columns=columns)

def disambiguate_country(df):
    # Create a new column 'country' with the found country names
    df["document_name_x_reformatted"] = df["document_name_x"].str.replace(r'[_20]+', ' ', regex=True)
    df["document_name_y_reformatted"] = df["document_name_y"].str.replace(r'[_20]+', ' ', regex=True)
    df['country_x'] = df['document_name_x_reformatted'].apply(find_country)
    df['country_y'] = df['document_name_y_reformatted'].apply(find_country)
    df['country'] = df['country_x'].combine_first(df['country_y'])
    # create 3 letter country code
    df['country_code'] = df['country'].apply(get_country_code)
    return df

if __name__ == '__main__':
    # set the display options to allow resizing columns
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    concepts_path = Path().absolute().parent / 'concepts'
    concept = "fossil-fuels"
    df_concepts = pd.read_excel(concepts_path / concept / "output_with_metadata.xlsx")
    df_spans = pd.read_csv(concepts_path / concept / "spans.csv")


    # Create a new column 'country' with the found country names
    df_concepts["document_name_x_reformatted"] = df_concepts["document_name_x"].str.replace(r'[_20]+', ' ', regex=True)
    df_concepts["document_name_y_reformatted"] = df_concepts["document_name_y"].str.replace(r'[_20]+', ' ', regex=True)
    df_concepts['country_x'] = df_concepts['document_name_x_reformatted'].apply(find_country)
    df_concepts['country_y'] = df_concepts['document_name_y_reformatted'].apply(find_country)
    df_concepts['country'] = df_concepts['country_x'].combine_first(df_concepts['country_y'])
    # create 3 letter country code
    df_concepts['country_code'] = df_concepts['country'].apply(get_country_code)

    df_eco = pd.DataFrame(economy.list())
    df_concepts = pd.merge(df_concepts, df_eco[['id', 'region']], left_on='country_code', right_on='id', how='left')

    docs_analysed_table = create_docs_table(df_concepts)


    indicator_table = create_indicator_tables(df_concepts, start_col_name="text", end_col_name="document_id", category_col="category",value_col="document_id")