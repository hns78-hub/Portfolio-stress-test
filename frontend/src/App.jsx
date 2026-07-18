import React, { useState, useEffect, useRef } from 'react';

// Predefined scenario configurations for React UI mapping
const SCENARIO_CONFIGS = {
  1: { name: "Rate Hike +100bps" },
  2: { name: "Tech Sector Selloff -20%" },
  3: { name: "Broad Market Correction -15%" },
  4: { name: "Crypto Crash -40%" },
  5: { name: "USD/SGD Shock -10%" }
};

// Inline SVGs for premium look
const UploadIcon = () => (
  <svg className="upload-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
  </svg>
);

const TrashIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

const PlusIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
  </svg>
);

const SpinnerIcon = () => (
  <svg className="spinner" viewBox="0 0 50 50">
    <circle className="path" cx="25" cy="25" r="20" fill="none" strokeWidth="5"></circle>
  </svg>
);

const API_BASE_URL = 'http://127.0.0.1:8000';

function App() {
  const [step, setStep] = useState(1); // 1: Upload, 2: Confirmation table, 3: Execution progress, 4: Results dashboard
  const [isUploading, setIsUploading] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [portfolio, setPortfolio] = useState([]);
  const [dragActive, setDragActive] = useState(false);
  const [executionId, setExecutionId] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  
  // API Keys state (loaded from local storage)
  const [apiKeys, setApiKeys] = useState({
    daytonaApiKey: localStorage.getItem("DAYTONA_API_KEY") || "",
    daytonaServerUrl: localStorage.getItem("DAYTONA_SERVER_URL") || "",
    daytonaTarget: localStorage.getItem("DAYTONA_TARGET") || "",
    geminiApiKey: localStorage.getItem("GEMINI_API_KEY") || "",
    oxylabsUsername: localStorage.getItem("OXYLABS_USERNAME") || "",
    oxylabsPassword: localStorage.getItem("OXYLABS_PASSWORD") || "",
    nosanaApiKey: localStorage.getItem("NOSANA_API_KEY") || ""
  });

  // SSE Logs & Statuses
  const [logs, setLogs] = useState([]);
  const [statuses, setStatuses] = useState({
    "1": "pending", "2": "pending", "3": "pending", "4": "pending", "5": "pending"
  });
  const [results, setResults] = useState(null);
  
  const consoleEndRef = useRef(null);

  // Auto-scroll console logs
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Handle key config updates
  const handleKeyChange = (field, value) => {
    setApiKeys(prev => ({ ...prev, [field]: value }));
  };

  const saveKeys = () => {
    localStorage.setItem("DAYTONA_API_KEY", apiKeys.daytonaApiKey);
    localStorage.setItem("DAYTONA_SERVER_URL", apiKeys.daytonaServerUrl);
    localStorage.setItem("DAYTONA_TARGET", apiKeys.daytonaTarget);
    localStorage.setItem("GEMINI_API_KEY", apiKeys.geminiApiKey);
    localStorage.setItem("OXYLABS_USERNAME", apiKeys.oxylabsUsername);
    localStorage.setItem("OXYLABS_PASSWORD", apiKeys.oxylabsPassword);
    localStorage.setItem("NOSANA_API_KEY", apiKeys.nosanaApiKey);
    setShowConfig(false);
    alert("API Keys saved successfully to browser storage!");
  };

  // Helper: Prepare Headers with custom API keys
  const getAuthHeaders = () => {
    return {
      "x-daytona-api-key": apiKeys.daytonaApiKey,
      "x-daytona-server-url": apiKeys.daytonaServerUrl,
      "x-daytona-target": apiKeys.daytonaTarget,
      "x-gemini-api-key": apiKeys.geminiApiKey,
      "x-oxylabs-username": apiKeys.oxylabsUsername,
      "x-oxylabs-password": apiKeys.oxylabsPassword,
      "x-nosana-api-key": apiKeys.nosanaApiKey,
    };
  };

  // Handle Drag & Drop
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await uploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await uploadFile(e.target.files[0]);
    }
  };

  // Upload screenshot to FastAPI backend
  const uploadFile = async (file) => {
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    const isImage = file.type.startsWith("image/");
    const endpoint = isImage ? "/api/parse-screenshot" : "/api/upload-csv";

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: {
          "x-gemini-api-key": apiKeys.geminiApiKey
        },
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error parsing ${isImage ? 'screenshot' : 'CSV'}`);
      }
      const data = await response.json();
      setPortfolio(data.portfolio);
      // Optional: Store how it was scraped if we want to display it
      // setScrapedVia(data.scraped_via); 
      setStep(2);
    } catch (err) {
      console.error(err);
      alert(`Upload Parse Failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  // OxyLabs Real-Time Web Scraper Integration
  const enrichPricesViaOxyLabs = async () => {
    setEnriching(true);
    const tickers = portfolio.map(p => p.ticker);

    try {
      const response = await fetch(`${API_BASE_URL}/api/enrich-portfolio`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "x-oxylabs-username": apiKeys.oxylabsUsername,
          "x-oxylabs-password": apiKeys.oxylabsPassword
        },
        body: JSON.stringify(tickers)
      });

      if (!response.ok) throw new Error("OxyLabs enrichment failed");
      const data = await response.json();

      // Merge OxyLabs price & sector updates
      const updatedPortfolio = portfolio.map(pos => {
        const enrichedItem = data.enriched.find(e => e.ticker.toUpperCase() === pos.ticker.toUpperCase());
        if (enrichedItem) {
          return {
            ...pos,
            price: enrichedItem.price,
            sector: enrichedItem.sector,
            is_usd_exposed: enrichedItem.is_usd_exposed
          };
        }
        return pos;
      });

      setPortfolio(updatedPortfolio);
      alert("Portfolio enriched with real-time Google/Yahoo Finance data via OxyLabs Scraper API!");
    } catch (err) {
      console.error(err);
      alert("Failed to enrich using live OxyLabs API. Running simulated local price lookups instead.");
    } finally {
      setEnriching(false);
    }
  };

  // Table row management
  const handleCellChange = (index, field, value) => {
    const updated = [...portfolio];
    if (field === 'shares' || field === 'cost_basis' || field === 'price') {
      updated[index][field] = parseFloat(value) || 0.0;
    } else if (field === 'is_usd_exposed') {
      updated[index][field] = value;
    } else {
      updated[index][field] = value;
    }
    setPortfolio(updated);
  };

  const addPortfolioRow = () => {
    setPortfolio([
      ...portfolio,
      { ticker: "AAPL", shares: 10, cost_basis: 150, price: 180, sector: "Technology", is_usd_exposed: true }
    ]);
  };

  const removePortfolioRow = (index) => {
    setPortfolio(portfolio.filter((_, idx) => idx !== index));
  };

  // Run Stress testing inside sandboxes
  const triggerStressTest = async () => {
    setStep(3);
    setLogs(["[Orchestrator] Connecting to FastAPI backend..."]);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/run-stress-test`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          ...getAuthHeaders()
        },
        body: JSON.stringify({ portfolio, use_mock: false })
      });

      if (!response.ok) throw new Error("Orchestrator execution failed to trigger");
      const initData = await response.json();
      const execId = initData.execution_id;
      setExecutionId(execId);

      // Connect to Server Sent Events for live logs and status
      const eventSource = new EventSource(`${API_BASE_URL}/api/stream-logs/${execId}`);
      
      eventSource.onmessage = (event) => {
        const eventData = JSON.parse(event.data);
        
        if (eventData.type === 'log') {
          setLogs(prev => [...prev, eventData.message]);
        } else if (eventData.type === 'status') {
          setStatuses(eventData.status);
        } else if (eventData.type === 'result') {
          setResults(eventData.data);
          eventSource.close();
          setStep(4);
        }
      };

      eventSource.onerror = (err) => {
        console.error("SSE stream error", err);
        eventSource.close();
        alert("Live execution encountered an SSE stream error. Please check your credentials and try again.");
      };

    } catch (err) {
      console.error(err);
      alert("Live execution failed. Please check your API keys and try again.");
    }
  };



  const getStatusText = (status) => {
    switch (status) {
      case "completed": return "SUCCESS";
      case "running": return "RUNNING";
      case "failed": return "FAILED";
      default: return "PENDING";
    }
  };

  const calculateTotalPortfolioValue = () => {
    return portfolio.reduce((acc, pos) => acc + (pos.shares * pos.price), 0);
  };

  return (
    <>
      {/* HEADER SECTION */}
      <header className="app-header">
        <div className="header-title-group">
          <h1 className="app-title">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="url(#cyan-purp)" strokeWidth="3">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              <defs>
                <linearGradient id="cyan-purp" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#06b6d4" />
                  <stop offset="100%" stopColor="#a855f7" />
                </linearGradient>
              </defs>
            </svg>
            RISK SHIELD
          </h1>
          <div className="app-subtitle">
            AI-Driven Portfolio Stress Tester 
            <span className={`sponsor-badge daytona ${apiKeys.daytonaApiKey ? 'daytona' : ''}`}>
              {apiKeys.daytonaApiKey ? 'Daytona Container (LIVE)' : 'Daytona (SIM)'}
            </span>
            <span className={`sponsor-badge kimi ${apiKeys.geminiApiKey ? 'kimi' : ''}`}>
              {apiKeys.geminiApiKey ? 'AI& (LIVE)' : 'AI& (SIM)'}
            </span>
            <span className={`sponsor-badge nosana ${apiKeys.nosanaApiKey ? 'nosana' : ''}`}>
              {apiKeys.nosanaApiKey ? 'Nosana Grid (LIVE)' : 'Nosana Grid (SIM)'}
            </span>
            <span className={`sponsor-badge oxylabs ${apiKeys.oxylabsUsername ? 'oxylabs' : ''}`}>
              {apiKeys.oxylabsUsername ? 'OxyLabs (LIVE)' : 'OxyLabs (SIM)'}
            </span>
          </div>
        </div>

        <div className="mode-controls">
          <button 
            className="btn-toggle-demo" 
            style={{ border: '1px solid var(--color-cyan-border)', color: 'var(--color-cyan)' }}
            onClick={() => setShowConfig(true)}
          >
            🔧 API Keys Setup
          </button>
        </div>
      </header>

      {/* API KEY CONFIGURATION MODAL */}
      {showConfig && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
          backgroundColor: 'rgba(0,0,0,0.85)', display: 'flex', alignItems: 'center',
          justifyContent: 'center', zIndex: 1000, backdropFilter: 'blur(8px)'
        }}>
          <div className="glass-card" style={{ width: '90%', maxWidth: '550px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h2 className="card-title">Configure Live Environment Integration API Keys</h2>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', textAlign: 'left' }}>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Daytona API Key</label>
                <input 
                  type="password"
                  placeholder="Paste your daytona API key here" 
                  value={apiKeys.daytonaApiKey} 
                  onChange={(e) => handleKeyChange('daytonaApiKey', e.target.value)}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Daytona Server URL (Optional)</label>
                  <input 
                    placeholder="e.g. https://server.daytona" 
                    value={apiKeys.daytonaServerUrl} 
                    onChange={(e) => handleKeyChange('daytonaServerUrl', e.target.value)}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Daytona Target (Optional)</label>
                  <input 
                    placeholder="e.g. local" 
                    value={apiKeys.daytonaTarget} 
                    onChange={(e) => handleKeyChange('daytonaTarget', e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Gemini API Key</label>
                <input 
                  type="password"
                  placeholder="Paste your Gemini API key here" 
                  value={apiKeys.geminiApiKey} 
                  onChange={(e) => handleKeyChange('geminiApiKey', e.target.value)}
                />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>OxyLabs API Username</label>
                  <input 
                    placeholder="Username" 
                    value={apiKeys.oxylabsUsername} 
                    onChange={(e) => handleKeyChange('oxylabsUsername', e.target.value)}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>OxyLabs API Password</label>
                  <input 
                    type="password"
                    placeholder="Password" 
                    value={apiKeys.oxylabsPassword} 
                    onChange={(e) => handleKeyChange('oxylabsPassword', e.target.value)}
                  />
                </div>
              </div>
              <div>
                <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '4px' }}>Nosana API Key (Optional)</label>
                <input 
                  type="password"
                  placeholder="Nosana compute auth key" 
                  value={apiKeys.nosanaApiKey} 
                  onChange={(e) => handleKeyChange('nosanaApiKey', e.target.value)}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', marginTop: '10px' }}>
              <button className="btn-secondary" onClick={() => setShowConfig(false)}>Cancel</button>
              <button className="btn-primary" onClick={saveKeys}>Save Configuration</button>
            </div>
          </div>
        </div>
      )}

      {/* STEP 1: UPLOAD SCREENSHOT */}
      {step === 1 && (
        <main className="glass-card" style={{ maxWidth: '800px', margin: '40px auto' }}>
          <h2 className="card-title" style={{ justifyContent: 'center', fontSize: '22px', marginBottom: '24px' }}>
            Upload CSV or Screenshot
          </h2>
          
          <div 
            className={`upload-container ${dragActive ? 'drag-active' : ''}`}
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={() => document.getElementById("file-upload").click()}
          >
            {isUploading ? (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                <SpinnerIcon />
                <p className="upload-text" style={{ color: 'var(--color-cyan)' }}>
                  Parsing file data...
                </p>
                <p className="upload-subtext">Extracting portfolio holdings...</p>
              </div>
            ) : (
              <>
                <UploadIcon />
                <p className="upload-text">Drag & drop your CSV or Screenshot here, or click to browse</p>
                <p className="upload-subtext">Supports .csv, .png, .jpg</p>
              </>
            )}
            <input 
              id="file-upload"
              type="file"
              className="hidden-file-input"
              accept=".csv,image/*"
              onChange={handleFileChange}
              disabled={isUploading}
            />
          </div>


        </main>
      )}

      {/* STEP 2: CONFIRM / EDIT PORTFOLIO */}
      {step === 2 && (
        <main className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="card-title">
            <span>Confirm Parsed Portfolio holdings</span>
            <div style={{ display: 'flex', gap: '8px' }}>
              
              <span className="badge success">Ready</span>
            </div>
          </div>

          <p style={{ color: 'var(--text-secondary)', fontSize: '14px', marginBottom: '8px' }}>
            Review your extracted portfolio holdings. You can add new assets, edit shares/prices, or trigger the **OxyLabs Scraper** to fetch real-time market valuations before launching the stress test.
          </p>

          <div className="table-wrapper">
            <table className="portfolio-table">
              <thead>
                <tr>
                  <th>Ticker</th>
                  <th>Shares</th>
                  <th>Cost Basis ($)</th>
                  <th>Current Price ($)</th>
                  <th>Sector / Category</th>
                  <th>USD exposed</th>
                  <th style={{ width: '50px' }}></th>
                </tr>
              </thead>
              <tbody>
                {portfolio.map((pos, idx) => (
                  <tr key={idx}>
                    <td>
                      <input 
                        value={pos.ticker} 
                        onChange={(e) => handleCellChange(idx, 'ticker', e.target.value.toUpperCase())}
                      />
                    </td>
                    <td>
                      <input 
                        type="number"
                        value={pos.shares} 
                        onChange={(e) => handleCellChange(idx, 'shares', e.target.value)}
                      />
                    </td>
                    <td>
                      <input 
                        type="number"
                        step="0.01"
                        value={pos.cost_basis} 
                        onChange={(e) => handleCellChange(idx, 'cost_basis', e.target.value)}
                      />
                    </td>
                    <td>
                      <input 
                        type="number"
                        step="0.01"
                        value={pos.price} 
                        onChange={(e) => handleCellChange(idx, 'price', e.target.value)}
                      />
                    </td>
                    <td>
                      <input 
                        value={pos.sector} 
                        onChange={(e) => handleCellChange(idx, 'sector', e.target.value)}
                      />
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', height: '36px' }}>
                        <input 
                          type="checkbox"
                          style={{ width: '20px', cursor: 'pointer' }}
                          checked={pos.is_usd_exposed} 
                          onChange={(e) => handleCellChange(idx, 'is_usd_exposed', e.target.checked)}
                        />
                      </div>
                    </td>
                    <td>
                      <button className="btn-remove" onClick={() => removePortfolioRow(idx)}>
                        <TrashIcon />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="table-actions">
            <div style={{ display: 'flex', gap: '10px' }}>
              <button className="btn-secondary" onClick={addPortfolioRow}>
                <PlusIcon /> Add Holding
              </button>
              <button 
                className="btn-secondary" 
                onClick={enrichPricesViaOxyLabs}
                disabled={enriching || portfolio.length === 0}
                style={{ borderColor: 'var(--color-green-border)', color: 'var(--color-green)' }}
              >
                {enriching ? <SpinnerIcon /> : '🌐 Enrich Real-Time Prices via OxyLabs'}
              </button>
            </div>
            
            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <div style={{ marginRight: '16px', textAlign: 'right' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Estimated Value</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: '16px', color: 'var(--color-cyan)' }}>
                  ${calculateTotalPortfolioValue().toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} USD
                </div>
              </div>
              <button className="btn-primary" onClick={triggerStressTest}>
                🚀 Run Parallel Stress-Test
              </button>
            </div>
          </div>
        </main>
      )}

      {/* STEP 3: RUNNING STRESS TEST */}
      {step === 3 && (
        <main className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <h2 className="card-title">
            <span>Executing Parallel Daytona Sandboxes...</span>
            <span className="badge warning" style={{ textTransform: 'none' }}>
              {apiKeys.daytonaApiKey ? 'Mode: Daytona Live Containers' : 'Mode: Daytona Simulated Containers'}
            </span>
          </h2>

          {/* Sandbox Status Grid */}
          <div className="grid-5col">
            {[1, 2, 3, 4, 5].map(id => {
              const status = statuses[id.toString()] || "pending";
              const conf = SCENARIO_CONFIGS[id];
              return (
                <div className={`status-card ${status}`} key={id}>
                  <div className="status-card-header">
                    <span className="scenario-title">{conf.name}</span>
                    <span className="status-indicator">
                      <span className={`dot-pulse ${status}`} />
                      {getStatusText(status)}
                    </span>
                  </div>
                  
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                    Sandbox container #{id}
                  </div>
                  
                  <div className="status-progress-bar">
                    <div className={`status-progress-fill ${status}`} />
                  </div>
                </div>
              );
            })}
          </div>

          {/* Console Output streaming */}
          <div>
            <div className="card-title" style={{ fontSize: '14px', marginBottom: '8px', color: 'var(--color-green)' }}>
              📟 Sandbox Container Orchestration Logs (Live Stream)
            </div>
            <div className="console-logs-panel">
              {logs.map((log, idx) => {
                let logClass = "log-line";
                if (log.includes("[Orchestrator]") || log.includes("[Daytona Sandbox") || log.includes("[Daytona Simulator")) {
                  if (!log.includes("STDOUT") && !log.includes("ERROR")) {
                    logClass = "log-line system";
                  }
                }
                if (log.includes("ERROR")) {
                  logClass = "log-line error";
                } else if (log.includes("complete") || log.includes("Value-at-Risk")) {
                  logClass = "log-line success";
                }
                
                return (
                  <div key={idx} className={logClass}>
                    {log}
                  </div>
                );
              })}
              <div ref={consoleEndRef} />
            </div>
          </div>
        </main>
      )}

      {/* STEP 4: RESULTS DASHBOARD */}
      {step === 4 && results && results.error && (
        <main className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <h2 style={{ color: 'var(--color-red)' }}>Stress Test Execution Failed</h2>
          <p>{results.error}</p>
          <p>Please verify your API keys (especially the Daytona API key and Gemini API Key) in the Setup menu.</p>
          <button className="btn-primary" style={{ width: 'fit-content' }} onClick={() => setStep(2)}>Go Back</button>
        </main>
      )}

      {step === 4 && results && !results.error && (
        <main style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Metrics summary widgets */}
          <section className="results-header-grid">
            <div className="result-metric-card" style={{ borderColor: 'var(--color-cyan-border)' }}>
              <span className="metric-label">
                💼 PORTFOLIO BASE VALUE
              </span>
              <span className="metric-value" style={{ color: 'var(--color-cyan)' }}>
                ${results.scenarios[0].current_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>

            <div className="result-metric-card" style={{ borderColor: 'var(--color-purple)' }}>
              <span className="metric-label" style={{ color: 'var(--color-purple)' }}>
                🟣 Combined VaR (Nosana Compute)
              </span>
              <span className="metric-value" style={{ color: 'var(--color-purple)' }}>
                ${results.combined_var.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>

            <div className="result-metric-card" style={{ borderColor: 'var(--color-orange-border)' }}>
              <span className="metric-label" style={{ color: 'var(--color-orange)' }}>
                ⚠️ Combined VaR %
              </span>
              <span className="metric-value" style={{ color: 'var(--color-orange)' }}>
                {results.combined_var_pct}%
              </span>
            </div>

            <div className="result-metric-card" style={{ borderColor: 'var(--color-red-border)' }}>
              <span className="metric-label">
                🚨 WORST CASE DRAWDOWN
              </span>
              <span className="metric-value" style={{ color: 'var(--color-red)' }}>
                {Math.min(...results.scenarios.map(s => s.pnl_percentage)).toFixed(2)}%
              </span>
            </div>
          </section>

          {/* Side by side comparison */}
          <div className="grid-2col">
            
            {/* Scenario P&L chart comparison */}
            <div className="glass-card">
              <h2 className="card-title">Scenario P&L Shock Comparison</h2>
              <div className="chart-sim-bar" style={{ marginTop: '16px' }}>
                {results.scenarios.map((sc, idx) => {
                  const maxAbsPct = Math.max(...results.scenarios.map(s => Math.abs(s.pnl_percentage)));
                  const fillPct = maxAbsPct > 0 ? (Math.abs(sc.pnl_percentage) / maxAbsPct) * 100 : 0;
                  const isNegative = sc.pnl < 0;

                  return (
                    <div className="chart-row" key={idx}>
                      <span className="chart-row-label">{sc.scenario_name}</span>
                      <div className="chart-bar-container">
                        <div 
                          className={`chart-bar-fill ${isNegative ? 'negative' : 'positive'}`}
                          style={{ width: `${fillPct}%` }}
                        />
                      </div>
                      <span className={`chart-row-val ${isNegative ? 'negative' : 'positive'}`}>
                        {sc.pnl_percentage > 0 ? '+' : ''}{sc.pnl_percentage.toFixed(2)}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Worst Hit Holdings */}
            <div className="glass-card">
              <h2 className="card-title">Top Risk-Contributing Assets</h2>
              <div className="table-wrapper" style={{ marginTop: '16px' }}>
                <table className="portfolio-table">
                  <thead>
                    <tr>
                      <th>Ticker</th>
                      <th>Shocked Scenario</th>
                      <th style={{ textAlign: 'right' }}>Worst Impact</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(() => {
                      const list = [];
                      results.scenarios.forEach(sc => {
                        sc.worst_hit_positions.forEach(wh => {
                          list.push({
                            ticker: wh.ticker,
                            scenario: sc.scenario_name,
                            pnl: wh.pnl,
                            pnl_pct: wh.pnl_pct
                          });
                        });
                      });
                      const sorted = list.sort((a, b) => a.pnl - b.pnl);
                      const seen = new Set();
                      const unique = [];
                      for (const item of sorted) {
                        if (!seen.has(item.ticker)) {
                          seen.add(item.ticker);
                          unique.push(item);
                        }
                        if (unique.length >= 4) break;
                      }
                      
                      return unique.length > 0 ? (
                        unique.map((item, idx) => (
                          <tr key={idx}>
                            <td><span style={{ fontWeight: 700 }}>{item.ticker}</span></td>
                            <td><span className="badge warning" style={{ fontSize: '10px' }}>{item.scenario}</span></td>
                            <td style={{ textAlign: 'right', color: 'var(--color-red)', fontFamily: 'var(--font-mono)' }}>
                              ${item.pnl.toLocaleString('en-US', { maximumFractionDigits: 0 })} ({item.pnl_pct}%)
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="3" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                            No negative risk exposures detected across positions.
                          </td>
                        </tr>
                      );
                    })()}
                  </tbody>
                </table>
              </div>
            </div>

          </div>

          {/* Scenarios Detail Breakdown */}
          <div className="glass-card">
            <h2 className="card-title">
              <span>Detailed Stress Scenario Reports</span>
              <span className="badge info">{apiKeys.geminiApiKey ? 'Gemini Live Risk verdicts' : 'Risk verdicts'}</span>
            </h2>
            <div className="scenarios-results-list" style={{ marginTop: '16px' }}>
              {results.scenarios.map((sc, idx) => {
                const isNeg = sc.pnl < 0;
                return (
                  <div className="result-scenario-row" key={idx}>
                    <div className="result-scen-meta">
                      <span className="result-scen-title">{sc.scenario_name}</span>
                      <span className="result-scen-desc">{sc.description}</span>
                    </div>

                    <div className="result-scen-verdict">
                      <strong>AI Verdict:</strong> "{sc.verdict}"
                    </div>

                    <div className="result-scen-impact">
                      <span className={`pnl-text ${isNeg ? 'negative' : 'positive'}`}>
                        {sc.pnl >= 0 ? '+' : ''}${sc.pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </span>
                      <span className="pnl-sub">
                        Impact: <strong style={{ color: isNeg ? 'var(--color-red)' : 'var(--color-green)' }}>
                          {sc.pnl >= 0 ? '+' : ''}{sc.pnl_percentage}%
                        </strong>
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Nosana Detail Grid Info */}
          {results.nosana_details && (
            <div className="glass-card" style={{ background: 'rgba(168, 85, 247, 0.03)', borderColor: 'rgba(168, 85, 247, 0.2)' }}>
              <div className="card-title" style={{ color: 'var(--color-purple)', fontSize: '15px', marginBottom: '8px' }}>
                ⚙️ Nosana Decentralized Compute Worker Details
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                The combined portfolio Value-at-Risk (VaR) calculation was distributed to the <strong>Nosana Compute Network</strong>. 
                Task compiled, routed, and executed on Worker Node <strong>{results.nosana_details.worker_node}</strong> (Job ID: <code>{results.nosana_details.job_id}</code>). 
                Result cryptographic verification hash: <code>{results.nosana_details.hash}</code>.
              </p>
            </div>
          )}

          {/* Reset button */}
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <button className="btn-secondary" onClick={() => setStep(1)} style={{ padding: '10px 24px' }}>
              🔄 Reset and Upload New Screenshot
            </button>
          </div>

        </main>
      )}
    </>
  );
}

export default App;
