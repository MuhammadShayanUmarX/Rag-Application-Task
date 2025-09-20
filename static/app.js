// HR Copilot Frontend JavaScript

class HRCopilot {
    constructor() {
        this.apiBase = '/api';
        this.currentUserId = this.generateUserId();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadInitialData();
    }

    generateUserId() {
        // Generate a simple user ID for session tracking
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }

    setupEventListeners() {
        // Question input
        const questionInput = document.getElementById('questionInput');
        const askBtn = document.getElementById('askBtn');

        askBtn.addEventListener('click', () => this.askQuestion());
        questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.askQuestion();
            }
        });

        // Quick questions
        document.querySelectorAll('.quick-question').forEach(btn => {
            btn.addEventListener('click', (e) => {
                questionInput.value = e.target.textContent;
                this.askQuestion();
            });
        });

        // Analytics modal
        document.getElementById('analyticsBtn').addEventListener('click', () => this.showAnalytics());
        document.getElementById('closeAnalytics').addEventListener('click', () => this.hideAnalytics());

        // Admin modal
        document.getElementById('adminBtn').addEventListener('click', () => this.showAdmin());
        document.getElementById('closeAdmin').addEventListener('click', () => this.hideAdmin());

        // Document upload
        document.getElementById('uploadDocument').addEventListener('click', () => this.uploadDocument());
    }

    async askQuestion() {
        const questionInput = document.getElementById('questionInput');
        const question = questionInput.value.trim();

        if (!question) return;

        // Clear input
        questionInput.value = '';

        // Add user message to chat
        this.addMessageToChat(question, 'user');

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch(`${this.apiBase}/query/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    question: question,
                    user_id: this.currentUserId
                })
            });

            const data = await response.json();

            // Hide typing indicator
            this.hideTypingIndicator();

            // Add AI response to chat
            this.addMessageToChat(data.answer, 'ai', data.confidence_score);

            // Show suggested forms
            this.showSuggestedForms(data.suggested_forms || []);

            // Add feedback buttons
            this.addFeedbackButtons(data.query_id);

        } catch (error) {
            console.error('Error asking question:', error);
            this.hideTypingIndicator();
            this.addMessageToChat('Sorry, I encountered an error. Please try again.', 'ai', 0);
        }
    }

    addMessageToChat(message, sender, confidence = null) {
        const chatContainer = document.getElementById('chatContainer');
        
        // Remove empty state if it exists
        const emptyState = chatContainer.querySelector('.text-center');
        if (emptyState) {
            emptyState.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `mb-4 flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `message-bubble px-4 py-3 rounded-lg ${
            sender === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 text-gray-800'
        }`;

        bubbleDiv.innerHTML = `
            <div class="message-content">${this.formatMessage(message)}</div>
            ${confidence !== null ? `<div class="text-xs mt-2 opacity-75">Confidence: ${(confidence * 100).toFixed(1)}%</div>` : ''}
        `;

        messageDiv.appendChild(bubbleDiv);
        chatContainer.appendChild(messageDiv);

        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    formatMessage(message) {
        // Convert line breaks to HTML
        return message.replace(/\n/g, '<br>');
    }

    showTypingIndicator() {
        document.getElementById('typingIndicator').classList.add('show');
    }

    hideTypingIndicator() {
        document.getElementById('typingIndicator').classList.remove('show');
    }

    showSuggestedForms(forms) {
        const formsContainer = document.getElementById('formsContainer');
        
        if (forms.length === 0) {
            formsContainer.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <i class="fas fa-file-alt text-4xl mb-4"></i>
                    <p>No relevant forms found</p>
                </div>
            `;
            return;
        }

        formsContainer.innerHTML = forms.map(form => `
            <div class="form-card bg-gray-50 p-4 rounded-lg mb-3 border border-gray-200">
                <h4 class="font-semibold text-gray-800 mb-2">${form.name}</h4>
                <p class="text-sm text-gray-600 mb-3">${form.description || 'No description available'}</p>
                <div class="flex justify-between items-center">
                    <span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">${form.category}</span>
                    ${form.file_url ? `<a href="${form.file_url}" target="_blank" class="text-blue-500 hover:text-blue-700 text-sm">
                        <i class="fas fa-download mr-1"></i>Download
                    </a>` : ''}
                </div>
            </div>
        `).join('');
    }

    addFeedbackButtons(queryId) {
        const chatContainer = document.getElementById('chatContainer');
        const lastMessage = chatContainer.lastElementChild;
        
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'flex justify-start mb-4';
        feedbackDiv.innerHTML = `
            <div class="bg-white border border-gray-200 rounded-lg p-3">
                <p class="text-sm text-gray-600 mb-2">Was this helpful?</p>
                <div class="flex space-x-2">
                    <button class="feedback-btn bg-green-100 hover:bg-green-200 text-green-800 px-3 py-1 rounded text-sm" data-query-id="${queryId}" data-rating="5">
                        <i class="fas fa-thumbs-up mr-1"></i>Yes
                    </button>
                    <button class="feedback-btn bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded text-sm" data-query-id="${queryId}" data-rating="1">
                        <i class="fas fa-thumbs-down mr-1"></i>No
                    </button>
                </div>
            </div>
        `;

        chatContainer.appendChild(feedbackDiv);

        // Add event listeners to feedback buttons
        feedbackDiv.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const rating = parseInt(e.target.dataset.rating);
                const isHelpful = rating >= 4;
                this.submitFeedback(queryId, rating, isHelpful);
                
                // Disable buttons after feedback
                feedbackDiv.querySelectorAll('.feedback-btn').forEach(b => b.disabled = true);
                feedbackDiv.innerHTML = '<p class="text-sm text-gray-600">Thank you for your feedback!</p>';
            });
        });
    }

    async submitFeedback(queryId, rating, isHelpful) {
        try {
            await fetch(`${this.apiBase}/query/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query_id: queryId,
                    rating: rating,
                    is_helpful: isHelpful
                })
            });
        } catch (error) {
            console.error('Error submitting feedback:', error);
        }
    }

    async showAnalytics() {
        const modal = document.getElementById('analyticsModal');
        modal.classList.remove('hidden');

        try {
            const response = await fetch(`${this.apiBase}/analytics/`);
            const data = await response.json();

            document.getElementById('totalQueries').textContent = data.total_queries || 0;
            document.getElementById('avgResponseTime').textContent = 
                data.avg_response_time_ms ? `${data.avg_response_time_ms.toFixed(0)}ms` : 'N/A';
            document.getElementById('confidenceScore').textContent = 
                data.avg_confidence_score ? `${(data.avg_confidence_score * 100).toFixed(1)}%` : 'N/A';

        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    hideAnalytics() {
        document.getElementById('analyticsModal').classList.add('hidden');
    }

    async showAdmin() {
        const modal = document.getElementById('adminModal');
        modal.classList.remove('hidden');

        // Load system health
        await this.loadSystemHealth();
    }

    hideAdmin() {
        document.getElementById('adminModal').classList.add('hidden');
    }

    async loadSystemHealth() {
        try {
            const response = await fetch(`${this.apiBase}/admin/system-health`);
            const data = await response.json();

            const healthDiv = document.getElementById('systemHealth');
            healthDiv.innerHTML = `
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span>Database:</span>
                        <span class="px-2 py-1 rounded text-sm ${data.database === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                            ${data.database}
                        </span>
                    </div>
                    <div class="flex justify-between">
                        <span>Vector DB:</span>
                        <span class="px-2 py-1 rounded text-sm ${data.vector_database === 'healthy' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                            ${data.vector_database}
                        </span>
                    </div>
                    <div class="flex justify-between">
                        <span>Policies:</span>
                        <span class="text-gray-600">${data.counts.policies}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Forms:</span>
                        <span class="text-gray-600">${data.counts.forms}</span>
                    </div>
                </div>
            `;
        } catch (error) {
            console.error('Error loading system health:', error);
        }
    }

    async uploadDocument() {
        const fileInput = document.getElementById('documentUpload');
        const titleInput = document.getElementById('documentTitle');
        const categorySelect = document.getElementById('documentCategory');

        const file = fileInput.files[0];
        const title = titleInput.value.trim();
        const category = categorySelect.value;

        if (!file || !title) {
            alert('Please select a file and enter a title');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', category);
        formData.append('title', title);

        try {
            const response = await fetch(`${this.apiBase}/admin/upload-document`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                alert(`Document uploaded successfully! Created ${data.chunks_created} chunks.`);
                fileInput.value = '';
                titleInput.value = '';
            } else {
                alert('Error uploading document: ' + data.message);
            }
        } catch (error) {
            console.error('Error uploading document:', error);
            alert('Error uploading document');
        }
    }

    async loadInitialData() {
        // Load any initial data if needed
        console.log('HR Copilot initialized');
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new HRCopilot();
});

