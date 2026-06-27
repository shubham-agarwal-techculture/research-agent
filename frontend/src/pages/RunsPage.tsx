import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { ResearchRun } from "../types";

function statusClass(status: string) {
  if (status === "completed") return "status-badge status-completed";
  if (status === "failed") return "status-badge status-failed";
  return "status-badge status-running";
}

export function RunsPage() {
  const { token } = useAuth();
  const [runs, setRuns] = useState<ResearchRun[]>([]);

  useEffect(() => {
    if (!token) return;
    api.listRuns(token, undefined, 50).then(setRuns);
  }, [token]);

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Research Runs</h2>
          <p>History of scheduled and manual research ingestion runs.</p>
        </div>
      </div>

      {runs.length === 0 ? (
        <div className="empty-state">No runs yet.</div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Run</th>
                <th>Subscription</th>
                <th>Status</th>
                <th>Started</th>
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
                  <td>{run.started_at ? new Date(run.started_at).toLocaleString() : "—"}</td>
                  <td>{run.documents_found}</td>
                  <td>
                    <Link to={`/runs/${run.id}`}>Open digest</Link>
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
