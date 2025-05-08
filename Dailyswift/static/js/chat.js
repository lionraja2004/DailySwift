document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    const chatForm = document.getElementById('chat-form');
    const messageInput = document.getElementById('message-input');
    const messagesContainer = document.getElementById('chat-messages');
    const currentUserId = document.body.getAttribute('data-user-id');
    
    if (chatForm) {
        // Join user's room
        socket.emit('join_room', { user_id: currentUserId });
        
        // Send message
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const message = messageInput.value.trim();
            
            if (message) {
                const receiverId = this.getAttribute('data-receiver-id');
                
                socket.emit('send_message', {
                    receiver_id: receiverId,
                    content: message
                });
                
                // Add message to UI immediately
                addMessageToUI({
                    sender_id: currentUserId,
                    content: message,
                    timestamp: new Date().toLocaleTimeString()
                });
                
                messageInput.value = '';
            }
        });
        
        // Receive message
        socket.on('receive_message', function(data) {
            addMessageToUI(data);
        });
    }
    
    function addMessageToUI(message) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('message');
        
        if (message.sender_id == currentUserId) {
            messageElement.classList.add('message-sent');
            messageElement.innerHTML = `
                <div class="message-content">${message.content}</div>
                <div class="message-info">You at ${message.timestamp}</div>
            `;
        } else {
            messageElement.classList.add('message-received');
            messageElement.innerHTML = `
                <div class="message-info">Them at ${message.timestamp}</div>
                <div class="message-content">${message.content}</div>
            `;
        }
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
});