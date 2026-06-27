import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { RunOutput, SourceDocument } from "../types";

export function RunDetailPage() {
  const { runId } = useParams();
  const { token } = useAuth();
  const [output, setOutput] = useState<RunOutput | null>(null);
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token || !runId) return;
    const id = Number(runId);
    Promise.all([api.getRunOutput(token, id), api.getRunDocuments(token, id)])
      .then(([runOutput, docs]) => {
        setOutput(runOutput);
        setDocuments(docs);
      })
      .catch((err) => setError(String(err)));
  }, [token, runId]);

  if (error) {
    return (
      <>
        <Link to="/runs" className="btn">
          ← Back to runs
        </Link>
        <div className="error-banner" style={{ marginTop: "1rem" }}>
          {error}
        </div>
      </>
    );
  }

  if (!output) {
    return <div className="empty-state">Loading digest...</div>;
  }

  return (
    <>
      <div className="page-header">
        <div>
          <Link to="/runs" style={{ color: "var(--text-muted)", fontSize: "0.9rem" }}>
            ← Back to runs
          </Link>
          <h2>Run #{output.run.id}</h2>
          <p>
            Subscription #{output.run.subscription_id} · {output.run.documents_found} documents
          </p>
        </div>
      </div>

      <section style={{ marginBottom: "1.5rem" }}>
        <h3 style={{ marginBottom: "0.75rem" }}>Sources</h3>
        <div className="card-grid">
          {documents.map((doc) => (
            <article className="card" key={`${doc.url}-${doc.title}`}>
              <h3>{doc.title}</h3>
              <p>
                {doc.origin} · {doc.source_type}
              </p>
              <p style={{ marginTop: "0.75rem" }}>{doc.content_snippet.slice(0, 220)}...</p>
              <div className="card-actions">
                <a className="btn" href={doc.url} target="_blank" rel="noreferrer">
                  Open source
                </a>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section>
        <h3 style={{ marginBottom: "0.75rem" }}>Markdown digest</h3>
        <div className="markdown-view">{output.markdown}</div>
      </section>
    </>
  );
}
