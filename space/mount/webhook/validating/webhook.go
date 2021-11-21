package validating

import (
	"context"
	"fmt"
	"log"

	"github.com/slok/kubewebhook/pkg/webhook"
	adv1beta1 "k8s.io/api/admission/v1beta1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

	"digi.dev/digi/space/mount/webhook/util"
)

// WebhookConfig is the Validating webhook configuration.
type WebhookConfig struct {
	// Name is the name of the webhook.
	Name string
	// Object is the object of the webhook, to use multiple types on the same webhook or
	// type inference, don't set this field (will be `nil`).
	Obj metav1.Object
}

func (c *WebhookConfig) validate() error {
	errs := ""

	if c.Name == "" {
		errs = errs + "name can't be empty"
	}

	if errs != "" {
		return fmt.Errorf("invalid configuration: %s", errs)
	}

	return nil
}

// NewWebhook is a validating webhook and will return a webhook ready for a type of resource
// it will validate the received resources.
func NewWebhook(cfg WebhookConfig, validator Validator) (webhook.Webhook, error) {
	if err := cfg.validate(); err != nil {
		return nil, err
	}

	// Create our webhook and wrap for instrumentation (metrics and tracing).
	return &validateWebhook{
		validator: validator,
		cfg:       cfg,
	}, nil
}

type validateWebhook struct {
	validator Validator
	cfg       WebhookConfig
}

func (w validateWebhook) Review(ctx context.Context, ar *adv1beta1.AdmissionReview) *adv1beta1.AdmissionResponse {
	log.Printf("reviewing request %s, named: %s/%s", ar.Request.UID, ar.Request.Namespace, ar.Request.Name)

	res, err := w.validator.Validate(ctx, ar)
	if err != nil {
		return w.toAdmissionErrorResponse(ar, err)
	}

	var status string
	if res.Valid {
		status = metav1.StatusSuccess
	}

	// Forge response.
	return &adv1beta1.AdmissionResponse{
		UID:     ar.Request.UID,
		Allowed: res.Valid,
		Result: &metav1.Status{
			Status:  status,
			Message: res.Message,
		},
	}
}

func (w validateWebhook) toAdmissionErrorResponse(ar *adv1beta1.AdmissionReview, err error) *adv1beta1.AdmissionResponse {
	return util.ToAdmissionErrorResponse(ar.Request.UID, err)
}
