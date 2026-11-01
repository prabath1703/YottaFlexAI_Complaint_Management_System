
import { useEffect, useState } from "react";
import api from "../services/api";

const TEAM_AGENTS = {
  CUSTOMER_SUPPORT: ["CS-001", "CS-002", "CS-003", "CS-004"],
  LOGISTICS: ["LG-001", "LG-002", "LG-003"],
  PAYMENTS: ["PY-001", "PY-002", "PY-003"],
  REFUNDS: ["RF-001", "RF-002", "RF-003"],
  PRODUCT_SAFETY: ["PS-001", "PS-002"],
};

export default function AssignmentControls({
  complaintId,
  safetyIssue = false,
  category = "",
}) {
  const [assignments, setAssignments] = useState([]);
  const [team, setTeam] = useState("CUSTOMER_SUPPORT");
  const [agentId, setAgentId] = useState("CS-001");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const loadAssignments = async () => {
    try {
      setLoading(true);
      const response = await api.get(
        `/assignments/${complaintId}`
      );

      const data = response.data;
      const records = Array.isArray(data)
        ? data
        : data?.items || data?.assignments || [];

      setAssignments(records);

      const current =
        records.find((item) => !item.unassigned_at) ||
        records[records.length - 1];

      if (current) {
        setTeam(current.team);
        setAgentId(current.agent_id);
      } else if (safetyIssue) {
        setTeam("PRODUCT_SAFETY");
        setAgentId("PS-001");
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load assignment details."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssignments();
  }, [complaintId]);

  const handleTeamChange = (value) => {
    setTeam(value);
    setAgentId(TEAM_AGENTS[value][0]);
  };

  const handleAssign = async () => {
    try {
      setSaving(true);
      setError("");
      setSuccess("");

      await api.post(`/assignments/${complaintId}/assign`, {
        assigned_by: "OPERATIONS_USER",
        team,
        agent_id: agentId,
      });

      setSuccess("Complaint successfully assigned.");
      await loadAssignments();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to assign complaint."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="assignment-controls">
      <h3>Assignment Management</h3>

      {error && <p className="action-error">{error}</p>}
      {success && <p className="assignment-success">{success}</p>}

      {loading ? (
        <p>Loading assignments...</p>
      ) : (
        <>
          <h4>Current Assignment</h4>

          {assignments.length > 0 ? (
            (() => {
              const current =
                assignments.find((item) => !item.unassigned_at) ||
                assignments[assignments.length - 1];

              return (
                <div className="current-assignment">
                  <p><strong>Team:</strong> {current.team}</p>
                  <p><strong>Agent:</strong> {current.agent_id}</p>
                  <p>
                    <strong>Assigned At:</strong>{" "}
                    {current.assigned_at
                      ? new Date(current.assigned_at).toLocaleString()
                      : "—"}
                  </p>
                </div>
              );
            })()
          ) : (
            <p>No assignment history found.</p>
          )}

          <div className="assignment-form">
            <h4>Assign / Reassign Complaint</h4>

            <label>
              Select Team
              <select
                value={team}
                onChange={(e) => handleTeamChange(e.target.value)}
                disabled={safetyIssue}
              >
                {Object.keys(TEAM_AGENTS).map((name) => (
                  <option key={name} value={name}>
                    {name.replaceAll("_", " ")}
                  </option>
                ))}
              </select>
            </label>

            {safetyIssue && (
              <small>
                Safety complaints must remain with Product Safety.
              </small>
            )}

            <label>
              Select Agent
              <select
                value={agentId}
                onChange={(e) => setAgentId(e.target.value)}
              >
                {TEAM_AGENTS[team].map((agent) => (
                  <option key={agent} value={agent}>
                    {agent}
                  </option>
                ))}
              </select>
            </label>

            <button
              className="primary-btn"
              onClick={handleAssign}
              disabled={saving || loading}
            >
              {saving ? "Assigning..." : "Assign / Reassign"}
            </button>
          </div>

          <h4>Assignment History</h4>

          <div className="assignment-history">
            {assignments.length === 0 ? (
              <p>No assignment history available.</p>
            ) : (
              [...assignments].reverse().map((item, index) => (
                <div
                  className="assignment-history-item"
                  key={item.assignment_id || index}
                >
                  <strong>{item.team}</strong>
                  <p>Agent: {item.agent_id}</p>
                  <small>
                    {item.assigned_at
                      ? new Date(item.assigned_at).toLocaleString()
                      : "—"}
                  </small>
                  {item.unassigned_at && (
                    <small>
                      Reassigned:{" "}
                      {new Date(item.unassigned_at).toLocaleString()}
                    </small>
                  )}
                </div>
              ))
            )}
          </div>
        </>
      )}
    </section>
  );
}
