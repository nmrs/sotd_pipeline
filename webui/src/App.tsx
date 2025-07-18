
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import UnmatchedAnalyzer from './pages/UnmatchedAnalyzer';
import MismatchAnalyzer from './pages/MismatchAnalyzer';
import './App.css';

function App() {
    return (
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <div className="App">
                <Header />
                <main className="min-h-screen bg-gray-50">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/unmatched" element={<UnmatchedAnalyzer />} />
                        <Route path="/mismatch" element={<MismatchAnalyzer />} />
                    </Routes>
                </main>
            </div>
        </Router>
    );
}

export default App; 