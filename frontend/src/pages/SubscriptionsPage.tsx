import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";
import type { PredefinedTopic, Subscription } from "../types";

export function SubscriptionsPage() {
  const { token } = useAuth();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [predefined, setPredefined] = useState<PredefinedTopic[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [queries, setQueries] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    if (!token) return;
    const [subs, topics] = await Promise.all([
      api.listSubscriptions(token),
      api.listPredefinedTopics(token),
    ]);
    setSubscriptions(subs);
    setPredefined(topics);
  }

  useEffect(() => {
    refresh().catch((err) => setError(String(err)));
  }, [token]);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setError(null);
    try {
      await api.createSubscription(token, {
        name,
        description,
        search_queries: queries
          .split(",")
          .map((q) => q.trim())
          .filter(Boolean),
      });
      setName("");
      setDescription("");
      setQueries("");
      await refresh();
    } catch (err) {
      setError(String(err));
    }
  }

  async function handlePredefined(topicId: string) {
    if (!token) return;
    setError(null);
    try {
      await api.subscribePredefined(token, topicId);
      await refresh();
    } catch (err) {
      setError(String(err));
    }
  }

  async function withBusy<T>(id: number, action: () => Promise<T>) {
    setBusyId(id);
    try {
      await action();
      await refresh();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h2>Subscriptions</h2>
          <p>Follow predefined topics or create your own custom research interests.</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <section style={{ marginBottom: "2rem" }}>
        <h3 style={{ marginBottom: "0.75rem" }}>Predefined topics</h3>
        <div className="card-grid">
          {predefined.map((topic) => (
            <article className="card" key={topic.id}>
              <h3>{topic.name}</h3>
              <p>{topic.description}</p>
              <div className="card-actions">
                <button className="btn btn-primary" onClick={() => handlePredefined(topic.id)}>
                  Subscribe
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section style={{ marginBottom: "2rem" }}>
        <h3 style={{ marginBottom: "0.75rem" }}>Create custom subscription</h3>
        <form className="card form-stack" onSubmit={handleCreate}>
          <label>
            Name
            <input value={name} onChange={(e) => setName(e.target.value)} required />
          </label>
          <label>
            Description
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={3} />
          </label>
          <label>
            Search queries (comma-separated)
            <input value={queries} onChange={(e) => setQueries(e.target.value)} placeholder="agentic AI, LLM tools" />
          </label>
          <button className="btn btn-primary" type="submit">
            Add subscription
          </button>
        </form>
      </section>

      <section>
        <h3 style={{ marginBottom: "0.75rem" }}>Your subscriptions</h3>
        {subscriptions.length === 0 ? (
          <div className="empty-state">No subscriptions yet.</div>
        ) : (
          <div className="card-grid">
            {subscriptions.map((sub) => (
              <article className="card" key={sub.id}>
                <h3>
                  {sub.name}{" "}
                  <span className={`status-badge ${sub.active ? "status-completed" : "status-failed"}`}>
                    {sub.active ? "active" : "paused"}
                  </span>
                </h3>
                <p>{sub.description || "No description"}</p>
                <p className="mono" style={{ marginTop: "0.75rem", color: "var(--text-muted)" }}>
                  {sub.search_queries.join(" · ")}
                </p>
                <div className="card-actions">
                  <button
                    className="btn btn-primary"
                    disabled={busyId === sub.id}
                    onClick={() =>
                      withBusy(sub.id, async () => {
                        if (!token) return;
                        await api.triggerSubscriptionRun(token, sub.id);
                      })
                    }
                  >
                    Run now
                  </button>
                  {sub.active ? (
                    <button
                      className="btn"
                      disabled={busyId === sub.id}
                      onClick={() => withBusy(sub.id, () => api.pauseSubscription(token!, sub.id))}
                    >
                      Pause
                    </button>
                  ) : (
                    <button
                      className="btn"
                      disabled={busyId === sub.id}
                      onClick={() => withBusy(sub.id, () => api.resumeSubscription(token!, sub.id))}
                    >
                      Resume
                    </button>
                  )}
                  <button
                    className="btn btn-danger"
                    disabled={busyId === sub.id}
                    onClick={() => withBusy(sub.id, () => api.deleteSubscription(token!, sub.id))}
                  >
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </>
  );
}
