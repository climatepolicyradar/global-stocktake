from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

CONCEPTS_TO_INDEX: set[str] = {
    "technologies",
    "renewables",
    "fossil-fuels",
    "vulnerable-groups",
    "challenges-and-opportunities",
    "financial-flows",
    "climate-related-hazards",
    "equity-and-justice",
    "deforestation",
    "greenhouse-gases",
    "mitigation",
    "adaptation",
    "loss-and-damage",
    "sectors",
    "policy-instruments",
}
FULL_PASSAGE_CONCEPTS: set[str] = {
    "sectors",
    "policy-instruments",
}  # Concepts which annoatate each full passage rather than a span within it
PARTIAL_PASSAGE_CONCEPTS_TO_INDEX: set[str] = CONCEPTS_TO_INDEX - FULL_PASSAGE_CONCEPTS
FULL_PASSAGE_CONCEPTS_TO_INDEX: set[str] = CONCEPTS_TO_INDEX & FULL_PASSAGE_CONCEPTS
