import React, { useState } from "react";
import Dashboard from "./pages/Dashboard";
import LandingPage from "./pages/LandingPage";

export default function App() {
  const [view, setView] = useState("landing");

  if (view === "dashboard") {
    return <Dashboard onBackHome={() => setView("landing")} />;
  }

  return <LandingPage onOpenDashboard={() => setView("dashboard")} />;
}