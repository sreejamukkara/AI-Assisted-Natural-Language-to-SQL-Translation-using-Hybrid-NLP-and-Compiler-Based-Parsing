document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const queryInput = document.getElementById('queryInput');
    const micBtn = document.getElementById('micBtn');
    const runBtn = document.getElementById('runBtn');
    const llmToggle = document.getElementById('llmToggle');
    const dialectSelect = document.getElementById('dialectSelect');
    const loading = document.getElementById('loading');
    const aiBanner = document.getElementById('aiBanner');
    const errorBanner = document.getElementById('errorBanner');
    
    // Result UI
    const tableHeadRow = document.getElementById('tableHeadRow');
    const tableBody = document.getElementById('tableBody');
    const emptyState = document.getElementById('emptyState');
    
    // Pipelines UI
    const tokensView = document.getElementById('tokensView');
    const astView = document.getElementById('astView');
    const semanticView = document.getElementById('semanticView');
    const irView = document.getElementById('irView');
    const optView = document.getElementById('optView');
    const sqlView = document.getElementById('sqlView');
    const copyBtn = document.getElementById('copyBtn');

    // Speech Recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        
        recognition.onstart = () => micBtn.classList.add('recording');
        recognition.onend = () => micBtn.classList.remove('recording');
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            queryInput.value = transcript;
        };
        
        micBtn.addEventListener('click', () => {
            micBtn.classList.contains('recording') ? recognition.stop() : recognition.start();
        });
    } else {
        micBtn.style.display = 'none';
    }

    // Accordions
    document.querySelectorAll('.accordion-header').forEach(btn => {
        btn.addEventListener('click', () => {
            const content = btn.nextElementSibling;
            btn.classList.toggle('active');
            if (content.classList.contains('open')) {
                content.classList.remove('open');
            } else {
                content.classList.add('open');
            }
        });
    });

    copyBtn.addEventListener('click', () => {
        const text = sqlView.textContent;
        navigator.clipboard.writeText(text);
        copyBtn.textContent = 'Copied!';
        setTimeout(() => copyBtn.textContent = 'Copy', 2000);
    });

    queryInput.addEventListener('keypress', (e) => {
        if(e.key === 'Enter') runQuery();
    });
    
    runBtn.addEventListener('click', runQuery);

    async function runQuery() {
        const q = queryInput.value.trim();
        if(!q) return;

        setLoading(true);
        resetUI();

        try {
            const res = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    query: q, 
                    use_llm_fallback: llmToggle.checked,
                    dialect: dialectSelect.value
                })
            });
            const data = await res.json();
            
            renderPipeline(data.steps);
            
            if(data.steps.diagnostics) {
                renderError(data.steps.diagnostics);
            }
            
            if(data.steps.used_llm) {
                aiBanner.classList.remove('hidden');
            }

            if(data.result && data.result.columns) {
                 renderTable(data.result.columns, data.result.rows);
            }
            
        } catch(e) {
            renderError({message: e.message || "Failed to execute query"});
        } finally {
            setLoading(false);
        }
    }

    function resetUI() {
         aiBanner.classList.add('hidden');
         errorBanner.classList.add('hidden');
         tableHeadRow.innerHTML = '';
         tableBody.innerHTML = '';
         emptyState.classList.remove('hidden');
         
         tokensView.innerHTML = '';
         astView.innerHTML = '';
         semanticView.innerHTML = '';
         semanticView.className = 'status-badge';
         irView.textContent = '';
         optView.innerHTML = '';
         sqlView.textContent = '';
    }

    function renderTable(cols, rows) {
        if(cols.length === 0 && rows.length === 0) return;
        
        emptyState.classList.add('hidden');
        
        cols.forEach(c => {
            const th = document.createElement('th');
            th.textContent = c;
            tableHeadRow.appendChild(th);
        });
        
        rows.forEach(r => {
            const tr = document.createElement('tr');
            r.forEach(v => {
                const td = document.createElement('td');
                td.textContent = v;
                tr.appendChild(td);
            });
            tableBody.appendChild(tr);
        });
    }

    function renderPipeline(steps) {
        // Tokens
        if(steps.tokens) {
            steps.tokens.forEach(t => {
                const span = document.createElement('span');
                span.className = `badge b-type-${t.type} b-val-${typeof t.value === 'string' ? t.value.toUpperCase() : t.value}`;
                span.textContent = `${t.value} [${t.type}]`;
                tokensView.appendChild(span);
            });
        }
        
        // AST
        if(steps.ast) {
             renderAstTree(steps.ast, astView);
        }
        
        // Semantic
        if(steps.semantic_validation) {
             semanticView.textContent = '✓ Passed';
             semanticView.classList.remove('error');
        }
        
        // IR
        if(steps.ir) {
             irView.textContent = JSON.stringify(steps.ir, null, 2);
        }
        
        // Optimization
        if(steps.optimization) {
             steps.optimization.forEach(msg => {
                 const li = document.createElement('li');
                 li.textContent = msg;
                 optView.appendChild(li);
             });
        }
        
        // SQL / Code
        if(steps.sql) {
            // Check if it's MongoDB json string
            try {
                if (steps.sql.startsWith("{") && steps.sql.includes("pipeline")) {
                    sqlView.className = "language-json";
                } else {
                    sqlView.className = "language-sql";
                }
            } catch(e) {}
            sqlView.textContent = steps.sql;
        }
    }

    function renderError(diag) {
        errorBanner.classList.remove('hidden');
        let html = `<strong>${diag.type || 'Error'}</strong>: ${diag.message}`;
        if(diag.suggestion) html += `<br/><em>Suggestion: ${diag.suggestion}</em>`;
        errorBanner.innerHTML = html;
        
        if(!semanticView.textContent.includes('Passed')) {
             semanticView.textContent = '✗ Failed: ' + diag.message;
             semanticView.classList.add('error');
        }
    }

    function setLoading(isLoading) {
        if(isLoading) {
             loading.classList.remove('hidden');
             runBtn.disabled = true;
        } else {
             loading.classList.add('hidden');
             runBtn.disabled = false;
        }
    }

    function createTreeBranch(label, value) {
        const li = document.createElement('li');
        const nodeDiv = document.createElement('div');
        nodeDiv.className = 'ast-node';
        
        let displayLabel = String(label).replace(/_/g, ' ');
        if(displayLabel.length > 0) {
            displayLabel = displayLabel.charAt(0).toUpperCase() + displayLabel.slice(1);
        }

        let isObj = value !== null && typeof value === 'object';
        let isArray = Array.isArray(value);

        if (isObj && !isArray) {
            let title = displayLabel;
            if (value.operation) {
                 title = label === "ROOT" ? value.operation : `${title} (${value.operation})`;
            }
            nodeDiv.innerHTML = `<span class="ast-title">${title}</span>`;
            li.appendChild(nodeDiv);

            const ul = document.createElement('ul');
            for (const key in value) {
                if (key === 'operation') continue;
                
                const childVal = value[key];
                if (childVal === null || childVal === "" || (Array.isArray(childVal) && childVal.length === 0) || (typeof childVal === 'object' && Object.keys(childVal).length === 0)) continue;
                
                ul.appendChild(createTreeBranch(key, childVal));
            }
            if (ul.childNodes.length > 0) li.appendChild(ul);
        } else if (isArray) {
            nodeDiv.innerHTML = `<span class="ast-title">${displayLabel}</span>`;
            li.appendChild(nodeDiv);

            const ul = document.createElement('ul');
            for (let i = 0; i < value.length; i++) {
                let childLabel = typeof value[i] === 'object' ? `Node ${i+1}` : value[i];
                ul.appendChild(createTreeBranch(childLabel, value[i]));
            }
            if (ul.childNodes.length > 0) li.appendChild(ul);
        } else {
            if (String(label) === String(value)) {
                nodeDiv.innerHTML = `<span class="ast-val">${value}</span>`;
            } else {
                nodeDiv.innerHTML = `<span class="ast-title">${displayLabel}</span><div class="ast-val">${value}</div>`;
            }
            li.appendChild(nodeDiv);
        }

        return li;
    }

    function renderAstTree(astObj, container) {
        container.innerHTML = '';
        const wrapper = document.createElement('div');
        wrapper.className = 'ast-graphical-tree';
        
        const rootUl = document.createElement('ul');
        rootUl.appendChild(createTreeBranch('ROOT', astObj));
        wrapper.appendChild(rootUl);
        
        container.appendChild(wrapper);
    }
});
