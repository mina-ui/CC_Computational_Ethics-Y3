const SERVER = "server";

// 'free trial' session timer
let sessionStart = Date.now();
const SESSION_MS = 5 * 60 * 1000; // 5 minutes

function checkTimer() {
    const elapsed = Date.now() - sessionStart;

    if (elapsed >= SESSION_MS) {
        window.location.href = "results.html";
    }
}

// check every second
setInterval(checkTimer, 1000);

// ask to be explained
function escapeHtml(str) {
    return str.replace(/[&<>"']/g, function (match) {
        return ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[match];
    });
}

const chatBody = document.querySelector(".chat-body");
const messageInput = document.querySelector(".message-input");
const sendMessageButton = document.querySelector("#send-message");

// Create message element
const createMessageElement = (content, ...classes) => {
    const div = document.createElement("div");
    div.classList.add("message", ...classes);
    div.innerHTML = content;
    return div;
};

// Handle outgoing user messages
const handleOutgoingMessage = (e) => {
    e.preventDefault();
    const userMessage = messageInput.value.trim();
    if (!userMessage) return;

    messageInput.value = "";

    // Add user message to chat
    const outgoingDiv = createMessageElement(
        `<div class="message-text">${userMessage}</div>`,
        "user-message"
    );
    chatBody.appendChild(outgoingDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    // Add thinking indicator
    const thinkingDiv = createMessageElement(
        `<div class="message-text">
            <div class="thinking-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>`,
        "bot-message",
        "thinking"
    );
    chatBody.appendChild(thinkingDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    // Fetch bot reply
    fetch(`${SERVER}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage })
    })
        .then(res => res.json())
        .then(data => {
            // Remove thinking indicator
            thinkingDiv.remove();

            // Add bot reply
            const botDiv = createMessageElement(
                `<div class="message-text">${data.reply}</div>`,
                "bot-message"
            );
            chatBody.appendChild(botDiv);
            chatBody.scrollTop = chatBody.scrollHeight;
        })
        .catch(err => {
            thinkingDiv.remove();
            const errorDiv = createMessageElement(
                `<div class="message-text">Error getting response. Try again.</div>`,
                "bot-message"
            );
            chatBody.appendChild(errorDiv);
            chatBody.scrollTop = chatBody.scrollHeight;
            console.error(err);
        });
};

const picker = new EmojiMart.Picker({
    theme: "light",
    skinTonePosition: "none",
    previewPosition: "none",
    onEmojiSelect: (emoji) => {
        const { selectionStart: start, selectionEnd: end } = messageInput;
        messageInput.setRangeText(emoji.native, start, end, "end");
        messageInput.focus()
    }
});

// Toggle when clicking emoji button
document.getElementById("emoji-picker").addEventListener("click", (e) => {
    e.stopPropagation(); // prevents closing instantly
    document.body.classList.toggle("show-emoji-picker");
});

// Close when clicking outside
document.addEventListener("click", (e) => {
    const pickerEl = document.querySelector("em-emoji-picker");
    const emojiButton = document.getElementById("emoji-picker");

    if (!pickerEl.contains(e.target) && e.target !== emojiButton) {
        document.body.classList.remove("show-emoji-picker");
    }
});

document.querySelector(".chat-form").appendChild(picker);

// Enter key and send button handlers
messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleOutgoingMessage(e);
});
sendMessageButton.addEventListener("click", handleOutgoingMessage);
