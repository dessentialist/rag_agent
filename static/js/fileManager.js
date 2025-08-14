// File management functionality for BigChat

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const fileUploadForm = document.getElementById('file-upload-form');
    const fileInput = document.getElementById('file-input');
    const fileUploadArea = document.querySelector('.file-upload-area');
    const pineconeFileList = document.querySelector('.pinecone-file-list');
    const fileList = document.querySelector('.pinecone-file-list'); // Use pineconeFileList as fileList
    const uploadProgressContainer = document.getElementById('upload-progress-container');
    const uploadProgressBar = document.getElementById('upload-progress-bar');
    const uploadStatusMessage = document.getElementById('upload-status-message');
    const searchButton = document.getElementById('search-button');
    
    // Configure Marked.js for markdown rendering
    marked.setOptions({
        renderer: new marked.Renderer(),
        highlight: function(code, language) {
            const validLanguage = hljs.getLanguage(language) ? language : 'plaintext';
            return hljs.highlight(validLanguage, code).value;
        },
        pedantic: false,
        gfm: true,
        breaks: true,
        sanitize: false,
        smartLists: true,
        smartypants: false,
        xhtml: false
    });
    
    // Event listeners
    if (fileUploadForm) {
        fileUploadForm.addEventListener('submit', handleFileUpload);
    }
    
    if (fileUploadArea) {
        fileUploadArea.addEventListener('click', () => fileInput.click());
        fileUploadArea.addEventListener('dragover', handleDragOver);
        fileUploadArea.addEventListener('drop', handleDrop);
    }
    
    // Delete All button
    const deleteAllBtn = document.getElementById('delete-all-btn');
    if (deleteAllBtn) {
        deleteAllBtn.addEventListener('click', deleteAllFiles);
    }
    
    // Sync knowledge base button
    const syncKbBtn = document.getElementById('sync-kb-btn');
    if (syncKbBtn) {
        syncKbBtn.addEventListener('click', syncKnowledgeBase);
    }
    
    // Search input
    const fileSearch = document.getElementById('file-search');
    if (fileSearch) {
        fileSearch.addEventListener('input', function() {
            filterPineconeDocuments(this.value.toLowerCase());
        });
        
        fileSearch.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                filterPineconeDocuments(this.value.toLowerCase());
            }
        });
    }
    
    // Search button
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            if (fileSearch) {
                filterPineconeDocuments(fileSearch.value.toLowerCase());
            }
        });
    }
    
    // Load Pinecone documents on page load
    loadPineconeDocuments();
    
    // Load files on page load
    loadFiles();
    
    // Handle file upload form submission
    async function handleFileUpload(event) {
        event.preventDefault();
        
        const files = fileInput.files;
        
        if (!files || files.length === 0) {
            showUploadStatus('error', 'Please select at least one file');
            return;
        }
        
        // Check if we're using the bulk upload API or single file uploads
        if (files.length > 1) {
            // Multiple files - process sequentially
            uploadMultipleFiles(files);
        } else {
            // Single file - use the existing API
            uploadSingleFile(files[0]);
        }
    }
    
    // Process multiple files sequentially
    async function uploadMultipleFiles(files) {
        // Initialize progress tracking
        let totalFiles = files.length;
        let uploadedFiles = 0;
        let failedFiles = 0;
        let successfulFiles = [];
        
        // Show progress container
        uploadProgressContainer.classList.remove('d-none');
        uploadProgressBar.style.width = '0%';
        uploadProgressBar.setAttribute('aria-valuenow', 0);
        uploadStatusMessage.textContent = `Uploading ${totalFiles} files (0/${totalFiles})...`;
        
        // Process files sequentially to avoid overwhelming the server
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            
            // Check file extension
            const fileExtension = file.name.split('.').pop().toLowerCase();
            if (!['txt', 'json', 'md', 'jsonl', 'csv'].includes(fileExtension)) {
                console.warn(`Skipping file ${file.name}: Unsupported file type`);
                failedFiles++;
                continue;
            }
            
            // Update status message
            uploadStatusMessage.textContent = `Uploading ${file.name} (${i+1}/${totalFiles})...`;
            
            try {
                // Upload the file
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch('/api/files/upload', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    uploadedFiles++;
                    successfulFiles.push(file.name);
                    
                    // Update progress
                    const percentComplete = Math.round((uploadedFiles / totalFiles) * 100);
                    uploadProgressBar.style.width = percentComplete + '%';
                    uploadProgressBar.setAttribute('aria-valuenow', percentComplete);
                } else {
                    failedFiles++;
                    console.error(`Failed to upload ${file.name}`);
                }
            } catch (error) {
                failedFiles++;
                console.error(`Error uploading ${file.name}:`, error);
            }
        }
        
        // All files processed - update status
        if (failedFiles === 0) {
            showUploadStatus('success', `Successfully uploaded ${uploadedFiles} files to the RAG database.`);
        } else if (uploadedFiles === 0) {
            showUploadStatus('error', `Failed to upload all ${totalFiles} files. Please try again.`);
        } else {
            showUploadStatus('warning', `Uploaded ${uploadedFiles} files, but ${failedFiles} files failed.`);
        }
        
        // Refresh the file list and clear the input
        loadFiles();
        fileInput.value = '';
    }
    
    // Upload a single file using XHR for progress tracking
    function uploadSingleFile(file) {
        // Check file extension
        const fileExtension = file.name.split('.').pop().toLowerCase();
        if (!['txt', 'json', 'md', 'jsonl', 'csv'].includes(fileExtension)) {
            showUploadStatus('error', 'Unsupported file type. Please upload files with .txt, .json, .md, .jsonl, or .csv extensions.');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        // Show progress container
        uploadProgressContainer.classList.remove('d-none');
        uploadProgressBar.style.width = '0%';
        uploadProgressBar.setAttribute('aria-valuenow', 0);
        uploadStatusMessage.textContent = `Uploading ${file.name}...`;
        
        try {
            const xhr = new XMLHttpRequest();
            
            // Progress handler
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percentComplete = Math.round((e.loaded / e.total) * 100);
                    uploadProgressBar.style.width = percentComplete + '%';
                    uploadProgressBar.setAttribute('aria-valuenow', percentComplete);
                }
            });
            
            // Setup completion handler
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        showUploadStatus('success', `Upload successful: ${file.name} has been added to the RAG database.`);
                        loadFiles(); // Refresh the file list
                        fileInput.value = ''; // Clear the file input
                    } else {
                        showUploadStatus('error', 'Upload failed. Please try again or contact support.');
                    }
                }
            };
            
            // Send the request
            xhr.open('POST', '/api/files/upload', true);
            xhr.send(formData);
            
        } catch (error) {
            console.error('Error:', error);
            showUploadStatus('error', 'Upload failed. Please try again or contact support.');
        }
    }
    
    // Handle file drag over
    function handleDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        fileUploadArea.classList.add('border-primary');
    }
    
    // Handle file drop
    function handleDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        fileUploadArea.classList.remove('border-primary');
        
        if (event.dataTransfer.files.length) {
            fileInput.files = event.dataTransfer.files;
            
            // Add a message about multiple files if applicable
            if (event.dataTransfer.files.length > 1) {
                uploadStatusMessage.textContent = `${event.dataTransfer.files.length} files selected`;
                uploadProgressContainer.classList.remove('d-none');
            }
            
            handleFileUpload(new Event('submit'));
        }
    }
    
    // Show upload status message
    function showUploadStatus(type, message) {
        uploadProgressContainer.classList.remove('d-none');
        uploadStatusMessage.textContent = message;
        
        // Reset classes first
        uploadProgressBar.classList.remove('bg-success', 'bg-danger', 'bg-warning');
        
        if (type === 'success') {
            uploadProgressBar.classList.add('bg-success');
            uploadProgressBar.style.width = '100%';
            uploadProgressBar.setAttribute('aria-valuenow', 100);
            
            // Hide after 5 seconds
            setTimeout(() => {
                uploadProgressContainer.classList.add('d-none');
            }, 5000);
        } else if (type === 'error') {
            uploadProgressBar.classList.add('bg-danger');
            uploadProgressBar.style.width = '100%';
            uploadProgressBar.setAttribute('aria-valuenow', 100);
        } else if (type === 'warning') {
            uploadProgressBar.classList.add('bg-warning');
            uploadProgressBar.style.width = '100%';
            uploadProgressBar.setAttribute('aria-valuenow', 100);
            
            // Hide after 8 seconds
            setTimeout(() => {
                uploadProgressContainer.classList.add('d-none');
            }, 8000);
        }
    }
    
    // Load files from the server
    async function loadFiles() {
        if (!fileList) return;
        
        try {
            const response = await fetch('/api/files');
            
            if (!response.ok) {
                throw new Error('Failed to load files');
            }
            
            const data = await response.json();
            
            // Clear current list
            fileList.innerHTML = '';
            
            if (data.files.length === 0) {
                const noFilesElement = document.createElement('div');
                noFilesElement.className = 'text-center p-4';
                noFilesElement.textContent = 'No files uploaded yet.';
                fileList.appendChild(noFilesElement);
                return;
            }
            
            // Add files to the list
            data.files.forEach(file => {
                const fileItem = document.createElement('div');
                fileItem.className = 'file-item d-flex justify-content-between align-items-center';
                
                const fileInfo = document.createElement('div');
                fileInfo.innerHTML = `
                    <div class="fw-bold">${file.filename}</div>
                    <div class="text-muted small">
                        ${formatFileSize(file.size)} • ${file.file_type} • 
                        ${new Date(file.created_at).toLocaleString()}
                    </div>
                `;
                
                const fileActions = document.createElement('div');
                const viewButton = document.createElement('button');
                viewButton.className = 'btn btn-sm btn-outline-secondary me-2';
                viewButton.innerHTML = '<i class="bi bi-eye"></i> View';
                viewButton.addEventListener('click', () => viewFile(file.id));
                
                const deleteButton = document.createElement('button');
                deleteButton.className = 'btn btn-sm btn-outline-danger';
                deleteButton.innerHTML = '<i class="bi bi-trash"></i> Delete';
                deleteButton.addEventListener('click', () => deleteFile(file.id, file.filename));
                
                fileActions.appendChild(viewButton);
                fileActions.appendChild(deleteButton);
                
                fileItem.appendChild(fileInfo);
                fileItem.appendChild(fileActions);
                fileList.appendChild(fileItem);
            });
            
            // After loading files, also load the Pinecone documents
            loadPineconeDocuments();
        } catch (error) {
            console.error('Error:', error);
            fileList.innerHTML = '<div class="alert alert-danger">Failed to load files. Please refresh the page.</div>';
        }
    }
    
    // Load Pinecone document information
    async function loadPineconeDocuments() {
        const pineconeFileList = document.querySelector('.pinecone-file-list');
        if (!pineconeFileList) return;
        
        try {
            // Show loading indicator
            pineconeFileList.innerHTML = `
                <div class="text-center p-4">
                    <div class="spinner-border spinner-border-sm" role="status" style="color: var(--bigid-purple);">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading Pinecone documents...</p>
                </div>
            `;
            
            const response = await fetch('/api/files/sync', {
                method: 'GET'
            });
            
            if (!response.ok) {
                throw new Error('Failed to retrieve Pinecone information');
            }
            
            const data = await response.json();
            
            // Clear the loading indicator
            pineconeFileList.innerHTML = '';
            
            if (!data.documents || data.documents.length === 0) {
                pineconeFileList.innerHTML = `
                    <div class="text-center p-4">
                        <p>No documents found in Pinecone vector database.</p>
                    </div>
                `;
                return;
            }
            
            // Add a header row with info about Pinecone
            const infoRow = document.createElement('div');
            infoRow.className = 'alert alert-info m-3';
            infoRow.innerHTML = `
                <i class="bi bi-info-circle-fill"></i> 
                Pinecone contains ${data.stats.total_chunks} chunks from ${data.stats.unique_files} documents
            `;
            pineconeFileList.appendChild(infoRow);
            
            // Add documents to the list
            data.documents.forEach(doc => {
                const docItem = document.createElement('div');
                docItem.className = 'file-item d-flex justify-content-between align-items-center';
                
                const docInfo = document.createElement('div');
                docInfo.innerHTML = `
                    <div class="fw-bold">${doc.filename}</div>
                    <div class="text-muted small">
                        <span class="badge bg-primary rounded-pill">${doc.chunks} chunks</span>
                        <span class="text-muted ms-2">Source ID: ${doc.file_id.substring(0, 8)}...</span>
                    </div>
                `;
                
                const docActions = document.createElement('div');
                const viewButton = document.createElement('button');
                viewButton.className = 'btn btn-sm btn-outline-secondary me-2';
                viewButton.innerHTML = '<i class="bi bi-eye"></i> View';
                viewButton.addEventListener('click', () => viewFile(doc.file_id));
                
                const deleteButton = document.createElement('button');
                deleteButton.className = 'btn btn-sm btn-outline-danger';
                deleteButton.innerHTML = '<i class="bi bi-trash"></i> Delete';
                deleteButton.addEventListener('click', () => deleteFile(doc.file_id, doc.filename));
                
                docActions.appendChild(viewButton);
                docActions.appendChild(deleteButton);
                
                docItem.appendChild(docInfo);
                docItem.appendChild(docActions);
                pineconeFileList.appendChild(docItem);
            });
        } catch (error) {
            console.error('Error:', error);
            pineconeFileList.innerHTML = `
                <div class="alert alert-danger m-3">
                    Failed to load Pinecone documents. 
                    <button class="btn btn-sm btn-outline-primary ms-2" onclick="loadPineconeDocuments()">
                        <i class="bi bi-arrow-repeat"></i> Retry
                    </button>
                </div>
            `;
        }
    }
    
    // Format file size
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
        else return (bytes / 1048576).toFixed(1) + ' MB';
    }
    
    // View file details
    async function viewFile(fileId) {
        try {
            const response = await fetch(`/api/files/${fileId}`);
            
            if (!response.ok) {
                throw new Error('Failed to load file');
            }
            
            const data = await response.json();
            
            // Create modal to display file details
            const modal = document.createElement('div');
            modal.className = 'modal fade';
            modal.id = 'fileViewModal';
            modal.setAttribute('tabindex', '-1');
            modal.innerHTML = `
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${data.file.filename}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <strong>Type:</strong> ${data.file.file_type}
                                <br>
                                <strong>Size:</strong> ${formatFileSize(data.file.size)}
                                <br>
                                <strong>Uploaded:</strong> ${new Date(data.file.created_at).toLocaleString()}
                            </div>
                            <h6>Content Preview:</h6>
                            ${data.file.file_type === 'md' 
                                ? `<div class="markdown-content p-3 rounded border" style="max-height: 500px; overflow-y: auto;">${marked.parse(data.content.substring(0, 5000))}${data.content.length > 5000 ? '<p><em>Content truncated for preview...</em></p>' : ''}</div>`
                                : `<pre class="bg-dark text-light p-3 rounded" style="max-height: 300px; overflow-y: auto;">${data.content.substring(0, 2000)}${data.content.length > 2000 ? '...' : ''}</pre>`
                            }
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Show the modal
            const bsModal = new bootstrap.Modal(modal);
            bsModal.show();
            
            // Clean up when modal is hidden
            modal.addEventListener('hidden.bs.modal', function() {
                document.body.removeChild(modal);
            });
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to load file details');
        }
    }
    
    // Delete file
    async function deleteFile(fileId, filename) {
        const confirmed = confirm(`Are you sure you want to delete "${filename}"?`);
        
        if (!confirmed) return;
        
        try {
            const response = await fetch(`/api/files/${fileId}`, {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete file');
            }
            
            loadFiles(); // Refresh the file list
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to delete file');
        }
    }
    
    // Delete all files
    async function deleteAllFiles() {
        const confirmed = confirm("Are you sure you want to delete ALL files? This action cannot be undone and will remove ALL corresponding data in the Pinecone database.");
        
        if (!confirmed) return;
        
        try {
            const response = await fetch('/api/files/all', {
                method: 'DELETE'
            });
            
            if (!response.ok) {
                throw new Error('Failed to delete all files');
            }
            
            const data = await response.json();
            alert(`Success! ${data.count} files have been deleted.`);
            loadFiles(); // Refresh the file list
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to delete all files. Please try again or contact support.');
        }
    }
    
    // Refresh Pinecone document information
    async function syncKnowledgeBase() {
        try {
            // Show progress indication
            showUploadStatus('warning', 'Refreshing Pinecone document information...');
            
            // Call the loadPineconeDocuments function to refresh the list
            await loadPineconeDocuments();
            
            // Show success message
            showUploadStatus('success', 'Pinecone document information refreshed');
        } catch (error) {
            console.error('Error:', error);
            showUploadStatus('error', 'Failed to refresh Pinecone document information. Please try again.');
        }
    }
    
    // Filter Pinecone documents based on search query
    function filterPineconeDocuments(query) {
        const pineconeFileList = document.querySelector('.pinecone-file-list');
        if (!pineconeFileList) return;
        
        const fileItems = pineconeFileList.querySelectorAll('.file-item');
        
        if (fileItems.length === 0) return;
        
        let hasVisibleItems = false;
        query = query.toLowerCase();
        
        fileItems.forEach(item => {
            const fileNameElement = item.querySelector('.fw-bold');
            if (!fileNameElement) return;
            
            const fileName = fileNameElement.textContent.toLowerCase();
            const fileMetadata = item.querySelector('.text-muted')?.textContent.toLowerCase() || '';
            
            if (fileName.includes(query) || fileMetadata.includes(query)) {
                item.style.display = '';
                hasVisibleItems = true;
            } else {
                item.style.display = 'none';
            }
        });
        
        // Show "no results" message if no documents match the search
        const noResultsMessage = pineconeFileList.querySelector('.no-results-message');
        
        if (!hasVisibleItems && query !== '') {
            if (!noResultsMessage) {
                const message = document.createElement('div');
                message.className = 'no-results-message text-center p-4';
                message.textContent = 'No documents match your search criteria.';
                pineconeFileList.appendChild(message);
            } else {
                noResultsMessage.style.display = '';
            }
        } else if (noResultsMessage) {
            noResultsMessage.style.display = 'none';
        }
    }
});
