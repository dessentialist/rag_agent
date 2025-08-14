// Chat functionality for BigChat UI

document.addEventListener('DOMContentLoaded', function() {
    // Elements
    const chatMessages = document.querySelector('.chat-messages');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const scrollBtn = document.getElementById('scroll-btn');
    
    // Configure Marked.js
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
    
    // Initial bot message with typing animation effect
    setTimeout(() => {
        // Use welcome message from config
        addBotMessage(BOT_WELCOME_MESSAGE, true);
        
        // Force immediate scroll for the initial message
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Add predefined prompts after the initial message with a slight delay
        setTimeout(() => {
            // Add predefined prompts from config
            addPredefinedPrompts(PREDEFINED_PROMPTS);
            
            // Force scroll again after adding predefined prompts
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 1500);
    }, 500);

    // Event listeners
    chatForm.addEventListener('submit', handleChatSubmit);
    
    // Initialize current agent type
    let currentAgentType = 'course'; // Default agent type
    
    // Function to update the UI with the selected agent type
    function updateAgentIndicator(agentType) {
        // Update the data attribute on the chat form
        chatForm.setAttribute('data-agent-type', agentType);
        
        // Get the badge element
        const agentBadge = document.getElementById('agent-type-badge');
        
        if (agentBadge) {
            // Clear existing classes
            agentBadge.classList.remove('course-agent', 'documentation-agent');
            
            // Set text and class based on agent type
            if (agentType === 'documentation') {
                agentBadge.textContent = 'Documentation Agent';
                agentBadge.classList.add('documentation-agent');
            } else {
                agentBadge.textContent = 'Course Agent';
                agentBadge.classList.add('course-agent');
            }
        }
    }
    
    // Scroll button functionality
    scrollBtn.addEventListener('click', () => {
        scrollToBottom();
    });
    
    // Listen for scroll events to show/hide scroll button
    chatMessages.addEventListener('scroll', () => {
        // Calculate if we're near the bottom (within 100px)
        const isNearBottom = chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight < 100;
        
        if (isNearBottom) {
            scrollBtn.style.display = 'none';
        } else {
            scrollBtn.style.display = 'flex';
        }
    });

    // Track the current conversation ID
    let currentConversationId = null;

    // Handle chat form submission
    async function handleChatSubmit(event) {
        event.preventDefault();
        
        const userMessage = userInput.value.trim();
        if (!userMessage) return;
        
        // Add user message to chat
        addUserMessage(userMessage);
        userInput.value = '';
        
        // Show typing animation
        const typingIndicator = addTypingIndicator();
        
        try {
            // Send message to backend including the conversation ID if we have one
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    message: userMessage,
                    conversation_id: currentConversationId
                    // Agent selection happens on server based on document type only
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to get response');
            }
            
            const data = await response.json();
            
            // Store conversation ID for future messages
            if (data.conversation_id) {
                currentConversationId = data.conversation_id;
            }
            
            // Display the agent type used by the server for this response
            if (data.agent_type) {
                currentAgentType = data.agent_type;
                console.log(`Agent type selected: ${currentAgentType}`);
                updateAgentIndicator(currentAgentType);
            }
            
            // Store the current response data globally for use after typing animation
            window.currentResponseData = data;
            
            // Remove typing indicator
            typingIndicator.remove();
            
            // Add bot response with Answer header
            const botMessageElement = addBotMessage(`${data.response}`, true);
                        
            // Scroll to bottom
            scrollToBottom();
        } catch (error) {
            console.error("Error in chat submission:", error);
            
            // Remove typing indicator if it exists
            if (typingIndicator) {
                typingIndicator.remove();
            }
            
            // Show error message to the user
            addBotMessage("I'm sorry, I encountered an error while processing your request. Please try again.", false);
        }
    }

    // Add user message to chat
    function addUserMessage(message) {
        const messageContainer = document.createElement('div');
        messageContainer.className = 'message-container d-flex justify-content-end w-100 mb-4';
        
        const messageElement = document.createElement('div');
        messageElement.className = 'message message-user';
        messageElement.textContent = message;
        
        messageContainer.appendChild(messageElement);
        chatMessages.appendChild(messageContainer);
        scrollToBottom();
    }

    // Add bot message to chat with optional typing effect
    function addBotMessage(message, withTypingEffect = false) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message message-bot';
        
        // Create a container for markdown content
        const markdownContainer = document.createElement('div');
        markdownContainer.className = 'markdown-content';
        messageElement.appendChild(markdownContainer);
        
        if (withTypingEffect) {
            typeMessage(markdownContainer, message);
        } else {
            // Render markdown
            markdownContainer.innerHTML = marked.parse(message);
            // Apply syntax highlighting to code blocks
            markdownContainer.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightBlock(block);
            });
        }
        
        chatMessages.appendChild(messageElement);
        scrollToBottom();
        return messageElement;
    }

    // Add typing indicator
    function addTypingIndicator() {
        const indicatorElement = document.createElement('div');
        indicatorElement.className = 'message message-bot typing-animation';
        indicatorElement.innerHTML = '<span></span><span></span><span></span>';
        chatMessages.appendChild(indicatorElement);
        scrollToBottom();
        return indicatorElement;
    }

    // Type message with animation effect
    function typeMessage(element, message, speed = 10) {
        // For typing effect with real-time markdown rendering
        let i = 0;
        element.innerHTML = '';
        const messageLength = message.length;
        let currentText = '';
        
        // Store the current conversation data for access after animation
        const currentData = window.currentResponseData;
        
        // Show typing effect with real-time markdown rendering
        function typeText() {
            if (i < messageLength) {
                currentText += message.charAt(i);
                // Render markdown after each character is added
                element.innerHTML = marked.parse(currentText);
                
                // Apply syntax highlighting to code blocks if they exist
                element.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightBlock(block);
                });
                
                i++;
                scrollToBottom();
                setTimeout(typeText, speed);
            } else {
                // Make sure final markdown is properly rendered
                element.innerHTML = marked.parse(message);
                // Apply syntax highlighting to code blocks
                element.querySelectorAll('pre code').forEach((block) => {
                    hljs.highlightBlock(block);
                });
                
                // Now directly add the next steps to the message element (not as a separate message)
                if (currentData && currentData.next_steps && currentData.next_steps.length > 0) {
                    // Add a divider before the next steps
                    const divider = document.createElement('hr');
                    divider.className = 'section-divider';
                    element.appendChild(divider);
                    
                    // Add the next steps directly to the message element (no separate container)
                    addNextSteps(currentData.next_steps, element);
                }
                
                // Add resource only when using course agent
                if (currentData && currentData.resources && currentAgentType === 'course') {
                    // Only render resource card for course agent responses
                    const resourceUrl = currentData.resources;
                    if (resourceUrl) {
                        // Create a simple resource card with the URL from the response
                        addCourseResource(resourceUrl);
                    }
                }
                
                scrollToBottom();
            }
        }
        
        typeText();
    }

    // Add resource carousel
    // Add a course resource card (simplified)
    function addCourseResource(resourceUrl) {
        const lastMessage = document.querySelector('.message-bot:last-child');
        if (!lastMessage) return;
        
        // Create a simple card for the course resource
        const card = document.createElement('div');
        card.className = 'card resource-card';
        
        // Create a thumbnail container
        const thumbnailContainer = document.createElement('div');
        thumbnailContainer.className = 'thumbnail-container';
        
        // Create a thumbnail image
        const thumbnail = document.createElement('img');
        thumbnail.className = 'course-thumbnail';
        thumbnail.src = DEFAULT_COURSE_THUMBNAIL; // Use the default thumbnail from config
        thumbnail.alt = 'BigID University Course Thumbnail';
        
        thumbnailContainer.appendChild(thumbnail);
        card.appendChild(thumbnailContainer);
        
        // Create card body
        const cardBody = document.createElement('div');
        cardBody.className = 'card-body';
        
        const title = document.createElement('h5');
        title.className = 'card-title';
        title.textContent = 'Course Resource';
        
        const description = document.createElement('p');
        description.className = 'card-text';
        description.textContent = 'BigID University course material';
        
        const link = document.createElement('a');
        link.className = 'btn btn-primary';
        link.textContent = 'Go to Course';
        link.href = resourceUrl || '#';
        link.target = '_blank';
        
        // Add elements to the card
        cardBody.appendChild(title);
        cardBody.appendChild(description);
        cardBody.appendChild(link);
        card.appendChild(cardBody);
        
        // Add resources section header
        const resourcesHeader = document.createElement('h6');
        resourcesHeader.className = 'mt-3 mb-2 resources-header';
        resourcesHeader.innerHTML = '<i class="bi bi-collection"></i> Related Course';
        
        // Add to message
        lastMessage.appendChild(resourcesHeader);
        lastMessage.appendChild(card);
        
        scrollToBottom();
    }
    
    // Simplified function that just delegates to addCourseResource
    function addResourceCarousel(resources) {
        // This function is kept for backward compatibility
        // but now just delegates to the simpler implementation
        console.log("Legacy addResourceCarousel called, delegating to simpler implementation");
        
        // We're not using this function for new code, but keeping it 
        // to avoid breaking existing code that might call it
    }

    // Scroll chat to bottom with smooth animation
    function scrollToBottom() {
        // Use smooth scrolling for better UX
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
        
        // Also force an immediate scroll to ensure visibility
        setTimeout(() => {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }, 100);
    }
    
    // Add predefined prompts after the introduction message
    function addPredefinedPrompts(prompts) {
        const container = document.createElement('div');
        container.className = 'message message-bot predefined-prompts-container';
        
        const content = document.createElement('div');
        content.className = 'predefined-prompts';
        
        // Create prompts list
        const promptsList = document.createElement('div');
        promptsList.className = 'predefined-prompts-list';
        
        prompts.forEach(prompt => {
            const promptItem = document.createElement('div');
            promptItem.className = 'predefined-prompt-item';
            
            const promptBox = document.createElement('div');
            promptBox.className = 'predefined-prompt-box';
            
            const title = document.createElement('h5');
            title.className = 'prompt-title';
            title.textContent = prompt.title;
            
            // Store the description in a data attribute but don't display it
            promptBox.setAttribute('data-description', prompt.description);
            
            promptBox.appendChild(title);
            
            promptBox.addEventListener('click', () => {
                try {
                    userInput.value = prompt.description;
                    // Create a proper submit event that will work with preventDefault
                    const submitEvent = new Event('submit', { 
                        bubbles: true, 
                        cancelable: true 
                    });
                    chatForm.dispatchEvent(submitEvent);
                } catch (error) {
                    console.error("Error submitting predefined prompt:", error);
                    addBotMessage("I'm sorry, I encountered an error. Please try typing your question manually.", false);
                }
            });
            
            promptItem.appendChild(promptBox);
            promptsList.appendChild(promptItem);
        });
        
        content.appendChild(promptsList);
        container.appendChild(content);
        chatMessages.appendChild(container);
        
        // Add CSS styles for predefined prompts if not already present
        if (!document.getElementById('predefined-prompts-styles')) {
            const style = document.createElement('style');
            style.id = 'predefined-prompts-styles';
            style.textContent = `
                .predefined-prompts-container {
                    max-width: 100%;
                }
                .predefined-prompts {
                    padding: 0.5rem;
                }
                .predefined-prompts-list {
                    display: flex;
                    flex-direction: column;
                    gap: 0.75rem;
                }
                .predefined-prompt-box {
                    background-color: rgba(var(--bs-primary-rgb), 0.1);
                    border-left: 3px solid var(--bs-primary);
                    border-radius: 0.5rem;
                    padding: 0.8rem 1.2rem;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    text-align: left;
                }
                .predefined-prompt-box:hover {
                    background-color: rgba(var(--bs-primary-rgb), 0.2);
                    transform: translateX(5px);
                }
                .prompt-title {
                    font-size: 0.9rem;
                    font-weight: 500;
                    margin-bottom: 0;
                    color: var(--bs-primary);
                }
            `;
            document.head.appendChild(style);
        }
        
        scrollToBottom();
    }
    
    // Add suggested topics in an elegant way
    function addSuggestedTopics() {
        const container = document.createElement('div');
        container.className = 'message message-bot';
        
        const content = document.createElement('div');
        content.className = 'suggested-topics-container';
        
        // Header
        const header = document.createElement('div');
        header.className = 'suggested-topics-header';
        header.innerHTML = '<h6 class="mb-2">Popular Topics:</h6>';
        content.appendChild(header);
        
        // Create topics grid
        const topicsGrid = document.createElement('div');
        topicsGrid.className = 'suggested-topics-grid';
        
        // Define popular topics
        const topics = [
            { icon: 'mortarboard-fill', text: 'Course Catalog', prompt: 'Show me the course catalog' },
            { icon: 'award', text: 'Certifications', prompt: 'What certifications are available?' },
            { icon: 'currency-dollar', text: 'Training Credits', prompt: 'How do training credits work?' },
            { icon: 'book', text: 'Learning Paths', prompt: 'Explain learning paths' },
            { icon: 'person-vcard', text: 'My Profile', prompt: 'How do I update my profile?' },
            { icon: 'patch-question', text: 'FAQ', prompt: 'Show me frequently asked questions' }
        ];
        
        // Add topic buttons
        topics.forEach(topic => {
            const topicBtn = document.createElement('div');
            topicBtn.className = 'suggested-topic-btn';
            topicBtn.innerHTML = `<i class="bi bi-${topic.icon}"></i>`;
            topicBtn.addEventListener('click', () => {
                try {
                    userInput.value = topic.prompt;
                    // Create a proper submit event that will work with preventDefault
                    const submitEvent = new Event('submit', { 
                        bubbles: true, 
                        cancelable: true 
                    });
                    chatForm.dispatchEvent(submitEvent);
                } catch (error) {
                    console.error("Error submitting suggested topic:", error);
                    addBotMessage("I'm sorry, I encountered an error. Please try typing your question manually.", false);
                }
            });
            topicsGrid.appendChild(topicBtn);
        });
        
        content.appendChild(topicsGrid);
        container.appendChild(content);
        chatMessages.appendChild(container);
        
        // Add some CSS dynamically if not already present
        if (!document.getElementById('suggested-topics-styles')) {
            const style = document.createElement('style');
            style.id = 'suggested-topics-styles';
            style.textContent = `
                .suggested-topics-container {
                    padding: 0.5rem;
                }
                .suggested-topics-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
                    gap: 0.75rem;
                    margin-top: 0.5rem;
                }
                .suggested-topic-btn {
                    background-color: rgba(var(--bs-primary-rgb), 0.1);
                    border-radius: 0.5rem;
                    padding: 0.75rem 0.5rem;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    gap: 0.5rem;
                }
                .suggested-topic-btn:hover {
                    background-color: rgba(var(--bs-primary-rgb), 0.2);
                    transform: translateY(-2px);
                }
                .suggested-topic-btn i {
                    font-size: 1.5rem;
                    color: var(--bs-primary);
                }
                .suggested-topic-btn span {
                    font-size: 0.85rem;
                    font-weight: 500;
                }
            `;
            document.head.appendChild(style);
        }
        
        scrollToBottom();
    }
    
    // Add suggested next steps after a bot response
    function addNextSteps(steps, targetElement = null) {
        // If targetElement is provided, add next steps directly to it
        // Otherwise create a standalone message container
        let container;
        let addToContainer = false;
        
        if (targetElement) {
            container = targetElement;
            addToContainer = true;
        } else {
            container = document.createElement('div');
            container.className = 'message message-bot next-steps-container';
        }
        
        const content = document.createElement('div');
        content.className = 'next-steps';
        
        // Steps list
        const stepsList = document.createElement('div');
        stepsList.className = 'next-steps-list';
        
        steps.forEach((step, index) => {
            const stepItem = document.createElement('div');
            stepItem.className = 'next-step-item';
            
            const stepButton = document.createElement('button');
            stepButton.className = 'btn btn-outline-primary btn-sm w-100 text-start';
            stepButton.innerHTML = `<i class="bi bi-arrow-right-circle me-2"></i>${step}`;
            stepButton.addEventListener('click', () => {
                try {
                    userInput.value = step;
                    // Create a proper submit event that will work with preventDefault
                    const submitEvent = new Event('submit', { 
                        bubbles: true, 
                        cancelable: true 
                    });
                    chatForm.dispatchEvent(submitEvent);
                } catch (error) {
                    console.error("Error submitting next step:", error);
                    addBotMessage("I'm sorry, I encountered an error. Please try typing your question manually.", false);
                }
            });
            
            stepItem.appendChild(stepButton);
            stepsList.appendChild(stepItem);
        });
        
        content.appendChild(stepsList);
        container.appendChild(content);
        
        // If we're not adding to an existing element, append the new container to chatMessages
        if (!addToContainer) {
            chatMessages.appendChild(container);
        }
        
        // Add CSS if not present
        if (!document.getElementById('next-steps-styles')) {
            const style = document.createElement('style');
            style.id = 'next-steps-styles';
            style.textContent = `
                .next-steps-container {
                    max-width: 90%;
                }
                .next-steps {
                    background-color: rgba(var(--bs-info-rgb), 0.05);
                    border-radius: 0.5rem;
                    padding: 0.75rem;
                    border-left: 3px solid var(--bs-info);
                }
                .next-steps-list {
                    display: flex;
                    flex-direction: column;
                    gap: 0.5rem;
                    margin-top: 0;
                }
                .next-step-item button {
                    text-align: left;
                    transition: all 0.2s ease;
                }
                .next-step-item button:hover {
                    transform: translateX(3px);
                }
            `;
            document.head.appendChild(style);
        }
        
        scrollToBottom();
        return content; // Return the content element for reference
    }
});
