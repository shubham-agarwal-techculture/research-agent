import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <h1>Research Agent</h1>
          <p>Your personal idea machine</p>
        </div>
        <nav className="nav-links">
          <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
            Dashboard
          </NavLink>
          <NavLink to="/subscriptions" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
            Subscriptions
          </NavLink>
          <NavLink to="/runs" className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}>
            Research Runs
          </NavLink>
        </nav>
        <div className="sidebar-footer">
          <div>{user?.display_name || user?.email}</div>
          <button className="btn" style={{ marginTop: "0.75rem" }} onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
