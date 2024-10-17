from flask import Flask, request, jsonify
import boto3
import requests
import os
from werkzeug.utils import secure_filename
import uuid
import json

app = Flask(__name__)

# Configurações do AWS S3 e DynamoDB
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('ImageUploads')

BUCKET_NAME = 'your-s3-bucket-name'

# Pasta onde as imagens serão temporariamente salvas
UPLOAD_FOLDER = '/tmp/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Rota para fazer o upload de uma imagem
@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({"error": "Nenhuma imagem enviada"}), 400

    image = request.files['image']
    if image.filename == '':
        return jsonify({"error": "Nenhuma imagem selecionada"}), 400

    # Salva a imagem com um nome seguro
    filename = secure_filename(image.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)

    # Gera um ID único para a imagem e faz o upload para o S3
    image_id = str(uuid.uuid4())
    s3.upload_file(filepath, BUCKET_NAME, image_id + '/' + filename)

    # Remove o arquivo local depois do upload
    os.remove(filepath)

    # Registra o upload no DynamoDB
    table.put_item(
        Item={
            'image_id': image_id,
            'filename': filename,
            'status': 'uploaded',
            'result': None
        }
    )

    # Chama a função Lambda para iniciar a detecção de objetos
    invoke_lambda(image_id, filename)

    return jsonify({"message": "Imagem enviada com sucesso!", "image_id": image_id}), 201

# Função para invocar a Lambda que processa a imagem
def invoke_lambda(image_id, filename):
    lambda_client = boto3.client('lambda')
    event = {
        "bucket": BUCKET_NAME,
        "image_id": image_id,
        "filename": filename
    }
    lambda_client.invoke(
        FunctionName='ObjectDetectionFunction',
        InvocationType='Event',
        Payload=json.dumps(event)
    )

# Rota para obter o resultado da detecção de objetos
@app.route('/results/<image_id>', methods=['GET'])
def get_result(image_id):
    try:
        response = table.get_item(Key={'image_id': image_id})
        item = response.get('Item', {})
        if not item:
            return jsonify({"error": "Imagem não encontrada"}), 404
        return jsonify({"image_id": image_id, "result": item.get('result')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)
