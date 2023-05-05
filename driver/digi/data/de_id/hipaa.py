from digi.data.de_id.util import PII_Fields, drop, truncate, replace

"""
Defines the PII Fields relevant to the HIPAA Privacy Rule mapped to Zed functions to de-identify them.
"""

# TODO fuzzy matching
# TODO if field is substring of field, do the same function

SMALL_POP_ZIPCODES = []

PII = {}


for field in PII_Fields["name"]:
    PII[field] = drop(field)

for field in PII_Fields["geography"]:
    PII[field] = replace(field, SMALL_POP_ZIPCODES, "000") # concatenate with truncate zed command

    # do we need the functions? or utils could just return a string, not a HOF