
import { useEffect, useState } from 'react'
import './App.css'

type Scenario = {
  description: string
  lead_id: string
}

type Scenarios = Record<string, Scenario>

type AgentOutput = {
  agent_name: string
  status?: string
  validated_lead?: Record<string, unknown> | null
  errors?: string[]
  score?: number
  days_since_last_contact?: number | null
  event_count?: number
  recognized_events?: string[]
  reason?: string
  fit_score?: number
  sla_flags?: string[]
  priority_score?: number
  action?: string
  triggered_rules?: string[]
  reasons?: string[]
}

type WorkflowContext = {
  workflow_id: string
  started_at: string
  lead_record: Record<string, unknown>
  engagement_events: Array<Record<string, unknown>>
  validated_lead: Record<string, unknown> | null
  recency_score: number | null
  engagement_score: number | null
  fit_score: number | null
  sla_flags: string[]
  agent_outputs: Record<string, AgentOutput>
  final_recommendation: Recommendation | null
  explanation: Record<string, unknown> | null
  audit_reference: string | null
  errors: string[]
}

type Recommendation = {
  priority_score: number
  action: string
  triggered_rules: string[]
  reasons: string[]
}

type AuditRecord = {
  audit_reference: string
  workflow_id: string
  timestamp: string
  lead_id: string
  agent_sequence: string[]
  agent_outputs: Record<string, AgentOutput>
  triggered_rules: string[]
  final_recommendation: Recommendation
  errors: string[]
}

type WorkflowResult = {
  workflow_id: string
  scenario?: string
  lead_id: string
  recommendation: Recommendation
  explanation: {
    summary: string
    executed_agents: string[]
    score_breakdown: {
      recency: number | null
      engagement: number | null
      fit: number | null
    }
    triggered_rules: string[]
    reasons: string[]
    limitations: string[]
  }
  audit_reference: string
  workflow_context: WorkflowContext
  audit_record: AuditRecord | null
  errors: string[]
}

const agentDefinitions: Record<string, {
  responsibility: string
  input: string
}> = {
  lead_intake: {
    responsibility: 'Validates mandatory lead fields and normalizes lead information.',
    input: 'Lead record',
  },
  recency: {
    responsibility: 'Evaluates how recently the lead was contacted.',
    input: 'Validated lead and last-contact date',
  },
  engagement: {
    responsibility: 'Scores recognized business engagement events.',
    input: 'Validated lead and engagement events',
  },
  fit_sla: {
    responsibility: 'Evaluates declared business need and pending follow-up SLA.',
    input: 'Validated lead and follow-up information',
  },
  lead_priority: {
    responsibility: 'Combines agent scores and business rules into a recommendation.',
    input: 'Recency, engagement, fit and SLA outputs',
  },
}

const agentOrder = [
  'lead_intake',
  'recency',
  'engagement',
  'fit_sla',
  'lead_priority',
]

const actionLabels: Record<string, string> = {
  FOLLOW_UP_NOW: 'Follow Up Now',
  FOLLOW_UP_SOON: 'Follow Up Soon',
  NURTURE: 'Nurture',
  REQUEST_DATA: 'Request Data',
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') {
    return 'Not provided'
  }

  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No'
  }

  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }

  return String(value)
}

function formatDate(value: unknown): string {
  if (!value || typeof value !== 'string') return 'Not provided'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return value

  return date.toLocaleString()
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
  async function runMissingContactTest() {
    setLoading(true)
    setError('')
    setResult(null)

    const now = new Date().toISOString()

    const testPayload = {
      lead: {
        lead_id: 'LEAD-TEST-MISSING-001',
        source: 'Website',
        created_at: now,
        last_contact_at: now,
        declared_need: 'Airline booking assistance',
        stage: 'New',
        contact_available: false,
        pending_follow_up: false,
        follow_up_due_at: null,
      },
      engagement_events: [],
    }

    try {
      const response = await fetch('/api/leads/prioritize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testPayload),
      })

      if (!response.ok) {
        throw new Error('Missing-contact test failed.')
      }

      const data: WorkflowResult = await response.json()
      setResult(data)
    } catch {
      setError('Unable to execute the missing-contact test. Please check the backend.')
    } finally {
      setLoading(false)
    }
  }
  const context = result?.workflow_context
  const executedOutputs = context?.agent_outputs ?? {}
  const executedAgentKeys = Object.keys(executedOutputs)

  const leadFields = [
    ['Lead ID', 'lead_id'],
    ['Source', 'source'],
    ['Created At', 'created_at'],
    ['Last Contact', 'last_contact_at'],
    ['Declared Need', 'declared_need'],
    ['Stage', 'stage'],
    ['Contact Available', 'contact_available'],
    ['Pending Follow-up', 'pending_follow_up'],
    ['Follow-up Due', 'follow_up_due_at'],
  ]

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
            <h2>Lead Follow-up Prioritization Intelligence</h2>
            <p className="subtitle">
              Transparent, evidence-based lead prioritization through a coordinated agent workflow.
            </p>
          </div>
          <div className="version-tag">AA007 · PHASE 1.2</div>
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
            <span>Run the selected lead through the workflow.</span>
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
        <section className="scenario-panel">
          <div className="section-heading">
            <div>
              <h3>Mandatory Data Validation Test</h3>
              <p>
                Test how the Lead Intake Agent handles a lead with missing contact information.
              </p>
            </div>
            <span className="scenario-count">EDGE CASE</span>
          </div>

          <div className="run-row">
            <span>
              Test input: LEAD-TEST-MISSING-001 · Contact Available: No
            </span>
            <button
              className="run-button"
              onClick={runMissingContactTest}
              disabled={loading}
            >
              {loading ? 'Running test...' : 'Run REQUEST_DATA Test'}
              <span>→</span>
            </button>
          </div>
        </section>
        {error && <div className="error-message">{error}</div>}

        {result && context && (
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
                  <h2>
                    {actionLabels[result.recommendation.action] || result.recommendation.action}
                  </h2>
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
                      style={{
                        width: `${Math.min(result.recommendation.priority_score, 100)}%`,
                      }}
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
                  {result.recommendation.triggered_rules.length > 0 ? (
                    result.recommendation.triggered_rules.map((rule) => (
                      <span className="rule-tag" key={rule}>{rule}</span>
                    ))
                  ) : (
                    <span className="muted-text">No rules recorded.</span>
                  )}
                </div>
              </div>
            </section>

            <section className="result-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">01 / BUSINESS INPUT</p>
                  <h3>Lead Record & Engagement</h3>
                  <p>The input supplied to this workflow execution.</p>
                </div>
              </div>

              <div className="input-grid">
                {leadFields.map(([label, key]) => {
                  const value = context.lead_record[key]
                  const displayValue =
                    key.endsWith('_at') ? formatDate(value) : formatValue(value)

                  return (
                    <div className="data-item" key={key}>
                      <span>{label}</span>
                      <strong>{displayValue}</strong>
                    </div>
                  )
                })}
              </div>

              <h4>Engagement Events ({context.engagement_events.length})</h4>
              {context.engagement_events.length > 0 ? (
                <div className="event-list">
                  {context.engagement_events.map((event, index) => (
                    <div className="event-row" key={String(event.event_id ?? index)}>
                      <strong>{formatValue(event.event_type)}</strong>
                      <span>{formatValue(event.event_id)}</span>
                      <small>{formatDate(event.occurred_at)}</small>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="muted-text">No engagement events supplied.</p>
              )}
            </section>

            <section className="result-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">02 / SHARED CONTEXT</p>
                  <h3>Run-Scoped Shared Workflow Context</h3>
                  <p>
                    A shared context created for this workflow run and updated as agents execute.
                  </p>
                </div>
                <span className="scenario-count">RUN-SCOPED</span>
              </div>

              <div className="context-meta">
                <div className="data-item">
                  <span>Workflow ID</span>
                  <strong>{context.workflow_id}</strong>
                </div>
                <div className="data-item">
                  <span>Started At</span>
                  <strong>{formatDate(context.started_at)}</strong>
                </div>
              </div>

              <div className="context-grid">
                <div className="context-item">
                  <span>Normalized Lead Snapshot</span>
                  <strong>{context.validated_lead ? 'Available' : 'Not available'}</strong>
                </div>
                <div className="context-item">
                  <span>Recency Score</span>
                  <strong>{formatValue(context.recency_score)}</strong>
                </div>
                <div className="context-item">
                  <span>Engagement Score</span>
                  <strong>{formatValue(context.engagement_score)}</strong>
                </div>
                <div className="context-item">
                  <span>Fit Score</span>
                  <strong>{formatValue(context.fit_score)}</strong>
                </div>
                <div className="context-item">
                  <span>Agent Outputs</span>
                  <strong>{executedAgentKeys.length} recorded</strong>
                </div>
                <div className="context-item">
                  <span>Workflow Errors</span>
                  <strong>{context.errors.length}</strong>
                </div>
              </div>

              <h4>Execution Summary</h4>
              <div className="context-updates">
                <div><span>01</span> Lead record and engagement events initialized</div>
                <div>
                  <span>02</span>
                  Lead Intake outcome: {context.agent_outputs.lead_intake?.status ?? 'Not recorded'}
                </div>
                <div><span>03</span> {executedAgentKeys.length} agent output(s) recorded in shared context</div>
                <div><span>04</span> Final recommendation: {context.final_recommendation?.action ?? 'Not available'}</div>
                <div><span>05</span> Audit reference: {context.audit_reference ?? 'Not available'}</div>
              </div>

              <p className="muted-text context-note">
                This context belongs to one workflow execution. It is not permanent or long-term memory.
              </p>
            </section>

            <section className="result-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">03 / AGENT EXECUTION</p>
                  <h3>Agent Workflow Timeline</h3>
                  <p>Only agents with recorded outputs are shown as executed.</p>
                </div>
                <span className="scenario-count">
                  {executedAgentKeys.length} EXECUTED
                </span>
              </div>

              <div className="workflow-line">
                {agentOrder.map((key, index) => {
                  const output = executedOutputs[key]
                  const definition = agentDefinitions[key]

                  return (
                    <article className={`agent-card ${output ? 'agent-executed' : 'agent-skipped'}`} key={key}>
                      <div className="agent-card-heading">
                        <span className="agent-number">
                          {String(index + 1).padStart(2, '0')}
                        </span>
                        <div>
                          <h4>{definition.responsibility.split('.')[0]}</h4>
                          <p>{definition.responsibility}</p>
                        </div>
                        <span className={output ? 'agent-status' : 'agent-skipped-status'}>
                          {output ? 'Executed' : 'Not executed'}
                        </span>
                      </div>

                      <div className="agent-detail-grid">
                        <div>
                          <span>Important Input</span>
                          <strong>{definition.input}</strong>
                        </div>
                        <div>
                          <span>Output</span>
                          {output ? (
                            <strong>{output.agent_name}</strong>
                          ) : (
                            <strong>None recorded</strong>
                          )}
                        </div>
                      </div>

                      {output && (
                        <>
                          <h5>Structured Output</h5>
                          <pre className="json-output">
                            {JSON.stringify(output, null, 2)}
                          </pre>
                        </>
                      )}
                    </article>
                  )
                })}
              </div>
            </section>

            <section className="result-panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">04 / DECISION EVIDENCE</p>
                  <h3>Rules, Scores & Evidence</h3>
                </div>
              </div>

              <h4>SLA Flags</h4>
              <div className="rule-list">
                {context.sla_flags.length > 0 ? (
                  context.sla_flags.map((flag) => (
                    <span className="rule-tag" key={flag}>{flag}</span>
                  ))
                ) : (
                  <span className="muted-text">No SLA flags recorded.</span>
                )}
              </div>

              <h4>Decision Reasons</h4>
              <ul className="reason-list">
                {result.explanation.reasons.map((reason, index) => (
                  <li key={index}>{reason}</li>
                ))}
              </ul>

              <h4>Explanation</h4>
              <p className="explanation-text">{result.explanation.summary}</p>

              {result.explanation.limitations.length > 0 && (
                <>
                  <h4>Limitations and Errors</h4>
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
                <p className="eyebrow">05 / AUDIT TRAIL</p>
                <h3>Workflow Traceability</h3>
                <p className="subtitle">
                  Recorded execution details from the in-memory audit service.
                </p>
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
                <div>
                  <span>Audit Timestamp</span>
                  <strong>{result.audit_record ? formatDate(result.audit_record.timestamp) : 'Not available'}</strong>
                </div>
                <div>
                  <span>Recorded Agent Sequence</span>
                  <strong>
                    {result.audit_record?.agent_sequence.join(' → ') || 'No agents recorded'}
                  </strong>
                </div>
                <div>
                  <span>Audit Storage</span>
                  <strong>In-memory · Process-local</strong>
                </div>
              </div>

              {result.audit_record && (
                <>
                  <h4>Recorded Recommendation</h4>
                  <pre className="json-output">
                    {JSON.stringify(result.audit_record.final_recommendation, null, 2)}
                  </pre>

                  <h4>Recorded Agent Outputs</h4>
                  <pre className="json-output">
                    {JSON.stringify(result.audit_record.agent_outputs, null, 2)}
                  </pre>
                </>
              )}

              {result.errors.length > 0 && (
                <p
                  className={
                    result.recommendation.action === 'REQUEST_DATA'
                      ? 'validation-message'
                      : 'error-message'
                  }
                >
                  {result.errors.join(', ')}
                </p>
              )}
            </section>
          </>
        )}

        {!result && !loading && !error && (
          <div className="empty-state">
            <div className="empty-icon">↗</div>
            <h3>Ready to evaluate leads</h3>
            <p>
              Select a scenario and run prioritization to explore the business input,
              shared workflow context, agent outputs, decision evidence and audit trail.
            </p>
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