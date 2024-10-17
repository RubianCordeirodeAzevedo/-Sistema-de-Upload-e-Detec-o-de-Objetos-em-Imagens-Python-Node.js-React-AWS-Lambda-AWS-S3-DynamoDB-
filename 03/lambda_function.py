import boto3
import json

s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('ImageUploads')

def lambda_handler(event, context):
    bucket = event['bucket']
    image_id = event['image_id']
    filename = event['filename']

    # Pega a imagem do bucket
    s3_response = s3.get_object(Bucket=bucket, Key=image_id + '/' + filename)
    image_content = s3_response['Body'].read()

    # Chama o AWS Rekognition para detectar objetos
    response = rekognition.detect_labels(
        Image={'Bytes': image_content},
        MaxLabels=10,
        MinConfidence=75
    )

    labels = [label['Name'] for label in response['Labels']]

    # Atualiza o DynamoDB com o resultado da detecção
    table.update_item(
        Key={'image_id': image_id},
        UpdateExpression="set result = :r, status = :s",
        ExpressionAttributeValues={
            ':r': labels,
            ':s': 'processed'
        }
    )

    return {
        'statusCode': 200,
        'body': json.dumps({'image_id': image_id, 'labels': labels})
    }
