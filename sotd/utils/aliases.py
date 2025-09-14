# Base aliases for soap field
SOAP_BASE_ALIASES = ["soap", "lather"]

# Post aliases that can be combined with soap
SOAP_POST_ALIASES = ["post", "aftershave", "a/s", "as", "splash"]

# Generate all combinations of base + post aliases
SOAP_COMBINED_ALIASES = []
for base in SOAP_BASE_ALIASES:
    for post in SOAP_POST_ALIASES:
        SOAP_COMBINED_ALIASES.append(f"{base} & {post}")

FIELD_ALIASES = {
    "razor": ["razor", "straight razor"],
    "blade": ["blade"],
    "brush": ["brush", "shaving brush"],
    "soap": SOAP_COMBINED_ALIASES + ["shaving soap"] + SOAP_BASE_ALIASES,
    # "pre-shave": ["pre-shave", "prep"],
    # "post-shave": ["post-shave"],
    # "fragrance": ["fragrance", "scent", "edp"],
}
