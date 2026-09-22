import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Briefcase,
  Activity,
  RefreshCw,
  ChevronRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Target,
  Sparkles,
  FileText,
  Lightbulb,
  Code2,
  FolderKanban,
  TrendingUp,
} from "lucide-react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [page, setPage] = useState("dashboard");
  const [dashboard, setDashboard] = useState(null);
  const [opportunities, setOpportunities] = useState([]);
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);

  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);

  const [refreshing, setRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState("");
  const [refreshError, setRefreshError] = useState("");

  useEffect(() => {
    loadDashboard();
  }, []);

  async function loadDashboard() {
    try {
      setLoading(true);

      const [dashboardRes, opportunitiesRes] = await Promise.all([
        fetch(`${API_URL}/api/dashboard`),
        fetch(`${API_URL}/api/opportunities`),
      ]);

      if (!dashboardRes.ok || !opportunitiesRes.ok) {
        throw new Error("Unable to load dashboard data");
      }

      const dashboardData = await dashboardRes.json();
      const opportunitiesData = await opportunitiesRes.json();

      setDashboard(dashboardData);
      setOpportunities(opportunitiesData.opportunities || opportunitiesData || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  async function openOpportunity(id) {
    try {
      setDetailLoading(true);
      setSelectedOpportunity(null);

      const response = await fetch(`${API_URL}/api/opportunities/${id}`);

      if (!response.ok) {
        throw new Error("Unable to load opportunity");
      }

      const data = await response.json();

      setSelectedOpportunity(data);
      setPage("opportunity");
    } catch (error) {
      console.error(error);
    } finally {
      setDetailLoading(false);
    }
  }

  async function handleRefresh() {
    if (refreshing) return;

    try {
      setRefreshing(true);
      setRefreshMessage("Checking Gmail for new opportunities...");
      setRefreshError("");

      const response = await fetch(`${API_URL}/api/refresh`, {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error("Unable to start Gmail refresh.");
      }

      pollRefreshStatus();
    } catch (error) {
      console.error(error);
      setRefreshing(false);
      setRefreshError(error.message);
      setRefreshMessage("");
    }
  }

  function pollRefreshStatus() {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_URL}/api/refresh/status`);

        if (!response.ok) {
          throw new Error("Unable to check refresh status");
        }

        const data = await response.json();

        if (data.running) {
          setRefreshMessage(data.message || "Processing...");
          return;
        }

        clearInterval(interval);

        if (data.error) {
          setRefreshing(false);
          setRefreshMessage("");
          setRefreshError(data.error);
          return;
        }

        setRefreshing(false);
        setRefreshError("");
        setRefreshMessage(
          data.message || "Gmail checked successfully. Opportunities updated."
        );

        await loadDashboard();

        setTimeout(() => {
          setRefreshMessage("");
        }, 5000);
      } catch (error) {
        clearInterval(interval);
        setRefreshing(false);
        setRefreshMessage("");
        setRefreshError(error.message);
      }
    }, 2000);
  }

  function goToOpportunities() {
    setPage("opportunities");
  }

  function renderRecommendation(recommendation) {
    if (!recommendation) return "NOT ANALYZED";

    const value = recommendation.toString().toUpperCase();

    if (value.includes("STRONG")) {
      return "STRONG APPLY";
    }

    if (value.includes("APPLY")) {
      return "APPLY";
    }

    if (value.includes("CONSIDER")) {
      return "CONSIDER";
    }

    if (value.includes("SKIP")) {
      return "SKIP";
    }

    return recommendation;
  }

  function getRecommendationClass(recommendation) {
    const value = (recommendation || "").toString().toUpperCase();

    if (value.includes("STRONG")) return "strong";
    if (value.includes("APPLY")) return "apply";
    if (value.includes("CONSIDER")) return "consider";
    if (value.includes("SKIP")) return "skip";

    return "neutral";
  }

  function getScore(opportunity) {
    return (
      opportunity.fit_score ??
      opportunity.score ??
      opportunity.analysis?.fit_score ??
      null
    );
  }

  function getAnalysis(opportunity) {
    return (
      opportunity.analysis ||
      opportunity.analysis_result ||
      opportunity.resume_analysis ||
      null
    );
  }

  function renderDashboard() {
    if (loading) {
      return <div className="loading">Loading dashboard...</div>;
    }

    const total = dashboard?.total_opportunities ?? 0;
    const analyzed = dashboard?.analyzed_opportunities ?? 0;
    const strong = dashboard?.strong_matches ?? 0;
    const consider = dashboard?.consider_matches ?? 0;
    const low = dashboard?.low_matches ?? 0;

    const recent = [...opportunities]
      .sort((a, b) => {
        const aScore = getScore(a);
        const bScore = getScore(b);

        if (aScore !== null && bScore === null) return -1;
        if (aScore === null && bScore !== null) return 1;

        return (b.id || 0) - (a.id || 0);
      })
      .slice(0, 6);

    return (
      <>
        <div className="page-header">
          <div>
            <h1>Placement Dashboard</h1>
            <p>
              Monitor opportunities and see how your resume fits each role.
            </p>
          </div>

          <button
            className="refresh-button"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw size={17} className={refreshing ? "spin" : ""} />
            {refreshing ? "Checking..." : "Check Mail"}
          </button>
        </div>

        {refreshMessage && (
          <div className="refresh-status success">
            <CheckCircle2 size={17} />
            {refreshMessage}
          </div>
        )}

        {refreshError && (
          <div className="refresh-status error">
            <AlertCircle size={17} />
            {refreshError}
          </div>
        )}

        <div className="metrics-grid">
          <MetricCard
            title="Total Opportunities"
            value={total}
            icon={<Briefcase size={21} />}
          />

          <MetricCard
            title="Analyzed"
            value={analyzed}
            icon={<Sparkles size={21} />}
          />

          <MetricCard
            title="Strong Matches"
            value={strong}
            icon={<Target size={21} />}
          />

          <MetricCard
            title="Consider"
            value={consider}
            icon={<Activity size={21} />}
          />

          <MetricCard
            title="Low Matches"
            value={low}
            icon={<XCircle size={21} />}
          />
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <div>
              <h2>Recent Opportunities</h2>
              <p>Click an opportunity to view the resume analysis.</p>
            </div>

            <button className="text-button" onClick={goToOpportunities}>
              View all
              <ChevronRight size={16} />
            </button>
          </div>

          <OpportunityTable
            opportunities={recent}
            onOpen={openOpportunity}
            getScore={getScore}
            renderRecommendation={renderRecommendation}
            getRecommendationClass={getRecommendationClass}
          />
        </div>

        <div className="dashboard-card">
          <div className="card-header">
            <div>
              <h2>Placement Pipeline</h2>
              <p>Current system workflow</p>
            </div>
          </div>

          <div className="pipeline">
            <PipelineStep
              number="01"
              title="Gmail Reader"
              description="Reads placement emails"
            />
            <PipelineArrow />
            <PipelineStep
              number="02"
              title="JD Extraction"
              description="Extracts job descriptions"
            />
            <PipelineArrow />
            <PipelineStep
              number="03"
              title="AI Analysis"
              description="Compares resume with JD"
            />
            <PipelineArrow />
            <PipelineStep
              number="04"
              title="Decision"
              description="Generates recommendations"
            />
          </div>
        </div>
      </>
    );
  }

  function renderOpportunities() {
    return (
      <>
        <div className="page-header">
          <div>
            <h1>Opportunities</h1>
            <p>All placement opportunities detected from Gmail.</p>
          </div>

          <button
            className="refresh-button"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw size={17} className={refreshing ? "spin" : ""} />
            {refreshing ? "Checking..." : "Check Mail"}
          </button>
        </div>

        {refreshMessage && (
          <div className="refresh-status success">
            <CheckCircle2 size={17} />
            {refreshMessage}
          </div>
        )}

        {refreshError && (
          <div className="refresh-status error">
            <AlertCircle size={17} />
            {refreshError}
          </div>
        )}

        <div className="dashboard-card">
          <div className="card-header">
            <div>
              <h2>All Opportunities</h2>
              <p>Select a company to view your resume analysis.</p>
            </div>
          </div>

          <OpportunityTable
            opportunities={opportunities}
            onOpen={openOpportunity}
            getScore={getScore}
            renderRecommendation={renderRecommendation}
            getRecommendationClass={getRecommendationClass}
          />
        </div>
      </>
    );
  }

  function renderOpportunityDetail() {
    if (detailLoading || !selectedOpportunity) {
      return <div className="loading">Loading opportunity analysis...</div>;
    }

    const opportunity = selectedOpportunity;
    const analysis = getAnalysis(opportunity);

    const score = getScore(opportunity);
    const recommendation =
      opportunity.recommendation ||
      analysis?.recommendation ||
      opportunity.decision ||
      null;

    const bestTrack =
      opportunity.best_track ||
      analysis?.best_track ||
      analysis?.best_fit_track ||
      null;

    return (
      <>
        <button
          className="back-button"
          onClick={() => setPage("opportunities")}
        >
          <ArrowLeft size={17} />
          Back to Opportunities
        </button>

        <div className="opportunity-header">
          <div>
            <div className="company-title-row">
              <div className="company-icon">
                <Briefcase size={23} />
              </div>

              <div>
                <h1>{opportunity.company || "Unknown Company"}</h1>
                <p>{opportunity.role || "Role not specified"}</p>
              </div>
            </div>
          </div>

          <div className="detail-actions">
            <span
              className={`recommendation ${getRecommendationClass(
                recommendation
              )}`}
            >
              {renderRecommendation(recommendation)}
            </span>
          </div>
        </div>

        {!analysis && (
          <div className="analysis-unavailable">
            <AlertCircle size={24} />
            <div>
              <h3>Analysis not available yet</h3>
              <p>
                This opportunity has been detected, but your resume analyzer
                has not generated an analysis for it yet.
              </p>
            </div>
          </div>
        )}

        {analysis && (
          <>
            <div className="analysis-summary-grid">
              <SummaryCard
                icon={<Target size={20} />}
                title="Resume Fit Score"
                value={
                  score !== null && score !== undefined ? `${score}/100` : "—"
                }
              />

              <SummaryCard
                icon={<TrendingUp size={20} />}
                title="Recommendation"
                value={renderRecommendation(recommendation)}
              />

              <SummaryCard
                icon={<Code2 size={20} />}
                title="Best Track"
                value={bestTrack || "—"}
              />
            </div>

            <AnalysisSection
              icon={<Sparkles size={19} />}
              title="AI Assessment"
            >
              <AnalysisText
                value={
                  analysis.ai_assessment ||
                  analysis.assessment ||
                  analysis.overall_assessment ||
                  analysis.summary ||
                  "No AI assessment available."
                }
              />
            </AnalysisSection>

            <div className="analysis-two-column">
              <AnalysisSection
                icon={<CheckCircle2 size={19} />}
                title="Direct Matches"
              >
                <AnalysisList
                  items={
                    analysis.direct_matches ||
                    analysis.direct_match ||
                    []
                  }
                />
              </AnalysisSection>

              <AnalysisSection
                icon={<FolderKanban size={19} />}
                title="Project / Domain Evidence"
              >
                <AnalysisList
                  items={
                    analysis.project_domain_evidence ||
                    analysis.project_evidence ||
                    analysis.domain_evidence ||
                    []
                  }
                />
              </AnalysisSection>
            </div>

            <div className="analysis-two-column">
              <AnalysisSection
                icon={<TrendingUp size={19} />}
                title="Transferable Matches"
              >
                <AnalysisList
                  items={
                    analysis.transferable_matches ||
                    analysis.transferable_skills ||
                    []
                  }
                />
              </AnalysisSection>

              <AnalysisSection
                icon={<AlertCircle size={19} />}
                title="Missing / Weak Areas"
              >
                <AnalysisList
                  items={
                    analysis.missing_weak ||
                    analysis.missing_or_weak ||
                    analysis.gaps ||
                    []
                  }
                />
              </AnalysisSection>
            </div>

            <AnalysisSection
              icon={<Lightbulb size={19} />}
              title="Resume Improvement Suggestions"
            >
              <AnalysisList
                items={
                  analysis.resume_improvements ||
                  analysis.resume_suggestions ||
                  analysis.suggestions ||
                  []
                }
              />
            </AnalysisSection>

            <AnalysisSection
              icon={<FileText size={19} />}
              title="Why This Score?"
            >
              <AnalysisText
                value={
                  analysis.why_score ||
                  analysis.score_reason ||
                  analysis.reason ||
                  "No score explanation available."
                }
              />
            </AnalysisSection>

            {(analysis.track_comparison ||
              analysis.track_comparisons) && (
              <AnalysisSection
                icon={<Code2 size={19} />}
                title="Track Comparison"
              >
                <AnalysisList
                  items={
                    analysis.track_comparison ||
                    analysis.track_comparisons ||
                    []
                  }
                />
              </AnalysisSection>
            )}
          </>
        )}
      </>
    );
  }

  function renderStatus() {
    return (
      <>
        <div className="page-header">
          <div>
            <h1>System Status</h1>
            <p>Current status of the placement assistant components.</p>
          </div>
        </div>

        <div className="status-grid">
          <StatusCard
            title="Gmail Reader"
            description="Reads placement emails and attachments"
            status="Operational"
          />

          <StatusCard
            title="JD Processor"
            description="Extracts and processes job descriptions"
            status="Operational"
          />

          <StatusCard
            title="Resume Analyzer"
            description="Matches resume against job descriptions"
            status="Operational"
          />

          <StatusCard
            title="Qwen LLM"
            description="Local AI model used for analysis"
            status="Operational"
          />
        </div>
      </>
    );
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Sparkles size={21} />
          </div>

          <div>
            <strong>Placement AI</strong>
            <span>Assistant</span>
          </div>
        </div>

        <nav className="navigation">
          <NavItem
            icon={<LayoutDashboard size={19} />}
            label="Dashboard"
            active={page === "dashboard"}
            onClick={() => setPage("dashboard")}
          />

          <NavItem
            icon={<Briefcase size={19} />}
            label="Opportunities"
            active={page === "opportunities" || page === "opportunity"}
            onClick={() => setPage("opportunities")}
          />

          <NavItem
            icon={<Activity size={19} />}
            label="System Status"
            active={page === "status"}
            onClick={() => setPage("status")}
          />
        </nav>

        <div className="sidebar-footer">
          <div className="system-dot"></div>
          <span>Local system active</span>
        </div>
      </aside>

      <main className="main-content">
        {page === "dashboard" && renderDashboard()}
        {page === "opportunities" && renderOpportunities()}
        {page === "opportunity" && renderOpportunityDetail()}
        {page === "status" && renderStatus()}
      </main>
    </div>
  );
}

function NavItem({ icon, label, active, onClick }) {
  return (
    <button
      className={`nav-item ${active ? "active" : ""}`}
      onClick={onClick}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function MetricCard({ title, value, icon }) {
  return (
    <div className="metric-card">
      <div className="metric-icon">{icon}</div>
      <div>
        <span>{title}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function SummaryCard({ icon, title, value }) {
  return (
    <div className="summary-card">
      <div className="summary-icon">{icon}</div>
      <div>
        <span>{title}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function OpportunityTable({
  opportunities,
  onOpen,
  getScore,
  renderRecommendation,
  getRecommendationClass,
}) {
  if (!opportunities.length) {
    return (
      <div className="empty-state">
        <Briefcase size={30} />
        <h3>No opportunities found</h3>
        <p>Check Gmail to look for new placement opportunities.</p>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table className="opportunity-table">
        <thead>
          <tr>
            <th>Company</th>
            <th>Role</th>
            <th>Fit Score</th>
            <th>Recommendation</th>
            <th></th>
          </tr>
        </thead>

        <tbody>
          {opportunities.map((opportunity) => {
            const score = getScore(opportunity);

            const recommendation =
              opportunity.recommendation ||
              opportunity.analysis?.recommendation ||
              null;

            return (
              <tr
                key={opportunity.id}
                className="clickable-row"
                onClick={() => onOpen(opportunity.id)}
              >
                <td>
                  <button
                    className="company-link"
                    onClick={(event) => {
                      event.stopPropagation();
                      onOpen(opportunity.id);
                    }}
                  >
                    {opportunity.company || "Unknown"}
                  </button>
                </td>

                <td>{opportunity.role || "—"}</td>

                <td>
                  {score !== null && score !== undefined ? (
                    <span className="score-value">{score}</span>
                  ) : (
                    <span className="not-analyzed">—</span>
                  )}
                </td>

                <td>
                  <span
                    className={`recommendation ${getRecommendationClass(
                      recommendation
                    )}`}
                  >
                    {renderRecommendation(recommendation)}
                  </span>
                </td>

                <td>
                  <ChevronRight size={18} className="row-arrow" />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function AnalysisSection({ icon, title, children }) {
  return (
    <section className="analysis-section">
      <div className="analysis-section-header">
        <div className="analysis-section-icon">{icon}</div>
        <h2>{title}</h2>
      </div>

      <div className="analysis-section-content">{children}</div>
    </section>
  );
}

function AnalysisList({ items }) {
  if (!items || items.length === 0) {
    return <p className="muted-text">No information available.</p>;
  }

  if (!Array.isArray(items)) {
    return <AnalysisText value={items} />;
  }

  return (
    <ul className="analysis-list">
      {items.map((item, index) => {
        if (typeof item === "string") {
          return <li key={index}>{item}</li>;
        }

        if (typeof item === "object" && item !== null) {
          const title =
            item.title ||
            item.skill ||
            item.name ||
            item.area ||
            item.category;

          const description =
            item.description ||
            item.reason ||
            item.evidence ||
            item.details ||
            item.explanation;

          return (
            <li key={index}>
              {title && <strong>{title}</strong>}
              {description && (
                <span className="list-description">{description}</span>
              )}
            </li>
          );
        }

        return <li key={index}>{String(item)}</li>;
      })}
    </ul>
  );
}

function AnalysisText({ value }) {
  if (!value) {
    return <p className="muted-text">No information available.</p>;
  }

  if (typeof value === "object") {
    return <AnalysisList items={[value]} />;
  }

  return <p className="analysis-text">{value}</p>;
}

function PipelineStep({ number, title, description }) {
  return (
    <div className="pipeline-step">
      <div className="pipeline-number">{number}</div>
      <div>
        <strong>{title}</strong>
        <span>{description}</span>
      </div>
    </div>
  );
}

function PipelineArrow() {
  return <ChevronRight className="pipeline-arrow" size={20} />;
}

function StatusCard({ title, description, status }) {
  return (
    <div className="status-card">
      <div className="status-card-top">
        <div>
          <h3>{title}</h3>
          <p>{description}</p>
        </div>

        <div className="operational">
          <span></span>
          {status}
        </div>
      </div>
    </div>
  );
}

export default App;