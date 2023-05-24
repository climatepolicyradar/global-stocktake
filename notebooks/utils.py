from dotenv import load_dotenv

load_dotenv()
import re

import numpy as np
import pandas as pd
import pycountry
from wbgapi import economy
import altair as alt


def find_country(text: str) -> str:
    """
    Given a text string, attempts to find the name of a country
    mentioned in the text. Returns the name of the country if found,
    or None otherwise.
    """
    if not isinstance(text, str):
        return None
    # Check for uppercase and lowercase country name
    for country in pycountry.countries:
        if text:
            if country.name.upper() in text.upper():
                return country.name
            elif country.name.lower() in text.lower():
                return country.name
        else:
            return None

    # Check for common name
    for country in pycountry.countries:
        if country.name in text:
            return country.name
        if hasattr(country, "common_name") and country.common_name in text:
            return country.common_name

        # Check for official name
        if hasattr(country, "official_name") and country.official_name in text:
            return country.official_name

        # Check for alpha_2 code (e.g., "US" for United States)
        if country.alpha_2 in re.findall(r"\b[A-Z]{2}\b", text):
            return country.name

        # Check for alpha_3 code (e.g., "USA" for United States)
        if country.alpha_3 in re.findall(r"\b[A-Z]{3}\b", text):
            return country.name

    return None


def get_country_code(x: str) -> str:
    """
    Given the name of a country, returns its ISO 3166-1 alpha-3
    code. Returns None if the country is not found.
    """
    try:
        return pycountry.countries.get(name=x).alpha_3
    except (AttributeError, LookupError):
        return None

def create_choropleth_map(merged, concept):
    merged["binary"] = np.where(merged["Number of mentions"] > 0, f"Parties that mention {concept}", f"Parties that do not mention {concept}")

    # create a cloropeth map with a binary indicator for whether the concept is mentioned or not

    choropleth_map = (
        alt.Chart(merged[merged["Concept"] == concept])
        .mark_geoshape(stroke="black", strokeWidth=1)
        .encode(
            color=alt.Color(
                "binary:N",
                scale=alt.Scale(domain=[f"Parties that mention {concept}", f"Parties that do not mention {concept}"], range=["lightblue", "grey"]),
                legend=alt.Legend(title="Mentioned"),
            ),
            tooltip=["country:N", "pop_est:N", "gdp_md_est:N", "continent:N", "Number of mentions:Q"],
        )
        .properties(
            width=800,
            height=400,
            title=f'UNFCCC Party members mentioning {concept} in GST submissions',
        )
    )
    return choropleth_map

def create_docs_table(df_concepts):
    # First, create a new column that categorizes each row as 'Party' or 'Non-Party'
    df_concepts["category"] = np.where(
        df_concepts["Party"].notna(), "Party", "Non-Party"
    )

    # Use groupby to count the unique document_id's for each category and for the total dataset
    docs_analysed = df_concepts.groupby("category")["document_id"].nunique()

    # Convert the resulting Series into a DataFrame with a single row and a custom index
    docs_analysed_table = pd.DataFrame(
        docs_analysed.values.reshape(1, -1),
        columns=docs_analysed.index,
        index=["Documents"],
    )

    return docs_analysed_table


def preprocess_concept_df(df_concepts, df_worldbank, df_eco):
    # Get columns surrounding indicator cols to find indices of indicator cols
    start_col_name = "text"
    end_col_name = "document_id"
    start_col = df_concepts.columns.get_loc(start_col_name)
    end_col = df_concepts.columns.get_loc(end_col_name)
    indicator_columns = df_concepts.columns[start_col + 1: end_col]
    # Melt the DataFrame and specify the columns to keep as id_vars
    df_concepts = df_concepts.rename(columns={"party": "Party"})
    df_concepts["category"] = np.where(df_concepts["Party"].notna(), "Party", "Non-Party")
    df_concepts_melted = df_concepts.melt(
        id_vars=[col for col in df_concepts.columns if col not in indicator_columns],
        var_name="Concept",
        value_name="value",
    )
    # filter where indicators are 1
    df_concepts_melted = df_concepts_melted[df_concepts_melted["value"] == 1]
    # Create a new column 'country' with the found country names
    df_concepts_melted["document_name_x_reformatted"] = df_concepts_melted[
        "document_name_x"
    ].str.replace(r"[_20]+", " ", regex=True)
    df_concepts_melted["document_name_y_reformatted"] = df_concepts_melted[
        "document_name_y"
    ].str.replace(r"[_20]+", " ", regex=True)
    df_concepts_melted["country_x"] = df_concepts_melted[
        "document_name_x_reformatted"
    ].apply(find_country)
    df_concepts_melted["country_y"] = df_concepts_melted[
        "document_name_y_reformatted"
    ].apply(find_country)
    df_concepts_melted["country"] = df_concepts_melted["country_x"].combine_first(
        df_concepts_melted["country_y"]
    )
    # create 3 letter country code
    df_concepts_melted["country_code"] = df_concepts_melted["country"].apply(
        get_country_code
    )
    # create 3 letter country code
    df_concepts_melted["country_code"] = df_concepts_melted["country"].apply(
        get_country_code
    )
    df_eco = pd.DataFrame(economy.list())
    # Assuming the 3-letter country code column in df_concepts_melted is named 'country_code'
    df_concepts_melted = pd.merge(
        df_concepts_melted,
        df_eco[["id", "region"]],
        left_on="country_code",
        right_on="id",
        how="left",
    )

    df_concepts_merged = df_concepts_melted.merge(df_worldbank, how='left', left_on='country_code', right_on='iso_a3')
    df_concepts_merged = df_concepts_merged.drop(columns='name')
    return df_concepts_merged

def add_zero_mentions(df_concepts_geoplot, df_worldbank):
    # for every country in world, check if the concept is in df_concepts_geoplot. If not, add a row with count 0
    for country in df_worldbank["iso_a3"]:
        for conc in df_concepts_geoplot["Concept"].unique():
            if not df_concepts_geoplot[
                (df_concepts_geoplot["iso_a3"] == country) & (df_concepts_geoplot["Concept"] == conc)
            ].empty:
                continue
            else:
                df_concepts_geoplot = pd.concat(
                    [
                        df_concepts_geoplot,
                        df_worldbank[df_worldbank["iso_a3"] == country]
                        .reset_index(drop=True)
                        .merge(
                            pd.DataFrame({"Concept": conc, "Number of mentions": 0}, index=[0]),
                            left_index=True,
                            right_index=True,
                        ),
                    ],
                    ignore_index=True,
                )
    return df_concepts_geoplot

def create_choropleth_map_co_occurrence(df, concept):
    df=df[df['combined_concept']==concept]
    concept1, concept2 = concept[0], concept[1]
    df['binary'] = df['indicator'].apply(lambda x: f"Parties that mention {concept1.title()} and {concept2.title()}" if x else f"Parties that do not mention {concept}")
    choropleth_map = (
        alt.Chart(df[df["combined_concept"] == concept])
        .mark_geoshape(stroke="black", strokeWidth=1)
        .encode(
            color=alt.Color(
                "binary:N",
                scale=alt.Scale(domain=[f"Parties that mention {concept}", f"Parties that do not mention {concept}"], range=["lightblue", "grey"]),
                legend=alt.Legend(title="Mentioned"),
            ),
            tooltip=["country:N", "pop_est:N", "gdp_md_est:N", "continent:N", "Number of mentions:Q"],
        )
        .properties(
            width=800,
            height=400,
            title=f'UNFCCC Party members mentioning {concept} in GST submissions',
        )
    )
    return choropleth_map

