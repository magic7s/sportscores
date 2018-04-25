# Sport Scores via RSS
## AWS Lambda Function with API Gateway

A terraform template to spin up an API Gateway and Lambda function with a vanity URL.
If you modify the lambda_function.py code, you need to re-zip the file. Terraform will detect a change in the zip file and re-upload to the lambda function. 

```
declare -x PYTHONPATH="./.pip:"
pip3.6 install pytz -t .pip
zip sportscores.zip lambda_function.py
cd .pip; zip -r ../sportscores.zip ./ -x \*.pyc; cd ..
cd terraform
terraform init
terraform plan
terrafrom apply
curl -L "https://your_domain_name/scores"
curl -L "https://your_domain_name/scores?sport=MLB&team=Giants&tz=US/Pacific"
```

If you change the code after deployment.
```
zip sportscores.zip lambda_function.py
cd terraform
terraform plan
terrafrom apply
```