const fileInput = document.getElementById('pdfFile');
const uploadBtn = document.getElementById('upload-button');
const anchorResult = document.getElementById('link-result');

function resetState() {
  uploadBtn.removeAttribute('disabled');
  uploadBtn.querySelector('.spinner-grow').classList.add('visually-hidden');
  uploadBtn.querySelector('[role="status"]').value = 'Upload';
}

function handleUpload() {
  uploadBtn.setAttribute('disabled', 'disabled');
  uploadBtn.querySelector('.spinner-grow').classList.remove('visually-hidden');
  uploadBtn.querySelector('[role="status"]').value = 'Uploading...';

  anchorResult.classList.add('disabled');
  anchorResult.href = '';

  const file = fileInput.files[0];

  if (!file) {
    alert('Please select a PDF file to upload.');
    resetState();
    return;
  }

  const formData = new FormData();
  formData.append('pdf_file', file);

  fetch('/tesseract/pdf-to-ocr', {
    method: 'POST',
    body: formData,
  })
    .then(async (response) => {
      if (response.ok) {
        const res = await response.json();

        anchorResult.href = res.document;
        anchorResult.classList.remove('disabled');
      } else {
        throw new Error('Failed to upload file.');
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      alert('Failed to upload file.');
    });

  const resultarea = document.getElementById('resultarea');
  resultarea.value = 'extracting text from pdf ...';

  fetch('/tesseract/pdf-to-text', {
    method: 'POST',
    body: formData,
  })
    .then(async (response) => {
      if (response.ok) {
        console.log('File uploaded successfully!');
        // Lakukan tindakan selanjutnya setelah pengunggahan selesai
        const res = await response.json();

        if (Array.isArray(res.extracted_text)) {
          resultarea.value = res.extracted_text.join();
        } else {
          resultarea.value = res.extracted_text;
        }
      } else {
        throw new Error('Failed to upload file.');
      }
    })
    .catch((error) => {
      console.error('Error:', error);
      resultarea.value = 'error: unable to extracting text from pdf';
    })
    .finally(() => {
      uploadBtn.removeAttribute('disabled');
      uploadBtn.querySelector('.spinner-grow').classList.add('visually-hidden');
      uploadBtn.querySelector('[role="status"]').value = 'Upload';
    });
}
