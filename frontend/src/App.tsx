import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';
import Dashboard from './components/Dashboard.tsx';
import AudioPlayer from './components/AudioPlayer.tsx';
import Header from './components/Header.tsx';

function App() {
  return (
    <Router>
      <div className="App">
        <Header />
        <main className="container mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/audio/:id" element={<AudioPlayer />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 