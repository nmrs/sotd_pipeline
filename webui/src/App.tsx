import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import BrushSplitValidator from './pages/BrushSplitValidator';
import BrushValidation from './pages/BrushValidation';
import UnmatchedAnalyzer from './pages/UnmatchedAnalyzer';
import PerformanceTest from './components/data/PerformanceTest';
import Header from './components/layout/Header';
import MessageDisplay from './components/feedback/MessageDisplay';
import { useMessaging } from './hooks/useMessaging';
import './App.css';
import MismatchAnalyzer from './pages/MismatchAnalyzer';
import CatalogValidator from './pages/CatalogValidator';
import SoapAnalyzer from './pages/SoapAnalyzer';

function App() {
  const messaging = useMessaging();

  return (
    <Router>
      <div className='h-screen flex flex-col'>
        <Header />
        <main className='flex-1 overflow-auto'>
          <Routes>
            <Route path='/' element={<Dashboard />} />
            <Route path='/brush-split-validator' element={<BrushSplitValidator />} />
            <Route path='/brush-validation' element={<BrushValidation />} />
            <Route path='/unmatched-analyzer' element={<UnmatchedAnalyzer />} />
            <Route path='/performance-test' element={<PerformanceTest />} />
            <Route path='/mismatch' element={<MismatchAnalyzer />} />
            <Route path='/catalog-validator' element={<CatalogValidator />} />
            <Route path='/soap-analyzer' element={<SoapAnalyzer />} />
          </Routes>
        </main>
        <MessageDisplay messages={messaging.messages} onRemoveMessage={messaging.removeMessage} />
      </div>
    </Router>
  );
}

export default App;
