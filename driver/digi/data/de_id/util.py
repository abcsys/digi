PII_Fields = {
    "name": ["name", "first_name", "last_name"],
    "geography": ["zipcode", "zip"], # TODO how to deal with different fields within a category requiring different processing, i.e. keep state or larger, or should we just separate these fields out in PII_fields? should PII_fields just be a list?
    # "location", "address", "city", "county", "region"
    "dates": ["date", "time", "year", "ts"],
    "phone": ["phone", "phone_number", "fax", "fax_number"],
    "email": ["email", "email_address"],
    "ssn": ["ssn", "social_security_number"],
    "mrn": ["mrn", "medical_record_number"],
    "hbn": ["hbn", "hpbn", "health_plan_beneficiary_number"],
    "account": ["account", "account_number", "acct"],
    # TODO



}

def drop(field):
    """Returns a function that generates a Zed command to drop the field FIELD"""
    def gen():
        return f"drop {field}"
    return gen

def truncate(field, digits):
    """Returns a function that generates a Zed command to truncate the field FIELD to the first DIGITS of its value"""
    def gen():
        return f"head {digits} {field}" # TODO
    return gen

def replace(field, criteria, value):
    """Returns a function that generates a Zed command to replace the field FIELD with VALUE if CRITERIA is met"""
    def gen():
        return f"switch ( case {criteria(field)} => put {field}:={value} default => yield this )" # TODO
    return gen

