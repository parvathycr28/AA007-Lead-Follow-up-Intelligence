
import { useEffect, useState } from 'react'
import './App.css'

type Scenario = {
  description: string
  lead_id: string
}

type Scenarios = Record<string, Scenario>

type Recommendation = {
  priority_score: number
  action: string
  triggered_rules: string[]
  reasons: string[]
}

type WorkflowResult = {
  workflow_id: string
  scenario: string
  lead_id: string
  recommendation: Recommendation
  explanation: {
    summary: string
    executed_agents: string[]
    score_breakdown: {
      recency: number
      engagement: number
      fit: number
    }
    triggered_rules: string[]
    reasons: string[]
    limitations: string[]
  }
  audit_reference: string
  errors: string[]
}

function App() {
  const [scenarios, setScenarios] = useState<Scenarios>({})
  const [selectedScenario, setSelectedScenario] = useState('hot')
  const [result, setResult] = useState<WorkflowResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadScenarios() {
      try {
        const response = await fetch('/api/leads/scenarios')

        if (!response.ok) {
          throw new Error('Unable to load scenarios.')
        }

        const data: Scenarios = await response.json()
        setScenarios(data)
      } catch {
        setError('Could not connect to the backend. Please check that the API server is running.')
      }
    }

    loadScenarios()
  }, [])

  async function runScenario() {
    setLoading(true)
    setError('')
    setResult(null)

    try {
      const response = await fetch(
        `/api/leads/scenarios/${selectedScenario}/run`,
        { method: 'POST' },
      )

      if (!response.ok) {
        throw new Error('Scenario execution failed.')
      }

      const data: WorkflowResult = await response.json()
      setResult(data)
    } catch {
      setError('Unable to execute the workflow. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const actionLabels: Record<string, string> = {
    FOLLOW_UP_NOW: 'Follow Up Now',
    FOLLOW_UP_SOON: 'Follow Up Soon',
    NURTURE: 'Nurture',
    REQUEST_DATA: 'Request Data',
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">A</div>
          <div>
            <h1>APEX</h1>
            <p>Lead Intelligence Platform</p>
          </div>
        </div>
        <div className="system-status">
          <span className="status-dot" />
          Deterministic Engine
        </div>
      </header>

      <section className="page-content">
        <div className="page-heading">
          <div>
            <p className="eyebrow">SALES OPERATIONS / INTELLIGENCE</p>
            <h2>Lead Follow-up Prioritization</h2>
            <p className="subtitle">
              Turn lead signals into transparent, actionable follow-up decisions.
            </p>
          </div>
          <div className="version-tag">AA007 · MVP 1.0</div>
        </div>

        <section className="scenario-panel">
          <div className="section-heading">
            <div>
              <h3>Workflow Scenarios</h3>
              <p>Select a sample lead to evaluate its follow-up priority.</p>
            </div>
            <span className="scenario-count">03 SCENARIOS</span>
          </div>

          <div className="scenario-grid">
            {Object.entries(scenarios).map(([key, scenario]) => (
              <button
                key={key}
                className={`scenario-card ${selectedScenario === key ? 'selected' : ''}`}
                onClick={() => {
                  setSelectedScenario(key)
                  setResult(null)
                  setError('')
                }}
              >
                <span className="scenario-name">{key.toUpperCase()}</span>
                <strong>{scenario.lead_id}</strong>
                <span className="scenario-description">
                  {scenario.description}
                </span>
              </button>
            ))}
          </div>

          <div className="run-row">
            <span>Evaluate the selected lead using all five agents.</span>
            <button
              className="run-button"
              onClick={runScenario}
              disabled={loading || !scenarios[selectedScenario]}
            >
              {loading ? 'Running workflow...' : 'Run Prioritization'}
              <span>→</span>
            </button>
          </div>
        </section>

        {error && <div className="error-message">{error}</div>}

        {result && (
          <>
            <section className="result-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">WORKFLOW RESULT</p>
                  <h3>Priority Recommendation</h3>
                </div>
                <span className="completed-tag">COMPLETED</span>
              </div>

              <div className="result-grid">
                <div className="recommendation-card">
                  <span className="metric-label">RECOMMENDED ACTION</span>
                  <h2>{actionLabels[result.recommendation.action] || result.recommendation.action}</h2>
                  <p>{result.recommendation.reasons.join(' ')}</p>
                </div>

                <div className="score-card">
                  <span className="metric-label">PRIORITY SCORE</span>
                  <div className="score-value">
                    {result.recommendation.priority_score}
                    <small>/100</small>
                  </div>
                  <div className="score-track">
                    <div
                      className="score-fill"
                      style={{ width: `${Math.min(result.recommendation.priority_score, 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="breakdown-section">
                <h4>Score Breakdown</h4>
                <div className="breakdown-grid">
                  {Object.entries(result.explanation.score_breakdown).map(
                    ([name, score]) => (
                      <div className="breakdown-item" key={name}>
                        <span>{name}</span>
                        <strong>{score}</strong>
                      </div>
                    ),
                  )}
                </div>
              </div>

              <div className="rules-section">
                <h4>Triggered Business Rules</h4>
                <div className="rule-list">
                  {result.recommendation.triggered_rules.map((rule) => (
                    <span className="rule-tag" key={rule}>{rule}</span>
                  ))}
                </div>
              </div>
            </section>

            <section className="result-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">AGENTIC EXECUTION</p>
                  <h3>Five-Agent Workflow</h3>
                </div>
                <span className="scenario-count">
                  {result.explanation.executed_agents.length} AGENTS
                </span>
              </div>

              <div className="agent-list">
                {result.explanation.executed_agents.map((agent, index) => (
                  <div className="agent-row" key={agent}>
                    <span className="agent-number">{String(index + 1).padStart(2, '0')}</span>
                    <span className="agent-name">{agent}</span>
                    <span className="agent-status">Executed</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="result-panel">
              <p className="eyebrow">DECISION EXPLANATION</p>
              <h3>Why this recommendation?</h3>
              <p className="explanation-text">{result.explanation.summary}</p>

              <h4>Evidence and Reasons</h4>
              <ul className="reason-list">
                {result.explanation.reasons.map((reason, index) => (
                  <li key={index}>{reason}</li>
                ))}
              </ul>

              {result.explanation.limitations.length > 0 && (
                <>
                  <h4>Limitations</h4>
                  <ul className="reason-list">
                    {result.explanation.limitations.map((item, index) => (
                      <li key={index}>{item}</li>
                    ))}
                  </ul>
                </>
              )}
            </section>

            <section className="audit-panel">
              <div>
                <p className="eyebrow">AUDIT TRAIL</p>
                <h3>Workflow Traceability</h3>
              </div>
              <div className="audit-details">
                <div>
                  <span>Workflow ID</span>
                  <strong>{result.workflow_id}</strong>
                </div>
                <div>
                  <span>Audit Reference</span>
                  <strong>{result.audit_reference}</strong>
                </div>
                <div>
                  <span>Lead ID</span>
                  <strong>{result.lead_id}</strong>
                </div>
              </div>
              {result.errors.length > 0 && (
                <p className="error-message">{result.errors.join(', ')}</p>
              )}
            </section>
          </>
        )}

        {!result && !loading && !error && (
          <div className="empty-state">
            <div className="empty-icon">↗</div>
            <h3>Ready to evaluate leads</h3>
            <p>Select a scenario and run prioritization to see the recommendation, scoring evidence, and agent execution.</p>
          </div>
        )}
      </section>

      <footer className="footer">
        <span>AA007 · Lead Follow-up Prioritization Intelligence</span>
        <span>Transparent rules · Explainable decisions</span>
      </footer>
    </main>
  )
}

export default App