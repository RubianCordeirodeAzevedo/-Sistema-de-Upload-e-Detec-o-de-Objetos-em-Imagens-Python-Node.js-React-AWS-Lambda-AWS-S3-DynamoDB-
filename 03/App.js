import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [detectionResult, setDetectionResult] = useState(null);

  const handleImageChange = (e) => {
    setSelectedImage(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedImage) {
      alert('Selecione uma imagem antes de enviar.');
      return;
    }

    const formData = new FormData();
    formData.append('image', selectedImage);

    try {
      const response = await axios.post('http://localhost:5000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setUploadStatus('Upload bem-sucedido! Processando...');
      const { image_id } = response.data;
      checkResults(image_id);
    } catch (error) {
      setUploadStatus('Erro no upload. Tente novamente.');
      console.error(error);
    }
  };

  const checkResults = async (image_id) => {
    try {
      const interval = setInterval(async () => {
        const response = await axios.get(`http://localhost:5000/results/${image_id}`);
        const { result } = response.data;

        if (result) {
          clearInterval(interval);
          setDetectionResult(result);
          setUploadStatus('Processamento concluído!');
        }
      }, 3000); // Verifica a cada 3 segundos
    } catch (error) {
      console.error('Erro ao buscar resultados', error);
    }
  };

  return (
    <div className="App">
      <h1>Upload e Detecção de Objetos em Imagens</h1>

      <input type="file" onChange={handleImageChange} />
      <button onClick={handleUpload}>Enviar Imagem</button>

      <p>{uploadStatus}</p>

      {detectionResult && (
        <div>
          <h2>Resultados de Detecção</h2>
          <ul>
            {detectionResult.map((label, index) => (
              <li key={index}>{label}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
