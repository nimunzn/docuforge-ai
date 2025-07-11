import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import { DocumentWorkspace } from './components/DocumentWorkspace';
import { DocumentList } from './components/DocumentList';
import { Settings } from './components/Settings';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App h-full">
        <MainLayout>
          <Routes>
            <Route path="/" element={<DocumentList />} />
            <Route path="/document/:id" element={<DocumentWorkspace />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </MainLayout>
      </div>
    </Router>
  );
}

export default App;