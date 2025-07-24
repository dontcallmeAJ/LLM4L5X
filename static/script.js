document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Element References ---
    const DOMElements = {
        body: document.body,
        toggleThemeButton: document.getElementById('toggleTheme'),
        settingsButton: document.getElementById('settingsButton'),
        settingsModal: document.getElementById('settingsModal'),
        ragFileNameDisplay: document.getElementById('ragFileNameDisplay'),
        ragFileInput: document.getElementById('ragFileInput'),
        browseRagFileButton: document.getElementById('browseRagFileButton'),
        uploadRagFileButton: document.getElementById('uploadRagFileButton'),
        ragUploadStatus: document.getElementById('ragUploadStatus'),
        chatWindow: document.getElementById('chatWindow'),
        inputBox: document.getElementById('inputBox'),
        enterButton: document.getElementById('enterButton'),
        attachButton: document.getElementById('attachButton'),
        fileInput: document.getElementById('fileInput')
    };

    // Destructure for easier access
    const {
        body, toggleThemeButton, settingsButton, settingsModal,
        ragFileNameDisplay, ragFileInput, browseRagFileButton,
        uploadRagFileButton, ragUploadStatus, chatWindow,
        inputBox, enterButton, attachButton, fileInput
    } = DOMElements;

    // A closure for the close button within the modal
    const closeButton = settingsModal.querySelector('.close-button');

    let attachedFile = null; // To store the currently attached file
    let lastUserMessage = ''; // To store the last message sent by the user (less critical with direct gen)

    // --- Constants for Status Messages ---
    const STATUS_CLASSES = {
        info: 'modal-status-message info',
        success: 'modal-status-message success',
        error: 'modal-status-message error',
        default: 'modal-status-message'
    };

    // --- Helper Functions ---

    /**
     * Updates the status message in the settings modal.
     * @param {string} message - The message to display.
     * @param {string} type - 'info', 'success', 'error', or 'default'.
     */
    function updateRagUploadStatus(message, type = 'default') {
        ragUploadStatus.textContent = message;
        ragUploadStatus.className = STATUS_CLASSES[type] || STATUS_CLASSES.default;
    }

    /**
     * Resets the RAG file input and status in the settings modal.
     */
    function resetRagFileInput() {
        ragUploadStatus.textContent = '';
        ragUploadStatus.className = STATUS_CLASSES.default;
        ragFileNameDisplay.value = '';
        ragFileInput.value = ''; // Clear actual file input
        uploadRagFileButton.disabled = true;
        browseRagFileButton.disabled = false;
    }

    /**
     * Scrolls the chat window to the bottom.
     */
    function scrollToBottom() {
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    /**
     * Helper function to trigger file download, capable of handling Blob or base64 content.
     * @param {object} downloadInfo - An object containing file download details.
     * Can have:
     * - {string} file_content: Base64 encoded string or raw text content.
     * - {string} file_name: Desired filename for the download.
     * - {string} content_type: The MIME type of the file (e.g., 'application/xml').
     * - {string} [encoding]: Optional, "base64" if file_content is base64 encoded.
     * OR directly a Blob object:
     * - {Blob} blob: The Blob object to download.
     * - {string} file_name: Desired filename for the download (required for Blob).
     */
    function downloadFile(downloadInfo) {
        if (!downloadInfo) {
            console.error('downloadFile: No download info provided.');
            return;
        }

        let blob;
        let filename = downloadInfo.file_name || 'download';
        let contentType = downloadInfo.content_type || 'application/octet-stream';

        if (downloadInfo.blob instanceof Blob) {
            // Case 1: Already a Blob object
            blob = downloadInfo.blob;
        } else if (downloadInfo.file_content) {
            // Case 2: Content (potentially base64 encoded) provided
            let fileContent = downloadInfo.file_content;
            if (downloadInfo.encoding === 'base64') {
                fileContent = atob(fileContent); // Decode base64
            }
            blob = new Blob([fileContent], { type: contentType });
        } else {
            console.error('downloadFile: Invalid download info. Neither blob nor file_content found.');
            return;
        }

        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url); // Clean up the URL object
    }


    /**
     * Adds a message to the chat window.
     * @param {string} sender - 'user' or 'bot'.
     * @param {string|Array<string>} content - The message content (plain text, code string, or array of options).
     * @param {string} type - 'text' for regular message, 'code' for code block, 'loading' for typing indicator, 'options' for clickable choices.
     * @param {number|null} duration - Optional duration in seconds for bot messages.
     * @param {boolean} requiresConfirmation - True if the message requires user confirmation (e.g., for UDT options).
     * @param {object|null} confirmationData - Data for confirmation options (e.g., UDT definition, actions).
     * @returns {HTMLElement|null} The message div element, or null for options/loading.
     */
    function addMessage(sender, content, type = 'text', duration = null, requiresConfirmation = false, confirmationData = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('chat-message', sender);

        let innerContent;

        switch (type) {
            case 'loading':
                const loadingSpan = document.createElement('span');
                loadingSpan.classList.add('loading-text');
                loadingSpan.innerHTML = `${content}<span class="loading-dot">.</span><span class="loading-dot">.</span><span class="loading-dot">.</span>`;
                messageDiv.appendChild(loadingSpan);
                break;
            case 'code':
                const preContent = document.createElement('pre');
                preContent.classList.add('code-style');
                preContent.textContent = content;

                const btnContainer = document.createElement('div');
                btnContainer.classList.add('btn-container');

                if (duration !== null) {
                    const durationSpan = document.createElement('span');
                    durationSpan.classList.add('duration');
                    durationSpan.textContent = `⏱️ ${duration.toFixed(2)}s`;
                    btnContainer.appendChild(durationSpan);
                }

                const actionsDiv = document.createElement('div');
                actionsDiv.classList.add('btn-actions');

                const copyButton = document.createElement('button');
                copyButton.classList.add('save-btn', 'copy-btn');
                copyButton.textContent = 'Copy';
                actionsDiv.appendChild(copyButton);

                const saveButton = document.createElement('button');
                saveButton.classList.add('save-btn', 'save-rung-btn');
                saveButton.textContent = 'Save';
                actionsDiv.appendChild(saveButton);

                btnContainer.appendChild(actionsDiv);

                messageDiv.appendChild(preContent);
                messageDiv.appendChild(btnContainer);
                break;
            case 'options':
                const prompt = document.createElement('p');
                prompt.textContent = "Did you mean to:";
                messageDiv.appendChild(prompt);

                const optionsContainer = document.createElement('div');
                optionsContainer.classList.add('chat-options-container');

                content.forEach(optionText => {
                    const optionBox = document.createElement('div');
                    optionBox.classList.add('chat-option-box');
                    optionBox.textContent = optionText;
                    optionBox.addEventListener('click', () => {
                        optionsContainer.querySelectorAll('.chat-option-box').forEach(box => {
                            box.classList.remove('selected');
                            box.classList.add('disabled');
                        });
                        optionBox.classList.add('selected');
                        sendConfirmedIntention(optionText, false, lastUserMessage);
                    });
                    optionsContainer.appendChild(optionBox);
                });
                messageDiv.appendChild(optionsContainer);
                break;
            case 'text':
            default:
                if (requiresConfirmation && confirmationData && confirmationData.type === 'udt_attachment') {
                    const promptMessage = document.createElement('p');
                    promptMessage.textContent = content;
                    messageDiv.appendChild(promptMessage);

                    const optionsContainer = document.createElement('div');
                    optionsContainer.classList.add('confirmation-options');

                    confirmationData.options.forEach(option => {
                        const button = document.createElement('button');
                        button.textContent = option.label;
                        button.classList.add('action-button');
                        button.addEventListener('click', (event) => handleUdtAttachmentAction(event, option.action, confirmationData));
                        optionsContainer.appendChild(button);
                    });
                    messageDiv.appendChild(optionsContainer);
                } else {
                    const textContent = document.createElement('div');
                    textContent.textContent = content;
                    messageDiv.appendChild(textContent);

                    if (duration !== null) {
                        const durationSpan = document.createElement('span');
                        durationSpan.classList.add('duration');
                        durationSpan.textContent = `⏱️ ${duration.toFixed(2)}s`;
                        messageDiv.appendChild(durationSpan);
                    }
                }
                break;
        }

        chatWindow.appendChild(messageDiv);
        scrollToBottom();
        return messageDiv;
    }

    // --- Theme Toggling Logic ---
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        body.classList.add(savedTheme);
    } else {
        body.classList.add('light-mode'); // Default
    }

    toggleThemeButton.addEventListener('click', () => {
        const newTheme = body.classList.contains('dark-mode') ? 'light-mode' : 'dark-mode';
        body.classList.remove('light-mode', 'dark-mode');
        body.classList.add(newTheme);
        localStorage.setItem('theme', newTheme);
    });

    // --- Modal Functionality ---
    settingsButton.addEventListener('click', () => {
        settingsModal.classList.add('show');
    });

    closeButton.addEventListener('click', () => {
        settingsModal.classList.remove('show');
        resetRagFileInput();
    });

    settingsModal.addEventListener('click', (event) => {
        if (event.target === settingsModal) {
            settingsModal.classList.remove('show');
            resetRagFileInput();
        }
    });

    // Handle RAG file input (Browse button)
    browseRagFileButton.addEventListener('click', () => {
        ragFileInput.click();
    });

    ragFileInput.addEventListener('change', () => {
        if (ragFileInput.files.length > 0) {
            ragFileNameDisplay.value = ragFileInput.files[0].name;
            uploadRagFileButton.disabled = false;
        } else {
            ragFileNameDisplay.value = '';
            uploadRagFileButton.disabled = true;
        }
        updateRagUploadStatus(''); // Clear previous status
    });

    // Handle RAG file upload (Upload Document button)
    uploadRagFileButton.addEventListener('click', async () => {
        if (ragFileInput.files.length === 0) {
            updateRagUploadStatus('Please select a file to upload.', 'error');
            return;
        }

        updateRagUploadStatus('Uploading...', 'info');
        uploadRagFileButton.disabled = true;
        browseRagFileButton.disabled = true;

        const formData = new FormData();
        formData.append('file', ragFileInput.files[0]);

        try {
            const response = await fetch('/upload_std_document', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok && result.status === 'success') {
                updateRagUploadStatus(result.message, 'success');
            } else {
                updateRagUploadStatus(result.message || `Failed to upload "${ragFileInput.files[0].name}".`, 'error');
            }
        } catch (error) {
            console.error('Error uploading document:', error);
            updateRagUploadStatus(`Network error: ${error.message}`, 'error');
        } finally {
            setTimeout(resetRagFileInput, 3000); // Status message visible for 3 seconds
        }
    });

    // --- Chat Functionality ---

    /**
     * Sends a confirmed intention back to the server.
     * @param {string} intention - The confirmed intention.
     * @param {boolean} isDirectConfirmation - True if this is a direct confirmation (e.g., UDT action), false if from options.
     * @param {string} originalUserQuestion - The original user's message.
     */
    async function sendConfirmedIntention(intention, isDirectConfirmation = false, originalUserQuestion = '') {
        if (!isDirectConfirmation) {
            addMessage('user', `Yes, ${intention}`);
        }

        const loadingMessageDiv = addMessage('bot', 'Model thinking....', 'loading');

        try {
            const response = await fetch('/confirm_intention', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ intention: intention, original_question: originalUserQuestion })
            });

            if (chatWindow.contains(loadingMessageDiv)) {
                chatWindow.removeChild(loadingMessageDiv);
            }

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.response?.text || 'Error confirming intention.');
            }

            const data = await response.json();
            const { text: botResponseText, is_code: isCode, duration, download: downloadInfo, requires_confirmation: requiresConfirmation, confirmation_data: confirmationData } = data.response;

            addMessage('bot', botResponseText, isCode ? 'code' : 'text', duration, requiresConfirmation, confirmationData);

            if (downloadInfo && !requiresConfirmation) {
                // Pass the downloadInfo object directly to the unified downloadFile function
                downloadFile(downloadInfo);
            }
        } catch (error) {
            console.error('Error confirming intention:', error);
            if (chatWindow.contains(loadingMessageDiv)) {
                chatWindow.removeChild(loadingMessageDiv);
            }
            addMessage('bot', `Error: ${error.message || 'Could not process your request.'}`);
        }
    }

    /**
     * Handles UDT attachment actions (e.g., "Keep Original", "Optimize").
     * @param {Event} event - The click event.
     * @param {string} action - The action chosen ('keep_original', 'optimize').
     * @param {object} confirmationData - Data related to the UDT confirmation.
     */
    async function handleUdtAttachmentAction(event, action, confirmationData) {
        const optionsContainer = event.target.closest('.confirmation-options');
        if (optionsContainer) {
            Array.from(optionsContainer.children).forEach(button => {
                button.disabled = true;
                button.style.opacity = '0.6';
                button.style.cursor = 'not-allowed';
            });
        }

        addMessage('user', `User has chosen: ${action.charAt(0).toUpperCase() + action.slice(1)}`);
        const loadingMessageDiv = addMessage('bot', `Processing '${action}' for UDT '${confirmationData.udt_name}'...`, 'loading');

        try {
            const response = await fetch('/process_udt_attachment', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action: action,
                    udt_definition: confirmationData.udt_definition,
                    original_filename: confirmationData.original_filename
                }),
            });
            const data = await response.json();
            const botResponse = data.response;

            if (chatWindow.contains(loadingMessageDiv)) {
                chatWindow.removeChild(loadingMessageDiv);
            }

            addMessage('bot', botResponse.text, botResponse.is_code ? 'code' : 'text', botResponse.duration);

            if (botResponse.download) {
                // Pass the downloadInfo object directly to the unified downloadFile function
                downloadFile(botResponse.download);
            }
        } catch (error) {
            console.error(`Error processing UDT attachment action (${action}):`, error);
            if (chatWindow.contains(loadingMessageDiv)) {
                chatWindow.removeChild(loadingMessageDiv);
            }
            addMessage('bot', `Error processing UDT attachment action: ${error.message}`);
        }
    }

    /**
     * Handles sending user messages to the server.
     */
    async function sendMessage() {
        const messageText = inputBox.value.trim();
        if (!messageText && !attachedFile) return;

        lastUserMessage = messageText;

        // Display user message in chat
        if (attachedFile && attachedFile.name.toLowerCase().endsWith('.xlsx')) {
            addMessage('user', `Attached Excel file: ${attachedFile.name}. Processing...`);
        } else {
            addMessage('user', messageText || (attachedFile ? `Attached: ${attachedFile.name}` : ''));
        }

        inputBox.value = '';
        inputBox.style.height = 'auto';
        enterButton.disabled = true;

        const loadingMessageDiv = addMessage('bot', 'Analyzing user intention...', 'loading');
        const loadingTextSpan = loadingMessageDiv.querySelector('.loading-text');

        // Simulate backend intention analysis delay
        setTimeout(() => {
            if (loadingTextSpan && chatWindow.contains(loadingMessageDiv)) {
                loadingTextSpan.innerHTML = 'Model thinking....<span class="loading-dot">.</span><span class="loading-dot">.</span><span class="loading-dot">.</span>';
            }
        }, 1500);

        try {
            let response;
            if (attachedFile) {
                const formData = new FormData();
                formData.append('message', messageText);
                formData.append('file', attachedFile);

                window.lastMessageTime = Date.now();

                response = await fetch('/attach', { method: 'POST', body: formData });

                // Check for direct file download response (e.g., from XLSX processing)
                const contentType = response.headers.get('Content-Type');
                const contentDisposition = response.headers.get('Content-Disposition');

                if (response.ok && contentType && contentType.includes('application/xml') && contentDisposition && contentDisposition.includes('attachment')) {
                    const blob = await response.blob();
                    const regex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
                    const match = regex.exec(contentDisposition);
                    const downloadFileName = match && match[1] ? decodeURIComponent(match[1].replace(/['"]/g, '')) : `generated_file_${Date.now()}.L5X`;

                    if (chatWindow.contains(loadingMessageDiv)) {
                        chatWindow.removeChild(loadingMessageDiv);
                    }
                    // Use the unified downloadFile function with a Blob
                    downloadFile({ blob: blob, file_name: downloadFileName, content_type: 'application/xml' });
                    addMessage('bot', `For the uploaded excel, "${downloadFileName}" has been generated. Download will begin shortly...`, 'text', (Date.now() - window.lastMessageTime) / 1000);
                    return; // Crucial: exit here if a file was downloaded directly
                }
                // If not a direct file download, proceed to parse as JSON
                const data = await response.json();
                const { text: botResponseText, is_code: isCode, duration, download: downloadInfo, requires_confirmation: requiresConfirmation, confirmation_data: confirmationData } = data.response;

                if (chatWindow.contains(loadingMessageDiv)) {
                    chatWindow.removeChild(loadingMessageDiv);
                }
                addMessage('bot', botResponseText, isCode ? 'code' : 'text', duration, requiresConfirmation, confirmationData);

                if (downloadInfo && !requiresConfirmation) {
                    // Pass the downloadInfo object (which will contain base64)
                    downloadFile(downloadInfo);
                }

            } else { // Regular chat message via /chat endpoint
                response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: messageText })
                });

                if (chatWindow.contains(loadingMessageDiv)) {
                    chatWindow.removeChild(loadingMessageDiv);
                }

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.response?.text || errorData.message || 'Server error.');
                }

                const data = await response.json();
                const { text: botResponseText, is_code: isCode, duration, download: downloadInfo, requires_confirmation: requiresConfirmation, confirmation_data: confirmationData } = data.response;

                addMessage('bot', botResponseText, isCode ? 'code' : 'text', duration, requiresConfirmation, confirmationData);

                if (downloadInfo && !requiresConfirmation) {
                    // Pass the downloadInfo object (which will contain base64)
                    downloadFile(downloadInfo);
                }
            }

        } catch (error) {
            console.error('Error sending message or getting response:', error);
            if (chatWindow.contains(loadingMessageDiv)) {
                chatWindow.removeChild(loadingMessageDiv);
            }
            addMessage('bot', `Error: ${error.message || 'Could not get response from server.'}`, 'text');
        } finally {
            attachedFile = null;
            fileInput.value = '';
            enterButton.disabled = inputBox.value.trim() === ''; // Ensure button state is correct
        }
    }

    // --- Event Listeners ---

    // Handle input box changes to enable/disable enter button
    inputBox.addEventListener('input', () => {
        enterButton.disabled = inputBox.value.trim() === '' && attachedFile === null;
        inputBox.style.height = 'auto';
        inputBox.style.height = inputBox.scrollHeight + 'px';
    });

    // Event listeners for sending messages (Enter button click and Enter key press)
    enterButton.addEventListener('click', sendMessage);

    inputBox.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            if (!enterButton.disabled) {
                sendMessage();
            }
        }
    });

    // Event listener for Attach button (opens file dialog)
    attachButton.addEventListener('click', () => {
        fileInput.click();
    });

    // Event listener for when a file is selected (triggers sendMessage immediately)
    fileInput.addEventListener('change', () => {
        attachedFile = fileInput.files[0];
        if (attachedFile) {
            sendMessage();
        } else {
            enterButton.disabled = inputBox.value.trim() === '';
        }
    });

    // --- Event Delegation for Copy Code to Clipboard and Save Rung ---
    chatWindow.addEventListener('click', async (event) => {
        const target = event.target;

        if (target.classList.contains('copy-btn')) {
            const copyButton = target;
            const codeBlock = copyButton.closest('.chat-message').querySelector('.code-style');
            if (!codeBlock) return;

            let textToCopy = codeBlock.textContent.replace('<![CDATA[', '').replace(']]>', '');

            try {
                await navigator.clipboard.writeText(textToCopy);
                const originalText = copyButton.textContent;
                copyButton.textContent = 'Copied!';
                copyButton.classList.add('saved');
                setTimeout(() => {
                    copyButton.textContent = originalText;
                    copyButton.classList.remove('saved');
                }, 2000);
            } catch (err) {
                console.error('Failed to copy text: ', err);
                alert('Failed to copy code to clipboard.');
            }
        } else if (target.classList.contains('save-rung-btn')) {
            const saveButton = target;
            const codeBlock = saveButton.closest('.chat-message').querySelector('.code-style');
            if (!codeBlock) return;

            // This is the raw IL code (or whatever format your GenerateRung expects)
            // It's the content displayed in the pre tag
            let rawIlCode = codeBlock.textContent.replace('<![CDATA[', '').replace(']]>', ''); // Keep the variable name consistent with what Flask expects

            saveButton.textContent = 'Saving...';
            saveButton.disabled = true;
            saveButton.classList.add('processing');

            try {
                // Generate a more descriptive filename if possible, or keep original logic
                let filename = `generated_rung_${new Date().toISOString().slice(0, 19).replace(/[^0-9]/g, "")}.L5X`;

                const response = await fetch('/generate_rung_from_saved_code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        code_content: rawIlCode, // <--- THIS IS THE CRITICAL CHANGE: changed from 'l5x_content' to 'code_content'
                        filename: filename
                    })
                });

                if (!response.ok) {
                    const errorResult = await response.json();
                    throw new Error(errorResult.error || 'Unknown error during save.');
                }

                const blob = await response.blob();
                // Pass the Blob directly to the unified downloadFile function
                downloadFile({ blob: blob, file_name: filename, content_type: 'application/xml' });


                saveButton.textContent = 'Downloaded!'; // Or "Saved!" if you prefer
                saveButton.classList.remove('processing');
                saveButton.classList.add('saved');
                setTimeout(() => {
                    saveButton.textContent = 'Save';
                    saveButton.disabled = false;
                    saveButton.classList.remove('saved');
                }, 3000);
            } catch (error) {
                console.error('Error saving Rung L5X:', error);
                saveButton.textContent = 'Error';
                saveButton.classList.remove('processing');
                saveButton.classList.add('error');
                setTimeout(() => {
                    saveButton.textContent = 'Save';
                    saveButton.disabled = false;
                    saveButton.classList.remove('error');
                }, 3000);
                alert(`Failed to save code: ${error.message}`);
            }
        }

    });
});