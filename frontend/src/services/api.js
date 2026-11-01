
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
});

export const getComplaints = (params = {}) =>
  api.get("/complaints/", { params });

export const getComplaint = (id) =>
  api.get(`/complaints/${id}`);

export const getCustomers = (params = {}) =>
  api.get("/customers/", { params });

export const getAnalytics = () =>
  api.get("/analytics/summary");

export const getAssignments = () =>
  api.get("/assignments/");

export const getSLAClocks = () =>
  api.get("/sla/");

export const getComplaintHistory = (id) =>
  api.get(`/complaints/${id}/history`);

export const updateComplaintStatus = (id, payload) =>
  api.patch(`/complaints/${id}/status`, payload);

export const createComplaint = (payload) =>
  api.post("/complaints/", payload);

export default api;
