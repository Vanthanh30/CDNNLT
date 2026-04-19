import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar/Sidebar";
import Header from "./components/Header/Header";
import Dashboard from "./pages/Dashboard/Dashboard";
import AnalyticsContent from "./pages/Analytics/AnalyticsContent";
import Reports from "./pages/Reports/ReportsContent";
import SearchContent from "./pages/Search/SearchContent";
import "./App.css";

function App() {
  return (
    <Router>
      <div className="dashboard-container">
        <Sidebar />
        <main className="main-content">
          <Header />
          <div className="content-body">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/analytics" element={<AnalyticsContent />} />
              <Route path="/reports" element={<Reports />} />
              <Route path="/search" element={<SearchContent />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
