import { useState } from 'react';
import axios from 'axios';
import "./fileUploader.css";

function FileUpload() {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [ocrResult, setOcrResult] = useState(''); // State to hold OCR results
    const [error, setError] = useState('');

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
        // Reset messages and results on new file selection
        setMessage('');
        setOcrResult('');
        setError('');
    };

    const handleUpload = async () => {
        if (file) {
            setLoading(true);
            const formData = new FormData();
            formData.append('file', file);

            try {
                const response = await axios.post('http://localhost:5000/uploads', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                });
                // Assuming the server responds with JSON that includes OCR insights
                setMessage('File successfully uploaded!');
                setOcrResult(response.data.insights); // Display OCR results
                setLoading(false);
            } catch (error) {
                console.error(error);
                setError('An error occurred while uploading the file.');
                setLoading(false);
            }
        }
    };

    return (
        <div className="file-upload-container">
            <input id="file" type="file" className="file-input" onChange={handleFileChange} />
            <label htmlFor="file" className="file-input-label">Choose a file</label>
            <button onClick={handleUpload} className="upload-button" disabled={loading}>
                {loading ? 'Uploading...' : 'Upload'}
            </button>
            {message && <div className="upload-message">{message}</div>}
            {ocrResult && <div className="upload-result">{ocrResult}</div>} {/* Display OCR results */}
            {error && <div className="upload-error">{error}</div>}
        </div>
    );
}

export default FileUpload;
