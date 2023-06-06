from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

CONCEPTS_TO_INDEX: set[str] = {
    "adaptation",
    "barriers-and-challenges",
    "capacity-building",
    "climate-related-hazards",
    "deforestation",
    "equity-and-just-transition",
    "financial-flows",
    "fossil-fuels",
    "good-practice-and-opportunities",
    "greenhouse-gases",
    "international-cooperation",
    "loss-and-damage",
    "mitigation",
    "policy-instruments",
    "renewables",
    "response-measures",
    "sectors",
    "technologies-br-adaptation-br",
    "technologies-br-mitigation-br",
    "vulnerable-groups",
}
FULL_PASSAGE_CONCEPTS: set[str] = {
    "sectors",
    "policy-instruments",
}  # Concepts which annoatate each full passage rather than a span within it
PARTIAL_PASSAGE_CONCEPTS_TO_INDEX: set[str] = CONCEPTS_TO_INDEX - FULL_PASSAGE_CONCEPTS
FULL_PASSAGE_CONCEPTS_TO_INDEX: set[str] = CONCEPTS_TO_INDEX & FULL_PASSAGE_CONCEPTS
