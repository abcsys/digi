package validating

import (
	"context"
	admissionv1beta1 "k8s.io/api/admission/v1beta1"
)

// ValidatorResult is the result of a validator.
type ValidatorResult struct {
	Valid   bool
	Message string
}

// Validator knows how to validate the received kubernetes object.
type Validator interface {
	// Validate will received a pointer to an object, validators can be
	// grouped in chains, that's why a stop boolean to stop executing the chain
	// can be returned the validator, the valid parameter will denotate if the
	// object is valid (if not valid the chain will be stopped also) and a error.
	Validate(context.Context,  *admissionv1beta1.AdmissionReview) (valid ValidatorResult, err error)
}

// ValidatorFunc is a helper type to create validators from functions.
type ValidatorFunc func(context.Context, *admissionv1beta1.AdmissionReview) (valid ValidatorResult, err error)

// Validate satisfies Validator interface.
func (f ValidatorFunc) Validate(ctx context.Context, ar *admissionv1beta1.AdmissionReview) (valid ValidatorResult, err error) {
	return f(ctx, ar)
}

