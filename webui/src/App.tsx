
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import UnmatchedAnalyzer from './pages/UnmatchedAnalyzer';
import MismatchAnalyzer from './pages/MismatchAnalyzer';
import BrushSplitValidator from './pages/BrushSplitValidator';
import MessageDisplay from './components/MessageDisplay';
import { useMessaging } from './hooks/useMessaging';
import './App.css';

function App() {
    const messaging = useMessaging();

    return (
        <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <div className="App">
                <Header />
                <main className="min-h-screen bg-gray-50">
                    <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/unmatched" element={<UnmatchedAnalyzer />} />
                        <Route path="/mismatch" element={<MismatchAnalyzer />} />
                        <Route path="/brush-split-validator" element={<BrushSplitValidator />} />
                    </Routes>
                </main>
                <MessageDisplay
                    messages={messaging.messages}
                    onRemoveMessage={messaging.removeMessage}
                />
            </div>
        </Router>
    );
}

export default App; 