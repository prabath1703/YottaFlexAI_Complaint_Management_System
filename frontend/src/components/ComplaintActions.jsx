import { useEffect, useState } from "react";
import api from "../services/api";

export default function ComplaintActions({ complaintId }) {
  const [messages, setMessages] = useState([]);
  const [resolutions, setResolutions] = useState([]);
  const [messageText, setMessageText] = useState("");
  const [resolutionType, setResolutionType] = useState("REFUND");
  const [resolutionDescription, setResolutionDescription] = useState("");
  const [resolvedBy, setResolvedBy] = useState("");
  const [refundAmount, setRefundAmount] = useState("0");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      const [messageRes, resolutionRes] = await Promise.all([
        api.get(`/messages/complaint/${complaintId}`),
        api.get(`/resolutions/complaint/${complaintId}`),
      ]);

      setMessages(messageRes.data);
      setResolutions(resolutionRes.data);
    } catch (err) {
      setError("Could not load messages or resolutions.");
    }
  };

  useEffect(() => {
    loadData();
  }, [complaintId]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!messageText.trim()) return;

    setLoading(true);
    setError("");

    try {
      await api.post(`/messages/complaint/${complaintId}`, {
        sender_type: "AGENT",
        message_text: messageText,
        channel: "WEB",
      });

      setMessageText("");
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to send message.");
    } finally {
      setLoading(false);
    }
  };

  const submitResolution = async (e) => {
    e.preventDefault();

    if (!resolutionDescription.trim() || !resolvedBy.trim()) {
      setError("Enter the resolution description and agent name.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      await api.post(`/resolutions/complaint/${complaintId}`, {
        resolution_type: resolutionType,
        resolution_description: resolutionDescription,
        resolved_by: resolvedBy,
        refund_amount: Number(refundAmount) || 0,
      });

      setResolutionDescription("");
      setRefundAmount("0");
      await loadData();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to save resolution.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="complaint-actions">
      <h3>Customer Communication</h3>

      {error && <p className="action-error">{error}</p>}

      <form onSubmit={sendMessage} className="action-form">
        <textarea
          value={messageText}
          onChange={(e) => setMessageText(e.target.value)}
          placeholder="Write a message or update..."
          rows={3}
        />
        <button type="submit" disabled={loading || !messageText.trim()}>
          Send Message
        </button>
      </form>

      <div className="message-list">
        {messages.length === 0 ? (
          <p>No messages recorded yet.</p>
        ) : (
          messages.map((message) => (
            <article className="message-item" key={message.message_id}>
              <strong>{message.sender_type}</strong>
              <p>{message.message_text}</p>
              <small>
                {message.channel} ·{" "}
                {new Date(message.message_time).toLocaleString()}
              </small>
            </article>
          ))
        )}
      </div>

      <hr />

      <h3>Resolution Management</h3>

      <form onSubmit={submitResolution} className="action-form">
        <label>Resolution type</label>
        <select
          value={resolutionType}
          onChange={(e) => setResolutionType(e.target.value)}
        >
          <option value="REFUND">Refund</option>
          <option value="REPLACEMENT">Replacement</option>
          <option value="REPAIR">Repair</option>
          <option value="INFORMATION">Information Provided</option>
          <option value="OTHER">Other</option>
        </select>

        <label>Resolution description</label>
        <textarea
          value={resolutionDescription}
          onChange={(e) => setResolutionDescription(e.target.value)}
          rows={3}
          placeholder="Describe how the complaint was resolved..."
        />

        <label>Resolved by</label>
        <input
          value={resolvedBy}
          onChange={(e) => setResolvedBy(e.target.value)}
          placeholder="Agent name or ID"
        />

        <label>Refund amount</label>
        <input
          type="number"
          min="0"
          step="0.01"
          value={refundAmount}
          onChange={(e) => setRefundAmount(e.target.value)}
        />

        <button type="submit" disabled={loading}>
          Save Resolution
        </button>
      </form>

      <div className="resolution-list">
        <h4>Resolution History</h4>
        {resolutions.length === 0 ? (
          <p>No resolutions recorded yet.</p>
        ) : (
          resolutions.map((resolution) => (
            <article
              className="message-item"
              key={resolution.resolution_id}
            >
              <strong>{resolution.resolution_type}</strong>
              <p>{resolution.resolution_description}</p>
              <small>
                By {resolution.resolved_by} ·{" "}
                {new Date(resolution.resolved_at).toLocaleString()}
                {" · "}Refund: {resolution.refund_amount ?? 0}
              </small>
            </article>
          ))
        )}
      </div>
    </section>
  );
}