import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { ResearchRun, Subscription } from "../types";

function statusClass(status: string) {
  if (status === "completed") return "status-badge status-completed";
  if (status === "failed") return "status-badge status-failed";
  return "status-badge status-running";
}

export function DashboardPage() {
  const { token } = useAuth();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [runs, setRuns] = useState<ResearchRun[]>([]);
  const [runningAll, setRunningAll] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!token) return;
    Promise.all([api.listSubscriptions(token), api.listRuns(token, undefined, 5)]).then(
      ([subs, recentRuns]) => {
        setSubscriptions(subs);
        setRuns(recentRuns);
      },
    );
  }, [token]);

  async function handleRunAll() {
    if (!token) return;
    setRunningAll(true);
    setMessage(null);
    try {
      const result = await api.triggerAllRuns(token);
      setMessage(`Started research runs for ${result.started} active subscription(s).`);
      const recentRuns = await api.listRuns(token, undefined, 5);
      setRuns(recentRuns);
    } finally {
      setRunningAll(false);
    }
  }

  const activeCount = subscriptions.filter((s) => s.active).length;

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Dashboard</h2>
          <p>Overview of your research pipeline and recent digests.</p>
        </div>
        <button className="btn btn-primary" onClick={handleRunAll} disabled={runningAll || activeCount === 0}>
          {runningAll ? "Starting..." : "Run all active topics"}
        </button>
      </div>

      {message && <div className="card" style={{ marginBottom: "1rem" }}>{message}</div>}

      <div className="card-grid" style={{ marginBottom: "1.5rem" }}>
        <div className="card">
          <h3>{subscriptions.length}</h3>
          <p>Total subscriptions</p>
        </div>
        <div className="card">
          <h3>{activeCount}</h3>
          <p>Active topics</p>
        </div>
        <div className="card">
          <h3>{runs[0]?.documents_found ?? 0}</h3>
          <p>Documents in latest run</p>
        </div>
      </div>

      <div className="page-header">
        <div>
          <h2 style={{ fontSize: "1.25rem" }}>Recent runs</h2>
        </div>
        <Link to="/runs" className="btn">
          View all
        </Link>
      </div>

      {runs.length === 0 ? (
        <div className="empty-state">No research runs yet. Subscribe to a topic and run your first digest.</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Subscription</th>
                <th>Status</th>
                <th>Documents</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id}>
                  <td className="mono">#{run.id}</td>
                  <td>#{run.subscription_id}</td>
                  <td>
                    <span className={statusClass(run.status)}>{run.status}</span>
                  </td>
                  <td>{run.documents_found}</td>
                  <td>
                    <Link to={`/runs/${run.id}`}>View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
