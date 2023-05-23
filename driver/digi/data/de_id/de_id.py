from digi.data.de_id.hipaa import PII as hipaa_PII
from digi.data.de_id.ccpa import PII as ccpa_PII
from digi.data.de_id.util import operations

"""
A de_id object can be initialized with different sets of privacy rules, 
ignoring fields specified in a list of exceptions. It defaults to HIPAA compliance.
Invoking the gen() method will generate a Zed flow encompassing all specified privacy rules. 
"""

class De_id:
    def __init__(self, hipaa=True, ccpa=False, exceptions=[]):
        self.hipaa = hipaa
        self.ccpa = ccpa
        self.exceptions = exceptions
        self.PII = {}
        if self.hipaa:
            self.PII = dict(hipaa_PII)
        if self.ccpa:
            for operation in operations:
                operator = list(operation.keys())[0]
                self.PII[operator].extend(ccpa_PII[operator])

    def gen(self):
        zed_flow = ["yield this"]
        for operation in operations:
            operator = list(operation.keys())[0]
            if self.PII[operator]:
                operation_list = []
                for d in self.PII[operator]:
                    field = list(d.keys())[0]
                    if field not in self.exceptions:
                        operation_list.append(d[field])
                operation_string = operation[operator].join(operation_list)
                if operator == "drop": 
                    # TODO generalize, ex: when operator is trim, "put" needs to be added to the beginning of the operation string
                    operation_string = f"{operator} " + operation_string
            zed_flow.append(operation_string)
        return " | ".join(zed_flow)
