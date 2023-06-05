from dotenv import load_dotenv

load_dotenv()

import pycountry

from dotenv import load_dotenv

load_dotenv()
import re

import geopandas as gpd
import numpy as np
import pandas as pd
from IPython.core.display_functions import display
from IPython.display import Markdown
from wordcloud import STOPWORDS
import altair as alt

from nltk import FreqDist
from nltk.util import ngrams
from nltk.tokenize import word_tokenize


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


def preprocess_concept_df(df_concepts, df_worldbank, df_world_economics):
    # Get columns surrounding indicator cols to find indices of indicator cols
    start_col_name = "text"
    end_col_name = "document_id"
    start_col = df_concepts.columns.get_loc(start_col_name)
    end_col = df_concepts.columns.get_loc(end_col_name)
    indicator_columns = df_concepts.columns[start_col + 1 : end_col]
    # Melt the DataFrame so that each concept is in a single row
    df_concepts_melted = df_concepts.melt(
        id_vars=[col for col in df_concepts.columns if col not in indicator_columns],
        var_name="Concept",
        value_name="value",
    )
    df_concepts_melted = pd.merge(
        df_concepts_melted,
        df_world_economics[["id", "region"]],
        left_on="Geography ISO",
        right_on="id",
        how="left",
    )

    df_concepts_merged = df_concepts_melted.merge(df_worldbank, how='left', left_on='Geography ISO', right_on='iso_a3')
    df_concepts_merged = df_concepts_merged.drop(columns='name')
    return df_concepts_merged

def process_spans(df_spans, df_concepts_processed):
    mapping = df_concepts_processed[
        ["document_id", "document_name", "Category", "Author", "Author Type", "Submission Type"]
    ].drop_duplicates()

    # remove stop words for co-occurrence analysis
    df_spans["processed_sentence"] = df_spans["sentence"].apply(
        lambda x: " ".join([word for word in x.split() if word not in (STOPWORDS)])
    )
    df_spans["normalised_text"] = df_spans["text"].str.lower()
    old_to_new_doc_ids = pd.read_csv("/home/stefan/unfccc-global-stocktake-documents/notebooks/old-to-new-dataset-mapping.csv")
    old_to_new_doc_ids.drop_duplicates(subset='document_id_old', keep='first', inplace=True)
    df_spans['document_id'] = df_spans.document_id.map(old_to_new_doc_ids.set_index('document_id_old')['document_id_new'])
    df_spans = df_spans.merge(mapping, on=["document_id"], how="left")
    return df_spans


def add_zero_mentions(df_concepts_geoplot, df_worldbank):
    # for every country in df_worldbank, check if the concept is in df_concepts_geoplot. If not, add a row with count 0
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


def create_geodataframe(df_concepts, df_worldbank):
    # create a geodataframe for plotting
    df_concepts_geoplot = df_concepts.groupby('iso_a3').agg(
        **{'Number of mentions': ('value', 'sum')},
        Concept=('Concept', lambda x: x[x.first_valid_index()] if x.first_valid_index() else None),
        geometry=('geometry', 'first'),
        pop_est=('pop_est', 'first'),
        gdp_md_est=('gdp_md_est', 'first'),
        continent=('continent', 'first'),
        country=('Geography', 'first'),
    ).reset_index();

    df_concepts_geoplot = add_zero_mentions(df_concepts_geoplot, df_worldbank)
    df_concepts_geoplot.rename(columns={"name": "Geography"})
    # Remove Antarctica and convert to geodataframe
    df_concepts_geoplot = df_concepts_geoplot[df_concepts_geoplot["country"] != "Antarctica"]
    df_concepts_geoplot = gpd.GeoDataFrame(df_concepts_geoplot)
    return df_concepts_geoplot

def create_choropleth_map(merged, concept):
    merged["binary"] = np.where(merged["Number of mentions"] > 0, f"Parties mentioning {concept}", f"Parties not mentioning {concept}")
    # where category is Non-Party, set binary to 'Non-Party'

    # create a cloropeth map with a binary indicator for whether the concept is mentioned or not

    choropleth_map = (
        alt.Chart(merged[merged["Concept"] == concept])
        .mark_geoshape(stroke="black", strokeWidth=1)
        .encode(
            color=alt.Color(
                "binary:N",
                scale=alt.Scale(domain=[f"Parties mentioning {concept}", f"Parties not mentioning {concept}"], range=["darkblue", "lightgrey"]),
                legend=alt.Legend(title="Mentioned"),
            ),
            tooltip=["country:N", "pop_est:N", "gdp_md_est:N", "continent:N", "Number of mentions:Q"],
        )
        .properties(
            width=800,
            height=400,
        )
    )
    return choropleth_map

def create_stacked_chart(df):
    if df['Concept'].nunique() == 1:
        bar_chart = alt.Chart(df).mark_bar().encode(
            alt.Y('Author Type:N'),
            alt.X('count:Q', axis=alt.Axis(title='Total number')),
            alt.Color('Author Type:N', scale=alt.Scale(domain=['Party', 'Non-Party'], range=['darkblue', 'lightblue']), legend=alt.Legend(title="Author Type")),
            alt.Column('Concept:N')
        ).properties(width=400)
    else:
        concepts = df['Concept'].unique()

        # Define an empty list to hold each individual chart
        charts = []

        # Loop over the concepts and create a chart for each one
        for concept in concepts:
            # Subset df for the current concept
            df_subset = df[df['Concept'] == concept]

            # Create the chart for the current concept
            chart = alt.Chart(df_subset).mark_bar().encode(
                alt.Y('Author Type:N', title=None),
                alt.X('count:Q', axis=alt.Axis(title='Total number')),
                alt.Color('Author Type:N', scale=alt.Scale(domain=['Party', 'Non-Party'], range=['darkblue', 'lightblue']), legend=alt.Legend(title="Author Type"))
            ).properties(title=f'Concept: {concept}', width=400)

            # Append the chart to the list of charts
            charts.append(chart)

        # Vertically stack all the charts
        bar_chart = alt.vconcat(*charts)

    return bar_chart

def extract_ngrams(df, concept, n, text_col="processed_sentence"):
    # Filter the DataFrame for the given concept
    concept_df = df[df["type"] == concept]

    # Tokenize the sentences and extract n-grams
    tokens = [word_tokenize(sentence) for sentence in concept_df[text_col]]
    ngram_list = [ngram for sentence in tokens for ngram in ngrams(sentence, n)]

    # Filter out n-grams containing non-word characters
    word_ngrams = [
        ngram for ngram in ngram_list if all(re.match(r"^\w+$", word) for word in ngram)
    ]

    # Calculate the frequency distribution of n-grams1
    freq_dist = FreqDist(word_ngrams)

    return freq_dist

def plot_ngrams(df_spans):
    concepts = df_spans['type'].unique()

    # Set the number of top bigrams and trigrams to display
    num_top_ngrams = 10

    for conc in concepts:
        display(
            Markdown(
                f"## Top {num_top_ngrams} bigrams and trigrams (frequent word combinations) relating to {conc.title().replace('_',' ')} across UNFCCC input documents\n"
            )
        )

        # Extract bigrams and trigrams for the given concept
        bigrams_freq = extract_ngrams(df_spans, conc, n=2, text_col="processed_sentence")
        trigrams_freq = extract_ngrams(df_spans, conc, n=3, text_col="processed_sentence")

        # create a single DataFrame with the bigrams and trigrams
        ngrams_df = pd.DataFrame(
            bigrams_freq.most_common(num_top_ngrams), columns=["Total", "Total Bigrams"]
        )
        ngrams_df["trigram"] = [
            trigram for trigram, _ in trigrams_freq.most_common(num_top_ngrams)
        ]
        ngrams_df["Total Trigrams"] = [
            count for _, count in trigrams_freq.most_common(num_top_ngrams)
        ]

        # # Create DataFrames for bigrams and trigrams
        # bigrams_df = pd.DataFrame(bigrams_freq.most_common(num_top_ngrams), columns=['Bigrams', 'Frequency'])
        # trigrams_df = pd.DataFrame(trigrams_freq.most_common(num_top_ngrams), columns=['Trigrams', 'Frequency'])

        display(ngrams_df)

def plot_submission_type_frequencies(df_concepts_processed, formatted_concept, n=5):
    df=df_concepts_processed.groupby('Submission Type').document_id.nunique().reset_index()

    # Creating the chart
    chart = alt.Chart(df[0:n]).mark_bar(color='#3CD1A9').encode(
        y=alt.Y('Submission Type:N', sort='-x', title='Document Type'),
        x=alt.X('document_id:Q',title='Number of documents'),
    )
    chart = chart.properties(title=f"Top 5 UNFCCC input document types that mention {formatted_concept}")

    return chart



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


