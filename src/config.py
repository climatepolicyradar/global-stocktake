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
FULL_SPAN_CONCEPTS: set[str] = {"sectors", "policy-instruments"}
