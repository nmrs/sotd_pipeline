import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import BrushSplitValidator from './pages/BrushSplitValidator';
import UnmatchedAnalyzer from './pages/UnmatchedAnalyzer';
import PerformanceTest from './components/data/PerformanceTest';
import Header from './components/layout/Header';
import MessageDisplay from './components/feedback/MessageDisplay';
import { useMessaging } from './hooks/useMessaging';
import './App.css';

function App() {
  const messaging = useMessaging();

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className='h-screen flex flex-col'>
        <Header />
        <main className='flex-1 overflow-auto'>
          <Routes>
            <Route path='/' element={<Dashboard />} />
            <Route path='/brush-split-validator' element={<BrushSplitValidator />} />
            <Route path='/unmatched-analyzer' element={<UnmatchedAnalyzer />} />
            <Route path='/performance-test' element={<PerformanceTest />} />
          </Routes>
        </main>
        <MessageDisplay messages={messaging.messages} onRemoveMessage={messaging.removeMessage} />
      </div>
    </Router>
  );
}

export default App;
