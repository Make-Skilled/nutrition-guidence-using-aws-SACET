import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-west-2', endpoint_url='http://localhost:8000')
table = dynamodb.Table('MealPlans')

print('Current meal plans:')
response = table.scan()
for item in response['Items']:
    print(f"Plan: {item['plan_type']}, Day: {item['day']}")
