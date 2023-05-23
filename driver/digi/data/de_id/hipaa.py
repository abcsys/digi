from digi.data.de_id.util import PII_Fields, operations, drop, trim, replace

"""
Defines the PII Fields relevant to the HIPAA Privacy Rule mapped to Zed functions to de-identify them.
"""

# TODO fuzzy matching
# TODO if field is substring of field, do the same function

SMALL_POP_ZIPCODES = ["036", "059", "063", "102", "203", "556", "692", "790", "821", "823", "830", "831", "878", "879", "884", "890", "893"]

# dictionary of dictionaries, mapping operation to a list of { fields to Zed commands }
PII = {}
for operation in operations:
    operator = list(operation.keys())[0]
    PII[operator] = []

drop_categories = []
drop_categories.append("name")
drop_categories.append("date")
drop_categories.append("phone")
drop_categories.append("email")
drop_categories.append("ssn")
drop_categories.append("mrn")
drop_categories.append("hbn")
drop_categories.append("account")
drop_categories.append("certificate")
drop_categories.append("vehicle")
drop_categories.append("device")
drop_categories.append("url")
drop_categories.append("ip")
drop_categories.append("biometric")
drop_categories.append("image")

# drop all fields associated with the specified categories
for category in drop_categories:
    for field in PII_Fields[category]:
        PII["drop"].append({ field: drop(field) })

# replace fields
for field in PII_Fields["geography"]:
    PII["replace"].append({field: replace(field, lambda value: value in SMALL_POP_ZIPCODES, "000")})

# # trim fields
# for field in PII_Fields["geography"]:
#   PII[field] = trim(field, 3)
