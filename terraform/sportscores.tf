variable "aws_region_name" { default = "us-west-2" }
variable "use_api_domain_name" { default = "api.magic7s.com" }
variable "use_api_base_path" { default = "scores" }
variable "lambda_code_zip" { default = "../sportscores.zip"}

provider "aws" {
  # Use keys in home dir.
  #  access_key = "ACCESS_KEY_HERE"
  #  secret_key = "SECRET_KEY_HERE"
  region = "${var.aws_region_name}"
}

resource "aws_iam_role" "sportscores_iam_role" {
    assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "lambda_iam_role_policy" {
  name = "sportscores_iam_role_policy"
  role = "${aws_iam_role.sportscores_iam_role.id}"
  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:us-west-2:929779736070:*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": [
                "arn:aws:logs:us-west-2:929779736070:log-group:/aws/lambda/sport_scores_rss:*"
            ]
        }
    ]
}
EOF
}


resource "aws_lambda_function" "sportscores_lambda" {
  filename         = "${var.lambda_code_zip}"
  function_name    = "sport_scores_rss"
  role             = "${aws_iam_role.sportscores_iam_role.arn}"
  handler          = "lambda_function.lambda_handler"
  source_code_hash = "${base64sha256(file(var.lambda_code_zip))}"
  runtime          = "python3.6"
  tags             = { 
                     App = "sportscores"
                     }

  environment {
    variables = {
      foo = "bar"
    }
  }
}

resource "aws_api_gateway_rest_api" "sportscores_api" {
  name        = "SportScoresAPIGateway"
  description = "Sport Scores API Gateway"
}

resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = "${aws_api_gateway_rest_api.sportscores_api.id}"
  resource_id   = "${aws_api_gateway_rest_api.sportscores_api.root_resource_id}"
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = "${aws_api_gateway_rest_api.sportscores_api.id}"
  resource_id = "${aws_api_gateway_method.proxy.resource_id}"
  http_method = "${aws_api_gateway_method.proxy.http_method}"

  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "${aws_lambda_function.sportscores_lambda.invoke_arn}"
}

resource "aws_api_gateway_deployment" "sportscores_deploy" {
  depends_on = [
    "aws_api_gateway_integration.lambda"
  ]

  rest_api_id = "${aws_api_gateway_rest_api.sportscores_api.id}"
  stage_name  = "v1"
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = "${aws_lambda_function.sportscores_lambda.arn}"
  principal     = "apigateway.amazonaws.com"

  # The /*/* portion grants access from any method on any resource
  # within the API Gateway "REST API".
  source_arn = "${aws_api_gateway_deployment.sportscores_deploy.execution_arn}/*/*"
}

resource "aws_api_gateway_base_path_mapping" "sportscore_domain_name" {
  depends_on  = ["aws_api_gateway_deployment.sportscores_deploy"]
  api_id      = "${aws_api_gateway_rest_api.sportscores_api.id}"
  stage_name  = "${aws_api_gateway_deployment.sportscores_deploy.stage_name}"
  domain_name = "${var.use_api_domain_name}"
  base_path   = "${var.use_api_base_path}"
}

output "base_url" {
  value = "${aws_api_gateway_deployment.sportscores_deploy.invoke_url}"
}
output "fancy_url" {
  value = "https://${aws_api_gateway_base_path_mapping.sportscore_domain_name.domain_name}/${aws_api_gateway_base_path_mapping.sportscore_domain_name.base_path}"
  }
