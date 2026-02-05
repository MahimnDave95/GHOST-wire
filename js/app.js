// GhostWire - Complete Interactive Application

// Theme Management
function initTheme() {
    const savedTheme = localStorage.getItem('ghostwire-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('ghostwire-theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
}

// Personas Data
const PERSONAS = [
    {
        id: 'lakshmi',
        name: 'Lakshmi Amma',
        age: 68,
        location: 'Coimbatore, Tamil Nadu',
        occupation: 'Retired School Teacher',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Lakshmi&gender=female',
        traits: ['Trusting', 'Low Tech-Savvy', 'Polite', 'Religious'],
        backstory: 'Widow living alone, son works in Bangalore. Receives pension, not comfortable with technology.',
        quote: 'I don\'t understand computers beta, my son Ramesh handles this.',
        vulnerabilities: ['Lonely', 'Trusts authority', 'Confused by tech'],
        responses: {
            tech_support: [
                'Oh my! I don\'t understand computers. My son handles this.',
                'What is AnyDesk? I only know Facebook.',
                'My computer makes funny noises. Is that the virus?'
            ],
            lottery: [
                'I never win anything! Are you sure?',
                'My husband said I was lucky, but I don\'t trust this.',
                'Do I need to pay? I only have pension money.'
            ],
            banking: [
                'I don\'t like giving details on phone.',
                'My son said never share OTP. Is this real?',
                'I will call bank directly first.'
            ],
            romance: [
                'You are very kind. I don\'t get many compliments.',
                'I miss my husband. It\'s lonely here.',
                'Where are you from? You sound nice.'
            ]
        }
    },
    {
        id: 'rajesh',
        name: 'Rajesh Kumar',
        age: 45,
        location: 'Delhi, NCR',
        occupation: 'Small Business Owner',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Rajesh&gender=male',
        traits: ['Busy', 'Impatient', 'Money-conscious', 'Street-smart'],
        backstory: 'Runs a small electronics shop. Looking for investment opportunities but skeptical of online schemes.',
        quote: 'I don\'t have time for this. Give me straight answer.',
        vulnerabilities: ['Wants quick profits', 'Overconfident', 'Impatient'],
        responses: {
            tech_support: [
                'I run computer shop, I know this is fake.',
                'Why would Microsoft call me? I fix computers!',
                'Send me your office address, I will visit.'
            ],
            lottery: [
                'Lottery? I never bought ticket. How I win?',
                'If I won, deduct fee and send rest.',
                'This is scam. I know these tricks.'
            ],
            banking: [
                'I will visit branch personally.',
                'Give me your employee ID.',
                'My CA handles all banking.'
            ],
            investment: [
                'Guaranteed returns? Show me SEBI registration.',
                'I have CA, he will check this.',
                'Too good to be true means fake.'
            ]
        }
    },
    {
        id: 'priya',
        name: 'Priya Sharma',
        age: 28,
        location: 'Bangalore, Karnataka',
        occupation: 'IT Professional',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Priya&gender=female',
        traits: ['Tech-savvy', 'Cautious', 'Detail-oriented', 'Skeptical'],
        backstory: 'Software engineer at startup. Aware of scams but curious about new tactics.',
        quote: 'I work in tech. Explain how this works technically.',
        vulnerabilities: ['Curiosity', 'Overconfidence in tech knowledge'],
        responses: {
            tech_support: [
                'I work in IT. Tell me your IP address.',
                'Run `ipconfig` and tell me output.',
                'This is classic tech support scam. Nice try.'
            ],
            phishing: [
                'What\'s the SSL certificate of your site?',
                'I will check WHOIS of your domain.',
                'This email failed SPF check. Fake.'
            ],
            investment: [
                'Show me smart contract address.',
                'Is this audited by CertiK?',
                'Liquidity locked? Show proof.'
            ]
        }
    },
    {
        id: 'suresh',
        name: 'Suresh Patel',
        age: 72,
        location: 'Ahmedabad, Gujarat',
        occupation: 'Retired Bank Manager',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Suresh&gender=male',
        traits: ['Experienced', 'Cautious', 'Detail-oriented', 'Slow to trust'],
        backstory: 'Former bank manager. Very careful with finances but aging memory makes him slightly vulnerable.',
        quote: 'I was bank manager for 35 years. I know all tricks.',
        vulnerabilities: ['Aging memory', 'Pride in experience', 'Overly trusting of "official" calls'],
        responses: {
            banking: [
                'I was bank manager. This is not procedure.',
                'Show me written notice. I know RBI rules.',
                'I will call my branch directly.'
            ],
            investment: [
                'I managed loans for 35 years. This is Ponzi.',
                'Show me prospectus. I will read fine print.',
                'My pension is enough. No risky investments.'
            ],
            tech_support: [
                'My grandson is engineer. He will check.',
                'I don\'t use computer for banking. Only passbook.',
                'What is your escalation matrix?'
            ]
        }
    }
];

// Scam Scenarios
const SCENARIOS = {
    tech_support: {
        name: 'Tech Support Scam',
        icon: 'fa-laptop-medical',
        color: '#ff6b6b',
        messages: [
            { sender: 'scammer', text: 'Hello, this is Microsoft Technical Support. We have detected a virus on your computer.' },
            { sender: 'persona', text: 'Oh my! I don\'t understand computers. My son handles this.' },
            { sender: 'scammer', text: 'This is very urgent madam! Your data will be deleted in 1 hour. Open AnyDesk immediately.' },
            { sender: 'persona', text: 'What is AnyDesk? I only know how to open Facebook.' },
            { sender: 'scammer', text: 'Don\'t worry, I will guide you. Go to anydesk.com and download. Then give me your ID.' },
            { sender: 'persona', text: 'My grandson told me not to download unknown things. Is this safe?' },
            { sender: 'scammer', text: 'I am Microsoft certified engineer! Trust me. Call me at +91-9876543210 if you have doubt.' },
            { sender: 'persona', text: 'Okay I am trying... but my internet is slow. Can you wait?' }
        ],
        iocs: [
            { type: 'Software', value: 'AnyDesk', delay: 4 },
            { type: 'Phone', value: '+91-9876543210', delay: 6 }
        ]
    },
    lottery: {
        name: 'Lottery Scam',
        icon: 'fa-trophy',
        color: '#6bcb77',
        messages: [
            { sender: 'scammer', text: 'Congratulations! Your mobile number has won 5 crore in Lucky Draw!' },
            { sender: 'persona', text: 'I never win anything! Are you sure you have right number?' },
            { sender: 'scammer', text: 'Yes! This is confirmed. You are selected from 1 million numbers. Pay 10,000 processing fee to claim.' },
            { sender: 'persona', text: 'I have to pay first? That sounds strange.' },
            { sender: 'scammer', text: 'It is government tax madam. Pay to UPI winner@okaxis or bank account 1234567890.' },
            { sender: 'persona', text: 'I will ask my son first. He handles money matters.' },
            { sender: 'scammer', text: 'No time! Offer expires in 2 hours. Send money immediately or lose prize!' },
            { sender: 'persona', text: 'Please don\'t rush me. I am old person. Give me your number I will call back.' }
        ],
        iocs: [
            { type: 'UPI ID', value: 'winner@okaxis', delay: 4 },
            { type: 'Bank Account', value: '1234567890', delay: 4 },
            { type: 'Amount', value: '₹10,000', delay: 2 }
        ]
    },
    banking: {
        name: 'Bank Fraud Alert',
        icon: 'fa-university',
        color: '#ffd93d',
        messages: [
            { sender: 'scammer', text: 'Madam, this is SBI Fraud Department. Suspicious transaction detected on your account.' },
            { sender: 'persona', text: 'Oh no! I didn\'t do any transaction. What happened?' },
            { sender: 'scammer', text: 'Someone is trying to withdraw 50,000. We need to verify your identity immediately.' },
            { sender: 'persona', text: 'What should I do? I am very worried.' },
            { sender: 'scammer', text: 'Give me your OTP that just came. And your card number for verification.' },
            { sender: 'persona', text: 'My son told me never to share OTP. Is this real call?' },
            { sender: 'scammer', text: 'I am bank manager! If you don\'t verify, account will be frozen. Give OTP now!' },
            { sender: 'persona', text: 'I will visit branch tomorrow. I don\'t share details on phone.' }
        ],
        iocs: [
            { type: 'Impersonation', value: 'SBI Fraud Department', delay: 0 },
            { type: 'Amount', value: '₹50,000', delay: 2 }
        ]
    },
    romance: {
        name: 'Romance Scam',
        icon: 'fa-heart',
        color: '#ec4899',
        messages: [
            { sender: 'scammer', text: 'Hello beautiful! I saw your profile. You look like my dream woman.' },
            { sender: 'persona', text: 'Oh! Thank you. Who is this?' },
            { sender: 'scammer', text: 'I am David, doctor from London. I am coming to India next week. Want to meet?' },
            { sender: 'persona', text: 'I am widow, living alone. Not used to such compliments.' },
            { sender: 'scammer', text: 'I feel connection with you. But my luggage stuck at customs. Can you help with 30,000?' },
            { sender: 'persona', text: 'I don\'t have much money. Only my husband\'s pension.' },
            { sender: 'scammer', text: 'I will return double when we meet! Send to my friend\'s account: lovehelp@upi' },
            { sender: 'persona', text: 'I need to think. This is happening too fast.' }
        ],
        iocs: [
            { type: 'UPI ID', value: 'lovehelp@upi', delay: 6 },
            { type: 'Impersonation', value: 'Doctor from London', delay: 2 }
        ]
    }
};

// State Management
let currentPersonaIndex = 0;
let currentScenario = 'tech_support';
let simulationStep = 0;
let simulationInterval = null;
let chatTimer = null;
let chatSeconds = 0;
let isAutoPlay = false;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    animateStats();
    setupSmoothScroll();
    renderPersonas();
    initSimulation();
});

// Animate Statistics
function animateStats() {
    const stats = [
        { id: 'scams-prevented', target: 15420, suffix: '+' },
        { id: 'iocs-extracted', target: 8934, suffix: '' },
        { id: 'time-wasted', target: 3420, suffix: 'h' }
    ];

    stats.forEach(stat => {
        const element = document.getElementById(stat.id);
        if (!element) return;
        
        let current = 0;
        const increment = stat.target / 100;
        const timer = setInterval(() => {
            current += increment;
            if (current >= stat.target) {
                current = stat.target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current).toLocaleString() + stat.suffix;
        }, 20);
    });
}

// Smooth Scroll
function setupSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
}

// Personas Carousel
function renderPersonas() {
    const carousel = document.getElementById('personas-carousel');
    const dots = document.getElementById('persona-dots');
    
    if (!carousel) return;
    
    carousel.innerHTML = PERSONAS.map((persona, index) => `
        <div class="persona-card-large ${index === 0 ? 'active' : ''}" data-index="${index}">
            <img src="${persona.avatar}" alt="${persona.name}" class="persona-avatar-large">
            <div class="persona-info-large">
                <h3>${persona.name}</h3>
                <p class="persona-meta-large">${persona.age} • ${persona.occupation} • ${persona.location}</p>
            </div>
            <div class="persona-details">
                <h4>Backstory</h4>
                <p>${persona.backstory}</p>
            </div>
            <div class="persona-traits-large">
                ${persona.traits.map(t => `<span class="trait">${t}</span>`).join('')}
            </div>
            <blockquote class="persona-quote">"${persona.quote}"</blockquote>
        </div>
    `).join('');
    
    dots.innerHTML = PERSONAS.map((_, index) => `
        <div class="persona-dot ${index === 0 ? 'active' : ''}" onclick="goToPersona(${index})"></div>
    `).join('');
}

function updatePersonaDisplay() {
    const cards = document.querySelectorAll('.persona-card-large');
    const dots = document.querySelectorAll('.persona-dot');
    
    cards.forEach((card, i) => {
        card.classList.toggle('active', i === currentPersonaIndex);
    });
    
    dots.forEach((dot, i) => {
        dot.classList.toggle('active', i === currentPersonaIndex);
    });
    
    // Update simulation sidebar if exists
    const activePersona = PERSONAS[currentPersonaIndex];
    const display = document.getElementById('active-persona-display');
    if (display) {
        display.querySelector('img').src = activePersona.avatar;
        display.querySelector('h4').textContent = activePersona.name;
        display.querySelector('p').textContent = `${activePersona.age} • ${activePersona.occupation}`;
        display.querySelector('.persona-traits-mini').innerHTML = 
            activePersona.traits.slice(0, 2).map(t => `<span class="trait">${t}</span>`).join('');
    }
}

function nextPersona() {
    currentPersonaIndex = (currentPersonaIndex + 1) % PERSONAS.length;
    updatePersonaDisplay();
    const carousel = document.getElementById('personas-carousel');
    const card = carousel.querySelector(`[data-index="${currentPersonaIndex}"]`);
    card.scrollIntoView({ behavior: 'smooth', inline: 'center' });
}

function prevPersona() {
    currentPersonaIndex = (currentPersonaIndex - 1 + PERSONAS.length) % PERSONAS.length;
    updatePersonaDisplay();
    const carousel = document.getElementById('personas-carousel');
    const card = carousel.querySelector(`[data-index="${currentPersonaIndex}"]`);
    card.scrollIntoView({ behavior: 'smooth', inline: 'center' });
}

function goToPersona(index) {
    currentPersonaIndex = index;
    updatePersonaDisplay();
}

// Simulation Management
function initSimulation() {
    updatePersonaDisplay();
    resetSimulation();
}

function changeScenario() {
    const select = document.getElementById('scenario-select');
    currentScenario = select.value;
    resetSimulation();
}

function resetSimulation() {
    stopSimulation();
    simulationStep = 0;
    chatSeconds = 0;
    
    const messagesContainer = document.getElementById('simulation-messages');
    const iocsContainer = document.getElementById('live-iocs');
    const timer = document.getElementById('chat-timer');
    
    if (messagesContainer) {
        messagesContainer.innerHTML = `
            <div class="system-message" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                <i class="fas fa-info-circle" style="font-size: 2rem; margin-bottom: 1rem; display: block;"></i>
                Click "Start Simulation" to begin the conversation
            </div>
        `;
    }
    
    if (iocsContainer) {
        iocsContainer.innerHTML = '<p class="empty-state">Waiting for scammer...</p>';
    }
    
    if (timer) {
        timer.textContent = '00:00';
    }
    
    document.getElementById('step-btn').disabled = true;
}

function startSimulation() {
    resetSimulation();
    document.getElementById('step-btn').disabled = false;
    
    // Remove system message
    const messagesContainer = document.getElementById('simulation-messages');
    messagesContainer.innerHTML = '';
    
    // Start timer
    startChatTimer();
    
    // Show first message
    stepSimulation();
}

function startChatTimer() {
    if (chatTimer) clearInterval(chatTimer);
    chatTimer = setInterval(() => {
        chatSeconds++;
        const mins = Math.floor(chatSeconds / 60).toString().padStart(2, '0');
        const secs = (chatSeconds % 60).toString().padStart(2, '0');
        const timer = document.getElementById('chat-timer');
        if (timer) timer.textContent = `${mins}:${secs}`;
    }, 1000);
}

function stopSimulation() {
    if (simulationInterval) {
        clearInterval(simulationInterval);
        simulationInterval = null;
    }
    if (chatTimer) {
        clearInterval(chatTimer);
        chatTimer = null;
    }
    isAutoPlay = false;
    updateAutoPlayButton();
}

function toggleAutoPlay() {
    isAutoPlay = !isAutoPlay;
    updateAutoPlayButton();
    
    if (isAutoPlay) {
        if (simulationStep === 0) startSimulation();
        autoPlayLoop();
    } else {
        clearInterval(simulationInterval);
    }
}

function updateAutoPlayButton() {
    const btn = document.getElementById('autoplay-btn');
    if (btn) {
        btn.innerHTML = isAutoPlay ? 
            '<i class="fas fa-pause"></i> Pause' : 
            '<i class="fas fa-magic"></i> Auto-Play';
        btn.classList.toggle('btn-accent', isAutoPlay);
    }
}

function autoPlayLoop() {
    if (!isAutoPlay) return;
    
    stepSimulation();
    
    const scenario = SCENARIOS[currentScenario];
    if (simulationStep < scenario.messages.length) {
        simulationInterval = setTimeout(autoPlayLoop, 2000 + Math.random() * 1000);
    } else {
        isAutoPlay = false;
        updateAutoPlayButton();
    }
}

function stepSimulation() {
    const scenario = SCENARIOS[currentScenario];
    const messagesContainer = document.getElementById('simulation-messages');
    const iocsContainer = document.getElementById('live-iocs');
    
    if (simulationStep >= scenario.messages.length) {
        // End of conversation
        addMessage({
            sender: 'system',
            text: '--- Conversation ended. Scammer disconnected. ---',
            isSystem: true
        });
        stopSimulation();
        return;
    }
    
    const msg = scenario.messages[simulationStep];
    
    // Show typing indicator for persona
    if (msg.sender === 'persona') {
        showTypingIndicator();
        setTimeout(() => {
            hideTypingIndicator();
            addMessage(msg);
            checkForIOCs(simulationStep);
        }, 1000 + Math.random() * 1000);
    } else {
        addMessage(msg);
        checkForIOCs(simulationStep);
    }
    
    simulationStep++;
    
    // Disable step button at end
    if (simulationStep >= scenario.messages.length) {
        document.getElementById('step-btn').disabled = true;
    }
}

function showTypingIndicator() {
    const container = document.getElementById('simulation-messages');
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator active';
    indicator.id = 'typing-indicator';
    indicator.innerHTML = `
        <span>Persona is typing</span>
        <div class="typing-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    container.appendChild(indicator);
    container.scrollTop = container.scrollHeight;
}

function hideTypingIndicator() {
    const indicator = document.getElementById('typing-indicator');
    if (indicator) indicator.remove();
}

function addMessage(msg) {
    const container = document.getElementById('simulation-messages');
    const persona = PERSONAS[currentPersonaIndex];
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${msg.sender}`;
    
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    if (msg.isSystem) {
        messageDiv.innerHTML = `<div class="message-content" style="text-align: center; color: var(--text-muted); font-style: italic;">${msg.text}</div>`;
    } else {
        messageDiv.innerHTML = `
            <div class="message-header">
                <i class="fas fa-${msg.sender === 'scammer' ? 'user-secret' : 'user'}"></i>
                <span>${msg.sender === 'scammer' ? 'Scammer' : persona.name}</span>
            </div>
            <div class="message-content">${msg.text}</div>
            <div class="message-time">${time}</div>
        `;
    }
    
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

function checkForIOCs(stepIndex) {
    const scenario = SCENARIOS[currentScenario];
    const iocsContainer = document.getElementById('live-iocs');
    
    // Check if any IOCs should be revealed at this step
    const newIOCs = scenario.iocs.filter(ioc => ioc.delay === stepIndex);
    
    if (newIOCs.length > 0) {
        // Clear empty state if first IOC
        if (iocsContainer.querySelector('.empty-state')) {
            iocsContainer.innerHTML = '';
        }
        
        newIOCs.forEach(ioc => {
            const iocDiv = document.createElement('div');
            iocDiv.className = 'ioc-item-live';
            iocDiv.innerHTML = `
                <div class="ioc-type">${ioc.type}</div>
                <div class="ioc-value">${ioc.value}</div>
            `;
            iocsContainer.appendChild(iocDiv);
            
            // Flash effect
            iocDiv.style.animation = 'none';
            setTimeout(() => {
                iocDiv.style.animation = 'slideIn 0.3s ease';
            }, 10);
        });
    }
}

// Utility Functions
function copyCode(btn) {
    const codeBlock = btn.closest('.code-block').querySelector('code');
    navigator.clipboard.writeText(codeBlock.textContent).then(() => {
        const original = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => {
            btn.innerHTML = original;
        }, 2000);
    });
}

// Expose functions to window for HTML onclick handlers
window.toggleTheme = toggleTheme;
window.nextPersona = nextPersona;
window.prevPersona = prevPersona;
window.goToPersona = goToPersona;
window.changeScenario = changeScenario;
window.startSimulation = startSimulation;
window.resetSimulation = resetSimulation;
window.stepSimulation = stepSimulation;
window.toggleAutoPlay = toggleAutoPlay;
window.copyCode = copyCode;