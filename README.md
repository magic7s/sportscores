# Sport Scores via RSS
## AWS Lambda Function with API Gateway

A terraform template to spin up an API Gateway and Lambda function with a vanity URL.
If you modify the lambda_function.py code, you need to re-zip the file. Terraform will detect a change in the zip file and re-upload to the lambda function. 

```
zip sportscores.zip lambda_function.py
cd terraform
terraform init
terraform plan
terrafrom apply
curl -L "https://your_domain_name/sportscores"
curl -L "https://your_domain_name/sportscores?sport=MLB&team=Giants&date=20180329"
```

If you change the code after deployment.
```
zip sportscores.zip lambda_function.py
cd terraform
terraform plan
terrafrom apply
```