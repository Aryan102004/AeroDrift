
import { useCallback, useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowDown,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  Cloud,
  Database,
  GitBranch,
  History,
  LayoutDashboard,
  LoaderCircle,
  Network,
  RefreshCw,
  Server,
  Shield,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import "./index.css";

const navigation = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "topology", label: "Cloud topology", icon: Network },
  { id: "findings", label: "Drift findings", icon: ShieldAlert },
  { id: "history", label: "Snapshot history", icon: History },
];

const API = "/api";

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed: ${response.status}`);
  }

  return response.json();
}

function MetricCard({ label, value, icon: Icon, tone = "cyan", detail }) {
  return (
    <article className="metric-card">
      <div className="metric-heading">
        <span>{label}</span>
        <span className={`metric-icon ${tone}`}>
          <Icon size={19} />
        </span>
      </div>
      <div className="metric-value">{value ?? "—"}</div>
      <div className="metric-detail">{detail}</div>
    </article>
  );
}

function TopologyGraph({ topology }) {
  const nodes = topology?.nodes ?? [];
  const edges = topology?.edges ?? [];

  if (!nodes.length) {
    return <div className="empty-state">No topology nodes returned by the API.</div>;
  }

  const columns = [
    nodes.filter((node) => node.resource_type === "external"),
    nodes.filter((node) => ["vpc", "subnet"].includes(node.resource_type)),
    nodes.filter((node) =>
      ["ec2", "security_group", "database"].includes(node.resource_type)
    ),
  ];

  const visibleColumns = columns.map((column) =>
    column.length ? column : []
  );

  return (
    <div className="topology-scroll">
      <div className="topology-graph">
        {visibleColumns.map((column, index) => (
          <div className="topology-column" key={index}>
            {column.map((node) => {
              const incoming = edges.filter((edge) => edge.target === node.id);
              const outgoing = edges.filter((edge) => edge.source === node.id);
              const isExternal = node.resource_type === "external";
              const isDatabase = node.resource_type === "database";

              return (
                <div
                  className={`resource-node ${isExternal ? "external" : ""} ${
                    isDatabase ? "database" : ""
                  }`}
                  key={node.id}
                >
                  <div className="resource-node-icon">
                    {isExternal ? (
                      <Cloud size={18} />
                    ) : isDatabase ? (
                      <Database size={18} />
                    ) : node.resource_type === "ec2" ? (
                      <Server size={18} />
                    ) : (
                      <Network size={18} />
                    )}
                  </div>
                  <div className="resource-node-name">
                    {node.name || node.id}
                  </div>
                  <div className="resource-node-type">{node.resource_type}</div>
                  <div className="resource-node-meta">
                    {incoming.length + outgoing.length} connections
                  </div>
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <div className="topology-summary">
        <span><i className="legend-dot cyan" /> {nodes.length} nodes</span>
        <span><i className="legend-dot green" /> {edges.length} edges</span>
        <span>Graph supplied by FastAPI</span>
      </div>
    </div>
  );
}

function App() {
  const [activeView, setActiveView] = useState("overview");
  const [overview, setOverview] = useState(null);
  const [topology, setTopology] = useState(null);
  const [snapshots, setSnapshots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [snapshotLabel, setSnapshotLabel] = useState("Web dashboard snapshot");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [overviewData, topologyData, snapshotData] = await Promise.all([
        apiRequest("/overview"),
        apiRequest("/topology"),
        apiRequest("/snapshots"),
      ]);

      setOverview(overviewData);
      setTopology(topologyData);
      setSnapshots(snapshotData.snapshots ?? []);
    } catch (err) {
      setError(
        `${err.message}. Check that FastAPI is running at 127.0.0.1:8000.`
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  
    
async function createSnapshot(event) {
  event.preventDefault();

  const label = snapshotLabel.trim();
  if (!label || saving) return;

  setSaving(true);
  setNotice("");
  setError("");

  try {
    // Save the snapshot to FastAPI / SQLite.
    const saved = await apiRequest("/snapshots", {
      method: "POST",
      body: JSON.stringify({ label }),
    });

    // Confirm the save independently of list refreshing.
    setNotice(
      saved.message ||
        `Snapshot #${saved.id} saved successfully to SQLite.`
    );

    // Refresh the snapshot list separately.
    try {
      const result = await apiRequest("/snapshots");
      setSnapshots(result.snapshots ?? []);
    } catch (refreshError) {
      setError(
        `Snapshot saved successfully, but the list could not refresh: ${refreshError.message}`
      );
    }
  } catch (err) {
    setError(`Snapshot could not be saved: ${err.message}`);
  } finally {
    setSaving(false);
  }
}


  const resourceCounts = overview?.resources ?? {};
  const findings = overview?.findings ?? [];

  const pageTitles = {
    overview: ["Security overview", "Monitor infrastructure and review cloud drift."],
    topology: ["Cloud topology", "Explore the resource graph returned by AeroDrift."],
    findings: ["Drift findings", "Review newly detected exposure paths."],
    history: ["Snapshot history", "View and save persistent topology snapshots."],
  };

  const [pageTitle, pageSubtitle] = pageTitles[activeView];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-symbol"><Shield size={23} /></div>
          <div>
            <div className="brand-title">AERODRIFT</div>
            <div className="brand-caption">CLOUD SECURITY GRAPH</div>
          </div>
        </div>

        <div className="sidebar-label">WORKSPACE</div>
        <nav className="sidebar-nav">
          {navigation.map(({ id, label, icon: Icon }) => (
            <button
              className={`nav-item ${activeView === id ? "active" : ""}`}
              key={id}
              onClick={() => setActiveView(id)}
            >
              <Icon size={18} />
              <span>{label}</span>
              {id === "findings" && findings.length > 0 && (
                <span className="nav-count">{findings.length}</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-spacer" />

        <div className="environment-card">
          <div className="environment-label">EXECUTION ENVIRONMENT</div>
          <div className="environment-status">
            <span className="status-dot" /> Mock mode enabled
          </div>
          <p>Using mock infrastructure. No live AWS changes are performed.</p>
        </div>

        <div className="sidebar-footer">AeroDrift · Week 4</div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">CLOUD OPERATIONS / SECURITY POSTURE</div>
            <h1>{pageTitle}</h1>
            <p className="page-subtitle">{pageSubtitle}</p>
          </div>
          <div className="topbar-actions">
            <span className="environment-badge">
              <span className="status-dot" /> MOCK ENVIRONMENT
            </span>
            <button
              className="icon-button"
              onClick={loadDashboard}
              title="Refresh dashboard data"
              disabled={loading}
            >
              <RefreshCw size={17} className={loading ? "spin" : ""} />
            </button>
          </div>
        </header>

        {error && (
          <div className="alert-banner error-banner">
            <XCircle size={19} />
            <div><strong>API request failed</strong><p>{error}</p></div>
            <button className="banner-close" onClick={() => setError("")}>×</button>
          </div>
        )}

        {notice && (
          <div className="alert-banner success-banner">
            <CheckCircle2 size={19} />
            <span>{notice}</span>
            <button className="banner-close" onClick={() => setNotice("")}>×</button>
          </div>
        )}

        {activeView === "overview" && (
          <>
            <section className="metric-grid">
              <MetricCard label="VPCs" value={resourceCounts.vpcs} icon={Cloud} detail="Virtual private clouds" />
              <MetricCard label="EC2 instances" value={resourceCounts.ec2_instances} icon={Server} detail="Compute resources" tone="green" />
              <MetricCard label="Graph relationships" value={overview?.graph_edges} icon={GitBranch} detail={`${overview?.graph_nodes ?? "—"} graph nodes`} tone="purple" />
              <MetricCard label="New exposure findings" value={overview?.finding_count} icon={AlertTriangle} detail="Requires review" tone="red" />
            </section>

            <section className="content-grid">
              <article className="panel topology-panel">
                <div className="panel-header">
                  <div>
                    <h2><Network size={17} /> Cloud topology graph</h2>
                    <p>Resources and relationships from the AeroDrift API</p>
                  </div>
                  <button className="text-button" onClick={() => setActiveView("topology")}>
                    Explore graph <ChevronRight size={15} />
                  </button>
                </div>
                <TopologyGraph topology={topology} />
              </article>

              <article className="panel findings-panel">
                <div className="panel-header">
                  <div>
                    <h2><ShieldAlert size={17} /> Priority findings</h2>
                    <p>Detected by the current graph comparison</p>
                  </div>
                  <span className="count-badge">{findings.length}</span>
                </div>

                {loading ? (
                  <div className="empty-state"><LoaderCircle className="spin" size={20} /> Loading findings…</div>
                ) : findings.length === 0 ? (
                  <div className="empty-state"><CheckCircle2 size={22} /> No new graph exposure findings.</div>
                ) : findings.map((finding) => (
                  <div className="finding-card" key={finding.resource_id}>
                    <div className="finding-top">
                      <span className="severity-badge"><AlertTriangle size={13} /> HIGH</span>
                      <span className="demo-badge">SYNTHETIC</span>
                    </div>
                    <h3>{finding.resource_id}</h3>
                    <p>{finding.message}</p>
                    <div className="finding-path">
                      {(finding.path ?? []).map((node, index) => (
                        <span className="path-step" key={`${node}-${index}`}>
                          {index > 0 && <ArrowRight size={13} />}
                          <code>{node}</code>
                        </span>
                      ))}
                    </div>
                    <button className="secondary-button full-button" onClick={() => setActiveView("findings")}>
                      View finding details <ArrowRight size={15} />
                    </button>
                  </div>
                ))}
              </article>
            </section>

            <section className="metric-grid secondary-metrics">
              <MetricCard label="Subnets" value={resourceCounts.subnets} icon={Network} detail="Network segments" />
              <MetricCard label="Security groups" value={resourceCounts.security_groups} icon={Shield} detail="Security controls" tone="purple" />
              <MetricCard label="Databases" value={resourceCounts.databases} icon={Database} detail="Includes synthetic demo DB" tone="green" />
              <MetricCard label="Saved snapshots" value={snapshots.length} icon={History} detail="SQLite history records" />
            </section>
          </>
        )}

        {activeView === "topology" && (
          <section className="panel standalone-panel">
            <div className="panel-header">
              <div>
                <h2><Network size={18} /> Resource topology</h2>
                <p>Each node is returned by the backend. Columns group resources by type.</p>
              </div>
              <span className="count-badge">{topology?.nodes?.length ?? 0} nodes</span>
            </div>
            <TopologyGraph topology={topology} />
            <div className="topology-footnote">
              <Activity size={15} /> This is a grouped graph view; connection counts are based on API edges.
              A later iteration can add positioned edge lines and zoom controls.
            </div>
          </section>
        )}

        {activeView === "findings" && (
          <section className="panel standalone-panel">
            <div className="panel-header">
              <div>
                <h2><ShieldAlert size={18} /> Drift findings</h2>
                <p>Graph-reachability findings from the synthetic comparison.</p>
              </div>
              <span className="count-badge">{findings.length} findings</span>
            </div>
            {findings.length === 0 ? (
              <div className="empty-state">No new findings were returned.</div>
            ) : findings.map((finding) => (
              <div className="finding-detail" key={finding.resource_id}>
                <div className="finding-detail-icon"><AlertTriangle size={21} /></div>
                <div className="finding-detail-content">
                  <span className="severity-badge"><AlertTriangle size={13} /> HIGH · SYNTHETIC</span>
                  <h3>{finding.resource_id}</h3>
                  <p>{finding.message}</p>
                  <div className="finding-path large-path">
                    {(finding.path ?? []).map((node, index) => (
                      <span className="path-step" key={`${node}-${index}`}>
                        {index > 0 && <ArrowRight size={13} />}
                        <code>{node}</code>
                      </span>
                    ))}
                  </div>
                  <p className="disclaimer">This is a graph-reachability result from mock data, not an AWS packet-level permission validation.</p>
                </div>
              </div>
            ))}
          </section>
        )}

        {activeView === "history" && (
          <section className="panel standalone-panel">
            <div className="panel-header">
              <div>
                <h2><History size={18} /> Snapshot history</h2>
                <p>Snapshots are stored using the existing SQLite persistence module.</p>
              </div>
              <button className="secondary-button" onClick={loadDashboard}>
                <RefreshCw size={15} /> Refresh history
              </button>
            </div>

            <form className="snapshot-form" onSubmit={createSnapshot}>
              <label htmlFor="snapshot-label">Snapshot label</label>
              <div className="snapshot-form-row">
                <input
                  id="snapshot-label"
                  value={snapshotLabel}
                  maxLength={100}
                  onChange={(event) => setSnapshotLabel(event.target.value)}
                  required
                />
                <button className="primary-button" type="submit" disabled={saving || !snapshotLabel.trim()}>
                  {saving ? <LoaderCircle size={16} className="spin" /> : <History size={16} />}
                  {saving ? "Saving…" : "Save snapshot"}
                </button>
              </div>
            </form>

            {snapshots.length === 0 ? (
              <div className="empty-state">No snapshots have been saved to the database yet.</div>
            ) : (
              <div className="snapshot-list">
                {snapshots.map((snapshot) => (
                  <div className="snapshot-row" key={snapshot.id}>
                    <div className="snapshot-row-icon"><Database size={17} /></div>
                    <div className="snapshot-row-content">
                      <strong>{snapshot.label}</strong>
                      <span>Snapshot #{snapshot.id} · {new Date(snapshot.timestamp).toLocaleString()}</span>
                    </div>
                    <span className="snapshot-status">Persisted</span>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        <footer className="app-footer">
          <span>AeroDrift · Agentic Cloud Topology &amp; Remediation Graph</span>
          <span>{loading ? "Fetching API data…" : "API connected when requests succeed"} · Mock environment</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
