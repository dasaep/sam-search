import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import OpportunityList from './components/OpportunityList';
import OpportunityDetail from './components/OpportunityDetail';
import CapabilityManager from './components/CapabilityManager';
import HighMatches from './components/HighMatches';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav className="navbar">
          <h1>SAM.gov Opportunity Analyzer</h1>
          <div className="nav-links">
            <Link to="/">Dashboard</Link>
            <Link to="/opportunities">Opportunities</Link>
            <Link to="/capabilities">Capabilities</Link>
            <Link to="/matches">High Matches</Link>
          </div>
        </nav>
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/opportunities" element={<OpportunityList />} />
            <Route path="/opportunities/:id" element={<OpportunityDetail />} />
            <Route path="/capabilities" element={<CapabilityManager />} />
            <Route path="/matches" element={<HighMatches />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;