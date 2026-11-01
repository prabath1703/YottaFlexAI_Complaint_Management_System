import { useEffect, useState } from "react";
import api from "../services/api";

export default function Reports() {
  const [teamData, setTeamData] = useState([]);
  const [datasets, setDatasets] = useState(null);
  const [loading, setLoading] = useState(false);
  const [datasetsLoading, setDatasetsLoading] = useState(false);
  const [downloading, setDownloading] = useState("");
  const [error, setError] = useState("");

  // Download CSV report or generated dataset
  const downloadReport = async (endpoint, filename) => {
    try {
      setError("");
      setDownloading(filename);

      const response = await api.get(endpoint, {
        responseType: "blob",
      });

      const url = window.URL.createObjectURL(
        new Blob([response.data], { type: "text/csv" })
      );

      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Unable to download ${filename}. Please try again.`);
    } finally {
      setDownloading("");
    }
  };

  // Load generated dataset information
  const loadDatasets = async () => {
    try {
      setDatasetsLoading(true);
      setError("");

      const response = await api.get("/reports/datasets");
      setDatasets(response.data);
    } catch (err) {
      setError("Unable to load generated dataset information.");
    } finally {
      setDatasetsLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  // Load team performance
  const loadTeamPerformance = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await api.get("/reports/team-performance");
      setTeamData(response.data);
    } catch (err) {
      setError("Unable to load team performance.");
    } finally {
      setLoading(false);
    }
  };

  const datasetFiles = datasets?.datasets || [];

  return (
    <div className="reports-page">
      <h2>Reports & Analytics</h2>
      <p>Download operational reports and review team assignments.</p>

      {error && <p className="action-error">{error}</p>}

      {/* EXISTING OPERATIONAL REPORTS */}

      <div className="report-cards">
        <div className="report-card">
          <h3>Complaint Report</h3>
          <p>Export complaint IDs, categories, priorities and statuses.</p>
          <button
            onClick={() =>
              downloadReport(
                "/reports/complaints.csv",
                "complaint_report.csv"
              )
            }
            disabled={downloading === "complaint_report.csv"}
          >
            {downloading === "complaint_report.csv"
              ? "Downloading..."
              : "Download CSV"}
          </button>
        </div>

        <div className="report-card">
          <h3>SLA Breach Report</h3>
          <p>Export breached SLA deadlines and elapsed durations.</p>
          <button
            onClick={() =>
              downloadReport(
                "/reports/sla-breaches.csv",
                "sla_breach_report.csv"
              )
            }
            disabled={downloading === "sla_breach_report.csv"}
          >
            {downloading === "sla_breach_report.csv"
              ? "Downloading..."
              : "Download CSV"}
          </button>
        </div>

        <div className="report-card">
          <h3>Team Performance</h3>
          <p>Review active complaint assignments by team and agent.</p>
          <button onClick={loadTeamPerformance} disabled={loading}>
            {loading ? "Loading..." : "View Performance"}
          </button>
        </div>
      </div>

      {/* GENERATED DATASET INFORMATION */}

      <section className="team-performance">
        <h3>Dataset Information</h3>

        <p>
          Generated synthetic datasets used by the Complaint Management
          System.
        </p>

        {datasetsLoading ? (
          <p>Loading dataset information...</p>
        ) : datasets ? (
          <>
            <div className="overview-grid">
              <div>
                <strong>Dataset Type</strong>
                <p>{datasets.dataset_type}</p>
              </div>

              <div>
                <strong>Random Seed</strong>
                <p>{datasets.seed}</p>
              </div>

              <div>
                <strong>Available CSV Files</strong>
                <p>{datasets.files_available}</p>
              </div>

              <div>
                <strong>Reproducibility Check</strong>
                <p>
                  {datasets.reproducibility?.verified
                    ? "Passed"
                    : "Not verified"}
                </p>
              </div>

              <div>
                <strong>Verification Runs</strong>
                <p>{datasets.reproducibility?.runs ?? "—"}</p>
              </div>

              <div>
                <strong>Matching Checksums</strong>
                <p>
                  {datasets.reproducibility?.matching_files ?? "—"}
                </p>
              </div>
            </div>

            {/* INDIVIDUAL DATASET DOWNLOADS */}

            <h3>Generated Dataset Downloads</h3>

            {datasetFiles.length === 0 ? (
              <p>No generated CSV files are currently available.</p>
            ) : (
              <div className="report-cards">
                {datasetFiles.map((file) => (
                  <div className="report-card" key={file.filename}>
                    <h3>{file.filename}</h3>

                    <p>
                      File size:{" "}
                      {(file.size_bytes / 1024).toFixed(2)} KB
                    </p>

                    <button
                      onClick={() =>
                        downloadReport(
                          `/reports/datasets/${encodeURIComponent(
                            file.filename
                          )}`,
                          file.filename
                        )
                      }
                      disabled={downloading === file.filename}
                    >
                      {downloading === file.filename
                        ? "Downloading..."
                        : "Download CSV"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </>
        ) : (
          <p>Dataset information is unavailable.</p>
        )}
      </section>

      {/* EXISTING TEAM PERFORMANCE TABLE */}

      {teamData.length > 0 && (
        <div className="team-performance">
          <h3>Active Team Assignments</h3>

          <table>
            <thead>
              <tr>
                <th>Team</th>
                <th>Assigned Complaints</th>
                <th>Agents</th>
              </tr>
            </thead>

            <tbody>
              {teamData.map((team) => (
                <tr key={team.team}>
                  <td>{team.team}</td>
                  <td>{team.assigned_complaints}</td>
                  <td>
                    {Object.entries(team.agents)
                      .map(([agent, count]) => `${agent}: ${count}`)
                      .join(", ")}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}