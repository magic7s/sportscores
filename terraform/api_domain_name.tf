variable "r53domain_name" { default = "magic7s.com." }
variable "custom_domain_name" { default = "api.magic7s.com" }

provider "aws" {
  alias  = "us-east-1"
  # Use keys in home dir.
  #  access_key = "ACCESS_KEY_HERE"
  #  secret_key = "SECRET_KEY_HERE"
  region = "us-east-1"
}

data "aws_route53_zone" "myzone" {
  name         = "${var.r53domain_name}"
  private_zone = false
}

resource "aws_acm_certificate" "cert" {
  provider = "aws.us-east-1"
  domain_name = "${var.custom_domain_name}"
  validation_method = "DNS"
}

resource "aws_route53_record" "cert_validation" {
  name = "${aws_acm_certificate.cert.domain_validation_options.0.resource_record_name}"
  type = "${aws_acm_certificate.cert.domain_validation_options.0.resource_record_type}"
  zone_id = "${data.aws_route53_zone.myzone.id}"
  records = ["${aws_acm_certificate.cert.domain_validation_options.0.resource_record_value}"]
  ttl = 60
}

resource "aws_acm_certificate_validation" "cert" {
  provider = "aws.us-east-1"
  certificate_arn = "${aws_acm_certificate.cert.arn}"
  validation_record_fqdns = ["${aws_route53_record.cert_validation.fqdn}"]
}

resource "aws_api_gateway_domain_name" "api_domain_name" {
  domain_name = "${var.custom_domain_name}"

  certificate_arn  = "${aws_acm_certificate_validation.cert.certificate_arn}"
}

resource "aws_route53_record" "api" {
  zone_id = "${data.aws_route53_zone.myzone.zone_id}"

  name = "${aws_api_gateway_domain_name.api_domain_name.domain_name}"
  type = "A"

  alias {
    name                   = "${aws_api_gateway_domain_name.api_domain_name.cloudfront_domain_name}"
    zone_id                = "${aws_api_gateway_domain_name.api_domain_name.cloudfront_zone_id}"
    evaluate_target_health = true
  }
}
