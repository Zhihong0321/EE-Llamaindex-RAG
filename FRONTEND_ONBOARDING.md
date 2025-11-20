# Frontend Team Onboarding Guide
## Building a Company RAG System

Welcome to the RAG API! This guide will help you understand the system architecture, workflow, and how to integrate the API into your frontend application.

---

## 🎯 What is This System?

This is a **Retrieval-Augmented Generation (RAG)** system that allows your company to:

1. **Upload company documents** (policies, manuals, knowledge bases, etc.)
2. **Ask questions** in natural language
3. **Get AI-powered answers** based on your company's actual documents
4. **Maintain conversation context** across multiple questions
5. **Track sources** to verify where answers come from

Think of it as "ChatGPT for your company's internal knowledge."

---

## 🏗️ System Architecture

```
┌─────────────────┐
│   Frontend UI   │  ← You build this
│  (React/Vue/etc)│
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│   RAG API       │  ← Already built & deployed
│  (FastAPI)      │
└────────┬────────┘
         │
    ┌────┴────┬──────────┐
    ▼         ▼          ▼
┌────────┐ ┌──────┐ ┌─────────┐
│Postgres│ │Vector│ │ OpenAI  │
│   DB   │ │Store │ │   API   │
└────────┘ └──────┘ └─────────┘
```

**Your Role**: Build the frontend that calls the RAG API endpoints.

---

## 📋 Typical Use Cases

### Use Case 1: Employee Knowledge Portal
Employees can ask questions about company policies, benefits, procedures, etc.

### Use Case 2: Customer Support Assistant
Support agents get instant answers from product documentation and FAQs.

### Use Case 3: Internal Documentation Search
Developers search through technical docs, API specs, and architecture guides.

### Use Case 4: Onboarding Assistant
New hires get answers about company culture, processes, and tools.

---

## 🔄 Complete Workflow

### Phase 1: Initial Setup (Admin/One-time)

```
Admin uploads documents → API processes & stores → Ready for queries
```

**Steps:**
1. Admin logs into your frontend
2. Uploads company documents (PDFs, text files, etc.)
3. Frontend calls `/ingest` endpoint for each document
4. API chunks, embeds, and stores documents
5. Documents are now searchable

### Phase 2: User Interaction (Ongoing)

```
User asks question → API retrieves relevant docs → AI generates answer → User sees response
```

**Steps:**
1. User types a question in chat interface
2. Frontend calls `/chat` endpoint
3. API finds relevant document chunks
4. AI generates answer based on those chunks
5. Frontend displays answer + sources
6. User can ask follow-up questions (same session)

---

## 🚀 Quick Start Integration

### Step 1: Set Up Your Environment

```javascript
// config.js
export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

### Step 2: Create API Client

```javascript
// api/ragClient.js
class RAGClient {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  async checkHealth() {
    const response = await fetch(`${this.baseURL}/health`);
    return await response.json();
  }

  async ingestDocument(content, metadata) {
    const response = await fetch(`${this.baseURL}/ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, metadata })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to ingest document');
    }
    
    return await response.json();
  }

  async chat(message, sessionId = null, stream = false) {
    const response = await fetch(`${this.baseURL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        stream
      })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Chat request failed');
    }
    
    return await response.json();
  }

  async listDocuments(limit = 10, offset = 0) {
    const response = await fetch(
      `${this.baseURL}/documents?limit=${limit}&offset=${offset}`
    );
    return await response.json();
  }

  async deleteDocument(documentId) {
    const response = await fetch(`${this.baseURL}/documents/${documentId}`, {
      method: 'DELETE'
    });
    return await response.json();
  }
}

export default new RAGClient(API_BASE_URL);
```

### Step 3: Build Document Upload Component

```javascript
// components/DocumentUpload.jsx
import React, { useState } from 'react';
import ragClient from '../api/ragClient';

function DocumentUpload() {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState('');

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setStatus('Reading file...');

    try {
      // Read file content
      const content = await file.text();
      
      setStatus('Uploading to API...');
      
      // Upload to API
      const result = await ragClient.ingestDocument(content, {
        title: file.name,
        source: file.name,
        uploaded_at: new Date().toISOString()
      });

      setStatus(`✅ Success! Document ID: ${result.document_id}`);
      setFile(null);
    } catch (error) {
      setStatus(`❌ Error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="document-upload">
      <h2>Upload Company Documents</h2>
      <input 
        type="file" 
        onChange={handleFileChange}
        accept=".txt,.md,.pdf"
        disabled={uploading}
      />
      <button 
        onClick={handleUpload}
        disabled={!file || uploading}
      >
        {uploading ? 'Uploading...' : 'Upload Document'}
      </button>
      {status && <p>{status}</p>}
    </div>
  );
}

export default DocumentUpload;
```

### Step 4: Build Chat Interface

```javascript
// components/ChatInterface.jsx
import React, { useState, useEffect, useRef } from 'react';
import ragClient from '../api/ragClient';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    
    // Add user message to chat
    setMessages(prev => [...prev, {
      role: 'user',
      content: userMessage
    }]);

    setLoading(true);

    try {
      // Call API
      const response = await ragClient.chat(userMessage, sessionId);
      
      // Save session ID for follow-up questions
      if (!sessionId) {
        setSessionId(response.session_id);
      }

      // Add AI response to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.response,
        sources: response.sources
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'error',
        content: `Error: ${error.message}`
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h2>Company Knowledge Assistant</h2>
        {sessionId && (
          <button onClick={() => {
            setSessionId(null);
            setMessages([]);
          }}>
            New Conversation
          </button>
        )}
      </div>

      <div className="chat-messages">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-content">
              {msg.content}
            </div>
            {msg.sources && msg.sources.length > 0 && (
              <div className="message-sources">
                <strong>Sources:</strong>
                <ul>
                  {msg.sources.map((source, i) => (
                    <li key={i}>
                      {source.metadata.title || 'Unknown'} 
                      (Score: {(source.score * 100).toFixed(1)}%)
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="message assistant loading">
            <div className="typing-indicator">●●●</div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about company documents..."
          disabled={loading}
          rows={3}
        />
        <button onClick={handleSend} disabled={!input.trim() || loading}>
          Send
        </button>
      </div>
    </div>
  );
}

export default ChatInterface;
```

### Step 5: Build Document Management

```javascript
// components/DocumentList.jsx
import React, { useState, useEffect } from 'react';
import ragClient from '../api/ragClient';

function DocumentList() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [total, setTotal] = useState(0);
  const limit = 10;

  useEffect(() => {
    loadDocuments();
  }, [page]);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const response = await ragClient.listDocuments(limit, page * limit);
      setDocuments(response.documents);
      setTotal(response.total);
    } catch (error) {
      console.error('Failed to load documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (documentId) => {
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      await ragClient.deleteDocument(documentId);
      loadDocuments(); // Reload list
    } catch (error) {
      alert(`Failed to delete: ${error.message}`);
    }
  };

  if (loading) return <div>Loading documents...</div>;

  return (
    <div className="document-list">
      <h2>Uploaded Documents ({total})</h2>
      
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Source</th>
            <th>Uploaded</th>
            <th>Chunks</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {documents.map(doc => (
            <tr key={doc.id}>
              <td>{doc.metadata.title || 'Untitled'}</td>
              <td>{doc.metadata.source || 'N/A'}</td>
              <td>{new Date(doc.created_at).toLocaleDateString()}</td>
              <td>{doc.chunk_count || 0}</td>
              <td>
                <button onClick={() => handleDelete(doc.id)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="pagination">
        <button 
          onClick={() => setPage(p => Math.max(0, p - 1))}
          disabled={page === 0}
        >
          Previous
        </button>
        <span>Page {page + 1} of {Math.ceil(total / limit)}</span>
        <button 
          onClick={() => setPage(p => p + 1)}
          disabled={(page + 1) * limit >= total}
        >
          Next
        </button>
      </div>
    </div>
  );
}

export default DocumentList;
```

---

## 🎨 Recommended UI/UX Patterns

### 1. Admin Dashboard
- Document upload interface
- Document management (list, delete)
- System health monitoring
- Usage statistics

### 2. User Chat Interface
- Clean chat UI (like ChatGPT)
- Message history
- Source citations
- "New conversation" button
- Loading indicators

### 3. Source Display
- Show which documents were used
- Relevance scores
- Click to view full document
- Highlight relevant excerpts

### 4. Error Handling
- Network errors → "Connection lost, retrying..."
- API errors → Show user-friendly message
- Empty results → "No relevant documents found"
- Rate limits → "Please wait a moment..."

---

## 🔐 Security Considerations

### Authentication (To Implement)
Currently, the API has no authentication. You should add:

1. **User authentication** in your frontend
2. **API key or JWT** to secure API calls
3. **Role-based access** (admin vs regular user)
4. **Document permissions** (who can see what)

### Example with API Key:
```javascript
async chat(message, sessionId = null) {
  const response = await fetch(`${this.baseURL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.apiKey}` // Add this
    },
    body: JSON.stringify({ message, session_id: sessionId })
  });
  return await response.json();
}
```

---

## 📊 Monitoring & Analytics

### Metrics to Track
1. **Usage metrics**
   - Number of queries per day
   - Active users
   - Popular questions

2. **Performance metrics**
   - Response time
   - API availability
   - Error rates

3. **Quality metrics**
   - User feedback (thumbs up/down)
   - Source relevance
   - Answer accuracy

### Implementation Example:
```javascript
// Track query
async chat(message, sessionId = null) {
  const startTime = Date.now();
  
  try {
    const response = await fetch(/* ... */);
    const data = await response.json();
    
    // Log success
    this.logMetric({
      type: 'chat_success',
      duration: Date.now() - startTime,
      sessionId: data.session_id
    });
    
    return data;
  } catch (error) {
    // Log error
    this.logMetric({
      type: 'chat_error',
      error: error.message,
      duration: Date.now() - startTime
    });
    throw error;
  }
}
```

---

## 🚦 Development Workflow

### Phase 1: Local Development (Week 1)
1. Set up frontend project
2. Connect to local API (`http://localhost:8000`)
3. Build basic UI components
4. Test with sample documents

### Phase 2: Integration (Week 2)
1. Connect to staging API
2. Implement all features
3. Add error handling
4. Test edge cases

### Phase 3: Testing (Week 3)
1. User acceptance testing
2. Performance testing
3. Security review
4. Bug fixes

### Phase 4: Production (Week 4)
1. Connect to production API
2. Deploy frontend
3. Monitor usage
4. Gather feedback

---

## 🧪 Testing Checklist

### Functional Testing
- [ ] Upload document successfully
- [ ] Ask question and get response
- [ ] Multi-turn conversation works
- [ ] Sources are displayed correctly
- [ ] Delete document works
- [ ] Pagination works
- [ ] New conversation resets session

### Error Testing
- [ ] Handle network errors gracefully
- [ ] Handle API errors (404, 500, etc.)
- [ ] Handle empty responses
- [ ] Handle malformed data
- [ ] Handle timeout scenarios

### UX Testing
- [ ] Loading states are clear
- [ ] Error messages are helpful
- [ ] Interface is responsive
- [ ] Keyboard shortcuts work
- [ ] Mobile-friendly (if applicable)

---

## 📚 Additional Resources

### API Documentation
- **Interactive Docs**: `{API_URL}/docs`
- **API Reference**: See `API_DOCUMENTATION.md`
- **OpenAPI Schema**: `{API_URL}/openapi.json`

### Example Projects
- React example: [Link to repo if available]
- Vue example: [Link to repo if available]
- Vanilla JS example: [Link to repo if available]

### Support
- Backend team contact: [Email/Slack]
- API status page: [URL]
- Issue tracker: [GitHub/Jira]

---

## 🎯 Success Criteria

Your integration is successful when:

1. ✅ Users can upload company documents
2. ✅ Users can ask questions and get relevant answers
3. ✅ Conversations maintain context across multiple turns
4. ✅ Sources are clearly displayed and verifiable
5. ✅ Error handling is robust and user-friendly
6. ✅ Performance is acceptable (< 3s response time)
7. ✅ UI is intuitive and requires no training

---

## 🚀 Next Steps

1. **Review this guide** with your team
2. **Explore the API** at `{API_URL}/docs`
3. **Set up your dev environment**
4. **Build a proof-of-concept** (upload 1 doc, ask 1 question)
5. **Schedule a sync** with backend team for questions
6. **Start building!**

---

**Questions?** Contact the backend team or check the interactive API docs at `/docs`.

**Last Updated**: November 17, 2025
