
import { useEffect, useState } from "react";
import api from "../services/api";

export default function SLAControls({ complaintId }) {
  const [sla, setSla] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadSLA = async () => {
    try {
      const response = await api.get(`/sla/${complaintId}`);
      setSla(response.data);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Could not load SLA.");
    }
  };

  useEffect(() => {
    loadSLA();
  }, [complaintId]);

  const performAction = async (action) => {
    setLoading(true);
    setError("");

    try {
      await api.post(`/sla/${complaintId}/${action}`, {
        performed_by: "AGENT",
      });
      await loadSLA();
    } catch (err) {
      setError(
        err.response?.data?.detail || `Could not ${action} SLA.`
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="sla-controls">
      <h3>SLA Management</h3>

      {error && <p className="action-error">{error}</p>}

      {sla && (
        <>
          <p><strong>Status:</strong> {sla.sla_status}</p>
          <p><strong>Priority:</strong> {sla.priority}</p>
          <p><strong>Deadline:</strong> {
            sla.sla_deadline
              ? new Date(sla.sla_deadline).toLocaleString()
              : "—"
          }</p>

          <div className="sla-buttons">
            {sla.sla_status === "ACTIVE" && (
              <button disabled={loading} onClick={() => performAction("pause")}>
                Pause SLA
              </button>
            )}

            {sla.sla_status === "PAUSED" && (
              <button disabled={loading} onClick={() => performAction("resume")}>
                Resume SLA
              </button>
            )}

            {["ACTIVE", "PAUSED"].includes(sla.sla_status) && (
              <button disabled={loading} onClick={() => performAction("complete")}>
                Complete SLA
              </button>
            )}
          </div>
        </>
      )}

      {!sla && !error && <p>Loading SLA details...</p>}
    </section>
  );
}
