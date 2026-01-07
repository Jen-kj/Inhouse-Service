// ==========================================
// 온보딩 시스템 - Vanilla JavaScript
// ==========================================

// State
const USER_ID = 'user_001'; // In production, get from authentication
let questProgress = {};
let allQA = [];
let votedQuestions = new Set(); // Track voted questions

const DUMMY_QA = [
    {
        id: 101,
        question: '동호회는 어떤 게 있나요?',
        answer: 'Nota Clubs 페이지에서 러닝 크루, 독서 모임, 요가 클럽 등 다양한 동호회를 확인할 수 있습니다.',
        tags: '문화, 동호회',
        helpful_count: 14,
        asker: '송민재'
    },
    {
        id: 102,
        question: '모니터 추가 신청은 어디서 하나요?',
        answer: 'Service Desk > IT 지원 카테고리에서 "외부 모니터 구매 신청"을 작성하시면 됩니다.',
        tags: '장비, IT',
        helpful_count: 12,
        asker: '이지은'
    },
    {
        id: 103,
        question: '재택근무는 어떻게 신청하나요?',
        answer: '팀 리드에게 사전 공유 후 슬랙 #출퇴근 채널에 알려주시면 됩니다.',
        tags: '근무, 재택',
        helpful_count: 10,
        asker: '강혜진'
    },
    {
        id: 104,
        question: '법인카드는 어떻게 사용하나요?',
        answer: '법인카드는 경영지원팀에 신청하시면 됩니다. 사용 후 영수증은 반드시 보관해주세요.',
        tags: '복지, 장비',
        helpful_count: 18,
        asker: '김민수'
    },
    {
        id: 105,
        question: '리더십 원칙(LP)은 어디서 확인할 수 있나요?',
        answer: '사내 위키의 Culture 섹션에서 확인하실 수 있습니다. 주요 LP는 Ownership, Trust, Customer-Centric입니다.',
        tags: 'LP, 문화',
        helpful_count: 20,
        asker: '박준호'
    },
    {
        id: 106,
        question: '회의실 예약은 어떻게 하나요?',
        answer: 'Nota Space > Timeline View에서 빈 시간대를 클릭하여 예약할 수 있습니다.',
        tags: '시설, 회의실',
        helpful_count: 8,
        asker: '최서연'
    },
];

// DOM Elements
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const congratsToast = document.getElementById('congratsToast');
const questItems = document.querySelectorAll('.quest-item');
const qaList = document.getElementById('qaList');
const searchInput = document.getElementById('searchInput');
const tagButtons = document.querySelectorAll('.tag-btn');
const askQuestionBtn = document.getElementById('askQuestionBtn');
const questionModal = document.getElementById('questionModal');
const cancelBtn = document.getElementById('cancelBtn');
const submitBtn = document.getElementById('submitBtn');

// ==========================================
// 1. Initialize App
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    loadQuestProgress();
    loadQA();
    setupEventListeners();
});

// ==========================================
// 2. Quest Tracking (LocalStorage)
// ==========================================
function loadQuestProgress() {
    // Try to load from localStorage first (for demo purposes)
    const savedProgress = localStorage.getItem('nota_quest_progress');
    if (savedProgress) {
        questProgress = JSON.parse(savedProgress);
        updateQuestUI();
    }
    
    // In production, fetch from API:
    // fetch(`/api/quests/${USER_ID}`)
    //     .then(res => res.json())
    //     .then(data => {
    //         questProgress = data;
    //         updateQuestUI();
    //     });
}

function updateQuestUI() {
    questItems.forEach(item => {
        const questId = item.dataset.quest;
        if (questProgress[questId]) {
            item.classList.add('completed');
        }
    });
    
    updateProgressBar();
}

function updateProgressBar() {
    const totalQuests = questItems.length;
    const completedQuests = Object.values(questProgress).filter(Boolean).length;
    const percentage = Math.round((completedQuests / totalQuests) * 100);
    
    progressBar.style.width = `${percentage}%`;
    progressBar.textContent = `${percentage}%`;
    progressText.textContent = `노타 적응 ${percentage}% 완료!`;
}

// ==========================================
// 3. Event Listeners
// ==========================================
function setupEventListeners() {
    // Quest item click (Event Delegation)
    questItems.forEach(item => {
        item.addEventListener('click', () => handleQuestClick(item));
    });
    
    // Live Search (keyup event)
    searchInput.addEventListener('keyup', (e) => {
        handleSearch(e.target.value);
    });
    
    // Tag filter
    tagButtons.forEach(btn => {
        btn.addEventListener('click', () => handleTagFilter(btn));
    });
    
    // Helpful button (Event Delegation on parent)
    qaList.addEventListener('click', (e) => {
        if (e.target.classList.contains('helpful-btn') || e.target.closest('.helpful-btn')) {
            const btn = e.target.closest('.helpful-btn');
            handleHelpfulVote(btn);
        }
    });
    
    // Question modal
    askQuestionBtn.addEventListener('click', () => {
        questionModal.classList.add('show');
    });
    
    cancelBtn.addEventListener('click', () => {
        questionModal.classList.remove('show');
    });
    
    submitBtn.addEventListener('click', handleQuestionSubmit);
}

// ==========================================
// 4. Quest Click Handler
// ==========================================
function handleQuestClick(item) {
    const questId = item.dataset.quest;
    const isCompleted = item.classList.contains('completed');
    
    // Toggle state
    questProgress[questId] = !isCompleted;
    
    // Update UI
    if (!isCompleted) {
        item.classList.add('completed');
        showCongratsToast();
    } else {
        item.classList.remove('completed');
    }
    
    updateProgressBar();
    
    // Save to localStorage
    localStorage.setItem('nota_quest_progress', JSON.stringify(questProgress));
    
    // In production, also save to API:
    // fetch(`/api/quests/${USER_ID}/${questId}`, {
    //     method: 'POST',
    //     headers: { 'Content-Type': 'application/json' },
    //     body: JSON.stringify({ completed: !isCompleted })
    // });
}

function showCongratsToast() {
    congratsToast.classList.add('show');
    setTimeout(() => {
        congratsToast.classList.remove('show');
    }, 2000);
}

// ==========================================
// 5. Load Q&A (Fetch API)
// ==========================================
async function loadQA() {
    try {
        const response = await fetch('/api/qa');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        allQA = await response.json();
        renderQA(allQA);
    } catch (error) {
        console.error('Failed to load Q&A:', error);
        allQA = [...DUMMY_QA];
        renderQA(allQA);
    }
}

function renderQA(qaData) {
    qaList.innerHTML = qaData.map(qa => createQAItem(qa)).join('');
}

function createQAItem(qa) {
    const tags = qa.tags ? qa.tags.split(',').map(t => t.trim()) : [];
    const isVoted = votedQuestions.has(qa.id);
    
    return `
        <div class="qa-item" data-qa-id="${qa.id}">
            <div class="qa-question">${qa.question}</div>
            <div class="qa-answer">${qa.answer}</div>
            <div class="qa-footer">
                <div class="qa-tags">
                    ${tags.map(tag => `<span class="qa-tag">${tag}</span>`).join('')}
                </div>
                <button class="helpful-btn ${isVoted ? 'voted' : ''}" data-qa-id="${qa.id}">
                    👍 <span class="helpful-count">${qa.helpful_count}</span>
                </button>
            </div>
        </div>
    `;
}

// ==========================================
// 6. Live Search (keyup event)
// ==========================================
function handleSearch(searchTerm) {
    const filtered = allQA.filter(qa => {
        const searchLower = searchTerm.toLowerCase();
        return qa.question.toLowerCase().includes(searchLower) || 
               qa.answer.toLowerCase().includes(searchLower);
    });
    
    renderQA(filtered);
}

// ==========================================
// 7. Tag Filter
// ==========================================
function handleTagFilter(button) {
    const tag = button.dataset.tag;
    
    // Update active state
    tagButtons.forEach(btn => btn.classList.remove('active'));
    button.classList.add('active');
    
    // Filter Q&A
    if (tag === '') {
        renderQA(allQA);
    } else {
        const filtered = allQA.filter(qa => 
            qa.tags && qa.tags.includes(tag)
        );
        renderQA(filtered);
    }
}

// ==========================================
// 8. Helpful Vote (classList.toggle)
// ==========================================
async function handleHelpfulVote(button) {
    const qaId = parseInt(button.dataset.qaId);
    
    // Prevent double voting
    if (votedQuestions.has(qaId)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/qa/${qaId}/helpful`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update UI
            button.classList.add('voted');
            button.querySelector('.helpful-count').textContent = data.helpful_count;
            votedQuestions.add(qaId);
            
            // Update local data
            const qa = allQA.find(q => q.id === qaId);
            if (qa) {
                qa.helpful_count = data.helpful_count;
            }
            
            // Animation effect
            button.style.transform = 'scale(1.1)';
            setTimeout(() => {
                button.style.transform = 'scale(1)';
            }, 200);
        }
    } catch (error) {
        console.error('Failed to vote:', error);
    }
}

// ==========================================
// 9. Ask Question
// ==========================================
async function handleQuestionSubmit() {
    const question = document.getElementById('questionInput').value.trim();
    const detail = document.getElementById('detailInput').value.trim();
    const asker = document.getElementById('askerInput').value.trim();
    const tags = document.getElementById('tagsInput').value.trim();
    
    if (!question || !asker) {
        alert('질문과 이름을 모두 입력해주세요.');
        return;
    }
    
    // 질문과 상세내용 합치기
    const fullAnswer = detail ? `${detail}` : '답변 대기 중...';
    
    // Knowledge Distillation: Check for similar questions
    const similarQuestions = allQA.filter(qa => {
        const similarity = calculateSimilarity(question.toLowerCase(), qa.question.toLowerCase());
        return similarity > 0.5;
    });
    
    if (similarQuestions.length > 0) {
        const shouldContinue = confirm(
            '비슷한 질문이 이미 있습니다:\n\n' + 
            similarQuestions.map(q => `• ${q.question}`).join('\n') + 
            '\n\n그래도 질문을 등록하시겠습니까?'
        );
        
        if (!shouldContinue) {
            return;
        }
    }
    
    try {
        const response = await fetch('/api/qa', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                answer: fullAnswer,
                asker: asker,
                tags: tags
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Close modal
            questionModal.classList.remove('show');
            
            // Reset form
            document.getElementById('questionInput').value = '';
            document.getElementById('detailInput').value = '';
            document.getElementById('askerInput').value = '';
            document.getElementById('tagsInput').value = '';
            
            // Reload Q&A
            loadQA();
            
            alert('✅ 질문이 등록되었습니다! 곧 답변이 달릴 거예요 😊');
        }
    } catch (error) {
        console.error('Failed to submit question:', error);
        alert('❌ 질문 등록에 실패했습니다.');
    }
}

// ==========================================
// 10. Similarity Calculation (Simple)
// ==========================================
function calculateSimilarity(str1, str2) {
    const words1 = str1.split(' ');
    const words2 = str2.split(' ');
    
    let matchCount = 0;
    words1.forEach(word => {
        if (words2.includes(word) && word.length > 2) {
            matchCount++;
        }
    });
    
    return matchCount / Math.max(words1.length, words2.length);
}
