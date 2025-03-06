document.addEventListener('DOMContentLoaded', function() {
    const chatForm = document.getElementById('chat-form');
    const userMessageInput = document.getElementById('user-message');
    const chatMessages = document.getElementById('chat-messages');
    const suggestionItems = document.querySelectorAll('.suggestion-item');
    
    // Get CSRF token from the form
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Function to create a message element
    function createMessageElement(message, isUser) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `flex mb-3 ${isUser ? 'justify-end' : ''}`;
        
        const innerDiv = document.createElement('div');
        innerDiv.className = isUser 
            ? 'bg-indigo-600 text-white rounded-lg py-2 px-4 max-w-[80%]' 
            : 'bg-indigo-100 rounded-lg py-2 px-4 max-w-[80%]';
        
        const paragraph = document.createElement('p');
        paragraph.className = isUser ? 'text-white' : 'text-gray-800';
        paragraph.textContent = message;
        
        innerDiv.appendChild(paragraph);
        messageDiv.appendChild(innerDiv);
        
        return messageDiv;
    }

    // Function to create typing indicator
    function createTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'flex mb-3 typing-indicator';
        typingDiv.id = 'typing-indicator';
        
        const innerDiv = document.createElement('div');
        innerDiv.className = 'bg-gray-100 rounded-lg py-2 px-4';
        
        const content = document.createElement('div');
        content.className = 'flex items-center';
        content.innerHTML = '<span class="mr-2">Typing</span><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';
        
        innerDiv.appendChild(content);
        typingDiv.appendChild(innerDiv);
        
        return typingDiv;
    }

    // Handle form submission
    chatForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const userMessage = userMessageInput.value.trim();
        if (!userMessage) return;
        
        // Add user message to chat
        const userMessageElement = createMessageElement(userMessage, true);
        userMessageElement.classList.add('new-message');
        chatMessages.appendChild(userMessageElement);
        
        // Clear input field
        userMessageInput.value = '';
        
        // Add typing indicator
        const typingIndicator = createTypingIndicator();
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Send message to backend
        fetch('/api/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ message: userMessage })
        })
        .then(response => response.json())
        .then(data => {
            // Remove typing indicator
            const indicator = document.getElementById('typing-indicator');
            if (indicator) indicator.remove();
            
            // Add bot response
            const botMessageElement = createMessageElement(data.response, false);
            botMessageElement.classList.add('new-message');
            chatMessages.appendChild(botMessageElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        })
        .catch(error => {
            // Remove typing indicator
            const indicator = document.getElementById('typing-indicator');
            if (indicator) indicator.remove();
            
            // Add error message
            const errorElement = createMessageElement("Sorry, there was an error processing your request. Please try again.", false);
            errorElement.classList.add('new-message');
            chatMessages.appendChild(errorElement);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            console.error("Error:", error);
        });
    });

    // Handle suggestion clicks
    suggestionItems.forEach(item => {
        item.addEventListener('click', function() {
            userMessageInput.value = this.textContent.trim();
            chatForm.dispatchEvent(new Event('submit'));
        });
    });
});
