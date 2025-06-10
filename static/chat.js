const socket = io();
const chatBox = document.getElementById('chat-box');

socket.on('new_message', (msg) => {
    const msgElem = document.createElement('div');
    msgElem.textContent = `[${msg.timestamp}] ${msg.user}: ${msg.message}`;
    chatBox.appendChild(msgElem);
    chatBox.scrollTop = chatBox.scrollHeight;
});

function sendMessage() {
    const username = document.getElementById('username').value;
    const message = document.getElementById('message').value;
    if (!username || !message) return;
    fetch('/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user: username, message: message })
    });
    document.getElementById('message').value = '';
}