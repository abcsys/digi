# dict of PII categories to possible data fields
PII_Fields = {
    "name": ["name", "first_name", "last_name"],
    "geography": ["zipcode", "zip"], # TODO add logic to deal with different fields within a category requiring different processing, i.e. keep state or larger, or should we just separate these fields out in PII_fields? should PII_fields just be a list?
    # "location", "address", "city", "county", "region"
    "date": ["date", "time", "year", "ts"],
    "phone": ["phone", "phone_number", "fax", "fax_number"],
    "email": ["email", "email_address"],
    "ssn": ["ssn", "social_security_number"],
    "mrn": ["mrn", "medical_record_number"],
    "hbn": ["hbn", "hpbn", "health_plan_beneficiary_number"],
    "account": ["account", "account_number", "acct"],
    "certificate": ["certificate", "certificate_num", "license", "license_num"],
    "vehicle": ["vehicle_identifier", "vehicle_serial_number", "license_plate", "license_plate_num"],
    "device": ["device_identifier", "device_serial_number"],
    "url": ["url", "internet_url"],
    "ip": ["ip", "tcp", "ip_address"],
    "biometric": ["biometric", "biometric_identifier", "fingerprint", "voice_print"],
    "image": ["image", "photo", "photograph", "face"]
    # TODO when to do fuzzy matching in the analytics engine, soundex library
}

# list of dictionaries mapping de-id operations to zed command separators
operations = [{"drop": ", "}, {"replace": " | "}, {"trim": ", "}]

def drop(field):
    """Returns a Zed expression to drop the field FIELD.
    The full Zed command should be preceded by DROP"""
    return f"{field}"

def trim(field, digits):
    """Returns a Zed expression to trim the field FIELD to the first DIGITS of its value.
    The full Zed command shoudl be preceded by PUT"""
    return""
    return f"{field}:={str(this)[:digits]}"
    # TODO zed field should handle this digi
    # TODO preserve original type of this, add type as argument?
    # TODO generalize for first n digits or last n digits, add boolean?

def replace(field, criteria, value):
    """Returns a Zed command to replace the field FIELD with VALUE if CRITERIA is met"""
    return f"switch ( case {criteria(field)} => put {field}:={value} default => yield this )"
