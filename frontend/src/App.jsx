
import ComplaintActions from "./components/ComplaintActions";
import SLAControls from "./components/SLAControls";
import AssignmentControls from "./components/AssignmentControls";
import Reports from "./components/Reports";
import { useEffect, useState } from "react";

import {
  getComplaints,
  getAnalytics,
  getSLAClocks,
  getComplaint,
  getComplaintHistory,
  updateComplaintStatus,
  createComplaint,
} from "./services/api";

import {
  LayoutDashboard,
  MessageSquare,
  Clock,
  AlertTriangle,
  RefreshCw,
  Search,
  ChevronLeft,
  ChevronRight,
  X,
} from "lucide-react";

import "./index.css";

function App() {
  const [page, setPage] = useState("Dashboard");

  const [complaints, setComplaints] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [slaClocks, setSlaClocks] = useState([]);

  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [selectedHistory, setSelectedHistory] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [skip, setSkip] = useState(0);

  const [statusDraft, setStatusDraft] = useState("");
  const [updatingStatus, setUpdatingStatus] = useState(false);

  const limit = 20;

  // ----------------------------------
  // ERROR MESSAGE HELPER
  // ----------------------------------

  const getErrorMessage = (err, fallback) => {
    const detail = err.response?.data?.detail;

    if (typeof detail === "string") return detail;

    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg).join(", ");
    }

    return fallback;
  };

  // ----------------------------------
  // LOAD DASHBOARD ANALYTICS
  // ----------------------------------

  const loadDashboard = async () => {
    try {
      setError("");

      const [analyticsRes, slaRes] = await Promise.all([
        getAnalytics(),
        getSLAClocks(),
      ]);

      setAnalytics(analyticsRes.data);

      const slaData = slaRes.data;

      setSlaClocks(
        Array.isArray(slaData)
          ? slaData
          : slaData?.items || slaData?.sla_clocks || []
      );
    } catch (err) {
      setError(
        getErrorMessage(err, "Unable to load dashboard information.")
      );
    }
  };

  // ----------------------------------
  // LOAD COMPLAINTS
  // ----------------------------------

  const loadComplaints = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await getComplaints({
        skip,
        limit,
        search: search || undefined,
        status: status || undefined,
        priority: priority || undefined,
      });

      const data = response.data;

      setComplaints(
        Array.isArray(data)
          ? data
          : data?.items || data?.complaints || []
      );
    } catch (err) {
      setError(
        getErrorMessage(err, "Unable to load complaints.")
      );

      setComplaints([]);
    } finally {
      setLoading(false);
    }
  };

  // ----------------------------------
  // INITIAL DASHBOARD LOAD
  // ----------------------------------

  useEffect(() => {
    loadDashboard();
  }, []);

  // ----------------------------------
  // LOAD COMPLAINTS WHEN PAGE/FILTERS CHANGE
  // ----------------------------------

  useEffect(() => {
    if (page === "Complaints" || page === "Priority Queue") {
      loadComplaints();
    }
  }, [page, skip, status, priority]);

  // ----------------------------------
  // OPEN COMPLAINT DETAILS + HISTORY
  // ----------------------------------

  const openComplaint = async (id) => {
    try {
      setError("");

      const [complaintRes, historyRes] = await Promise.all([
        getComplaint(id),
        getComplaintHistory(id),
      ]);

      setSelectedComplaint(complaintRes.data);

      setSelectedHistory(
        Array.isArray(historyRes.data)
          ? historyRes.data
          : historyRes.data?.items || []
      );

      setStatusDraft(complaintRes.data.status || "OPEN");
    } catch (err) {
      setError(
        getErrorMessage(err, "Could not load complaint details.")
      );
    }
  };

  // ----------------------------------
  // UPDATE COMPLAINT STATUS
  // ----------------------------------

  const handleStatusUpdate = async () => {
    if (!selectedComplaint || !statusDraft) return;

    try {
      setUpdatingStatus(true);
      setError("");

      await updateComplaintStatus(
        selectedComplaint.complaint_id,
        {
          status: statusDraft,
          performed_by: "OPERATIONS_USER",
        }
      );

      const [complaintRes, historyRes] = await Promise.all([
        getComplaint(selectedComplaint.complaint_id),
        getComplaintHistory(selectedComplaint.complaint_id),
      ]);

      setSelectedComplaint(complaintRes.data);

      setSelectedHistory(
        Array.isArray(historyRes.data)
          ? historyRes.data
          : historyRes.data?.items || []
      );

      setStatusDraft(complaintRes.data.status || "OPEN");

      await loadDashboard();

      if (page === "Complaints" || page === "Priority Queue") {
        await loadComplaints();
      }
    } catch (err) {
      setError(
        getErrorMessage(err, "Unable to update complaint status.")
      );
    } finally {
      setUpdatingStatus(false);
    }
  };

  // ----------------------------------
  // NAVIGATION
  // ----------------------------------

  const goTo = (nextPage) => {
    setPage(nextPage);

    setSelectedComplaint(null);
    setSelectedHistory([]);

    setSkip(0);
    setStatus("");
    setPriority("");
    setSearch("");
  };

  // ----------------------------------
  // SEARCH
  // ----------------------------------

  const searchComplaints = (event) => {
    event.preventDefault();
    setSkip(0);
    loadComplaints();
  };

  // ----------------------------------
  // REFRESH
  // ----------------------------------

  const refreshPage = () => {
    loadDashboard();

    if (page === "Complaints" || page === "Priority Queue") {
      loadComplaints();
    }
  };

  // ----------------------------------
  // DASHBOARD VALUES
  // ----------------------------------

  const total = analytics?.total_complaints || 0;

  const byStatus = analytics?.by_status || {};
  const byPriority = analytics?.by_priority || {};
  const byCategory = analytics?.by_category || {};

  const resolutionMetrics = analytics?.resolution_metrics || {};
  const slaMetrics = analytics?.sla_metrics || {};
  const teamWorkload = analytics?.team_workload || {};

  const resolutionRate = resolutionMetrics.resolution_rate || 0;
  const slaComplianceRate = slaMetrics.sla_compliance_rate || 0;
  const resolvedCount = resolutionMetrics.resolved_complaints || 0;
  const completedSLA = slaMetrics.completed_sla || 0;

  const breachedCount = slaClocks.filter(
    (s) => (s.sla_status || "").toUpperCase() === "BREACHED"
  ).length;

  const priorityQueue = page === "Priority Queue";

  // ----------------------------------
  // MAIN UI
  // ----------------------------------

  return (
    <div className="app">

      {/* SIDEBAR */}

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">Y</div>

          <div>
            <h2>YottaFlexAI</h2>
            <span>Complaint Management</span>
          </div>
        </div>

        <nav>

          <NavItem
            icon={<LayoutDashboard size={19} />}
            label="Dashboard"
            active={page === "Dashboard"}
            onClick={() => goTo("Dashboard")}
          />

          <NavItem
            icon={<MessageSquare size={19} />}
            label="Complaints"
            active={page === "Complaints"}
            onClick={() => goTo("Complaints")}
          />

          <NavItem
            icon={<Clock size={19} />}
            label="SLA Monitoring"
            active={page === "SLA Monitoring"}
            onClick={() => goTo("SLA Monitoring")}
          />

          <NavItem
            icon={<AlertTriangle size={19} />}
            label="Priority Queue"
            active={page === "Priority Queue"}
            onClick={() => goTo("Priority Queue")}
          />

          <NavItem
            icon={<LayoutDashboard size={19} />}
            label="Reports & Analytics"
            active={page === "Reports"}
            onClick={() => goTo("Reports")}
          />

        </nav>

        <div className="sidebar-footer">
          Complaint Operations Platform
          <span>Development Environment</span>
        </div>

      </aside>

      {/* MAIN CONTENT */}

      <main className="main">

        {/* TOP HEADER */}

        <header className="topbar">

          <div>
            <h1>{page}</h1>

            <p>
              {page === "Dashboard"
                ? "Monitor complaint operations and performance."
                : page === "Complaints"
                ? "Search, filter and inspect customer complaints."
                : page === "Priority Queue"
                ? "Review urgent and high-priority complaints."
                : page === "Create Complaint"
                ? "Register a new customer complaint."
                : page === "Reports"
                ? "Download operational reports and review team assignments."
                : "Monitor service-level agreements and breaches."}
            </p>
          </div>

          <div className="topbar-actions">

            <button
              className="primary-btn"
              onClick={() => {
                setError("");
                setSelectedComplaint(null);
                setPage("Create Complaint");
              }}
            >
              + New Complaint
            </button>

            <button className="refresh-btn" onClick={refreshPage}>
              <RefreshCw size={16} />
              Refresh
            </button>

          </div>

        </header>

        {/* ERROR MESSAGE */}

        {error && (
          <div className="error">
            <AlertTriangle size={17} />
            {error}
          </div>
        )}

        {/* CREATE COMPLAINT */}

        {page === "Create Complaint" && (
          <CreateComplaintForm
            onCancel={() => goTo("Complaints")}
            onCreated={() => {
              setSkip(0);
              setSearch("");
              setStatus("");
              setPriority("");
              setSelectedComplaint(null);
              setError("");
              setPage("Complaints");
              loadDashboard();
            }}
          />
        )}

        {/* DASHBOARD */}

        {page === "Dashboard" && (
          <>

            {/* KEY PERFORMANCE INDICATORS */}

            <section className="stats-grid">

              <StatCard
                title="Total Complaints"
                value={total}
              />

              <StatCard
                title="Open"
                value={byStatus.OPEN || 0}
              />

              <StatCard
                title="In Progress"
                value={byStatus.IN_PROGRESS || 0}
              />

              <StatCard
                title="Resolved"
                value={resolvedCount}
              />

              <StatCard
                title="High Priority (P1 + P2)"
                value={
                  (byPriority.P1 || 0) +
                  (byPriority.P2 || 0)
                }
              />

              <StatCard
                title="SLA Breached"
                value={slaMetrics.breached_sla ?? breachedCount}
              />

            </section>

            {/* PERFORMANCE METRICS */}

            <section className="stats-grid">

              <StatCard
                title="Resolution Rate"
                value={`${resolutionRate}%`}
              />

              <StatCard
                title="SLA Compliance"
                value={`${slaComplianceRate}%`}
              />

              <StatCard
                title="Completed SLA"
                value={completedSLA}
              />

            </section>

            {/* COMPLAINT ANALYTICS */}

            <section className="panel">

              <div className="panel-heading">

                <div>
                  <h2>Complaint Analytics</h2>
                  <p>
                    Operational distribution and performance metrics
                  </p>
                </div>

              </div>

              <div className="overview-grid">

                <div>
                  <h3>By Priority</h3>

                  {Object.entries(byPriority).map(
                    ([key, value]) => (
                      <div className="overview-row" key={key}>
                        <span>{key}</span>
                        <strong>{value}</strong>
                      </div>
                    )
                  )}

                  {Object.keys(byPriority).length === 0 && (
                    <p className="message">No priority data available.</p>
                  )}
                </div>

                <div>
                  <h3>By Status</h3>

                  {Object.entries(byStatus).map(
                    ([key, value]) => (
                      <div className="overview-row" key={key}>
                        <span>{key.replaceAll("_", " ")}</span>
                        <strong>{value}</strong>
                      </div>
                    )
                  )}

                  {Object.keys(byStatus).length === 0 && (
                    <p className="message">No status data available.</p>
                  )}
                </div>

                <div>
                  <h3>By Category</h3>

                  {Object.entries(byCategory).map(
                    ([key, value]) => (
                      <div className="overview-row" key={key}>
                        <span>{key}</span>
                        <strong>{value}</strong>
                      </div>
                    )
                  )}

                  {Object.keys(byCategory).length === 0 && (
                    <p className="message">No category data available.</p>
                  )}
                </div>

                <div>
                  <h3>Team Workload</h3>

                  {Object.entries(teamWorkload).map(
                    ([key, value]) => (
                      <div className="overview-row" key={key}>
                        <span>{key.replaceAll("_", " ")}</span>
                        <strong>{value}</strong>
                      </div>
                    )
                  )}

                  {Object.keys(teamWorkload).length === 0 && (
                    <p className="message">No team workload data available.</p>
                  )}
                </div>

              </div>

              <button
                className="primary-btn"
                onClick={() => goTo("Complaints")}
              >
                View all complaints
              </button>

            </section>

          </>
        )}

        {/* COMPLAINTS + PRIORITY QUEUE */}

        {(page === "Complaints" || priorityQueue) && (

          <section className="panel">

            <div className="panel-heading">

              <div>
                <h2>
                  {priorityQueue ? "Priority Queue" : "All Complaints"}
                </h2>

                <p>
                  {priorityQueue
                    ? "P1 and P2 complaints requiring attention"
                    : "Browse and inspect complaint records"}
                </p>
              </div>

            </div>

            {/* FILTERS */}

            <form
              className="filters"
              onSubmit={searchComplaints}
            >

              <div className="search-box">
                <Search size={17} />

                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search complaint ID..."
                />
              </div>

              {!priorityQueue && (
                <select
                  value={status}
                  onChange={(e) => {
                    setStatus(e.target.value);
                    setSkip(0);
                  }}
                >
                  <option value="">All statuses</option>
                  <option value="OPEN">Open</option>
                  <option value="IN_PROGRESS">In Progress</option>
                  <option value="RESOLVED">Resolved</option>
                  <option value="CLOSED">Closed</option>
                  <option value="REOPENED">Reopened</option>
                </select>
              )}

              <select
                value={priority}
                onChange={(e) => {
                  setPriority(e.target.value);
                  setSkip(0);
                }}
              >
                <option value="">All priorities</option>
                <option value="P1">P1 - Critical</option>
                <option value="P2">P2 - High</option>

                {!priorityQueue && (
                  <>
                    <option value="P3">P3 - Medium</option>
                    <option value="P4">P4 - Low</option>
                  </>
                )}
              </select>

              <button className="primary-btn" type="submit">
                Search
              </button>

            </form>

            {/* COMPLAINT TABLE */}

            {loading ? (

              <p className="message">Loading complaints...</p>

            ) : complaints.length === 0 ? (

              <p className="message">
                No matching complaints found.
              </p>

            ) : (

              <>

                <ComplaintTable
                  complaints={
                    priorityQueue
                      ? complaints.filter((c) =>
                          ["P1", "P2"].includes(c.priority)
                        )
                      : complaints
                  }
                  onOpen={openComplaint}
                />

                {/* PAGINATION */}

                <div className="pagination">

                  <button
                    disabled={skip === 0}
                    onClick={() =>
                      setSkip(Math.max(0, skip - limit))
                    }
                  >
                    <ChevronLeft size={16} />
                    Previous
                  </button>

                  <span>
                    Showing {skip + 1}–{skip + complaints.length}
                  </span>

                  <button
                    disabled={complaints.length < limit}
                    onClick={() => setSkip(skip + limit)}
                  >
                    Next
                    <ChevronRight size={16} />
                  </button>

                </div>

              </>

            )}

          </section>

        )}

        {/* SLA MONITORING */}

        {page === "SLA Monitoring" && (

          <section className="panel">

            <div className="panel-heading">

              <div>
                <h2>SLA Clocks</h2>
                <p>Current SLA records returned by the backend</p>
              </div>

            </div>

            <div className="stats-grid">

              <StatCard
                title="Total SLA Records"
                value={slaClocks.length}
              />

              <StatCard
                title="Breached"
                value={breachedCount}
              />

              <StatCard
                title="Paused"
                value={
                  slaClocks.filter(
                    (s) => (s.sla_status || "").toUpperCase() === "PAUSED"
                  ).length
                }
              />

            </div>

            <div className="table-wrapper">

              <table>

                <thead>
                  <tr>
                    <th>SLA ID</th>
                    <th>Complaint ID</th>
                    <th>Priority</th>
                    <th>Deadline</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>

                  {slaClocks.length === 0 ? (

                    <tr>
                      <td colSpan="5">No SLA records found.</td>
                    </tr>

                  ) : (

                    slaClocks.map((s) => (

                      <tr key={s.sla_id}>
                        <td>{s.sla_id}</td>
                        <td>{s.complaint_id}</td>
                        <td>{s.priority}</td>

                        <td>
                          {s.sla_deadline
                            ? new Date(s.sla_deadline).toLocaleString()
                            : "—"}
                        </td>

                        <td>{s.sla_status || "—"}</td>
                      </tr>

                    ))

                  )}

                </tbody>

              </table>

            </div>

          </section>

        )}

        {/* REPORTS & ANALYTICS */}

        {page === "Reports" && <Reports />}

      </main>

      {/* COMPLAINT DETAILS MODAL */}

      {selectedComplaint && (

        <div
          className="modal-backdrop"
          onClick={() => setSelectedComplaint(null)}
        >

          <div
            className="detail-modal"
            onClick={(e) => e.stopPropagation()}
          >

            {/* MODAL HEADER */}

            <div className="modal-heading">

              <div>
                <h2>Complaint Details</h2>
                <p>{selectedComplaint.complaint_id}</p>
              </div>

              <button
                className="close-btn"
                onClick={() => setSelectedComplaint(null)}
              >
                <X size={20} />
              </button>

            </div>

            {/* COMPLAINT INFORMATION */}

            <Detail
              label="Category"
              value={selectedComplaint.category}
            />

            <Detail
              label="Priority"
              value={selectedComplaint.priority}
            />

            <Detail
              label="Customer ID"
              value={selectedComplaint.customer_id}
            />

            <Detail
              label="Order ID"
              value={selectedComplaint.order_id}
            />

            <Detail
              label="Product ID"
              value={selectedComplaint.product_id}
            />

            <Detail
              label="Channel"
              value={selectedComplaint.channel}
            />

            <Detail
              label="Created At"
              value={
                selectedComplaint.created_at
                  ? new Date(
                      selectedComplaint.created_at
                    ).toLocaleString()
                  : "—"
              }
            />

            <div className="detail-description">
              <strong>Description</strong>

              <p>
                {selectedComplaint.description ||
                  "No description available."}
              </p>
            </div>

            {/* STATUS UPDATE */}

            <div className="status-editor">

              <h3>Update Complaint Status</h3>

              <select
                value={statusDraft}
                onChange={(e) => setStatusDraft(e.target.value)}
              >
                <option value="OPEN">Open</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="RESOLVED">Resolved</option>
                <option value="CLOSED">Closed</option>
                <option value="REOPENED">Reopened</option>
              </select>

              <button
                className="primary-btn"
                onClick={handleStatusUpdate}
                disabled={
                  updatingStatus ||
                  statusDraft === selectedComplaint.status
                }
              >
                {updatingStatus ? "Updating..." : "Save Status"}
              </button>

            </div>

            {/* ACTIVITY HISTORY */}

            <div className="history-section">

              <h3>Complaint Activity History</h3>

              {selectedHistory.length === 0 ? (

                <p className="message">
                  No activity history available.
                </p>

              ) : (

                selectedHistory.map((event) => (

                  <div
                    className="history-item"
                    key={event.event_id}
                  >

                    <div className="history-dot" />

                    <div>

                      <strong>
                        {event.event_type?.replaceAll("_", " ")}
                      </strong>

                      <p>
                        {event.from_status || "NEW"}
                        {" → "}
                        {event.to_status || "—"}
                      </p>

                      <span>
                        {event.event_time
                          ? new Date(
                              event.event_time
                            ).toLocaleString()
                          : "Time unavailable"}
                      </span>

                      <small>
                        By: {event.performed_by || "Unknown"}
                      </small>

                    </div>

                  </div>

                ))

              )}

            </div>

            {/* CUSTOMER MESSAGES AND RESOLUTIONS */}

            <ComplaintActions
              complaintId={selectedComplaint.complaint_id}
            />

            <SLAControls
              complaintId={selectedComplaint.complaint_id}
            />

            <AssignmentControls
              complaintId={selectedComplaint.complaint_id}
              safetyIssue={selectedComplaint.safety_issue_flag}
              category={selectedComplaint.category}
            />

          </div>

        </div>

      )}

    </div>
  );
}

// ----------------------------------
// SIDEBAR NAVIGATION ITEM
// ----------------------------------

function NavItem({ icon, label, active, onClick }) {
  return (
    <button
      className={`nav-item ${active ? "active" : ""}`}
      onClick={onClick}
    >
      {icon}
      {label}
    </button>
  );
}

// ----------------------------------
// DASHBOARD STAT CARD
// ----------------------------------

function StatCard({ title, value }) {
  return (
    <div className="stat-card">
      <span>{title}</span>
      <strong>{value}</strong>
    </div>
  );
}

// ----------------------------------
// COMPLAINT TABLE
// ----------------------------------

function ComplaintTable({ complaints, onOpen }) {
  return (
    <div className="table-wrapper">

      <table>

        <thead>
          <tr>
            <th>Complaint ID</th>
            <th>Category</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Created At</th>
            <th>Action</th>
          </tr>
        </thead>

        <tbody>

          {complaints.map((c) => (

            <tr key={c.complaint_id}>

              <td className="complaint-id">
                {c.complaint_id}
              </td>

              <td>{c.category || "—"}</td>

              <td>
                <span
                  className={`priority ${(c.priority || "").toLowerCase()}`}
                >
                  {c.priority || "—"}
                </span>
              </td>

              <td>
                {(c.status || "—").replaceAll("_", " ")}
              </td>

              <td>
                {c.created_at
                  ? new Date(c.created_at).toLocaleDateString()
                  : "—"}
              </td>

              <td>
                <button
                  className="view-btn"
                  onClick={() => onOpen(c.complaint_id)}
                >
                  View
                </button>
              </td>

            </tr>

          ))}

        </tbody>

      </table>

    </div>
  );
}

// ----------------------------------
// COMPLAINT DETAIL ROW
// ----------------------------------

function Detail({ label, value }) {
  return (
    <div className="detail-row">
      <span>{label}</span>
      <strong>{value || "—"}</strong>
    </div>
  );
}

// ----------------------------------
// CREATE COMPLAINT FORM
// ----------------------------------

function CreateComplaintForm({ onCancel, onCreated }) {
  const [form, setForm] = useState({
    customer_id: "",
    order_id: "",
    product_id: "",
    channel: "WEB",
    description: "",
    category_id: "",
    category: "",
    severity: "MEDIUM",
    sentiment: "NEUTRAL",
    repeat_complaint_flag: false,
    related_complaint_id: "",
    safety_issue_flag: false,
    priority: "P3",
    status: "OPEN",
  });

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const updateField = (field, value) => {
    setForm((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    try {
      setSaving(true);
      setError("");

      const payload = {
        ...form,
        order_id: form.order_id || null,
        product_id: form.product_id || null,
        sentiment: form.sentiment || null,
        related_complaint_id: form.related_complaint_id || null,
      };

      await createComplaint(payload);

      onCreated();
    } catch (err) {
      const detail = err.response?.data?.detail;

      setError(
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
          ? detail.map((item) => item.msg).join(", ")
          : "Unable to create complaint. Check the entered details."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="panel create-form-panel">

      <div className="panel-heading">
        <div>
          <h2>Create New Complaint</h2>
          <p>Register a customer complaint in the system.</p>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <form onSubmit={handleSubmit} className="create-form">

        <div className="form-grid">

          <label>
            Customer ID *
            <input
              required
              value={form.customer_id}
              placeholder="CUS-000001"
              onChange={(e) =>
                updateField("customer_id", e.target.value)
              }
            />
          </label>

          <label>
            Order ID
            <input
              value={form.order_id}
              placeholder="ORD-2026-000001"
              onChange={(e) =>
                updateField("order_id", e.target.value)
              }
            />
          </label>

          <label>
            Product ID
            <input
              value={form.product_id}
              placeholder="Enter product ID"
              onChange={(e) =>
                updateField("product_id", e.target.value)
              }
            />
          </label>

          <label>
            Channel *
            <select
              value={form.channel}
              onChange={(e) =>
                updateField("channel", e.target.value)
              }
            >
              <option value="WEB">Web</option>
              <option value="EMAIL">Email</option>
              <option value="PHONE">Phone</option>
              <option value="CHAT">Chat</option>
            </select>
          </label>

          <label>
            Category ID *
            <input
              required
              value={form.category_id}
              placeholder="Enter existing category ID"
              onChange={(e) =>
                updateField("category_id", e.target.value)
              }
            />
          </label>

          <label>
            Category Name *
            <input
              required
              value={form.category}
              placeholder="e.g. DELIVERY"
              onChange={(e) =>
                updateField("category", e.target.value)
              }
            />
          </label>

          <label>
            Severity *
            <select
              value={form.severity}
              onChange={(e) =>
                updateField("severity", e.target.value)
              }
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </label>

          <label>
            Priority *
            <select
              value={form.priority}
              onChange={(e) =>
                updateField("priority", e.target.value)
              }
            >
              <option value="P1">P1 - Critical</option>
              <option value="P2">P2 - High</option>
              <option value="P3">P3 - Medium</option>
              <option value="P4">P4 - Low</option>
            </select>
          </label>

          <label>
            Sentiment
            <select
              value={form.sentiment}
              onChange={(e) =>
                updateField("sentiment", e.target.value)
              }
            >
              <option value="NEUTRAL">Neutral</option>
              <option value="POSITIVE">Positive</option>
              <option value="NEGATIVE">Negative</option>
            </select>
          </label>

          <label>
            Related Complaint ID
            <input
              value={form.related_complaint_id}
              placeholder="Optional"
              onChange={(e) =>
                updateField("related_complaint_id", e.target.value)
              }
            />
          </label>

        </div>

        <label className="full-width-field">
          Complaint Description *
          <textarea
            required
            minLength={5}
            rows={4}
            value={form.description}
            placeholder="Describe the customer's complaint..."
            onChange={(e) =>
              updateField("description", e.target.value)
            }
          />
        </label>

        <div className="form-checkboxes">

          <label>
            <input
              type="checkbox"
              checked={form.repeat_complaint_flag}
              onChange={(e) =>
                updateField("repeat_complaint_flag", e.target.checked)
              }
            />
            Repeat Complaint
          </label>

          <label>
            <input
              type="checkbox"
              checked={form.safety_issue_flag}
              onChange={(e) =>
                updateField("safety_issue_flag", e.target.checked)
              }
            />
            Safety Issue
          </label>

        </div>

        <div className="form-actions">

          <button
            type="button"
            className="refresh-btn"
            onClick={onCancel}
          >
            Cancel
          </button>

          <button
            type="submit"
            className="primary-btn"
            disabled={saving}
          >
            {saving ? "Creating..." : "Create Complaint"}
          </button>

        </div>

      </form>

    </section>
  );
}

export default App;
