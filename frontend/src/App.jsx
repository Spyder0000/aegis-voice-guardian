import React from "react";
import { BrowserRouter, Routes, Route, useNavigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Landing from "./pages/Landing";

function LandingWrapper() {
  const navigate = useNavigate();
  return <Landing onOpenDashboard={() => navigate("/dashboard")} />;
}

function DashboardWrapper() {
  const navigate = useNavigate();
  return <Dashboard onBackHome={() => navigate("/")} />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingWrapper />} />
        <Route path="/dashboard" element={<DashboardWrapper />} />
      </Routes>
    </BrowserRouter>
  );
}