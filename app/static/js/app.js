document.addEventListener("DOMContentLoaded", () => {
    // --- STORES AND STATES ---
    let activeTab = "qa";
    let lastGeneratedResponseText = ""; // Stored for copy commands

    // --- DOM REFERENCES ---
    const navItems = document.querySelectorAll(".nav-item");
    const tabTitle = document.getElementById("tab-title");
    const tabDescription = document.getElementById("tab-description");
    const formViews = document.querySelectorAll(".form-view");
    const assistantForm = document.getElementById("assistant-form");
    const modelSelect = document.getElementById("model-select");
    const submitBtn = document.getElementById("submit-btn");
    const clearBtn = document.getElementById("clear-btn");
    const loader = document.getElementById("loader");
    const loaderTip = document.getElementById("loader-tip");
    const alertBox = document.getElementById("alert-box");
    const alertMessage = document.getElementById("alert-message");
    const closeAlertBtn = document.getElementById("close-alert-btn");
    const outputPanel = document.getElementById("output-panel");
    const outputEngine = document.getElementById("output-engine");
    const outputContent = document.getElementById("output-content");
    const copyBtn = document.getElementById("copy-btn");
    const clearOutputBtn = document.getElementById("clear-output-btn");
    const backendStatusText = document.getElementById("backend-status");
    const pulseDot = document.querySelector(".pulse-dot");

    // Dynamic loader suggestions
    const loaderTips = [
        "Consulting learning curriculums...",
        "Formulating pedagogical analogies...",
        "Compiling multiple-choice distractors...",
        "Analyzing text structure for key arguments...",
        "Selecting curated educational references...",
        "Translating complex paradigms into simple concepts..."
    ];
    let loaderTipInterval = null;

    // Tab metadata dictionary
    const tabMeta = {
        qa: {
            title: "Q&A Tutor",
            desc: "Submit academic questions to receive structured answers, step-by-step logic, and real-world examples."
        },
        explain: {
            title: "Concept Explainer",
            desc: "Demystify complex ideas by tailoring the explanation level to your current knowledge profile."
        },
        quiz: {
            title: "Quiz Generator",
            desc: "Test your comprehension with custom multiple-choice quizzes complete with answers and explanations."
        },
        summarize: {
            title: "Note Summarizer",
            desc: "Paste notes or textbook chapters to distill them into concise paragraphs, structural logs, or bullet points."
        },
        recommend: {
            title: "Study Roadmap",
            desc: "Set up a personalized study plan complete with timeline checkpoints, resource libraries, and projects."
        }
    };

    // --- TAB SWITCH LOGIC ---
    navItems.forEach(item => {
        item.addEventListener("click", () => {
            const selectedTab = item.getAttribute("data-tab");
            if (selectedTab === activeTab) return;

            // Update sidebar buttons
            navItems.forEach(btn => btn.classList.remove("active"));
            item.classList.add("active");

            // Update workspace headings
            activeTab = selectedTab;
            tabTitle.textContent = tabMeta[selectedTab].title;
            tabDescription.textContent = tabMeta[selectedTab].desc;

            // Toggle form views
            formViews.forEach(view => {
                if (view.getAttribute("id-view") === selectedTab) {
                    view.classList.add("active");
                } else {
                    view.classList.remove("active");
                }
            });

            // Adjust form validation requirements on-the-fly
            toggleFormRequirements(selectedTab);

            // Re-initialize Lucide icons in text header updates if any
            if (window.lucide) {
                window.lucide.createIcons();
            }
        });
    });

    function toggleFormRequirements(tab) {
        // Reset all required flags
        document.querySelectorAll("#dynamic-inputs input, #dynamic-inputs textarea").forEach(el => {
            el.required = false;
        });

        // Set active views specific requirements
        if (tab === "qa") {
            document.getElementById("qa-question").required = true;
        } else if (tab === "explain") {
            document.getElementById("explain-concept").required = true;
        } else if (tab === "quiz") {
            document.getElementById("quiz-topic").required = true;
        } else if (tab === "summarize") {
            document.getElementById("summarize-text").required = true;
        } else if (tab === "recommend") {
            document.getElementById("recommend-topic").required = true;
            document.getElementById("recommend-goals").required = true;
        }
    }

    // Initialize required flags
    toggleFormRequirements("qa");

    // --- LOADER EFFECTS ---
    function startLoaderTipCycle() {
        let i = 0;
        loaderTip.textContent = loaderTips[0];
        loaderTipInterval = setInterval(() => {
            i = (i + 1) % loaderTips.length;
            loaderTip.textContent = loaderTips[i];
        }, 3000);
    }

    function stopLoaderTipCycle() {
        if (loaderTipInterval) {
            clearInterval(loaderTipInterval);
            loaderTipInterval = null;
        }
    }

    // --- DISPLAY UTILITIES ---
    function showAlert(message) {
        alertMessage.textContent = message;
        alertBox.classList.remove("hidden");
        alertBox.scrollIntoView({ behavior: "smooth" });
    }

    function hideAlert() {
        alertBox.classList.add("hidden");
    }

    closeAlertBtn.addEventListener("click", hideAlert);

    // --- RENDER COMPONENT FORMATTERS ---

    // Lightweight Markdown parser
    function renderMarkdown(text) {
        if (!text) return "";
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Code blocks: ```language ... ```
        html = html.replace(/```(?:[a-zA-Z0-9]+)?\n([\s\S]*?)\n```/g, "<pre><code>$1</code></pre>");
        // Inline code blocks: `code`
        html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
        // Headers (H3, H4, H2)
        html = html.replace(/^### (.*?)$/gm, "<h3>$1</h3>");
        html = html.replace(/^#### (.*?)$/gm, "<h4>$1</h4>");
        html = html.replace(/^## (.*?)$/gm, "<h3>$1</h3>");
        // Bold: **text**
        html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
        // Unordered lists
        html = html.replace(/^\s*[-*]\s+(.*?)$/gm, "<li>$1</li>");
        // Combine consecutive li elements
        html = html.replace(/(<li>.*?<\/li>)+/g, "<ul>$&</ul>");
        
        // Standard paragraphs by splitting double-newlines
        let segments = html.split(/\n\n+/);
        html = segments.map(seg => {
            const trimmed = seg.trim();
            if (trimmed.startsWith("<h3>") || trimmed.startsWith("<h4>") || trimmed.startsWith("<pre>") || trimmed.startsWith("<ul>")) {
                return trimmed;
            }
            return `<p>${trimmed.replace(/\n/g, "<br>")}</p>`;
        }).join("");

        return html;
    }

    // Dynamic Quiz generator renderer
    function renderQuizHTML(questions) {
        let html = '<div class="quiz-container">';
        questions.forEach((q, index) => {
            const text = q.questionText || q.question_text || "Malformed Question";
            const opts = q.options || [];
            const ans = q.correctAnswer || q.correct_answer || "";
            const expl = q.explanation || "No explanation provided.";

            html += `
            <div class="quiz-card" id="quiz-card-${index}">
                <div class="quiz-question-header">
                    <span class="quiz-num-badge">${index + 1}</span>
                    <span class="quiz-question-text">${text}</span>
                </div>
                <div class="quiz-options-list">
            `;

            opts.forEach(opt => {
                const isCorrect = opt.trim().toLowerCase() === ans.trim().toLowerCase();
                const escapedOpt = opt.replace(/"/g, "&quot;");
                html += `
                <button type="button" class="quiz-option-btn" 
                        data-question="${index}" 
                        data-option="${escapedOpt}" 
                        data-correct="${isCorrect}">${opt}</button>
                `;
            });

            html += `
                </div>
                <div class="quiz-explanation-box hidden" id="quiz-expl-${index}">
                    <p><strong>Correct Answer:</strong> ${ans}</p>
                    <p style="margin-top: 0.5rem; color: var(--color-text-main);">${expl}</p>
                </div>
            </div>
            `;
        });
        html += "</div>";
        return html;
    }

    // Dynamic Roadmap Timeline generator renderer
    function renderRoadmapHTML(data) {
        const roadmap = data.roadmap || [];
        const resources = data.resources || [];
        const suggestions = data.practice_suggestions || [];
        
        let html = '<div class="output-text-block">';
        
        // 1. Timeline layout
        html += `<h3><i data-lucide="map" style="display:inline-block; vertical-align:middle; margin-right:8px; width:20px; height:20px; color:var(--accent-secondary)"></i>Study Timeline</h3>`;
        html += '<div class="roadmap-timeline" style="margin-top: 1.5rem;">';
        roadmap.forEach((step, idx) => {
            html += `
            <div class="roadmap-phase-node ${idx === 0 ? 'active' : ''}">
                <div class="roadmap-phase-card">
                    <div class="roadmap-phase-meta">
                        <span>${step.phase || `Phase ${idx+1}`}</span>
                        <span><i data-lucide="clock" style="display:inline-block; vertical-align:middle; width:14px; height:14px; margin-right:4px;"></i>${step.duration || 'Flexible'}</span>
                    </div>
                    <div class="roadmap-phase-title">${step.title}</div>
                    <div class="roadmap-phase-desc">${step.description}</div>
                </div>
            </div>
            `;
        });
        html += '</div>';

        // 2. Resource recommendations grid
        if (resources.length > 0) {
            html += `<h3><i data-lucide="library" style="display:inline-block; vertical-align:middle; margin-right:8px; width:20px; height:20px; color:var(--accent-secondary)"></i>Curated Resources</h3>`;
            html += '<div class="resources-grid" style="margin-top: 1.5rem;">';
            resources.forEach(res => {
                html += `
                <div class="resource-card">
                    <span class="resource-badge">${res.type}</span>
                    <div class="resource-name">${res.name}</div>
                    <div class="resource-desc">${res.description}</div>
                </div>
                `;
            });
            html += '</div>';
        }

        // 3. Practice checklist
        if (suggestions.length > 0) {
            html += `<h3><i data-lucide="check-square" style="display:inline-block; vertical-align:middle; margin-right:8px; width:20px; height:20px; color:var(--accent-primary)"></i>Practice Challenges</h3>`;
            html += '<ul class="practice-checklist" style="margin-top: 1.5rem;">';
            suggestions.forEach(sug => {
                html += `
                <li class="practice-item">
                    <i data-lucide="check-circle-2"></i>
                    <div class="practice-text">${sug}</div>
                </li>
                `;
            });
            html += '</ul>';
        }

        html += '</div>';
        return html;
    }

    // --- FORM ACTIONS AND API SUBMISSIONS ---
    assistantForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        hideAlert();
        outputPanel.classList.add("hidden");
        
        const provider = modelSelect.value;
        let url = "";
        let bodyPayload = { model_preference: provider };

        // Structure payload based on active tab
        if (activeTab === "qa") {
            url = "/qa";
            bodyPayload.question = document.getElementById("qa-question").value;
        } else if (activeTab === "explain") {
            url = "/explain";
            bodyPayload.concept = document.getElementById("explain-concept").value;
            bodyPayload.level = document.getElementById("explain-level").value;
        } else if (activeTab === "quiz") {
            url = "/quiz";
            bodyPayload.topic = document.getElementById("quiz-topic").value;
            bodyPayload.difficulty = document.getElementById("quiz-difficulty").value;
            bodyPayload.num_questions = parseInt(document.getElementById("quiz-count").value, 10);
        } else if (activeTab === "summarize") {
            url = "/summarize";
            bodyPayload.text = document.getElementById("summarize-text").value;
            bodyPayload.format = document.getElementById("summarize-format").value;
        } else if (activeTab === "recommend") {
            url = "/recommend";
            bodyPayload.topic = document.getElementById("recommend-topic").value;
            bodyPayload.goals = document.getElementById("recommend-goals").value;
            bodyPayload.skill_level = document.getElementById("recommend-level").value;
        }

        // Show UI loader overlay and block button
        loader.classList.remove("hidden");
        submitBtn.disabled = true;
        startLoaderTipCycle();

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(bodyPayload)
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Server returned code ${response.status}`);
            }

            const data = await response.json();
            
            // Format and display response
            renderResponseData(data);
            
        } catch (err) {
            loggerError(`API Failure on endpoint ${url}: ${err.message}`);
            showAlert(`Failed to retrieve data: ${err.message}. Please verify settings or try again.`);
        } finally {
            // Unblock and hide loader
            loader.classList.add("hidden");
            submitBtn.disabled = false;
            stopLoaderTipCycle();
        }
    });

    function renderResponseData(data) {
        outputEngine.textContent = data.model_used || "AI Engine";
        outputContent.innerHTML = ""; // Flush previous outputs

        let htmlString = "";

        if (activeTab === "qa") {
            lastGeneratedResponseText = data.answer;
            htmlString = `<div class="output-text-block">${renderMarkdown(data.answer)}</div>`;
        } else if (activeTab === "explain") {
            lastGeneratedResponseText = data.explanation;
            htmlString = `<div class="output-text-block"><h3>Explanation: ${data.concept} (${data.level} Level)</h3>${renderMarkdown(data.explanation)}</div>`;
        } else if (activeTab === "quiz") {
            // Stringify JSON array for clipboard copies
            lastGeneratedResponseText = JSON.stringify(data.questions, null, 2);
            htmlString = renderQuizHTML(data.questions);
        } else if (activeTab === "summarize") {
            lastGeneratedResponseText = data.summary;
            htmlString = `
                <div class="output-text-block">
                    <h3>distilled Summary (${data.format})</h3>
                    <p style="font-size: 0.85rem; color: var(--accent-secondary); margin-bottom: 1rem;">
                        Original: ${data.original_length} chars | Summary: ${data.summary_length} chars
                    </p>
                    ${renderMarkdown(data.summary)}
                </div>
            `;
        } else if (activeTab === "recommend") {
            lastGeneratedResponseText = JSON.stringify({ roadmap: data.roadmap, resources: data.resources, practice: data.practice_suggestions }, null, 2);
            htmlString = renderRoadmapHTML(data);
        }

        outputContent.innerHTML = htmlString;
        outputPanel.classList.remove("hidden");
        
        // Auto scroll to results
        outputPanel.scrollIntoView({ behavior: "smooth" });

        // Update dynamic Lucide SVGs if any
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    // --- INTERACTIVE MCQ SELECT HANDLERS ---
    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("quiz-option-btn") && !e.target.classList.contains("disabled")) {
            const btn = e.target;
            const questionIdx = btn.getAttribute("data-question");
            const isCorrect = btn.getAttribute("data-correct") === "true";
            
            const card = document.getElementById(`quiz-card-${questionIdx}`);
            const options = card.querySelectorAll(".quiz-option-btn");
            const explanationBox = document.getElementById(`quiz-expl-${questionIdx}`);

            // Lock and disable inputs
            options.forEach(opt => {
                opt.classList.add("disabled");
                // Highlight the correct option in green if current was wrong
                if (opt.getAttribute("data-correct") === "true" && !isCorrect) {
                    opt.classList.add("highlight-correct");
                }
            });

            // Highlight choice
            if (isCorrect) {
                btn.classList.add("selected-correct");
            } else {
                btn.classList.add("selected-incorrect");
            }

            // Slide explanation box open
            explanationBox.classList.remove("hidden");
        }
    });

    // --- BUTTON CONTROLS ---

    // Clear Inputs Button
    clearBtn.addEventListener("click", () => {
        const activeFormView = document.querySelector(`.form-view[id-view="${activeTab}"]`);
        if (activeFormView) {
            activeFormView.querySelectorAll("textarea, input").forEach(el => {
                el.value = "";
            });
        }
        hideAlert();
    });

    // Dismiss Output Panel
    clearOutputBtn.addEventListener("click", () => {
        outputPanel.classList.add("hidden");
        outputContent.innerHTML = "";
        lastGeneratedResponseText = "";
    });

    // Copy to Clipboard Action
    copyBtn.addEventListener("click", async () => {
        if (!lastGeneratedResponseText) return;

        try {
            await navigator.clipboard.writeText(lastGeneratedResponseText);
            
            // UI feedback toggle
            const originalTooltip = copyBtn.getAttribute("data-tooltip");
            copyBtn.setAttribute("data-tooltip", "Copied!");
            copyBtn.innerHTML = '<i data-lucide="check" style="color: var(--color-success)"></i>';
            if (window.lucide) window.lucide.createIcons();

            setTimeout(() => {
                copyBtn.setAttribute("data-tooltip", originalTooltip);
                copyBtn.innerHTML = '<i data-lucide="copy"></i>';
                if (window.lucide) window.lucide.createIcons();
            }, 2000);
        } catch (err) {
            loggerError("Clipboard copy failed:", err);
            showAlert("Failed to copy results to clipboard.");
        }
    });

    // --- SYSTEM STATUS MONITOR ---
    async function checkBackendHealth() {
        try {
            const res = await fetch("/health");
            if (res.ok) {
                const data = await res.json();
                backendStatusText.textContent = "Engine Connected";
                pulseDot.className = "pulse-dot"; // reset
            } else {
                throw new Error("Bad response");
            }
        } catch (err) {
            backendStatusText.textContent = "Backend Offline";
            pulseDot.className = "pulse-dot error";
        }
    }

    // Trigger health checks
    checkBackendHealth();
    setInterval(checkBackendHealth, 15000);

    // Initial Lucide compilation
    if (window.lucide) {
        window.lucide.createIcons();
    }

    // Local debug logger
    function loggerError(...args) {
        console.error("[EduGenie UI]", ...args);
    }
});
